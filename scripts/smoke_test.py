import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")


def request(
    method: str, path: str, data: dict | None = None
) -> tuple[int, dict | list]:
    body = None
    headers = {}

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
        with urlopen(req, timeout=20) as response:
            raw_body = response.read().decode("utf-8")
            parsed_body = json.loads(raw_body) if raw_body else {}
            return response.status, parsed_body
    except HTTPError as exc:
        print(f"HTTP error for {method} {path}: {exc.code} {exc.reason}")
        sys.exit(1)
    except URLError as exc:
        print(f"URL error for {method} {path}: {exc.reason}")
        sys.exit(1)


def assert_status(status_code: int, expected: int, method: str, path: str) -> None:
    if status_code != expected:
        print(f"Expected {expected} for {method} {path}, got {status_code}")
        sys.exit(1)


def wait_for_job(job_id: int) -> dict:
    for _ in range(10):
        status_code, job = request("GET", f"/jobs/{job_id}")
        assert_status(status_code, 200, "GET", f"/jobs/{job_id}")

        if job["status"] != "pending":
            return job

        time.sleep(1)

    print(f"Job {job_id} stayed pending for too long")
    sys.exit(1)


def main() -> None:
    print(f"Running smoke test against {BASE_URL}")

    status_code, root = request("GET", "/")
    assert_status(status_code, 200, "GET", "/")
    assert root["status"] == "ok"

    status_code, health = request("GET", "/health")
    assert_status(status_code, 200, "GET", "/health")
    assert health["status"] == "ok"

    status_code, db_health = request("GET", "/health/db")
    assert_status(status_code, 200, "GET", "/health/db")
    assert db_health["status"] == "ok"
    assert db_health["database"] == "ok"

    status_code, preview = request(
        "POST",
        "/scrape/preview",
        {"url": "https://example.com"},
    )
    assert_status(status_code, 200, "POST", "/scrape/preview")
    assert preview["title"] == "Example Domain"

    status_code, created_job = request(
        "POST",
        "/jobs",
        {"url": "https://example.com"},
    )
    assert_status(status_code, 201, "POST", "/jobs")
    assert created_job["status"] == "pending"

    finished_job = wait_for_job(created_job["id"])

    assert finished_job["status"] == "success"
    assert finished_job["title"] == "Example Domain"

    status_code, jobs = request("GET", "/jobs")
    assert_status(status_code, 200, "GET", "/jobs")
    assert jobs["total"] >= 1
    assert len(jobs["items"]) >= 1

    print("Smoke test passed")


if __name__ == "__main__":
    main()
