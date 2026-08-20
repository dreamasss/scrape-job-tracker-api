def test_scrape_preview_rejects_localhost_url(client):
    response = client.post("/scrape/preview", json={"url": "http://localhost:8000"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Blocked private or local URL"}
