from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse

def change(start, current):
    """Calculate the percent of change between two values.

    Args:
       start (float): The starting value.
       current (float):  The current values.

    Returns:
        float
    """
    return round((current - start) / start, 4)

def timestamps_per_minute(days, start=False):
    """Generate timestamps at 1 minute intervals.

    Args:
        days (int): The number of days to create timestamps for.

    Returns:
        list(dict(list(dict)))
    """

    if start:
        _start = parse(start)
    else:
        _start = dt.utcnow()


    ret = []
    for i in range(days):
        start = dt.isoformat(
            _start.replace(hour=13, minute=30, second=0, microsecond=0) - timedelta(days=i)
        )
        _stop = _start.replace(hour=13, minute=31, second=0, microsecond=0) - timedelta(days=i)

        ret.append({i: []})

        for j in range(390):
            stop = dt.isoformat(_stop + timedelta(minutes=j))
            ret[-1][i].append({'start': f'{start}Z', 'stop': f'{stop}Z'})

    return ret

def timestamps_per_day(days, start):
    """Generate timestamps at 1 day intervals.

    Args:
        days (int): The number of days to create timestamps for.

    Returns:
        list(dict(list(dict)))
    """

    if start:
        _start = parse(start)
    else:
        _start = dt.utcnow()


    ret = []
    for i in range(days):
        start = dt.isoformat(
            _start.replace(hour=13, minute=30, second=0, microsecond=0) - timedelta(days=i)
        )
        stop = dt.isoformat(
            _start.replace(hour=20, minute=00, second=0, microsecond=0) - timedelta(days=i)
        )

        ret.append({i: [{'start': f'{start}Z', 'stop': f'{stop}Z'}]})

    return ret

def timestamps_one_day_by_minute(dst=True):
    """Generate minute timestamps for one day.

    Args:
        dst (bool): Flag to convert timestamps to dst.

    Returns:
        list()
    """
    ret = []
    start = dt.utcnow().replace(hour=13, minute=30, second=0, microsecond=0)

    for i in range(391):
        ts = to_dst(start + timedelta(minutes=i)).strftime('%H:%M:%S')
        ret.append(ts)
    return ret

def min(df):
   # pylint: disable=redefined-builtin
    return round(df['_value'].min(), 2)

def max(df):
   # pylint: disable=redefined-builtin
    return round(df['_value'].max(), 2)

def open(df):
   # pylint: disable=redefined-builtin
    return round(df.iloc[0]['_value'], 2)

def close(df):
    return round(df.iloc[-1]['_value'], 2)

def result(df):
    if df.iloc[0]['_value'] < df.iloc[-1]['_value']:
        return "gain"
    return "loss"

def change_df(df):
    return round((df.iloc[-1]['_value'] - df.iloc[0]['_value']) / df.iloc[0]['_value'], 4)

def weekday(df):
    return df.iloc[0]['_time'].strftime('%A')

def date(df):
    return df.iloc[-1]['_time'].date()

def to_ttl(exp, start=None):
    """Return the number of days until a date is reached.

    Args:
        exp (str): The target date
        start (datetime.datetime): The day to start from

    Returns:
        integer
    """
    start_date = dt.now()
    if start:
        start_date = start
    return dt.strptime(exp, '%d %b %y') - start_date

def to_vmr(vix, mark):
    """Return the vix to mark ratio

    Args:
        vix (float): The vix.
        mark (float): The mark.

    Returns:
        float
    """
    if vix and mark:
        return round(vix / mark, 2)
    return 0

def moneyness(putCall, vix, strike):
    """Return how far in or out of the money a contract is

    Args:
        vix (float): The vix.
        strike (float): A contract's strike.

    Returns:
        string
    """
    diff = round(strike - vix)
    if 'call' in putCall:
        diff = round(vix - strike)

    if diff > 0:
        ness = 'ITM'
    elif diff < 0:
        ness = 'OTM'
        diff = diff * -1
    else:
        ness = 'ATM'
    return f'{ness} {diff}'

def stats(df):
    """Generate basic finance stats for a single day.

    Args:
        df (dataframe): 1 day's worth of timeseries data to process.

    Returns:
        dict
    """
    return {
        'date': date(df),
        'low': min(df),
        'high': max(df),
        'open': open(df),
        'close': close(df),
        'result': result(df),
        'change': change_df(df),
        'weekday': weekday(df)
    }

def to_dst(timestamp):
    _date = timestamp.strftime('%m-%d')
    short_date = dt.strptime(_date, '%m-%d')

    mar13 = dt.strptime('03-13', '%m-%d')
    nov6 = dt.strptime('11-06', '%m-%d')

    dst_offset = 4
    if short_date < mar13 or short_date > nov6:
        dst_offset = 5

    return timestamp - timedelta(hours=dst_offset)
