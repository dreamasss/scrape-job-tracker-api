import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.services.fetcher import fetch_html
from app.services.parser import parse_html
from app.services.url_safety import validate_public_url

router = APIRouter(prefix="/scrape", tags=["scrape"])


class ScrapePreviewRequest(BaseModel):
    url: HttpUrl


class ScrapePreviewResponse(BaseModel):
    url: str
    title: str | None
    h1: str | None
    meta_description: str | None
    links_count: int


@router.post("/preview", response_model=ScrapePreviewResponse)
async def scrape_preview(request: ScrapePreviewRequest) -> ScrapePreviewResponse:
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
