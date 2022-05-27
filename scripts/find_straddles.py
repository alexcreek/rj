#!/usr/bin/env python3 -u
import argparse
from datetime import datetime as dt
from dotenv import load_dotenv
from dateutil.parser import parse as date_parse
from time import sleep
import spivey

def parse_arguments():
    parser = argparse.ArgumentParser(description='Poll live options contracts looking for puts and calls around the same price')
    parser.add_argument('-t', '--ticker', help='ticker', required=True)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    parser.add_argument('-n', '--notify', help='notify datadog on findings', action='store_true')
    parser.add_argument('-e', '--exp', help='specific expiration to search for', default='')
    return parser.parse_args()

def notify(msg, ticker, exp, strike):
    pass

def main(ticker, client, _notify, _exp, verbose):
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
        'NVDA': 0.5,
        'MSFT': 1,
        'AAPL': 1,
        'V': 1,
        'XOM': 1,
        'SNAP': 1,
        'SNOW': 1,
    }

    # pylint: disable=too-many-nested-blocks
    for i in puts:
        exp = dt.strftime(date_parse(i.split(':')[0]),'%d %b %y').upper()
        if _exp:
            # Used an if not to avoid yet another nested block.
            if not _exp in exp:
                continue
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
    try:
        while True:
            main(args.ticker.upper(), c, args.notify, args.exp.upper(), args.verbose)
            sleep(30)
    except KeyboardInterrupt:
        pass
