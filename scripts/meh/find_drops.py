#!/usr/bin/env python3
import argparse
import os
from collections import deque
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import numpy as np
import utils
from lib.models import Window

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('-d', '--days', help='number of days to backtest', type=int, default=30)
    parser.add_argument('-s', '--start', help='day to start with', type=str)
    parser.add_argument('-p', '--points', help='points to use in the eval window', type=int, default=1)
    parser.add_argument('-c', '--change', help='percentage to signal an inversion', type=float, default=0.01)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()

def find_inversion(df, points, change):
    """Find change in timeseries data.

    A timeseries evaluation window consists of 2 things, time and change.
    This function applies an eval window to a series of data and reports
    when the data's value changes direction e.g. inverts
    1. Create an eval window from supplied parameters
    2. Evaluate data using the window
    3. Record each instance the data's value inverts

    Args:
        df (dataframe): A days worth of timeseries data.
        points (int): The number of datapoints to use in the eval window.
        change (float): The percentage of change used to identify an inversion.

    Returns:
        idk
    """
    e = EvalWindow(points, change)
    for i in df.itertuples():
        # time i[5]
        # value i[6]
        e.eval(i[5], i[6])

    return e.results()

class EvalWindow(Window):
    """Track change in data"""
    def __init__(self, points_threshold, change_threshold):
        # pylint: disable=redefined-outer-name
        self.points_threshold = points_threshold
        self.change_threshold = change_threshold
        self.points = deque(maxlen=points_threshold)
        self.times = deque(maxlen=points_threshold)
        self.triggered = []

    def eval(self, time, value):
        """Apply an evaluation window to timeseries data

        Args:
            time (datetime.datetime) - The measurement's time.
            value (float) - The measurement's value.
        """
        self.points.append(value)
        self.times.append(time)

        # Skip evaluation until we have enough points
        if len(self.points) != self.points_threshold:
            return

        # Actually do the eval
        # Matches positive and negative change
        # changed = abs(self.change(self.points[0], self.points[-1]))
        # if changed >= self.change_threshold:

        # Matches negative change
        changed = self.change(self.points[0], self.points[-1])
        if changed <= self.change_threshold * -1:
            self.triggered.append({
                'change': changed,
                'value': self.points[-1],
                'timestamp': utils.to_dst(self.times[-1])
            })

    def results(self):
        return self.triggered


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
                        days_holder.append(find_inversion(df, points, change))

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
