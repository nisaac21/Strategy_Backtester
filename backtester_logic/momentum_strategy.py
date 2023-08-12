import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dateutil import relativedelta
import sqlite3

from utils import _ticker_to_table_name, _int_to_datetime


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
        1. Determine date variable type 
        2. Fix absolute momentum 
        Test! 
    """

    def __init__(self,
                 database_name: str,
                 tickers,
                 look_back: int = 12,
                 firms_held: int = 50,
                 rebalance: int = 3,
                 momentum_consistency: int = 0.5,
                 max_d_return: int = 0.05) -> None:

        self.connector = sqlite3.connect(database_name)
        self.cursor = self.connector.cursor()
        self.tickers = tickers
        self.universe_size = len(self.tickers)

        self.look_back = look_back
        self.firms_held = firms_held
        self.rebalance = rebalance
        self.momentum_consistency = momentum_consistency
        self.max_d_return = max_d_return  # number of months to look back

    def _access_stock_ohlc(self, ticker: str, date: int) -> int or dict:
        """"Returns a stock's Open, High, Low, and Close data for a specific date.
        If the date does not exist returns -1

        Parameters
        ----------
        ticker : (str) the stock symbol.US in all caps
        date : (int) representing the date in YYYYMMDD"""

        query = (f"""SELECT Open, High, Low, Close
                 FROM {_ticker_to_table_name(ticker)} WHERE Date = {date}""")

        ohlc = self.crusor.execute(query).fetchall()

        if ohlc is None:
            return -1

        ohlc = ohlc[0]

        return {'Open': ohlc[0], 'High': ohlc[1], 'Low': ohlc[2], 'Close': ohlc[3]}

    def _absolute_momentum(self, ticker: str, date: datetime) -> float:
        """Calculates the absolute momentum of the stock

            stock : (int) the index of the stock to look at 
        """
        look_back_date = date - \
            relativedelta(
                months=self.look_back)  # get date from look back period ago
        return self._access_stock_ohlc(ticker, date)['Close'] / self._access_stock_ohlc(ticker, look_back_date)['close'] - 1

    def _calculate_postive_days(self, ticker: int, date: int) -> (float, float):
        """Returns the % of postive days within the lookback period

        Parameters
        ----------
        ticker : (str) ticker of the stock given in all caps .US
        date : (int) representing the date given as YYYYMMDD

        TODO: Combine with _find_max_daily_return"""

        date = _int_to_datetime(date)

        cur_date = date - relativedelta(months=self.look_back)
        # 252 days in a trading year, relevant portion for one full calculation
        min_days = int(252 * (self.look_back / 12))
        positive_days = 0
        negative_days = 0
        total_days = 0

        while cur_date <= date:
            prev_day = cur_date - timedelta(days=1)

            prev_close = self._access_stock_ohlc(ticker, cur_date)['Close']
            current_close = self._access_stock_ohlc(
                ticker, prev_day)['Close'] - 1

            if prev_close == -1:
                return -1

            perc_return = current_close / prev_close - 1

            if perc_return > 1:
                positive_days += 1
            elif perc_return < 1:
                negative_days += 1

            total_days += 1

            cur_date += timedelta(days=1)

        return positive_days / total_days, negative_days / total_days

    def compute_parameters(self):
        """Appends the following columns to each table in the Stock database 
            - Generic Momentum for x Months: Return over last self.lookback months
            - Percent Positive Days over x Months: The percent of positive return days over last self.lookback months
            """

        # 252 trading days in a year
        min_days = int((self.look_back / 12) * 252)

        for ticker in self.tickers['Ticker']:
            current_table = pd.read_sql_query(
                f"SELECT * from {_ticker_to_table_name(ticker)}",
                con=self.connector)

            num_of_dates = len(current_table)
            new_columns = pd.DataFrame({
                "Positive_Sum": np.zeros(num_of_dates),
                "Current_Return": np.zeros(num_of_dates),
                f"Return_{self.look_back}_Month": np.full(num_of_dates, -1),
                f"Percent_Positive_Over_{self.look_back}_Months": np.full(num_of_dates, -1)})

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
                        # If stock made a positive return
                        if row['Close'] > current_table.loc[index - 1, "Close"] and current_table.loc[index - 1, "Close"] != -1:
                            new_columns.loc[index, 'Positive_Sum'] += 1
                            new_columns.loc[index, 'Current_Return'] = 1
                        # If stock made a negative return
                        elif row['Close'] < current_table.loc[index - 1, "Close"]:
                            new_columns.loc[index, 'Current_Return'] = -1
                else:
                    # Generic Momentum
                    new_columns.loc[index, f"Return_{self.look_back}_Month"] = (
                        row['Close'] / current_table.loc[index - min_days, "Close"]) - 1
                    positive_sum = new_columns.loc[index - 1, 'Positive_Sum']

                    # If the beginning of the look back period was positive,
                    # we need to remove that from our count
                    if new_columns.loc[index - min_days, "Current_Return"] == 1:
                        positive_sum -= 1

                    # If stock made a positive return
                    if row['Close'] > current_table.loc[index - 1, 'Close']:
                        positive_sum += 1
                        new_columns.loc[index, 'Current_Return'] = 1
                    # If stock made a negative return
                    elif row['Close'] < current_table.loc[index - 1, "Close"]:
                        new_columns.loc[index, 'Current_Return'] = -1

                    # Necessary statistics
                    new_columns.loc[index, 'Positive_Sum'] = positive_sum
                    new_columns.loc[index,
                                    f"Percent_Positive_Over_{self.look_back}_Months"] = positive_sum / min_days

            # update sql table
            pd.merge(
                left=current_table,
                right=new_columns[[
                    f"Return_{self.look_back}_Month", f"Percent_Positive_Over_{self.look_back}_Months"]],
                left_index=True,
                right_index=True
            ).to_sql(_ticker_to_table_name(ticker), self.connector, if_exists='replace', index=False)

    def portfolio_construction(self, year: int, month: int, day: int):
        """Returns the self.firm_size number of stocks that should be invested in for given date
        """

        date = datetime.date(year, month, day)

        momentum_chart = np.zeros(shape=(self.universe_size, 3))

        # momentum_chart is a numpy array where
        # momentum_chart[i][0] gives stock ticker index
        # momentum_chart[i][1] gives absolute momentum of the i-th stock
        # momentum_chart[i][2] gives the FIP score of the stock

        def _fip_score(perc_return: float, perc_pos_days: float, perc_neg_days: float) -> float:
            return perc_return * (perc_pos_days - perc_neg_days)

        for stock in range(self.universe_size):
            stock_abs_momentum = self._absolute_momentum(stock, date)
            # stock_max_d_return = self._find_max_daily_return(stock, date)
            stock_pos_days, stock_neg_days = self._calculate_postive_days(
                stock, date)

            momentum_chart[stock][0] = stock
            momentum_chart[stock][1] = stock_abs_momentum
            momentum_chart[stock][2] = _fip_score(
                stock_abs_momentum, stock_pos_days, stock_neg_days)

        ten_perc = self.universe_size // 10

        top_ten_perc = momentum_chart[momentum_chart[:,
                                                     1].argsort()][:ten_perc + 1]

        top_firms = top_ten_perc[top_ten_perc[:,
                                              2].argsort()][:self.firms_held]

        return top_firms[:, 0]


if __name__ == '__main__':

    nasdaq_tickers = pd.read_csv('data/nasdaq_stock_tickers.csv')
    nyse_tickers = pd.read_csv('data/nyse_stock_tickers.csv')

    universe = pd.concat([nasdaq_tickers, nyse_tickers], ignore_index=True)

    strategy = QuantitativeMomentum(
        'data/MarketHistoricalData.db',
        tickers=universe
    )
