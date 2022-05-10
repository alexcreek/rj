#!/usr/bin/env python3
import os
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

                # Calculate
                if not df.empty:
                    b = BacktestWindow(limit, stop, time, verbose)
                    return b.eval(df)

class BacktestWindow:
    """Test timeseries data against limits and stops"""
    def __init__(self, limit, stop, time, verbose):
        self.limit = limit
        self.stop = stop
        self.verbose = verbose
        self.start_time = parse(time).time()
        self.times = []
        self.changed = 0
        self.start = 0
        self.results = {}

    def eval(self, df):
        """Apply an evaluation window to timeseries data

        Args:
            df (dataframe): Timeseries data

        Returns:
            dict of format:
                result: limit|stop|runaway
                limit:  limit value
                stop:  stop value
                minutes: number of iterations
                start: start time
                stop: stop time
        """
        for i in df.itertuples():
            time = utils.to_dst(i[5]).time()
            value = i[6]

            if time < self.start_time:
                continue

            if not self.start:
                self.start = value
                continue

            self.times.append(time)
            self.changed = self.change(self.start, value)

            if self.verbose:
                print(f'{self.times[-1]} {self.changed}')

            if self.changed >= self.limit:
                if self.verbose:
                    print('limit hit')
                    print(f'{len(self.times)} minutes')
                self.generate_results()
                self.results['result'] = 'limit'
                return self.results

            if self.changed <= self.stop:
                if self.verbose:
                    print('stop hit')
                    print(f'{len(self.times)} minutes')
                self.generate_results()
                self.results['result'] = 'stop'
                return self.results

            if time == parse('16:00:00').time():
                if self.verbose:
                    print('runaway')
                    print(f'{len(self.times)} minutes')
                self.generate_results()
                self.results['result'] = 'runaway'
                return self.results

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

    def generate_results(self):
        self.results['limit'] = self.limit
        self.results['stop'] = self.stop
        self.results['minutes'] = len(self.times)
        self.results['begin'] = self.times[0]
        self.results['end'] = self.times[-1]
