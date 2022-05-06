#!/usr/bin/env python3
import argparse
import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import numpy as np
import utils

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-e', '--exp', help='expiration', required=True)
    parser.add_argument('-s', '--strike', help='strike', required=True)
    parser.add_argument('-t', '--type', help='put or call', required=True)
    parser.add_argument('-p', '--points', help='points to use in the eval window', type=int, default=2)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()


def iterate(start, exp, strike, putCall, points, verbose=False):
    # pylint: disable=too-many-locals
    load_dotenv()
    token = os.environ['INFLUXDB_TOKEN']
    url = os.environ['INFLUXDB_URL']

    client = InfluxDBClient(url=url, token=token, org="default")
    query_api = client.query_api()

    timestamps = utils.timestamps_per_day(1, start)

    for day in timestamps:
        for key in day:
            for times in day[key]: # One day per iteration
                query = f"""
                    from(bucket: "main")
                        |> range(start: {times['start']}, stop: {times['stop']})
                        |> filter(fn: (r) => r._measurement == "options")
                        |> filter(fn: (r) => r.symbol == "SPY")
                        |> filter(fn: (r) => r.exp == "{exp}")
                        |> filter(fn: (r) => r.strike == "{strike}.0")
                        |> filter(fn: (r) => r.putCall == "{putCall}")
                        |> filter(fn: (r) => r._field == "mark")
                        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                 """
                df = query_api.query_data_frame(query)
                output = []

                # Calculate
                if not df.empty:
                    output = utils.find_swings(df, points)

                for i in output:
                    print(f"{points} minutes from {i['timestamp'].time()} {round(i['change'] * 100, 1)} ")

def main(start, exp, strike, putCall, points, verbose=False):
    for p in [points]:
        iterate(start, exp, strike, putCall, p, verbose=verbose)

if __name__ == '__main__':
    args = parse_arguments()
    main(
        args.start,
        args.exp.upper(),
        args.strike,
        args.type,
        args.points,
        args.verbose,
    )
