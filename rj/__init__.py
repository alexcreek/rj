import os
import sys
import logging
from queue import Queue
from .models import Poller, Evaluator, Trader

def configure():
    """Collect app settings from environment variables.

    Returns:
        dict
    """
    try:
        return {
            'capital': int(os.environ['CAPITAL']),
            'days': int(os.getenv('DAYS', '14')),
            'dte_min': int(os.getenv('DTE_MIN', '1')),
            'dte_max': int(os.getenv('DTE_MAX', '4')),
            'ticker': os.getenv('TICKER', 'SPY').upper(),
            'points': int(os.getenv('POINTS', '4')),
            'change': float(os.getenv('CHANGE', '0.0025')),
            'bracket': float(os.getenv('BRACKET', '0.2')),
            'twilio_from': os.getenv('TWILIO_FROM', '+1234567890'),
            'twilio_to': os.getenv('TWILIO_TO', '+1234567890'),
            'cooldown_points': int(os.getenv('COOLDOWN_POINTS', '80')),
            'live_trading': os.getenv('LIVE_TRADING', 'ENABLED').upper(),
            'client_id': os.environ['CLIENT_ID'], # tdameritrade
            'refresh_token': os.environ['REFRESH_TOKEN'], # tdameritrade
            'td_account_id': os.environ['TD_ACCOUNT_ID'], # tdameritrade
            'twilio_account_sid': os.environ['TWILIO_ACCOUNT_SID'],
            'twilio_auth_token': os.environ['TWILIO_AUTH_TOKEN'],
        }
    except KeyError as e:
        print(f'Config error: {e} environment variable not found')
        sys.exit(1)

def main():
    logging.basicConfig(format='%(asctime)s %(message)s',
        datefmt='%d/%B/%Y %I:%M:%S', level=logging.INFO)

    config = configure()
    pointq = Queue()
    orderq = Queue()

    # Poll
    p = Poller(config, pointq)
    p.start()

    # Evaluate
    e = Evaluator(config['points'], config['change'],
            config['cooldown_points'], pointq, orderq)
    e.start()

    # Trade
    t = Trader(config, orderq)
    t.start()
