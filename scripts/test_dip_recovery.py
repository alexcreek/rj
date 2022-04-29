#!/usr/bin/env python3
import argparse
import os
from datetime import timedelta
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import utils

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('-d', '--days', help='number of days to backtest', type=int, default=30)
    parser.add_argument('-s', '--start', help='day to start with', type=str)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()

def main(days, start=None, verbose=False):
    # Init shit
    load_dotenv()
    token = os.environ['INFLUXDB_TOKEN']
    url = os.environ['INFLUXDB_URL']

    # Create client
    client = InfluxDBClient(url=url, token=token, org="default")
    query_api = client.query_api()

    timestamps = utils.timestamps_per_minute(days, start)

    # Start the loop
    for day in timestamps:
        for key in day:
            bottom_value = None
            bottom_time = None
            for times in day[key]:
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

                # Start the algo
                if not df.empty:
                    if bottom_value:
                        # Calculate change since bottom was met
                        current = df.iloc[-1]['_value']
                        change = utils.change(bottom_value, current)

                        # Calculate elapsed time since bottom was met
                        elapsed = df.iloc[-1]['_time'] - bottom_time

                        if verbose:
                            print(change, df.iloc[-1]['_time'])

                        # Make this a cli arg
                        if change > 0.002 and elapsed <= timedelta(minutes=30):
                            print(change, df.iloc[-1]['_time'])
                            print('buy')

                        continue # Keep processing for now. This will notify in the future

                    start = df.iloc[0]['_value']
                    current = df.iloc[-1]['_value']

                    change = utils.change(start, current)

                    if verbose:
                        print(change, df.iloc[-1]['_time'])

                    # Make these a cli arg
                    if change < -0.004 and df.iloc[-1]['_time'].hour > 14 and df.iloc[-1]['_time'].hour < 17:
                        print(change, df.iloc[-1]['_time'])
                        print('bottom hit')
                        bottom_value = current
                        bottom_time = df.iloc[-1]['_time']


if __name__ == '__main__':
    args = parse_arguments()
    main(args.days, args.start, args.verbose)
