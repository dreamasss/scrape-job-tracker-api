import httpx
import pytest

SUCCESS_HTML = """
<html>
  <head>
    <title>Example Domain</title>
    <meta name="description" content="Example description">
  </head>
  <body>
    <h1>Example Domain</h1>
    <a href="https://example.com/one">One</a>
    <a href="https://example.com/two">Two</a>
  </body>
</html>
"""


def mock_successful_fetch(monkeypatch):
    async def fake_fetch_html(url: str) -> str:
        return SUCCESS_HTML

    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html)


def mock_failed_fetch(monkeypatch):
    async def fake_fetch_html(url: str) -> str:
        raise httpx.ConnectError("Fetch failed")

    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html)


def create_job(client, monkeypatch, url: str = "https://example.com"):
    mock_successful_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": url})

    assert response.status_code == 201

    return response.json()


def test_create_scrape_job_starts_as_pending(client, monkeypatch):
    job = create_job(client, monkeypatch)

    assert job["url"] == "https://example.com/"
    assert job["status"] == "pending"
    assert job["title"] is None
    assert job["h1"] is None
    assert job["meta_description"] is None
    assert job["links_count"] is None
    assert job["error_message"] is None


def test_background_scrape_job_updates_to_success(client, monkeypatch):
    job = create_job(client, monkeypatch)

    response = client.get(f"/jobs/{job['id']}")

    assert response.status_code == 200

    updated_job = response.json()

    assert updated_job["status"] == "success"
    assert updated_job["title"] == "Example Domain"
    assert updated_job["h1"] == "Example Domain"
    assert updated_job["meta_description"] == "Example description"
    assert updated_job["links_count"] == 2
    assert updated_job["error_message"] is None


def test_background_scrape_job_updates_to_failed(client, monkeypatch):
    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})

    assert response.status_code == 201

    job = response.json()

    assert job["status"] == "pending"

    detail_response = client.get(f"/jobs/{job['id']}")

    assert detail_response.status_code == 200

    updated_job = detail_response.json()

    assert updated_job["status"] == "failed"
    assert updated_job["error_message"] == "Fetch failed"


def test_list_scrape_jobs(client, monkeypatch):
    first_job = create_job(client, monkeypatch, "https://example.com")
    second_job = create_job(client, monkeypatch, "https://example.org")

    response = client.get("/jobs")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == second_job["id"]
    assert data["items"][1]["id"] == first_job["id"]


def test_get_scrape_job_by_id(client, monkeypatch):
    job = create_job(client, monkeypatch)

    response = client.get(f"/jobs/{job['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == job["id"]
    assert data["url"] == "https://example.com/"


def test_get_scrape_job_returns_404_for_unknown_id(client):
    response = client.get("/jobs/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scrape job not found"}


def test_list_scrape_jobs_uses_limit_and_offset(client, monkeypatch):
    first_job = create_job(client, monkeypatch, "https://example.com")
    create_job(client, monkeypatch, "https://example.org")

    response = client.get("/jobs?limit=1&offset=1")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == first_job["id"]


def test_list_scrape_jobs_filters_by_success_status(client, monkeypatch):
    create_job(client, monkeypatch, "https://example.com")

    response = client.get("/jobs?status=success")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "success"


def test_list_scrape_jobs_filters_by_failed_status(client, monkeypatch):
    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})

    assert response.status_code == 201

    response = client.get("/jobs?status=failed")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "failed"


def test_list_scrape_jobs_rejects_invalid_status(client):
    response = client.get("/jobs?status=unknown")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid job status"}


@pytest.mark.parametrize("limit", [0, 101])
def test_list_scrape_jobs_rejects_invalid_limit(client, limit):
    response = client.get(f"/jobs?limit={limit}")

    assert response.status_code == 422


def test_list_scrape_jobs_rejects_invalid_offset(client):
    response = client.get("/jobs?offset=-1")

    assert response.status_code == 422


def test_get_scrape_job_stats(client, monkeypatch):
    create_job(client, monkeypatch, "https://example.com")
    create_job(client, monkeypatch, "https://example.org")

    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})

    assert response.status_code == 201

    response = client.get("/jobs/stats")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["pending"] == 0
    assert data["success"] == 2
    assert data["failed"] == 1


