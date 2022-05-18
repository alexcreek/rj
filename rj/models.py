from collections import deque
from threading import Thread
import datetime
import spivey
from twilio.rest import Client

class Evaluator(Thread):
    """Event driven class to evaluate timeseries data for change."""
    def __init__(self, max_points, change, inq, outq):
        """
        Args:
            max_points (int): The max number of points to evaluate.
            change (float): The amount of change to action on.
            inq (Queue): Queue to consume from.
            outq (Queue): Queue to publish to.
        """
        super().__init__()
        self.max_points = max_points
        self.change_threshold = change
        self.values = deque(maxlen=max_points)
        self.times = deque(maxlen=max_points)
        self.inq = inq
        self.outq = outq

    def run(self):
        while True:
            p = self.inq.get()
            self.eval(p.timestamp, p.value)
            self.inq.task_done()

    def eval(self, timestamp, value):
        """Apply evaluation logic to the data.

        Args:
            timestamp (datetime.datetime.time): The point's time.
            value (float):  The point's value.
        """
        self.values.append(value)
        self.times.append(timestamp)

        # Skip evaluation until we have enough points
        if len(self.values) < self.max_points:
            return

        # Evaluate using the values of the first and last points
        changed = self.percent_change(self.values[0], self.values[-1])

        #   -.1  <=  -.2 - do nothing
        #   -.2  <=  -.2 - buy
        #   -.3  <=  -.2 - buy

        #    .1  >=  .2 - do nothing
        #    .2  >=  .2 - buy
        #    .3  >=  .2 - buy
        # Take positive and negative change_thresholds into account
        if self.change_threshold > 0:
            if changed >= self.change_threshold:
                self.outq.put(Order('call', value))
        else:
            if changed <= self.change_threshold:
                self.outq.put(Order('put', value))

    @staticmethod
    def percent_change(start, current):
        """Calculate the percent of change between two values.

        Args:
           start (float): The starting value.
           current (float):  The current values.

        Returns:
            float
        """
        return round((current - start) / start, 3)


class Trader(Thread):
    """Event driven class to make trades"""
    def __init__(self, config, inq):
        super().__init__()
        self.client = spivey.Client()
        self.config = config
        self.inq = inq
        self.putCall = str
        self.last = float # Underlying ticker's price
        self.strike = str
        self.mark = float # Contract's price
        self.limit = float
        self.stop = float
        self.exp = str
        self.contracts = dict

    def run(self):
        while True:
            order = self.inq.get()
            self.putCall = order.putCall
            self.last = order.last

            # Set instance properties that are dependent on last
            self.set_strike()
            self.set_mark()
            self.set_limit()
            self.set_stop()

            # Set exp and contracts
            self.find_exp_by_dte()

            self.trade()
            self.inq.task_done()

    def trade(self):
        """Execute a trade"""
        contract_symbol = self.client.to_full_symbol(
            self.config['ticker'],
            self.exp,
            self.putCall,
            self.strike
        )

        self.client.buy_oco(
            self.config['capital'],
            contract_symbol,
            self.mark,
            self.limit,
            self.stop,
        )

    def set_strike(self):
        """Set strike using last.

        Strike is used as the key for contracts. As such, it must be a string with .0 suffixed.
        """
        self.strike = f'{str(round(self.last))}.0'

    def set_mark(self):
        """Set mark using contracts and strike."""
        self.mark = self.contracts[self.strike][0]['mark'] # type: ignore

    def set_limit(self):
        """Set limit using mark and self.config['bracket']"""
        self.limit = round(self.mark + (self.mark * self.config['bracket']), 4)

    def set_stop(self):
        """Set stop using mark and self.config['bracket']"""
        self.stop = self.mark - (self.mark * self.config['bracket'])

    def find_exp_by_dte(self):
        """Find the first expiration given a range of dtes"""
        options = self.client.options(
            self.config['ticker'],
            self.config['days']
        )

        _key = f'{self.putCall}ExpDateMap'

        for contract in options[_key].keys():
            exp, dte = contract.split(':')
            if int(dte) >= self.config['dte_min'] and int(dte) <= self.config['dte_max']:
                print(f'{exp} dte contract found - {exp}')
                self.exp = exp
                self.contracts = options[_key][contract]
                return
        raise RuntimeError('Contracts with dte between min and max not found')

    def notify(self, msg):
        """Send an sms via twilio.

        Args:
            msg (str): Body of the message.
        """
        client = Client(self.config['twilio_account_sid'], self.config['twilio_auth_token'])

        client.messages.create(
            body = msg,
            from_ = self.config['twilio_from'],
            to = self.config['twilio_to'],
        )


class Point():
    """Class to encode a format for points when communicating between queues"""
    def __init__(self, timestamp, value):
        if isinstance(timestamp, datetime.time):
            self._timestamp = timestamp
        else:
            raise TypeError(timestamp)

        if isinstance(value, float):
            self._value = value
        else:
            raise TypeError(value)

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def value(self):
        return self._value

class Order():
    """Class to encode a format for buy orders between queues"""
    def __init__(self, putCall, last):
        if 'put' in putCall.lower() or 'call' in putCall.lower():
            self._putCall = putCall.lower()
        else:
            raise ValueError(putCall)

        if isinstance(last, float):
            self._last = last
        else:
            raise TypeError(last)

    @property
    def putCall(self):
        return self._putCall

    @property
    def last(self):
        return self._last
