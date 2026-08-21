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


DEFAULT_ADMIN_API_KEY = ""


def get_admin_api_key() -> str:
    return os.getenv("ADMIN_API_KEY", DEFAULT_ADMIN_API_KEY).strip()


DEFAULT_RATE_LIMIT_MAX_REQUESTS = 30
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60


def get_rate_limit_max_requests() -> int:
    value = os.getenv("RATE_LIMIT_MAX_REQUESTS")

    if value is None:
        return DEFAULT_RATE_LIMIT_MAX_REQUESTS

    try:
        max_requests = int(value)
    except ValueError:
        return DEFAULT_RATE_LIMIT_MAX_REQUESTS

    return max_requests


def get_rate_limit_window_seconds() -> int:
    value = os.getenv("RATE_LIMIT_WINDOW_SECONDS")

    if value is None:
        return DEFAULT_RATE_LIMIT_WINDOW_SECONDS

    try:
        window_seconds = int(value)
    except ValueError:
        return DEFAULT_RATE_LIMIT_WINDOW_SECONDS

    return window_seconds
