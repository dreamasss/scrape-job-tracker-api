import os

DEFAULT_FETCH_TIMEOUT_SECONDS = 10.0
DEFAULT_USER_AGENT = "ScrapeJobTrackerBot/0.1"


def get_fetch_timeout_seconds() -> float:
    value = os.getenv("FETCH_TIMEOUT_SECONDS")

    if value is None:
        return DEFAULT_FETCH_TIMEOUT_SECONDS

    try:
        timeout = float(value)
    except ValueError:
        return DEFAULT_FETCH_TIMEOUT_SECONDS

    if timeout <= 0:
        return DEFAULT_FETCH_TIMEOUT_SECONDS

    return timeout


def get_user_agent() -> str:
    return os.getenv("USER_AGENT", DEFAULT_USER_AGENT)
