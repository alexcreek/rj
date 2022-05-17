from queue import Queue
from datetime import datetime as dt
import datetime
import pytest
import numpy as np
from rj.models import Evaluator, Point, Order, Trader
import rj

# pylint: skip-file
# https://docs.pytest.org/en/6.2.x/getting-started.html
# https://docs.pytest.org/en/6.2.x/monkeypatch.html
# https://docs.pytest.org/en/6.2.x/fixture.html
# https://docs.pytest.org/en/6.2.x/capture.html

@pytest.fixture
def config(monkeypatch):
    monkeypatch.setenv('CAPITAL', '1000')
    monkeypatch.setenv('CLIENT_ID', 'asdf')
    monkeypatch.setenv('REFRESH_TOKEN', 'asdf')
    monkeypatch.setenv('TD_ACCOUNT_ID', 'asdf')
    monkeypatch.setenv('TWILIO_ACCOUNT_SID', 'asdf')
    monkeypatch.setenv('TWILIO_AUTH_TOKEN', 'asdf')
    return rj.configure()

@pytest.fixture
def evaluator(points, change):
    return Evaluator(points, change, Queue(), Queue())

@pytest.fixture
def trader(config):
    return Trader(config, Queue())


class TestEvaluator:
    @pytest.mark.parametrize('points, change', [(4, 0.3)])
    def test_positive_change(self, evaluator, points, change):
        e = evaluator
        for value in np.arange(10.0, 14.0):
            e.eval(dt.now().time(), value)
        assert e.outq.get_nowait().putCall == 'call'

    @pytest.mark.parametrize('points, change', [(4, -0.2)])
    def test_negative_change(self, evaluator, points, change):
        e = evaluator
        for value in np.arange(14.0, 10.0, -1):
            e.eval(dt.now().time(), value)
        assert e.outq.get_nowait().putCall == 'put'

    @pytest.mark.parametrize('points, change', [(2, 0.1)])
    def test_that_maxpoints_is_honored(self, evaluator, points, change):
        e = evaluator
        for value in [1.0, 1.0, 1.0]:
            e.eval(dt.now().time(), value)
        assert len(e.values) == 2
        assert len(e.times) == 2

    def test_percent_change_precision(self):
        assert Evaluator.percent_change(9, 15) == 0.667

    @pytest.mark.parametrize('points, change', [(2, 0.1)])
    def test_consuming_from_a_queue(self, evaluator, points, change):
        e = evaluator
        e.daemon = True # Stop when pytest exits.
        e.inq.put(Point(dt.now().time(), 1.0))
        e.start()
        assert len(e.values) == 1
        assert len(e.times) == 1

class TestPoint:
    def test_that_timestamps_are_dt_objects(self):
        p = Point(dt.now().time(), 1.0)
        assert isinstance(p.timestamp, datetime.time)

    def test_that_values_are_floats(self):
        p = Point(dt.now().time(), 1.0)
        assert isinstance(p.value, float)

    def test_timestamp_exceptions(self):
        with pytest.raises(TypeError):
            Point(dt.now().time().isoformat(), 1.0)

    def test_value_exceptions(self):
        with pytest.raises(TypeError):
            Point(dt.now().time().isoformat(), '1.0')

class TestOrder:
    def test_that_putcall_is_lowercase(self):
        o = Order('CALL', 1.1)
        assert o.putCall == 'call'

    def test_that_last_is_a_float(self):
        o = Order('call', 1.1)
        assert isinstance(o.last, float)

    def test_last_exceptions(self):
        with pytest.raises(TypeError):
            Order('call', 1)

class TestTrader:
    def test_set_strike(self, trader):
        t = trader
        t.last = 400.4
        t.set_strike()
        assert t.strike == '400.0'

    def test_set_mark(self, trader):
        t = trader
        t.contracts = {'400.0': [{'mark': 0.55}]}
        t.strike = '400.0'
        t.set_mark()
        assert t.mark == 0.55

    def test_set_limit(self, trader, monkeypatch):
        t = trader
        t.mark = 0.55
        monkeypatch.setitem(trader.config, 'bracket', 0.5)
        t.set_limit()
        assert t.limit == 0.825

    def test_set_stop(self, trader, monkeypatch):
        t = trader
        t.mark = 0.55
        monkeypatch.setitem(trader.config, 'bracket', 0.5)
        t.set_stop()
        assert t.stop == 0.275

    def test_find_exp_by_dte(self):
        assert False

    def test_trade(default):
        assert False
