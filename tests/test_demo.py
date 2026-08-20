from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_page_returns_html():
    response = client.get("/demo")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Scrape Job Tracker Demo" in response.text
