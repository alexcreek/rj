#!/usr/bin/env python3
import argparse
import os
from collections import deque
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import utils
from lib.models import Window

def parse_arguments():
    parser = argparse.ArgumentParser(description='Find gains and losses in SPY contracts')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-e', '--exp', help='expiration', required=True)
    parser.add_argument('-s', '--strike', help='strike', required=True)
    parser.add_argument('-t', '--type', help='put or call', required=True)
    parser.add_argument('-p', '--points', help='points to use in the eval window', type=int, default=2)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()


def find_swings(df, points):
    """Find gains and losses in timeseries data.

    This function applies an eval window to a series of data and reports
    when the data's value changes.
    1. Create an eval window from supplied parameters
    2. Evaluate data using the window
    3. Record each instance the data's value changes

    Args:
        df (dataframe): A days worth of timeseries data.
        points (int): The number of datapoints to use in the eval window.

    Returns:
        idk
    """
    c = CumEvalWindow(points)
    for i in df.itertuples():
        # time i[5]
        # value i[6]
        c.eval(i[5], i[6])

    return c.results()

class CumEvalWindow(Window):
    """Sum the total change in timeseries data"""
    def __init__(self, points_threshold):
        # pylint: disable=redefined-outer-name
        self.points_threshold = points_threshold
        self.points = deque(maxlen=points_threshold)
        self.times = deque(maxlen=points_threshold)
        self.output = []

    def eval(self, time, value):
        """Apply an evaluation window to timeseries data

        Args:
            time (datetime.datetime) - The measurement's time.
            value (float) - The measurement's value.
        if we need more points, get more points
        if we have enough points,
            sum
            save stuff
            empty tracking list
            repeat the loop
        """

        self.points.append(value)
        self.times.append(time)

        # Wait until we have enough points
        if len(self.points) < self.points_threshold:
            return

        changed = 0
        start = self.points.popleft()
        for point in self.points:
            changed += self.change(start, point)

        self.output.append({
            'change': changed,
            'timestamp': utils.to_dst(self.times[0])
        })

    def results(self):
        return self.output

    def change(self, start, current):
        # pylint: disable=no-self-use
        """Calculate the percent of change between two values.

        Args:
           start (float): The starting value.
           current (float):  The current values.

        Returns:
            float
        """
        return round((current - start) / start, 4)


def main(start, exp, strike, putCall, points, verbose=False):
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
                    output = find_swings(df, points)

                for i in output:
                    print(f"{points} minutes from {i['timestamp'].time()} {round(i['change'] * 100, 1)} ")


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