def test_get_scrape_job_stats_empty(client):
    response = client.get("/jobs/stats")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "total": 0,
        "pending": 0,
        "success": 0,
        "failed": 0,
    }


def test_delete_scrape_job(client, monkeypatch):
    job = create_job(client, monkeypatch)

    response = client.delete(f"/jobs/{job['id']}")

    assert response.status_code == 204
    assert response.content == b""

    response = client.get(f"/jobs/{job['id']}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scrape job not found"}


def test_delete_scrape_job_returns_404_for_unknown_id(client):
    response = client.delete("/jobs/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scrape job not found"}


def test_retry_scrape_job(client, monkeypatch):
    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})

    assert response.status_code == 201

    failed_job = client.get(f"/jobs/{response.json()['id']}").json()

    assert failed_job["status"] == "failed"
    assert failed_job["error_message"] == "Fetch failed"

    mock_successful_fetch(monkeypatch)

    response = client.post(f"/jobs/{failed_job['id']}/retry")

    assert response.status_code == 202

    retried_job = response.json()

    assert retried_job["status"] == "pending"
    assert retried_job["title"] is None
    assert retried_job["h1"] is None
    assert retried_job["meta_description"] is None
    assert retried_job["links_count"] is None
    assert retried_job["error_message"] is None

    finished_job = client.get(f"/jobs/{failed_job['id']}").json()

    assert finished_job["status"] == "success"
    assert finished_job["title"] == "Example Domain"


def test_retry_scrape_job_returns_404_for_unknown_id(client):
    response = client.post("/jobs/999/retry")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scrape job not found"}


def test_list_scrape_jobs_sorts_by_id_ascending(client, monkeypatch):
    first_job = create_job(client, monkeypatch, "https://example.com")
    second_job = create_job(client, monkeypatch, "https://example.org")

    response = client.get("/jobs?sort_by=id&sort_order=asc")

    assert response.status_code == 200

    data = response.json()

    assert data["sort_by"] == "id"
    assert data["sort_order"] == "asc"
    assert data["items"][0]["id"] == first_job["id"]
    assert data["items"][1]["id"] == second_job["id"]


def test_list_scrape_jobs_rejects_invalid_sort_field(client):
    response = client.get("/jobs?sort_by=bad")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid sort field"}


def test_list_scrape_jobs_rejects_invalid_sort_order(client):
    response = client.get("/jobs?sort_order=sideways")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid sort order"}


def test_create_scrape_job_rejects_localhost_url(client):
    response = client.post("/jobs", json={"url": "http://localhost:8000"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Blocked private or local URL"}


def test_list_scrape_jobs_filters_by_url_contains(client, monkeypatch):
    create_job(client, monkeypatch, "https://example.com")
    create_job(client, monkeypatch, "https://github.com")

    response = client.get("/jobs?url_contains=github")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["url"] == "https://github.com/"


def test_list_scrape_jobs_filters_by_status_and_url_contains(client, monkeypatch):
    create_job(client, monkeypatch, "https://example.com")

    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})

    assert response.status_code == 201

    response = client.get("/jobs?status=failed&url_contains=broken")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "failed"
    assert data["items"][0]["url"] == "https://broken.example.com/"


def test_delete_scrape_job_requires_admin_api_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    job = create_job(client, monkeypatch)

    response = client.delete(f"/jobs/{job['id']}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}

    response = client.get(f"/jobs/{job['id']}")

    assert response.status_code == 200


def test_delete_scrape_job_accepts_admin_api_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    job = create_job(client, monkeypatch)

    response = client.delete(
        f"/jobs/{job['id']}",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == 204


def test_retry_scrape_job_requires_admin_api_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})
    failed_job = client.get(f"/jobs/{response.json()['id']}").json()

    response = client.post(f"/jobs/{failed_job['id']}/retry")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_retry_scrape_job_accepts_admin_api_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    mock_failed_fetch(monkeypatch)

    response = client.post("/jobs", json={"url": "https://broken.example.com"})
    failed_job = client.get(f"/jobs/{response.json()['id']}").json()

    mock_successful_fetch(monkeypatch)

    response = client.post(
        f"/jobs/{failed_job['id']}/retry",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "pending"
