import os
import sys
from time import sleep
import spivey
from .models import Order

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
            'points': int(os.getenv('POINTS', '10')),
            'change': float(os.getenv('CHANGE', '0.5')),
            'bracket': float(os.getenv('BRACKET', '0.2')),
            'twilio_from': os.getenv('TWILIO_FROM', '+1234567890'),
            'twilio_to': os.getenv('TWILIO_TO', '+1234567890'),
            'polling_interval': int(os.getenv('POLLING_INTERVAL', '30')),
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
    pass

# TASKS
# keep track of change
# order
# notify

# dont order before 10am and after 4pm
