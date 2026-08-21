from collections import defaultdict, deque
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.config import get_rate_limit_max_requests, get_rate_limit_window_seconds

RequestTimes = deque[float]

_requests: dict[str, RequestTimes] = defaultdict(deque)


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client is None:
        return "unknown"

    return request.client.host


def require_rate_limit(request: Request) -> None:
    max_requests = get_rate_limit_max_requests()
    window_seconds = get_rate_limit_window_seconds()

    if max_requests <= 0 or window_seconds <= 0:
        return

    now = monotonic()
    client_ip = get_client_ip(request)
    key = f"{client_ip}:{request.url.path}"
    request_times = _requests[key]

    while request_times and now - request_times[0] > window_seconds:
        request_times.popleft()

    if len(request_times) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
        )

    request_times.append(now)


RateLimit = Annotated[None, Depends(require_rate_limit)]
