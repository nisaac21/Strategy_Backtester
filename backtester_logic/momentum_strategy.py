import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import relativedelta


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
                 tickers: list(str),
                 look_back: int = 12,
                 firms_held: int = 50,
                 rebalance: int = 3,
                 momentum_consistency: int = 0.5,
                 max_d_return: int = 0.05) -> None:

        self.tickers = tickers
        self.universe_size = len(self.tickers)

        self.look_back = look_back
        self.firms_held = firms_held
        self.rebalance = rebalance
        self.momentum_consistency = momentum_consistency
        self.max_d_return = max_d_return  # number of months to look back

    def _ticker_to_index(self, ticker):
        """Based off ticker list, returns relevant index"""
        pass

    def _index_to_ticker(self, index):
        """Returns ticker based off of index"""
        return self.tickers[index]

    def _access_universe_info(self):
        """"""
        pass

    def _access_stock_ohlc(self, stock: int, date):
        """TODO: Accesses the ticker OHLC data for specific ticker"""
        pass

    def _absolute_momentum(self, stock: int, date: datetime) -> float:
        """TODO: Calculates the absolute momentum of the stock

            stock : (int) the index of the stock to look at 
        """
        look_back_date = date - \
            relativedelta(
                months=self.look_back)  # get date from look back period ago
        return self._access_stock_ohlc(stock, date)['close'] / self._access_stock_ohlc(stock, look_back_date)['close'] - 1

    # def _find_max_daily_return(self, stock: int, date: datetime):
    #     """Finds the max daily return in the last self.max_d_return months ago

    #     TODO: combine with _calculate_postive_days"""

    #     # start months ago
    #     cur_date = date - relativedelta(months=self.max_d_return)
    #     max_d_return = float("-inf")

    #     while cur_date <= date:
    #         max_d_return = max(
    #             max_d_return,
    #             self._access_stock_ohlc(stock, cur_date)['close']
    #         )

    #         cur_date += timedelta(days=1)  # increment date by one day

    #     return max_d_return

    def _calculate_postive_days(self, stock: int, date: datetime) -> (float, float):
        """Returns the % of postive days within the lookback period

        TODO: Combine with _find_max_daily_return"""

        cur_date = date - relativedelta(months=self.look_back)
        positive_days = 0
        negative_days = 0
        total_days = 0

        while cur_date <= date:
            prev_day = cur_date - timedelta(days=1)

            perc_return = self._access_stock_ohlc(stock, cur_date)[
                'close'] / self._access_stock_ohlc(stock, prev_day)['close'] - 1

            if perc_return > 1:
                positive_days += 1
            elif perc_return < 1:
                negative_days += 1

            total_days += 1

            cur_date += timedelta(days=1)

        return positive_days / total_days, negative_days / total_days

    def portfolio_construction(self, year: int, month: int, day: int):
        """Returns the self.firm_size number of stocks that should be invested in for given date

        TODO: Create ranking algorithm
        TODO: Create system for tracking top self.firms_size ranks while iterating
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
