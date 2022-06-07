#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from time import sleep
from queue import Queue
from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from dateutil.parser import parse
import pytz
import utils

sys.path.insert(1, os.path.join(sys.path[0], '..'))
# pylint: disable=import-error, wrong-import-position
from rj.models import Evaluator, Trader, Point

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest rj')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-c', '--cooldown', help='cooldown period', default=30, type=int)
    parser.add_argument('-p', '--points', help='points', type=int, required=True)
    parser.add_argument('--change', help='change', type=float, required=True)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true', default=True)
    return parser.parse_args()

def main(start, max_points, change, cooldown_points):
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    pointq = Queue()
    orderq = Queue()

    df = get_spy_timeseries_data(start)

    est = pytz.timezone('us/eastern')

    # Publish points to pointq
    begin = parse('11:00:00').astimezone(est).time()
    end = parse('14:30:00').astimezone(est).time()
    for i in df.itertuples():
        timestamp = i[5].astimezone(est).time()
        if timestamp > begin and timestamp < end:
            pointq.put(Point(utils.to_dst(i[5]).time(), i[6]))

    # Consume all the points in pointq
    e = Evaluator(max_points, change, cooldown_points, pointq, orderq)
    # pylint: disable=attribute-defined-outside-init
    e.daemon = True
    e.start()

    config = {
        'ticker': 'SPY',
        'days': 14,
        'dte_min': 1,
        'dte_max': 4,
        'bracket': 0.2,
        'live_trading': 'DISABLED',
        'capital': '100',
    }

    b = Backtester(config, orderq, start)
    b.daemon = True
    b.start()

    while True:
        # Sleep for a tiny bit to let Evaluator's thread close cleanly.
        if pointq.qsize() == 0:
            sleep(2)
            sys.exit(0)

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


class Backtester(Trader):
    def __init__(self, inq, outq, start):
        self._start = start
        super().__init__(inq, outq)

    def run(self):
        while True:
            order = self.inq.get()
            self.putCall = order.putCall
            self.last = order.last
            self.timestamp = order.timestamp
            self.set_strike()
            self.find_exp()

            # Query influx using the exp. Use the start and stop of self.timestamp to get the mark
            self.set_mark()
            self.set_limit()
            self.set_stop()

            msg = (f"{self.timestamp} {self.putCall} {self.exp} @ {self.strike} ${self.config['capital']} "
                   f"mark={self.mark}, limit={self.limit}, stop={self.stop}")

            self.notify(msg)

            self.set_mark_data()
            self.backtest()

            self.inq.task_done()

    def find_exp(self):
        month = parse(self._start).strftime('%b').upper()
        load_dotenv()
        token = os.environ['INFLUXDB_TOKEN']
        url = os.environ['INFLUXDB_URL']
        client = InfluxDBClient(url=url, token=token, org="default")
        query_api = client.query_api()

        query = f"""
            import "influxdata/influxdb/schema"

            schema.measurementTagValues(bucket: "main", measurement: "options", tag: "exp")
            |> filter(fn: (r) =>  r._value =~ /{month}/)
        """
        exps = query_api.query_data_frame(query)

        for exp in exps.itertuples():
            # > guraentees at least 1dte
            if parse(exp[3]) > parse(self._start):
                self.exp = exp[3]
                return

    def set_mark(self):
        # use the strike and exp to query influx and get the mark. also use the start and self.timestamp
        load_dotenv()
        token = os.environ['INFLUXDB_TOKEN']
        url = os.environ['INFLUXDB_URL']

        client = InfluxDBClient(url=url, token=token, org="default")
        query_api = client.query_api()

        start_dt = parse(self._start)
        _timestamp = timedelta(hours=self.timestamp.hour, minutes=self.timestamp.minute)
        stop_dt = start_dt + _timestamp

        utc = pytz.utc
        fmt = '%Y-%m-%dT%H:%M:%SZ'

        stop = stop_dt.astimezone(utc).strftime(fmt)
        start = start_dt.astimezone(utc).strftime(fmt)

        query = f"""
            from(bucket: "main")
                |> range(start: {start}, stop: {stop})
                |> filter(fn: (r) => r._measurement == "options")
                |> filter(fn: (r) => r.symbol == "SPY")
                |> filter(fn: (r) => r._field == "mark")
                |> filter(fn: (r) => r.putCall == "{self.putCall}")
                |> filter(fn: (r) => r.exp == "{self.exp}")
                |> filter(fn: (r) => r.strike == "{self.strike}")
                |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
                |> last()
        """
        df = query_api.query_data_frame(query)
        self.mark = df['_value'][0]

    def set_mark_data(self):
        load_dotenv()
        token = os.environ['INFLUXDB_TOKEN']
        url = os.environ['INFLUXDB_URL']

        client = InfluxDBClient(url=url, token=token, org="default")
        query_api = client.query_api()

        _timestamp = timedelta(hours=self.timestamp.hour, minutes=self.timestamp.minute)
        trade_open_dt = parse(self._start) + _timestamp
        market_close_dt = parse(self._start) + timedelta(hours=16)

        utc = pytz.utc
        fmt = '%Y-%m-%dT%H:%M:%SZ'

        start = trade_open_dt.astimezone(utc).strftime(fmt)
        stop = market_close_dt.astimezone(utc).strftime(fmt)

        query = f"""
            from(bucket: "main")
                |> range(start: {start}, stop: {stop})
                |> filter(fn: (r) => r._measurement == "options")
                |> filter(fn: (r) => r.symbol == "SPY")
                |> filter(fn: (r) => r._field == "mark")
                |> filter(fn: (r) => r.putCall == "{self.putCall}")
                |> filter(fn: (r) => r.exp == "{self.exp}")
                |> filter(fn: (r) => r.strike == "{self.strike}")
                |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
        """
        self.mark_data = query_api.query_data_frame(query)

    def backtest(self):
        est = pytz.timezone('us/eastern')

        for i in self.mark_data.itertuples():
            mark = i[6]
            timestamp = i[5].astimezone(est).strftime('%H:%M:%S')
            if mark >= self.limit:
                print(f'{timestamp} limit hit at {mark}\t\tSuccess')
                return
            elif mark <= self.stop:
                print(f'{timestamp} stop hit at {mark}\tFailed')
                return

    def notify(self, msg):
        print(msg)

if __name__ == '__main__':
    args = parse_arguments()
    main(args.start, args.points, args.change, args.cooldown)
