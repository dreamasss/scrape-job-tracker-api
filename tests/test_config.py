from app.config import (
    DEFAULT_FETCH_TIMEOUT_SECONDS,
    DEFAULT_USER_AGENT,
    get_fetch_timeout_seconds,
    get_user_agent,
)


def test_get_fetch_timeout_seconds_uses_default(monkeypatch):
    monkeypatch.delenv("FETCH_TIMEOUT_SECONDS", raising=False)

    assert get_fetch_timeout_seconds() == DEFAULT_FETCH_TIMEOUT_SECONDS


def test_get_fetch_timeout_seconds_uses_env_value(monkeypatch):
    monkeypatch.setenv("FETCH_TIMEOUT_SECONDS", "5.5")

    assert get_fetch_timeout_seconds() == 5.5


def test_get_fetch_timeout_seconds_falls_back_for_invalid_value(monkeypatch):
    monkeypatch.setenv("FETCH_TIMEOUT_SECONDS", "bad-value")

    assert get_fetch_timeout_seconds() == DEFAULT_FETCH_TIMEOUT_SECONDS


def test_get_fetch_timeout_seconds_falls_back_for_negative_value(monkeypatch):
    monkeypatch.setenv("FETCH_TIMEOUT_SECONDS", "-1")

    assert get_fetch_timeout_seconds() == DEFAULT_FETCH_TIMEOUT_SECONDS


def test_get_user_agent_uses_default(monkeypatch):
    monkeypatch.delenv("USER_AGENT", raising=False)

    assert get_user_agent() == DEFAULT_USER_AGENT


def test_get_user_agent_uses_env_value(monkeypatch):
    monkeypatch.setenv("USER_AGENT", "CustomBot/1.0")

    assert get_user_agent() == "CustomBot/1.0"
