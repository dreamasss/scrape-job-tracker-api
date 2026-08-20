import pytest
from fastapi import HTTPException

from app.services.url_safety import validate_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://172.16.0.1",
        "http://192.168.1.1",
        "http://0.0.0.0",
    ],
)
def test_validate_public_url_blocks_private_or_local_urls(url):
    with pytest.raises(HTTPException) as exc_info:
        validate_public_url(url)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Blocked private or local URL"


def test_validate_public_url_allows_public_domain():
    validate_public_url("https://example.com")
