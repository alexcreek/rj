#!/usr/bin/env python3
import os
import sys
import argparse
from time import sleep
from queue import Queue
from datetime import datetime as dt
import numpy as np
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import utils

sys.path.insert(1, os.path.join(sys.path[0], '..'))
# pylint: disable=import-error, wrong-import-position
from rj.models import Evaluator, Point

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest rj')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-c', '--cooldown', help='cooldown period', default=30, type=int)
    parser.add_argument('-p', '--points', help='points', type=int, required=True)
    parser.add_argument('--change', help='change', type=float, required=True)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true', default=True)
    return parser.parse_args()

def main(start, _cooldown_limit, points, change):
    pointq = Queue()
    orderq = Queue()

    df = get_spy_timeseries_data(start)

    #for i in np.arange(0.1, 10.1, .1):
    #    pointq.put(Point(dt.now().time(), i))
    for i in df.itertuples():
        pointq.put(Point(utils.to_dst(i[5]).time(), i[6]))

    e = TestEvaluator(points, change, pointq, orderq, _cooldown_limit)
    # pylint: disable=attribute-defined-outside-init
    e.daemon = True
    e.start()

    while True:
        if pointq.qsize() == 0:
            sleep(0.5)
            sys.exit(0)

class TestEvaluator(Evaluator):
    def __init__(self, max_points, change, inq, outq, cooldown_limit):
        super().__init__(max_points, change, inq, outq)
        self.cooldown_limit = cooldown_limit
        self._cooldown = False
        self.iterations = 0

    def eval(self, timestamp, value):
        """Apply evaluation logic to the data.

        Args:
            timestamp (datetime.datetime.time): The point's time.
            value (float):  The point's value.
        """
        self.values.append(value)
        self.times.append(timestamp)

        # Skip evaluation until we have enough points
        if len(self.values) < self.max_points:
            return

        if self._cooldown:
            self.iterations += 1
            if self.iterations == self.cooldown_limit:
                self._cooldown = False
                self.iterations = 0
            else:
                return

        # Evaluate using the values of the first and last points
        changed = self.percent_change(self.values[0], self.values[-1])

        if self.change_threshold > 0:
            if changed >= self.change_threshold:
                print(f'{self.times[-1]} call triggered by {changed} change')
                self._cooldown = True
        else:
            if changed <= self.change_threshold:
                print(f'{self.times[-1]} put triggered by {changed} change' )
                self._cooldown = True

def get_spy_timeseries_data(start):
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
                        |> filter(fn: (r) => r._measurement == "underlying")
                        |> filter(fn: (r) => r.symbol == "SPY")
                        |> filter(fn: (r) => r._field == "last")
                        |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
                 """
                return query_api.query_data_frame(query)


if __name__ == '__main__':
    args = parse_arguments()
    main(args.start, args.cooldown, args.points, args.change)
