import pytest
import rj

# https://docs.pytest.org/en/6.2.x/getting-started.html
# https://docs.pytest.org/en/6.2.x/monkeypatch.html
# https://docs.pytest.org/en/6.2.x/fixture.html
# https://docs.pytest.org/en/6.2.x/capture.html

class TestBuy:
    def test_something(self, monkeypatch):
        assert False

class TestFetchPrice:
    def test_success(self, monkeypatch):
        assert False

    def test_failure(self, monkeypatch):
        assert False

class TestCooldown:
    def test_ignoring_a_buy_while_cooling_down(self, monkeypatch):
        assert False

    def test_working_like_normal(self, monkeypatch):
        assert False
