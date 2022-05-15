from collections import deque
from threading import Thread
import datetime

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
                self.outq.put('call')
        else:
            if changed <= self.change_threshold:
                self.outq.put('put')

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
    def __init__(self):
        super().__init__()

    def run(self):
        pass

    def trade(self):
        pass

    def to_full_symbol(self):
        pass


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
        if isinstance(putCall, str):
            self._putCall = putCall.lower()
        else:
            raise TypeError(putCall)

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
