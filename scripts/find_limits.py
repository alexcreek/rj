#!/usr/bin/env python3
import os
import argparse
import utils
import pandas as pd
import numpy as np
import backtest

def parse_arguments():
    parser = argparse.ArgumentParser(description='What is the highest performing bracket for SPY options?')
    parser.add_argument('--start', help='day to start with', required=True)
    parser.add_argument('-e', '--exp', help='expiration', required=True)
    parser.add_argument('-s', '--strike', help='strike', required=True)
    parser.add_argument('-t', '--type', help='put or call', required=True)
    parser.add_argument('-v', '--verbose', help='enable verbose logging', action='store_true')
    return parser.parse_args()


def main(start, exp, strike, putCall, verbose=False):
    # start from every minute in the day
    total = []
    #for _limit in np.arange(0.05, 1.05, 0.05):
    for _limit in np.arange(0.05, .25, 0.05):
        day_by_min = []

        for m in utils.timestamps_one_day_by_minute():
            day_by_min.append(backtest.main(start, exp, strike, putCall, _limit, _limit * -1, m, verbose))

        res = pd.DataFrame(list(filter(None, day_by_min)))

        total.append({
            'limit': res['limit'][0],
            'stop': res['stop'][0],
            'limits percent': round(len(res.query('result == "limit"')) / len(res) * 100, 2),
            'stops percent': round(len(res.query('result == "stop"')) / len(res) * 100, 2),
            'runaways percent': round(len(res.query('result == "runaway"')) / len(res) * 100, 2),
            'limits': len(res.query('result == "limit"')),
            'stops': len(res.query('result == "stop"')),
            'runaways': len(res.query('result == "runaway"')),
        })
    pd.DataFrame(total).to_excel('find_limits.xlsx')
    os.system('open find_limits.xlsx')
    print('done')

if __name__ == '__main__':
    args = parse_arguments()
    main(
        args.start,
        args.exp.upper(),
        args.strike,
        args.type,
        args.verbose,
    )
