from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_contains_custom_endpoint_summaries():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert paths["/scrape/preview"]["post"]["summary"] == "Preview scrape result"
    assert paths["/jobs"]["post"]["summary"] == "Create scrape job"
    assert paths["/jobs"]["get"]["summary"] == "List scrape jobs"
    assert paths["/jobs/export.csv"]["get"]["summary"] == "Export scrape jobs as CSV"
    assert paths["/jobs/stats"]["get"]["summary"] == "Get scrape job stats"
