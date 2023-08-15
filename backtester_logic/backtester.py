from momentum_strategy import QuantitativeMomentum
from utils import _int_to_datetime
from dateutil.relativedelta import relativedelta


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

    def __init__(self, strategy: (QuantitativeMomentum)):
        self.strategy = strategy

    def _relative_performance(self, benchmark):
        """Calculates relative performance compared to a benchmark. 

        TODO: Choose a statistic to calculate on """
        pass

    def _performance_visualization(self):
        """Outputs a graph visualization of the strategies performance 

        ADDITION: Can add performance against a benchmark"""
        pass

    def backtest(self, starting_capital: int = 100_000, start_date: int = 19710102, end_date: int = 20230803):
        """Runs the backtesting algorithm
            - Will have to loop through all equities and generate signals
            - Will have to deploy optimal amount of capital to each ticker 
        """

        current_date = _int_to_datetime(start_date)
        rebalance_date = current_date + relativedelta(month=3)

        current_portfolio, cash_remaining = self.strategy.portfolio_construction(
            starting_capital, start_date)
        current_equity = starting_capital - cash_remaining

        def _calculate_equity(current_equity, portfolio):
            unrealized_change = 0

            for ticker, shares_purcahsed, cost in portfolio:
                current_price = 0

                unrealized_change *= (current_price - cost) * shares_purcahsed

            current_equity += unrealized_change
            return current_equity

        # Full backtest
        while current_date <= end_date:

            # Collecting equity changes
            while current_date < rebalance_date:
                current_equity = _calculate_equity(
                    current_equity, current_portfolio)

            # on the rebalance date, portfolio is fully sold at the close
            current_equity = _calculate_equity(
                current_equity, current_portfolio)

            # Ater the close calculate the new portfolio and buy it at the open
            current_portfolio, new_cash_reamining = self.strategy.portfolio_construction(
                current_capital=current_equity + cash_remaining,
                date=current_date
            )
