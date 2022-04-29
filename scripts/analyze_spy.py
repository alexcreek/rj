#!/usr/bin/env python3
import argparse
import os
from statistics import mode
from datetime import timedelta
from datetime import datetime as dt
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import pandas as pd
import utils

def parse_arguments():
    parser = argparse.ArgumentParser(description='Answer questions about timeseries data')
    parser.add_argument('-d', '--days', help='number of days to go back', type=int, default=30)
    parser.add_argument('-s', '--start', help='day to start with', type=str)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    parser.add_argument('-x', '--excel', help='output to excel', action='store_true')
    return parser.parse_args()

def compute_stats(df, holder):
    """Generate basic finance stats for a single day.

    Args:
        df (dataframe): 1 day's worth of timeseries data to process.
        holder (list):  Global list to store results.

    Returns:
        None
    """
    holder.append(utils.stats(df))

def find_when_price_changes_direction(df, holder, verbose=False):
    """Determines the time when price changes direction within a day.

    The algorithm is:
    1. calculate change and save it
    2. find the sign of change and save it
    3. if change has changed signs AND is greater than 0.6, we found a direction change

    Args:
        df (dataframe): 1 day's worth of timeseries data to process.
        holder (list):  Global list to store results.
        verbose (boolean): Flag to control logging.

    Returns:
        None
    """

    values = df['_value']
    _lasts = [
        values[30], values[30:90], values[90:150], values[150:210],
        values[210:270], values[270:330], values[330:390],
    ]
    lasts = [i.mean() for i in _lasts]

    times = [
        '10am', '10am-11am', '11am-12pm', '12pm-1pm',
        '1pm-2pm', '2pm-3pm', '3pm-4pm',
    ]
    data = zip(lasts, times)

    # Print date as a header
    if verbose:
        print(utils.date(df))

    flips = []
    previous = dict()
    previous_sign = ''
    for i in data:
        if not previous:
            previous = i
            continue

        # Calculate change
        change = i[0] - previous[0]
        previous = i

        # Determine change's sign
        if change < 0:
            sign = 'negative'
        else:
            sign = 'positive'

        if not previous_sign:
            previous_sign = sign
            continue

        if verbose:
            print(change, i[0], i[1])

        if sign != previous_sign and abs(change) > 0.6:
            flips.append(i[1])
            holder.append(i[1])

        previous_sign = sign

    if verbose:
        print(f'{utils.date(df)} - {len(flips)} flips')
        for i in flips: print(i)

def find_high_low(df, high_holder, low_holder):
    """Find the time of day when price is highest and lowest.

    Args:
        df (dataframe): 1 day's worth of timeseries data to process.
        high_holder (list):  Global list to store results for highs.
        low_holder (list):  Global list to store results for lows.

    Returns:
        None
    """

    # Set DST offset
    _date = df.iloc[-1]['_time'].date().strftime('%m-%d')
    short_date = dt.strptime(_date, '%m-%d')

    mar13 = dt.strptime('03-13', '%m-%d')
    nov6 = dt.strptime('11-06', '%m-%d')

    dst_offset = 4
    if short_date < mar13 or short_date > nov6:
        dst_offset = 5

    high = df.loc[df['_value'] == df['_value'].max()].iloc[0]['_time'] - timedelta(hours=dst_offset)
    low = df.loc[df['_value'] == df['_value'].min()].iloc[0]['_time'] - timedelta(hours=dst_offset)

    high_holder.append(high.strftime('%H'))
    low_holder.append(low.strftime('%H'))

def main(days, start=None, verbose=False, excel=False):
    # pylint: disable=too-many-locals
    # Init shit
    load_dotenv()
    token = os.environ['INFLUXDB_TOKEN']
    url = os.environ['INFLUXDB_URL']

    # Create client
    client = InfluxDBClient(url=url, token=token, org="default")
    query_api = client.query_api()

    timestamps = utils.timestamps_per_day(days, start)

    # Start the loop
    stats = []
    total_flips = []
    highs = []
    lows = []
    for day in timestamps:
        for key in day:
            for times in day[key]: # One day per query
                query = f"""
                    from(bucket: "main")
                        |> range(start: {times['start']}, stop: {times['stop']})
                        |> filter(fn: (r) => r["_measurement"] == "underlying")
                        |> filter(fn: (r) => r["symbol"] == "SPY")
                        |> filter(fn: (r) => r["_field"] == "last")
                        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                 """

                # Perform the query
                df = query_api.query_data_frame(query)

                # Calculate
                if not df.empty:
                    compute_stats(df, stats)
                    find_when_price_changes_direction(df, total_flips, verbose=verbose)
                    find_high_low(df, highs, lows)

    ### Output
    # Stats
    if excel:
        pd.DataFrame(stats).to_excel('output.xlsx')

    # Price direction change times
    if total_flips:
        _flips = mode(total_flips)
        _flip_percent = round(total_flips.count(_flips) / len(total_flips) * 100)
        print(f'[*] When price changes direction, what time does it happen? - {_flips} @ {_flip_percent}%')
    else:
        print(f'[*] When price changes direction, what time does it happen? - No flips')

    # High/lows
    _highs = mode(highs)
    _highs_percent = round(highs.count(_highs) / len(highs) * 100)

    _lows = mode(lows)
    _lows_percent = round(lows.count(_lows) / len(lows) * 100)

    print(f'[*] When are prices highest? - {mode(highs)} @ {_highs_percent}%')
    print(f'[*] When are prices lowest? - {mode(lows)} @ {_lows_percent}%')


if __name__ == '__main__':
    args = parse_arguments()
    main(args.days, args.start, args.verbose, args.excel)
