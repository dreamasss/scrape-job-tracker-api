import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.services.fetcher import fetch_html
from app.services.parser import parse_html
from app.services.rate_limiter import RateLimit
from app.services.url_safety import validate_public_url

router = APIRouter(prefix="/scrape", tags=["scrape"])


class ScrapePreviewRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"url": "https://example.com"}}
    )

    url: HttpUrl = Field(
        description="Public URL to fetch and parse without saving a job."
    )


class ScrapePreviewResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/",
                "title": "Example Domain",
                "h1": "Example Domain",
                "meta_description": None,
                "links_count": 1,
            }
        }
    )

    url: str = Field(description="Fetched URL.")
    title: str | None = Field(description="HTML page title, if found.")
    h1: str | None = Field(description="First H1 heading, if found.")
    meta_description: str | None = Field(
        description="Meta description content, if found."
    )
    links_count: int = Field(description="Number of links found on the page.")


@router.post(
    "/preview",
    response_model=ScrapePreviewResponse,
    summary="Preview scrape result",
    description="Fetch a public URL, parse basic metadata, and return the result without saving it as a job.",
)
async def scrape_preview(
    request: ScrapePreviewRequest,
    _rate_limit: RateLimit,
) -> ScrapePreviewResponse:
    url = str(request.url)

    validate_public_url(url)

    try:
        html = await fetch_html(url)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch URL: {exc}",
        ) from exc

    parsed = parse_html(html)

    return ScrapePreviewResponse(
        url=url,
        **parsed,
    )
