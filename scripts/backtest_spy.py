#!/usr/bin/env python3
import argparse
import os
import sys
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from dateutil.parser import parse
import utils
from lib import backtest

def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-e', '--exp', help='expiration', required=True)
    parser.add_argument('-s', '--strike', help='strike', required=True)
    parser.add_argument('-t', '--type', help='put or call', required=True)
    parser.add_argument('--limit', help='limit', type=float, required=True)
    parser.add_argument('--stop', help='stop limit', type=float, required=True)
    parser.add_argument('--time', help='time to start with', required=True)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()


def main(start, exp, strike, putCall, limit, stop, time, verbose=False):
    backtest.main(start, exp, strike, putCall, limit, stop, time, verbose)


if __name__ == '__main__':
    args = parse_arguments()
    main(
        args.start,
        args.exp.upper(),
        args.strike,
        args.type,
        args.limit,
        args.stop,
        args.time,
        args.verbose,
    )
