from queue import Queue
from datetime import datetime as dt
import pytest
from rj.models import Evaluator

# pylint: skip-file
# https://docs.pytest.org/en/6.2.x/getting-started.html
# https://docs.pytest.org/en/6.2.x/monkeypatch.html
# https://docs.pytest.org/en/6.2.x/fixture.html
# https://docs.pytest.org/en/6.2.x/capture.html

class TestEvaluator:
    def test_positive_change(self):
        e = Evaluator(4, 0.3, Queue(), Queue())
        for value in range(10, 14):
            e.eval(dt.now().time(), value)
        assert e.outq.get_nowait() == 'call'

    def test_negative_change(self):
        e = Evaluator(4, -0.2, Queue(), Queue())
        for value in range(14, 10, -1):
            e.eval(dt.now().time(), value)
        assert e.outq.get_nowait() == 'put'

    def test_that_maxpoints_is_honored(self):
        e = Evaluator(2, 0.1, Queue(), Queue())
        for value in [1, 1, 1]:
            e.eval(dt.now().time(), value)
        assert len(e.values) == 2
        assert len(e.times) == 2

    def test_percent_change_precision(self):
        assert Evaluator.percent_change(9, 15) == 0.667
