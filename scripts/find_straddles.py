#!/usr/bin/env python3 -u
import argparse
from datetime import datetime as dt
from dotenv import load_dotenv
from dateutil.parser import parse as date_parse
import spivey
from apscheduler.schedulers.blocking import BlockingScheduler
from datadog import initialize, api


def parse_arguments():
    parser = argparse.ArgumentParser(description='Backtest timeseries data')
    parser.add_argument('-t', '--ticker', help='ticker', type=str, default="$VIX.X")
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    parser.add_argument('-n', '--notify', help='notify datadog on findings', action='store_true')
    return parser.parse_args()

def notify(msg, ticker, exp, strike):
    initialize()
    tags=[f"source:{__file__.rsplit('/', maxsplit=1)[-1]}",
            f'ticker:{ticker}', f'strike:{strike}', f'exp:{exp}']
    api.Event.create(title='Straddle Found', text=msg, tags=tags)

def main(ticker, client, _notify, verbose):
    load_dotenv()
    options = client.options(ticker, 45)
    calls = options['callExpDateMap']
    puts = options['putExpDateMap']

    thresholds = {
        'AMZN': 10,
        'FB': 1,
        'TSLA': 1,
        'SPOT': 1,
        'GOOG': 1,
        'NFLX': 1,
        'SHOP': 1,
        'PTON': 1,
        'NVDA': 1,
        'MSFT': 1,
        'AAPL': 1,
        'V': 1,
        'XOM': 1,
        'SNAP': 1,
        'SNOW': 1,
        'AMD': 0.2,
    }

    # pylint: disable=too-many-nested-blocks
    for i in puts:
        exp = dt.strftime(date_parse(i.split(':')[0]),'%d %b %y').upper()
        if verbose:
            print(f"[*] working through {exp}")
        for j in puts[i]:
            for k in puts[i][j]:
                if k['mark'] > 0 and calls[i][j][0]['mark'] > 0:
                    delta = round(abs(k['mark'] - calls[i][j][0]['mark']), 2)
                    if verbose:
                        print(' ', 'put', k['strikePrice'], k['mark'])
                        print(' ', 'call', calls[i][j][0]['strikePrice'], calls[i][j][0]['mark'])
                        print(' ', 'delta', delta)
                    if delta <= thresholds[ticker]:
                        msg = f"{ticker} {exp} @ {k['strikePrice']} - mark={k['mark']} vol={k['totalVolume']} delta={delta}"
                        print(msg)
                        if _notify:
                            notify(msg, ticker, exp, k['strikePrice'])
    print('')


if __name__ == '__main__':
    print(f"Started {__file__.rsplit('/', maxsplit=1)[-1]}")
    args = parse_arguments()
    c = spivey.Client()
    sched = BlockingScheduler()
    sched.add_job(
        main, args=(args.ticker.upper(), c, args.notify, args.verbose),
        trigger='cron', second='*/30'
    )
    try:
        sched.start()
    except KeyboardInterrupt:
        pass
