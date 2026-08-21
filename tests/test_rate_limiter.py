from fastapi.testclient import TestClient

from app.main import app
from app.services.rate_limiter import _requests

client = TestClient(app)


def test_preview_rate_limit_returns_429(monkeypatch):
    _requests.clear()
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 400

    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded. Please try again later."}


def test_rate_limit_can_be_disabled(monkeypatch):
    _requests.clear()
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "0")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 400

    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 400


def test_rate_limit_response_includes_headers(monkeypatch):
    async def fake_fetch_html(url: str) -> str:
        return "<html><head><title>OK</title></head><body><h1>OK</h1></body></html>"

    _requests.clear()
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setattr("app.routers.scrape.fetch_html", fake_fetch_html)

    response = client.post("/scrape/preview", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_429_response_includes_retry_after(monkeypatch):
    _requests.clear()
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 400

    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 429
    assert response.headers["Retry-After"]
    assert response.headers["X-RateLimit-Limit"] == "1"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Reset" in response.headers
