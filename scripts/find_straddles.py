#!/usr/bin/env python3
import argparse
from datetime import datetime as dt
from dotenv import load_dotenv
from dateutil.parser import parse as date_parse
import spivey
from apscheduler.schedulers.blocking import BlockingScheduler
from datadog import initialize, api


def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('-t', '--ticker', help="ticker", type=str, default="$VIX.X")
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()

def notify(msg, ticker, exp, strike):
    initialize()
    tags=[f"source:{__file__.rsplit('/', maxsplit=1)[-1]}",
            f'ticker:{ticker}', f'strike:{strike}', f'exp:{exp}']
    api.Event.create(title='Straddle Found', text=msg, tags=tags)

def main(ticker, client, verbose):

    load_dotenv()
    options = client.options(ticker, 45)
    calls = options['callExpDateMap']
    puts = options['putExpDateMap']

    for i in puts:
        exp = dt.strftime(date_parse(i.split(':')[0]),'%d %b %y').upper()
        if verbose:
            print(f"[*] working through {exp}")
        for j in puts[i]:
            for k in puts[i][j]:
                if k['mark'] > 0:
                    if abs(k['mark'] - calls[i][j][0]['mark']) <= 0.1:
                        msg = f"{ticker} {exp} @ {k['strikePrice']} - {k['mark']} vol {k['totalVolume']}"
                        print(msg)
                        notify(msg, ticker, exp, k['strikePrice'])


if __name__ == '__main__':
    print(f"Started {__file__.rsplit('/', maxsplit=1)[-1]}")
    args = parse_arguments()
    c = spivey.Client()
    sched = BlockingScheduler()
    sched.add_job(
        main, args=(args.ticker.upper(), c, args.verbose),
        trigger='cron', second='*/30'
    )
    sched.start()
