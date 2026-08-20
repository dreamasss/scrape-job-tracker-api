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

    assert len(data) == 2
    assert data[0]["id"] == 2
    assert data[1]["id"] == 1


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
