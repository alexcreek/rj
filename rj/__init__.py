import os
import sys
from time import sleep
from collections import deque
from dotenv import load_dotenv
import spivey

def get_settings():
    """Collect app settings from environment variables

    Returns:
        dict
    """
    return {
        'days': int(os.getenv('DAYS', '14')),
        'ticker': os.getenv('TICKER', 'SPY').upper(),
        'points': int(os.getenv('POINTS', '10')),
        'change': float(os.getenv('CHANGE', '0.2')),
        'twilio_from': os.getenv('TWILIO_FROM', '+1234567890'),
        'twilio_to': os.getenv('TWILIO_TO', '+1234567890'),
    }

def assert_credentials_exist():
    """Assert the required env vars exist in the environment"""
    envvars = [
        'CLIENT_ID', # tdameritrade
        'REFRESH_TOKEN', # tdameritrade
        'TD_ACCOUNT_ID', # tdameritrade
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN'
    ]
    for e in envvars:
        does_envvar_exist(e)

def does_envvar_exist(var):
    try:
        os.environ[var]
    except KeyError as e:
        print(f'{e} environment variable not found')
        sys.exit(1)

def main():
    """Buy and sell options contracts when an stock's price changes.

    Args:
        ticker (str): The stock's ticker.
        days (int): The number of days to collect contracts for.
    Returns:
        Nothing yet
    """
    ticker='SPY'
    days=14
    load_dotenv()
    c = spivey.Client()
    while True:
        last = c.underlying(ticker)
        # add last to a window class instance

        # when the instance triggers, start fucking with the options
        c.options(ticker, days)
        sleep(30)
# dont order before 10am and after 4pm
# dont use apscheduler to poll
# tasks
    # keep track of change
    # order
    # notify
# when you order, text me
# only use a limit and stop of.20, $bracket
# when you buy, do the math for $bracket
# when you buy, convert to a full symbol
# when you buy,
    # find the value of spy from the api
    # find an exp within a range of 1dte to 5dte
    # drops buy puts
    # rises buy calls
# make a backend for testing - influx
# make a backend for prod - tda
# REMEMBER THE TEST DATA IS PER MINUTE BUT WE'RE GONNA HIT THE API EVERY 30S
# I think order when there's a .5% change, not sure how by much time tho
# add a backoff after triggering so there aren't repeated buys for the same change
    # poll open orders every n minutes


class EvalWindow():
    """Evaluate timeseries data for change"""
    def __init__(self, points_threshold, change_threshold):
        """
        Args:
            points_threshold (int): The amount of points to keep.
            change_threshold (float): The amount of change to action on.
        """
        self.points_threshold = points_threshold
        self.change_threshold = change_threshold
        self.points = deque(maxlen=points_threshold)
        self.times = deque(maxlen=points_threshold)

    def eval(self, time, value):
        """Apply an evaluation window to timeseries data

        Args:
            time (datetime.datetime) - The measurement's time.
            value (float) - The measurement's value.
        """
        self.points.append(value)
        self.times.append(time)

        # Skip evaluation until we have enough points
        if len(self.points) != self.points_threshold:
            return

        # Evaluate
        changed = self.change(self.points[0], self.points[-1])
        # If positive change is greater than or equal to change threshold
#        if changed <= self.change_threshold:
        # If negative change is greater than or equal to change threshold
#        if changed >= self.change_threshold:

    def change(self, start, current):
        """Calculate the percent of change between two values.

        Args:
           start (float): The starting value.
           current (float):  The current values.

        Returns:
            float
        """
        return round((current - start) / start, 4)

    def results(self):
        return self.triggered

