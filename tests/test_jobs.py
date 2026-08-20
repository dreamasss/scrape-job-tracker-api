import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


async def fake_fetch_html_success(url: str) -> str:
    return """
    <html>
      <head>
        <title>Example Page</title>
        <meta name="description" content="Example description">
      </head>
      <body>
        <h1>Main heading</h1>
        <a href="/one">One</a>
        <a href="/two">Two</a>
      </body>
    </html>
    """


async def fake_fetch_html_failure(url: str) -> str:
    request = httpx.Request("GET", url)
    raise httpx.ConnectError("Connection failed", request=request)


def test_create_scrape_job_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_success)

    response = client.post("/jobs", json={"url": "https://example.com"})

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["url"] == "https://example.com/"
    assert data["status"] == "success"
    assert data["title"] == "Example Page"
    assert data["h1"] == "Main heading"
    assert data["meta_description"] == "Example description"
    assert data["links_count"] == 2
    assert data["error_message"] is None
    assert data["created_at"] is not None


def test_list_scrape_jobs(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_success)

    client.post("/jobs", json={"url": "https://example.com"})
    client.post("/jobs", json={"url": "https://example.org"})

    response = client.get("/jobs")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == 2
    assert data["items"][1]["id"] == 1


def test_get_scrape_job_by_id(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_success)

    create_response = client.post("/jobs", json={"url": "https://example.com"})
    job_id = create_response.json()["id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["status"] == "success"


def test_get_scrape_job_returns_404_for_unknown_id(client):
    response = client.get("/jobs/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Scrape job not found"


def test_create_scrape_job_failed_fetch(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_failure)

    response = client.post("/jobs", json={"url": "https://example.com"})

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "failed"
    assert data["title"] is None
    assert data["error_message"] is not None
    assert "Connection failed" in data["error_message"]


def test_list_scrape_jobs_uses_limit_and_offset(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_success)

    client.post("/jobs", json={"url": "https://example.com/1"})
    client.post("/jobs", json={"url": "https://example.com/2"})
    client.post("/jobs", json={"url": "https://example.com/3"})

    response = client.get("/jobs?limit=1&offset=1")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == 2


def test_list_scrape_jobs_filters_by_success_status(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_success)

    client.post("/jobs", json={"url": "https://example.com"})

    response = client.get("/jobs?status=success")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "success"


def test_list_scrape_jobs_filters_by_failed_status(client, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.fetch_html", fake_fetch_html_failure)

    client.post("/jobs", json={"url": "https://example.com"})

    response = client.get("/jobs?status=failed")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "failed"


def test_list_scrape_jobs_rejects_invalid_status(client):
    response = client.get("/jobs?status=unknown")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid job status"


def test_list_scrape_jobs_rejects_invalid_limit(client):
    response = client.get("/jobs?limit=0")

    assert response.status_code == 422
