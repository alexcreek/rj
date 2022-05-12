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
