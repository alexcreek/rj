#!/usr/bin/env python3
import argparse
import os
from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import utils

def parse_arguments():
    parser = argparse.ArgumentParser(description='Determine the fair price for a contract')
    parser.add_argument('-e', '--exp', help="contract's expiration", type=str, required=True)
    parser.add_argument('-t', '--type', help='put or call', type=str, required=True)
    parser.add_argument('-s', '--strike', help="contract's strike", type=float, required=True)
    parser.add_argument('-v', '--vix', help='vix price', type=float)
    parser.add_argument('-m', '--mark', help='mark', type=float)
    parser.add_argument('--start', help='date to start on', type=str)
    parser.add_argument('--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()

def query_vix(client, lookback):
    query_api = client.query_api()
    df = query_api.query_data_frame(
        f"""
            from(bucket: "main")
                |> range(start: {dt.isoformat(lookback.replace(hour=13, minute=30, second=0, microsecond=0))}Z,
                    stop: {dt.isoformat(lookback.replace(hour=20, minute=00, second=0, microsecond=0))}Z)
                |> filter(fn: (r) => r["_measurement"] == "underlying")
                |> filter(fn: (r) => r["symbol"] == "$VIX.X")
                |> filter(fn: (r) => r["_field"] == "last")
                |> aggregateWindow(every: 24h, fn: mean, createEmpty: false)
        """
    )

    v = 0
    if not df.empty:
        v = round(df['_value'][0], 2)
    return v

def get_current_vix(client):
    last_week = dt.now() - timedelta(days=5)
    query_api = client.query_api()
    df = query_api.query_data_frame(
        f"""
            from(bucket: "main")
                |> range(start: {dt.isoformat(last_week)}Z,
                    stop: {dt.isoformat(dt.now())}Z)
                |> filter(fn: (r) => r["_measurement"] == "underlying")
                |> filter(fn: (r) => r["symbol"] == "$VIX.X")
                |> filter(fn: (r) => r["_field"] == "last")
                |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)
                |> last()
        """
    )

    v = 0
    if not df.empty:
        v = round(df['_value'][0], 2)
    return v

def query_mark(client, lookback, exp, putCall, strike):
    query_api = client.query_api()
    df = query_api.query_data_frame(
        f"""
            from(bucket: "main")
                |> range(start: {dt.isoformat(lookback.replace(hour=13, minute=30, second=0, microsecond=0))}Z,
                    stop: {dt.isoformat(lookback.replace(hour=20, minute=00, second=0, microsecond=0))}Z)
                |> filter(fn: (r) => r["_measurement"] == "options")
                |> filter(fn: (r) => r["_field"] == "mark")
                |> filter(fn: (r) => r["putCall"] == "{putCall}")
                |> filter(fn: (r) => r["exp"] == "{exp}")
                |> filter(fn: (r) => r["strike"] == "{strike}")
                |> aggregateWindow(every: 24h, fn: mean, createEmpty: false)
        """
    )

    m = 0
    if not df.empty:
        m = round(df['_value'][0], 2)
    return m

def get_current_mark(client, exp, putCall, strike):
    last_week = dt.now() - timedelta(days=5)
    query_api = client.query_api()
    df = query_api.query_data_frame(
        f"""
            from(bucket: "main")
                |> range(start: {dt.isoformat(last_week)}Z,
                    stop: {dt.isoformat(dt.now())}Z)
                |> filter(fn: (r) => r["_measurement"] == "options")
                |> filter(fn: (r) => r["_field"] == "mark")
                |> filter(fn: (r) => r["putCall"] == "{putCall}")
                |> filter(fn: (r) => r["exp"] == "{exp}")
                |> filter(fn: (r) => r["strike"] == "{strike}")
                |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)
                |> last()
        """
    )

    m = 0
    if not df.empty:
        m = round(df['_value'][0], 2)
    return m


def main(exp, putCall, strike, vix, mark, start, verbose=False):
    # pylint: disable=too-many-locals
    """
    The algorithm is:
    1. Find how many days until the contract expiress, this is the ttl.
    2. For each expiration we know about:
        1. Convert the exp to a timestamp.
        2. Calculate the date to match the input's ttl.
        2. Look back at the ttl date.
        3. Record the mark and the vix.
    """
    load_dotenv()
    token = os.environ['INFLUXDB_TOKEN']
    url = os.environ['INFLUXDB_URL']

    client = InfluxDBClient(url=url, token=token, org="default")

    if not vix:
        vix = get_current_vix(client)

    if not mark:
        mark = get_current_mark(client, exp, putCall, strike)

    # Find the exp's ttl.
    _start = None
    if start:
        _start = parse(start)
    ttl = utils.to_ttl(exp.strip(), _start)

    print(f'[*] {exp} expires in {ttl.days} days')
    print(f'[*] Searching for {putCall}s @ {strike} with a {ttl.days} day ttl')
    print( '    exp\t\tvix\tmark\tvmr\tmoneyness')

    historical_exps = ['16 FEB 22', '15 MAR 22', '20 APR 22']
    for _exp in historical_exps:
        lookback = dt.strptime(_exp, '%d %b %y') - ttl

        _vix = query_vix(client, lookback)
        _mark = query_mark(client, lookback, _exp, putCall, strike)
        print(f'    {_exp}\t{_vix}\t{_mark}\t{utils.to_vmr(_vix, _mark)}\t{utils.moneyness(putCall, _vix, strike)}')

    print(f'\n    {exp}\t{vix}\t{mark}\t{utils.to_vmr(vix, mark)}\t{utils.moneyness(putCall, vix, strike)}')

if __name__ == '__main__':
    args = parse_arguments()
    main(
        args.exp.upper().strip(),
        args.type.strip(),
        args.strike,
        args.vix,
        args.mark,
        args.start,
        args.verbose
    )
