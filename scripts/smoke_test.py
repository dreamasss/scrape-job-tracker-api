import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")


def request(
    method: str, path: str, data: dict | None = None
) -> tuple[int, dict | list]:
    body = None
    headers = {"Accept": "application/json"}

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(req, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
            parsed_body = json.loads(raw_body) if raw_body else {}
            return response.status, parsed_body
    except HTTPError as error:
        error_body = error.read().decode("utf-8")
        print(f"HTTP error for {method} {path}: {error.code} {error_body}")
        sys.exit(1)
    except URLError as error:
        print(f"Connection error for {method} {path}: {error}")
        sys.exit(1)


def assert_status(actual: int, expected: int, name: str) -> None:
    if actual != expected:
        print(f"{name} failed: expected {expected}, got {actual}")
        sys.exit(1)


def main() -> None:
    print(f"Running smoke test against {BASE_URL}")

    status, body = request("GET", "/")
    assert_status(status, 200, "root")
    assert body["name"] == "Scrape Job Tracker API"

    status, body = request("GET", "/health")
    assert_status(status, 200, "health")
    assert body == {"status": "ok"}

    status, body = request("GET", "/health/db")
    assert_status(status, 200, "database health")
    assert body == {"status": "ok", "database": "ok"}

    status, body = request("POST", "/scrape/preview", {"url": "https://example.com"})
    assert_status(status, 200, "scrape preview")
    assert body["title"] == "Example Domain"
    assert body["h1"] == "Example Domain"
    assert body["links_count"] == 1

    status, body = request("POST", "/jobs", {"url": "https://example.com"})
    assert_status(status, 201, "create job")
    assert body["status"] == "success"
    assert body["title"] == "Example Domain"

    job_id = body["id"]

    status, body = request("GET", "/jobs")
    assert_status(status, 200, "list jobs")
    assert body["total"] >= 1
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert any(item["id"] == job_id for item in body["items"])

    status, body = request("GET", f"/jobs/{job_id}")
    assert_status(status, 200, "get job")
    assert body["id"] == job_id
    assert body["status"] == "success"

    print("Smoke test passed")


if __name__ == "__main__":
    main()
