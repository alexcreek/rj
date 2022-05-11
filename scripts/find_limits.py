#!/usr/bin/env python3
import os
import argparse
import utils
import pandas as pd
import numpy as np
from lib import backtest

def parse_arguments():
    parser = argparse.ArgumentParser(description='Find the highest performing bracket for SPY options')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-e', '--exp', help='expiration', required=True)
    parser.add_argument('-s', '--strike', help='strike', required=True)
    parser.add_argument('-t', '--type', help='put or call', required=True)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()


def main(start, exp, strike, putCall, verbose=False):
    total = []
    ts = backtest.query_timeseries(start, exp, strike, putCall)

    for _limit in np.arange(0.05, 1.05, 0.05):
        limit = round(_limit, 2)
        day_by_min = []
        print(f'[*] processing {limit}')

        # start from every minute in the day
        for m in utils.timestamps_one_day_by_minute():
            day_by_min.append(backtest.main(ts, limit, limit * -1, m, verbose))

        res = pd.DataFrame(list(filter(None, day_by_min)))

        total.append({
            'limit': res['limit'][0],
            'stop': res['stop'][0],
            'limit %': round(len(res.query('result == "limit"')) / len(res) * 100, 2),
            'stop %': round(len(res.query('result == "stop"')) / len(res) * 100, 2),
            'runaway %': round(len(res.query('result == "runaway"')) / len(res) * 100, 2),
            'limits': len(res.query('result == "limit"')),
            'stops': len(res.query('result == "stop"')),
            'runaways': len(res.query('result == "runaway"')),
        })
    print('[*] done')
    filename = f"{exp.replace(' ', '')}_{strike}_{putCall}.xlsx"
    pd.DataFrame(total).to_excel(filename)
    os.system(f'open {filename}')

if __name__ == '__main__':
    args = parse_arguments()
    main(
        args.start,
        args.exp.upper(),
        args.strike,
        args.type,
        args.verbose,
    )
