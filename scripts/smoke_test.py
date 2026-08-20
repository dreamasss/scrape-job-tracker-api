import json
import os
import sys
import time
from http.client import HTTPResponse
from typing import NoReturn
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()


def fail(message: str) -> NoReturn:
    print(message)
    sys.exit(1)


def parse_json(raw_body: str) -> dict | list:
    if not raw_body:
        return {}

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        fail(f"Expected JSON response, got: {raw_body[:200]}")


def read_response(response: HTTPResponse) -> tuple[int, str, dict[str, str]]:
    raw_body = response.read().decode("utf-8")
    headers = dict(response.headers)
    return response.status, raw_body, headers


def request_raw(
    method: str,
    path: str,
    data: dict | None = None,
    headers: dict[str, str] | None = None,
    expected_error: int | None = None,
) -> tuple[int, str, dict[str, str]]:
    body = None
    request_headers = headers.copy() if headers else {}

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers=request_headers,
        method=method,
    )

    try:
        with urlopen(req, timeout=20) as response:
            return read_response(response)
    except HTTPError as exc:
        if expected_error is not None and exc.code == expected_error:
            raw_body = exc.read().decode("utf-8")
            return exc.code, raw_body, dict(exc.headers)

        print(f"HTTP error for {method} {path}: {exc.code} {exc.reason}")
        error_body = exc.read().decode("utf-8", errors="replace")
        if error_body:
            print(error_body)
        sys.exit(1)
    except URLError as exc:
        fail(f"URL error for {method} {path}: {exc.reason}")
    except TimeoutError:
        fail(f"Timeout for {method} {path}")


def request_json(
    method: str,
    path: str,
    data: dict | None = None,
    headers: dict[str, str] | None = None,
    expected_error: int | None = None,
) -> tuple[int, dict | list]:
    status_code, raw_body, _headers = request_raw(
        method,
        path,
        data=data,
        headers=headers,
        expected_error=expected_error,
    )
    return status_code, parse_json(raw_body)


def get_header(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def assert_status(status_code: int, expected: int, method: str, path: str) -> None:
    if status_code != expected:
        fail(f"Expected {expected} for {method} {path}, got {status_code}")


def wait_for_job(job_id: int) -> dict:
    for _ in range(10):
        status_code, job = request_json("GET", f"/jobs/{job_id}")
        assert_status(status_code, 200, "GET", f"/jobs/{job_id}")

        if job["status"] != "pending":
            return job

        time.sleep(1)

    fail(f"Job {job_id} stayed pending for too long")


def create_example_job() -> dict:
    status_code, created_job = request_json(
        "POST",
        "/jobs",
        {"url": "https://example.com"},
    )
    assert_status(status_code, 201, "POST", "/jobs")
    assert created_job["status"] == "pending"

    return created_job


def admin_headers() -> dict[str, str]:
    return {"X-API-Key": ADMIN_API_KEY}


def main() -> None:
    print(f"Running smoke test against {BASE_URL}")

    status_code, root = request_json("GET", "/")
    assert_status(status_code, 200, "GET", "/")
    assert root["status"] == "ok"

    status_code, health = request_json("GET", "/health")
    assert_status(status_code, 200, "GET", "/health")
    assert health["status"] == "ok"

    status_code, db_health = request_json("GET", "/health/db")
    assert_status(status_code, 200, "GET", "/health/db")
    assert db_health["status"] == "ok"
    assert db_health["database"] == "ok"

    status_code, demo_html, demo_headers = request_raw("GET", "/demo")
    assert_status(status_code, 200, "GET", "/demo")
    assert "text/html" in get_header(demo_headers, "Content-Type")
    assert "Scrape Job Tracker Demo" in demo_html

    status_code, preview = request_json(
        "POST",
        "/scrape/preview",
        {"url": "https://example.com"},
    )
    assert_status(status_code, 200, "POST", "/scrape/preview")
    assert preview["title"] == "Example Domain"

    status_code, blocked_preview = request_json(
        "POST",
        "/scrape/preview",
        {"url": "http://localhost:8000"},
        expected_error=400,
    )
    assert_status(status_code, 400, "POST", "/scrape/preview")
    assert blocked_preview["detail"] == "Blocked private or local URL"

    created_job = create_example_job()
    finished_job = wait_for_job(created_job["id"])

    assert finished_job["status"] == "success"
    assert finished_job["title"] == "Example Domain"

    status_code, stats = request_json("GET", "/jobs/stats")
    assert_status(status_code, 200, "GET", "/jobs/stats")
    assert stats["total"] >= 1
    assert "success" in stats

    status_code, jobs = request_json(
        "GET",
        "/jobs?sort_by=id&sort_order=asc&url_contains=example",
    )
    assert_status(
        status_code,
        200,
        "GET",
        "/jobs?sort_by=id&sort_order=asc&url_contains=example",
    )
    assert jobs["total"] >= 1
    assert jobs["sort_by"] == "id"
    assert jobs["sort_order"] == "asc"
    assert len(jobs["items"]) >= 1

    status_code, future_jobs = request_json(
        "GET",
        "/jobs?created_from=2999-01-01",
    )
    assert_status(status_code, 200, "GET", "/jobs?created_from=2999-01-01")
    assert future_jobs["total"] == 0
    assert future_jobs["items"] == []

    status_code, csv_body, csv_headers = request_raw(
        "GET",
        "/jobs/export.csv?sort_by=id&sort_order=asc&url_contains=example",
    )
    assert_status(status_code, 200, "GET", "/jobs/export.csv")
    assert "text/csv" in get_header(csv_headers, "Content-Type")
    content_disposition = get_header(csv_headers, "Content-Disposition")
    assert "attachment" in content_disposition.lower()
    assert "scrape_jobs.csv" in content_disposition
    assert (
        "id,url,status,title,h1,meta_description,links_count,error_message,created_at"
        in csv_body
    )
    assert "https://example.com/" in csv_body

    if ADMIN_API_KEY:
        admin_job = create_example_job()
        finished_admin_job = wait_for_job(admin_job["id"])
        assert finished_admin_job["status"] == "success"

        status_code, retried_job = request_json(
            "POST",
            f"/jobs/{admin_job['id']}/retry",
            headers=admin_headers(),
        )
        assert_status(status_code, 202, "POST", f"/jobs/{admin_job['id']}/retry")
        assert retried_job["status"] == "pending"

        finished_retried_job = wait_for_job(admin_job["id"])
        assert finished_retried_job["status"] == "success"

        status_code, _deleted_body = request_json(
            "DELETE",
            f"/jobs/{admin_job['id']}",
            headers=admin_headers(),
        )
        assert_status(status_code, 204, "DELETE", f"/jobs/{admin_job['id']}")

        status_code, deleted_detail = request_json(
            "GET",
            f"/jobs/{admin_job['id']}",
            expected_error=404,
        )
        assert_status(status_code, 404, "GET", f"/jobs/{admin_job['id']}")
        assert deleted_detail["detail"] == "Scrape job not found"
    else:
        print("ADMIN_API_KEY not set; skipping admin retry/delete smoke checks")

    print("Smoke test passed")


if __name__ == "__main__":
    main()
