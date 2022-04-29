#!/usr/bin/env python3
import argparse
import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import numpy as np
import utils

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('-d', '--days', help='number of days to backtest', type=int, default=30)
    parser.add_argument('-s', '--start', help='day to start with', type=str)
    parser.add_argument('-p', '--points', help='points to use in the eval window', type=int, default=1)
    parser.add_argument('-c', '--change', help='percentage to signal an inversion', type=float, default=0.001)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()


def iterate(days, points, change, start=None, verbose=False):
    # pylint: disable=too-many-locals
    load_dotenv()
    token = os.environ['INFLUXDB_TOKEN']
    url = os.environ['INFLUXDB_URL']

    client = InfluxDBClient(url=url, token=token, org="default")
    query_api = client.query_api()

    timestamps = utils.timestamps_per_day(days, start)

    for day in timestamps:
        for key in day:
            for times in day[key]: # One day per iteration
                query = f"""
                    from(bucket: "main")
                        |> range(start: {times['start']}, stop: {times['stop']})
                        |> filter(fn: (r) => r["_measurement"] == "underlying")
                        |> filter(fn: (r) => r["symbol"] == "SPY")
                        |> filter(fn: (r) => r["_field"] == "last")
                        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                 """
                df = query_api.query_data_frame(query)

                # Calculate
                days_holder = []
                if not df.empty:
                    stats = utils.stats(df)
                    if stats['low'] < stats['close']: # Dip
                        days_holder.append(utils.find_inversion(df, points, change))

                for d in days_holder:
                    print(f'[*] change {change} + points {points} triggered {len(d)} inversions')
                    for data in d:
                        if verbose:
                            print(f"  {data['timestamp'].date()} {data['timestamp'].time()} {data['change']} {data['value']}")

def main(days, points, change, start=None, verbose=False):
    for _change in np.arange(0.005, 0.007, 0.001):
        for _points in range(1, 60):
            iterate(days, _points, round(_change, 3), start=start, verbose=verbose)

if __name__ == '__main__':
    args = parse_arguments()
    main(
        args.days,
        args.points,
        args.change,
        args.start,
        args.verbose
    )
