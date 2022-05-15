from queue import Queue
from datetime import datetime as dt
import datetime
import pytest
from rj.models import Evaluator, Point, Order

# pylint: skip-file
# https://docs.pytest.org/en/6.2.x/getting-started.html
# https://docs.pytest.org/en/6.2.x/monkeypatch.html
# https://docs.pytest.org/en/6.2.x/fixture.html
# https://docs.pytest.org/en/6.2.x/capture.html

@pytest.fixture
def evaluator(points, change):
    return Evaluator(points, change, Queue(), Queue())

class TestEvaluator:
    @pytest.mark.parametrize('points, change', [(4, 0.3)])
    def test_positive_change(self, evaluator, points, change):
        e = evaluator
        for value in range(10, 14):
            e.eval(dt.now().time(), value)
        assert e.outq.get_nowait() == 'call'

    @pytest.mark.parametrize('points, change', [(4, -0.2)])
    def test_negative_change(self, evaluator, points, change):
        e = evaluator
        for value in range(14, 10, -1):
            e.eval(dt.now().time(), value)
        assert e.outq.get_nowait() == 'put'

    @pytest.mark.parametrize('points, change', [(2, 0.1)])
    def test_that_maxpoints_is_honored(self, evaluator, points, change):
        e = evaluator
        for value in [1, 1, 1]:
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
        o = Order('BUY', 1.1)
        assert o.putCall == 'buy'

    def test_that_last_is_a_float(self):
        o = Order('buy', 1.1)
        assert isinstance(o.last, float)

    def test_last_exceptions(self):
        with pytest.raises(TypeError):
            Order('buy', 1)
