
class Backtester():
    """Backtester will take a strategy and return the following statistics about 
    the strategies performance on the sample data 
    
    - Sharpe Ratio
    - ? """

    def __init__(self):
        pass

    def _relative_performance(self, benchmark):
        """Calculates relative performance compared to a benchmark. 
        
        TODO: Choose a statistic to calculate on """
        pass

    def _performance_visualization(self):
        """Outputs a graph visualization of the strategies performance 
        
        ADDITION: Can add performance against a benchmark"""
        pass

    def backtest(self, starting_capital, start_date, end_date):
        """Runs the backtesting algorithm
        
            - Will have to loop through all equities and generate signals
            - Will have to deploy optimal amount of capital to each ticker 
        """
        pass