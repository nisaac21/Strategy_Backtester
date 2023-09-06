from momentum_strategy import QuantitativeMomentum
from utils import _int_to_datetime, _datetime_to_int, _ticker_to_table_name
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import sqlite3
import pandas as pd
import numpy as np


class Backtester():
    """Backtester will take a strategy and return the following statistics about 
    the strategies performance on the sample data 

    - Overall Return
    - Compounded Annual Growth Rate 
    - Standard Deviation
    - Downside Deviation
    - Sharpe Ratio
    - Maximum Drawdown 
    - Worst Month Return 
    - Best Month Return 
    - Profitable months 
    - Equity Time Series  
    """

    def __init__(self, database: str) -> None:

        self.connector = sqlite3.connect(database)
        self.cursor = self.connector.cursor()

    def backtest(self, strategy: QuantitativeMomentum, rebalance_period: int = 3, starting_capital: int = 100_000, start_date: int = 19710104, end_date: int = 20230803) -> pd.DataFrame:
        """Runs the backtesting algorithm
            - Will have to loop through all equities and generate signals
            - Will have to deploy optimal amount of capital to each ticker 

        TODO: Make timeseries with pandas and/or numpy 
        TODO: Add statistics calculations in
        """

        query = f"""SELECT Date FROM {_ticker_to_table_name("GE.US")} 
        WHERE Date BETWEEN {start_date} AND {end_date}"""

        equity_timeseries = pd.read_sql_query(query, con=self.connector)

        equity_timeseries['Equity'] = 0

        rebalance_date = _datetime_to_int(
            _int_to_datetime(start_date) + relativedelta(months=rebalance_period))

        current_portfolio, capital_invested, cash_remaining = strategy.portfolio_construction(
            starting_capital, start_date)

        def _calculate_equity(date, capital_invested, portfolio):

            unrealized_change = 0
            for ticker, shares_purcahsed, cost in portfolio:
                query = f'''
                    SELECT
                    Close 
                    FROM {_ticker_to_table_name(ticker)}
                    WHERE Date = {date}
                '''
                return_value = self.cursor.execute(query).fetchone()
                current_price = cost if return_value is None else return_value[0]
                unrealized_change += (current_price - cost) * shares_purcahsed

            return capital_invested + unrealized_change

        # Full backtest
        for current_date in tqdm(equity_timeseries['Date']):

            # Collecting equity changes
            unrealized_equity = _calculate_equity(
                current_date, capital_invested, current_portfolio)

            equity_timeseries.loc[equity_timeseries['Date'] ==
                                  current_date, 'Equity'] = unrealized_equity + cash_remaining

            if current_date >= rebalance_date:
                # on the rebalance date, portfolio is fully sold at the close
                # Ater the close calculate the new portfolio and buy it at the open
                current_portfolio, capital_invested, cash_remaining = strategy.portfolio_construction(
                    current_capital=unrealized_equity + cash_remaining,
                    date=current_date
                )

                rebalance_date = _datetime_to_int(
                    _int_to_datetime(current_date) + relativedelta(months=rebalance_period))

        return equity_timeseries
