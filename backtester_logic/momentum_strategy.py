import numpy as np
import pandas as pd
import heapq
import sqlite3
from tqdm import tqdm
from decouple import config

from utils import _ticker_to_table_name, _int_to_datetime

SLIPPAGE_FACTOR = float(config('SLIPPAGE_FACTOR'))

"""
TODO: Make an abstract Strategy class, require self.tickers, self.rebalance_period, and self.portfolio_construction()
"""


class QuantitativeMomentum():
    """This class systematizes the momentum strategy presented in 
    'Quantitative Momentum: A Practitioner's Guide to Building a Momentum-Based Stock Selection System'
    This class builds out an intermediate term momentum strategy (look back period of 12 months)
    with 3 month holding periods.

    Momentum is the 'total return of a stock over some particular look-back period' [pg 80]
    Momentum comes in two forms 
        1. Absolute Momentum: Performance relative to stock's past price over lookback period
        2. Cross-Sectional Momentum: Performance relative to other stock's in the market over lookback period

    The following parameters determine our strategy:

        1. Look back period 
        2. Portfolio Construction (number of stocks and rebalancing frequency) affects returns. 
        Typically less stocks and more rebalancing means higher CAGRs over the long run
        3. Lottery vs boring: compare if the stock made a gradually made gains or suddenly shot up.
        Gradual gains tend to preform better. This is measured by max daily return over last month
            TODO: Could also use Beta as a measure
        4. Momentum can be characterized as 'smooth' vs 'choppy' where we prefer smooth momentum. 
        Momentum is smoother if the stock had a higher percentage of up days vs down days 
        5. Seasonality: When do we rebalance in order to take advantage of window-dressing and tax-loss selling
            Smart Rebalance: Close of trading in Feb, May, Aug, and Nov
            Avg Rebalance: Close of trading in Jan, Apr, Jul, and Oct
            Dumb: Close of trading in Dec, Mar, Jun, and Sep

    Class will determine the n best stocks to invest in on a given date based on the momentum strategy
        1. Classify the stocks and find the top 10% generic momentum names
        2. Determine the FIP score and take the top self.firms_held of the screened list 
            FIP = sign(Past return) * [%positive - %negative]


    TODO: 
        1. Make an abstract Strategy class 
        2. Test! 
    """

    def __init__(self,
                 database_name: str,
                 tickers,
                 rebalance_period: int = 3,
                 look_back: int = 12,
                 lottery_window: int = 1,
                 firms_held: int = 50) -> None:

        self.connector = sqlite3.connect(database_name)
        self.cursor = self.connector.cursor()
        self.tickers = tickers
        self.universe_size = len(self.tickers)

        self.look_back = look_back
        self.lottery_window = lottery_window
        self.firms_held = firms_held
        self.rebalance_period = rebalance_period

    def validate_data(self):
        """For missing dates in our csv, we will append the data as the average of the above and below. 
        Otherwise we will add in a row of -1's to signify trading has halted"""

        query = f"""SELECT Date FROM {_ticker_to_table_name("GE.US")}"""
        equity_timeseries = pd.read_sql_query(query, self.connector)
        dates_len = len(equity_timeseries)

        tickers_missing_dates = []

        for ticker in tqdm(self.tickers['Ticker']):

            query = f"SELECT * from {_ticker_to_table_name(ticker)}"
            ticker_df = pd.read_sql_query(query, self.connector)

            if len(ticker_df) != dates_len:
                missing_dates = equity_timeseries[~equity_timeseries['Date'].isin(
                    ticker_df['Date'])].copy()

                for date in missing_dates['Date']:
                    row_above_index = ticker_df.index[ticker_df['Date'] > date].min(
                    )

                    if pd.notna(row_above_index):
                        prev_open, prev_high, prev_low, prev_close, prev_vol = ticker_df.loc[row_above_index - 1, [
                            'Open', 'High', 'Low', 'Close', 'Vol']]
                        next_open, next_high, next_low, next_close, next_vol = ticker_df.loc[row_above_index, [
                            'Open', 'High', 'Low', 'Close', 'Vol']]

                        def average(a, b): return (a + b) / 2

                        missing_date_row = {
                            'Ticker': ticker,
                            'Per': 'D',
                            'Date': date,  # fill this with the missing date
                            'Time': -1,
                            'Open': average(prev_open, next_open),
                            'High': average(prev_high, next_high),
                            'Low': average(prev_low, next_low),
                            'Close': average(prev_close, next_close),
                            'Vol': average(prev_vol, next_vol),
                            'Openint': 0,
                            'Return_12_Month': -1,
                            'Percent_Positive_Over_12_Months': -1,
                            'Percent_Negative_Over_12_Months': -1,
                        }
                    else:

                        missing_date_row = {
                            'Ticker': ticker,
                            'Per': 'D',
                            'Date': date,  # fill this with the missing date
                            'Time': -1,
                            'Open': -1,
                            'High': -1,
                            'Low': -1,
                            'Close': -1,
                            'Vol': -1,
                            'Openint': -1,
                            'Return_12_Month': -1,
                            'Percent_Positive_Over_12_Months': -1,
                            'Percent_Negative_Over_12_Months': -1,
                        }

                    ticker_df.loc[row_above_index - 0.5] = missing_date_row
                    ticker_df = ticker_df.sort_index().reset_index(drop=True)

                ticker_df.to_sql(_ticker_to_table_name(
                    ticker), self.connector, if_exists='replace', index=False)
                tickers_missing_dates.append(ticker)

        return tickers_missing_dates

    def compute_parameters(self) -> None:
        # TODO: FIX SO THAT ONLY NEW COLUMNS ADDED
        """Appends the following columns to each table in the Stock database 
            - Generic Momentum for x Months: Return over last self.lookback months
            - Percent Positive Days over x Months: The percent of positive return days over last self.lookback months
            -  Percent Negative_Days over x Months: The percent of negative return days over last self.lookback months
            """

        # 252 trading days in a year
        min_days = int((self.look_back / 12) * 252)

        for ticker in tqdm(self.tickers['Ticker']):
            current_table = pd.read_sql_query(
                f"""SELECT 
                *
                FROM {_ticker_to_table_name(ticker)}""",
                con=self.connector)

            num_of_dates = len(current_table)
            new_columns = pd.DataFrame({
                "Positive_Sum": np.zeros(num_of_dates),
                "Negative_Sum": np.zeros(num_of_dates),
                "Current_Return": np.zeros(num_of_dates),
                f"Return_{self.look_back}_Month": np.full(num_of_dates, -1),
                f"Percent_Positive_Over_{self.lottery_window}_Months": np.full(num_of_dates, -1),
                f"Percent_Negative_Over_{self.lottery_window}_Months": np.full(num_of_dates, -1)})

            total_days = 0

            for index, row in current_table.iterrows():
                if row['Close'] == -1:
                    pass
                elif total_days <= min_days:
                    # We hit a valid OHLC data point but have not gathered enough data to draw a data point
                    if index == 0:
                        total_days += 1
                    else:
                        total_days += 1
                        new_columns.loc[index,
                                        'Positive_Sum'] = new_columns.loc[index - 1, 'Positive_Sum']
                        new_columns.loc[index,
                                        'Negative_Sum'] = new_columns.loc[index - 1, 'Negative_Sum']
                        # If stock made a positive return
                        if row['Close'] > current_table.loc[index - 1, "Close"] and current_table.loc[index - 1, "Close"] != -1:
                            new_columns.loc[index, 'Positive_Sum'] += 1
                            new_columns.loc[index, 'Current_Return'] = 1
                        # If stock made a negative return
                        elif row['Close'] < current_table.loc[index - 1, "Close"]:
                            new_columns.loc[index, 'Negative_Sum'] += 1
                            new_columns.loc[index, 'Current_Return'] = -1
                else:
                    # Generic Momentum
                    new_columns.loc[index, f"Return_{self.look_back}_Month"] = (
                        row['Close'] / current_table.loc[index - min_days, "Close"]) - 1
                    positive_sum = new_columns.loc[index - 1, 'Positive_Sum']
                    negative_sum = new_columns.loc[index - 1, 'Negative_Sum']

                    # If the beginning of the look back period was positive,
                    # we need to remove that from our count
                    if new_columns.loc[index - min_days, "Current_Return"] == 1:
                        positive_sum -= 1
                    # If negative we have to remove that
                    elif new_columns.loc[index - min_days, "Current_Return"] == -1:
                        negative_sum -= 1

                    # If stock made a positive return
                    if row['Close'] > current_table.loc[index - 1, 'Close']:
                        positive_sum += 1
                        new_columns.loc[index, 'Current_Return'] = 1
                    # If stock made a negative return
                    elif row['Close'] < current_table.loc[index - 1, "Close"]:
                        negative_sum += 1
                        new_columns.loc[index, 'Current_Return'] = -1

                    # Necessary statistics
                    new_columns.loc[index, 'Positive_Sum'] = positive_sum
                    new_columns.loc[index, 'Negative_Sum'] = negative_sum

                    new_columns.loc[index,
                                    f"Percent_Positive_Over_{self.lottery_window}_Months"] = positive_sum / min_days
                    new_columns.loc[index,
                                    f"Percent_Negative_Over_{self.lottery_window}_Months"] = negative_sum / min_days

            # update sql table
            pd.merge(
                left=current_table,
                right=new_columns[[
                    f"Return_{self.look_back}_Month",
                    f"Percent_Positive_Over_{self.lottery_window}_Months",
                    f"Percent_Negative_Over_{self.lottery_window}_Months"]],
                left_index=True,
                right_index=True
            ).to_sql(_ticker_to_table_name(ticker), self.connector, if_exists='replace', index=False)

    def portfolio_construction(self, current_capital: int, date: int) -> tuple[list[tuple[str, int, float]], float]:
        """Returns the self.firm_size number of stocks that should be invested in for given date

        Parameters
        ----------
        current_capital : (int) representing the amount of cash currently available to invest
        date : (int) given as YYYYMMDD

        Returns
        --------
        portfolio : list[(ticker, shares_purcahsed, cost)] where each tuple represents an allocation into the ticker
                    buying shares_purchased amount at the next date open with slippage factor included in cost

        cash_left : (int) uninvested capital
        """

        generic_momentum_size = int(self.universe_size * 0.1)
        generic_momentum_screen = []

        def _fip_score(perc_return: float, perc_pos_days: float, perc_neg_days: float) -> float:
            return perc_return * (perc_pos_days - perc_neg_days)

        # Top 10% of generic momentum tickers
        for ticker in self.tickers['Ticker']:
            query = f"""SELECT 
            Return_{self.look_back}_Month,
            Percent_Positive_Over_{self.lottery_window}_Months, 
            Percent_Negative_Over_{self.lottery_window}_Months,
            OPEN
            FROM {_ticker_to_table_name(ticker)} 
            WHERE Date >= {date}
            ORDER BY Date
            LIMIT 2"""
            return_value = self.cursor.execute(query).fetchall()
            if return_value == []:
                pass
            elif return_value[0][0] == -1:
                pass
            else:
                generic_momentum, perc_pos, perc_neg, _ = return_value[0]
                next_open = return_value[1][3]
                heapq.heappush(generic_momentum_screen,
                               (generic_momentum,
                                _fip_score(
                                    generic_momentum, perc_pos, perc_neg),
                                   next_open,
                                   ticker))
                if len(generic_momentum_screen) > generic_momentum_size:
                    heapq.heappop(generic_momentum_screen)

        # Choose top firms by fip_score next, calculate capital to deploy for each
        top_firms = []
        # will allocate to all stocks in universe if pool is too small
        capital_available = (
            1 / min(self.firms_held, len(generic_momentum_screen))) * current_capital
        for generic_momentum, fip_score, next_open, ticker in generic_momentum_screen:
            # cost of each share
            cost = SLIPPAGE_FACTOR * next_open

            # maximum possible deployment
            shares_purchased = int(capital_available / cost)

            # Can't afford any shares (e.g. potentially Berkshare Hathaway), skip
            if shares_purchased == 0:
                pass
            # Insert correctly into heap while maintaining size
            elif len(top_firms) < self.firms_held:
                heapq.heappush(
                    top_firms, (fip_score, shares_purchased, cost, ticker))
            else:
                heapq.heappushpop(
                    top_firms, (fip_score, shares_purchased, cost, ticker))

        portfolio = [(ticker, shares_purcahsed, cost)
                     for _, shares_purcahsed, cost, ticker in top_firms]
        capital_invested = sum(asset[1] * asset[2] for asset in portfolio)
        cash_left = current_capital - capital_invested

        if cash_left < 0:
            raise Exception("Invested over max capital available")
        return portfolio, capital_invested, cash_left
