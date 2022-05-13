import pytest
import rj

# https://docs.pytest.org/en/6.2.x/getting-started.html
# https://docs.pytest.org/en/6.2.x/monkeypatch.html
# https://docs.pytest.org/en/6.2.x/fixture.html
# https://docs.pytest.org/en/6.2.x/capture.html

class TestGetSettings:
    def test_reading_from_the_environment(self, monkeypatch):
        assert False

    def test_ticker_gets_upcased(self, monkeypatch):
        assert False

class TestDoesEnvvarExist:
    def test_a_missing_envvar_raises_an_exception(self, monkeypatch):
        assert False

    def test_a_present_envvar_does_nothing(self, monkeypatch):
        assert False

class TestNotify:
    def test_sending_a_text(self, monkeypatch):
        assert False

class TestBuy:
    def test_something(self, monkeypatch):
        assert False

class TestFindExp:
    def test_finding_an_exp(self, monkeypatch):
        assert False

    def test_no_exp_found(self, monkeypatch):
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

class TestEvalWindow:
    def test_calculating_change(self, monkeypatch):
        assert False

    def test_evaluating_a_time_window(self, monkeypatch):
        assert False
