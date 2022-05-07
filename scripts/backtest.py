#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from dateutil.parser import parse
import utils

def main(start, exp, strike, putCall, limit, stop, time, verbose=False):
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
                    backtest(df, limit, stop, time)

def backtest(df, limit, stop, time):
    """Backtest timeseries data using limit and stop limit.

    Args:
        df (dataframe): A days worth of timeseries data.
        limit(float): The percentage of the strike to use as the limit.
        stop(float): The percentage of the strike to use as the stop limit.

    Returns:
        idk
    """
    b = BacktestWindow(limit, stop, time)
    for i in df.itertuples():
        # time i[5]
        # value i[6]
        b.eval(i[5], i[6])


class BacktestWindow:
    """Sum the total change in timeseries data"""
    def __init__(self, limit, stop, time):
        self.limit = limit
        self.stop = stop
        self.time = parse(time).time()
        self.times = []
        self.changed = 0
        self.start = 0

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
        if utils.to_dst(time).time() < self.time:
            return

        if not self.start:
            self.start = value
            return

        self.times.append(time)
        self.changed = self.change(self.start, value)

        print(f'{utils.to_dst(self.times[-1])} {self.changed}')

        if self.changed >= self.limit:
            print('limit hit')
            print(f'{len(self.times)} minutes')
            sys.exit(0)

        if self.changed <= self.stop:
            print('stop hit')
            print(f'{len(self.times)} minutes')
            sys.exit(0)


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
