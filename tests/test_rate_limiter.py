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
