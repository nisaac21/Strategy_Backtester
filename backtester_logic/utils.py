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
    date : (int) representing the date in YYYYMMDD"""

    date = str(datetime_int)
    year = int(date[:4])
    month = int(date[4: 6])
    day = int(date[-2:])
    return datetime(year=year, month=month, day=day)
