from datetime import datetime


def _ticker_to_table_name(ticker: str) -> str:
    """Coverts a ticker into its SQL table name

    Parameters
    -----------
    ticker : (str) the stock symbol.US in all caps 
    """

    return f'{ticker[:-3].replace("-", "_")}_US'


def _int_to_datetime(datetime_int: int) -> datetime:
    """Converts a datetime int from the database into a datetime object

    Parameters
    ----------
    datetime_int : (int) representing the date in YYYYMMDD"""

    date = str(datetime_int)
    year = int(date[:4])
    month = int(date[4: 6])
    day = int(date[-2:])
    return datetime(year=year, month=month, day=day)


def _datetime_to_int(datetime_date: datetime) -> int:
    """Converts a datetime date into and int of the format YYYYMMDD

    Parameters
    ----------
    datetime_date : (datetime) representing the date """

    date_str = datetime_date.strftime('%Y%m%d')
    return int(date_str)


def _strategy_table_convention(look_back, lottery_window, rebalance, firms_held):
    return f'equity_lw{lottery_window}_lb{look_back}_reb{rebalance}_fh{firms_held}'
