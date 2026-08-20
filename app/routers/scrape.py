import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.services.fetcher import fetch_html
from app.services.parser import parse_html

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
async def scrape_preview(data: ScrapePreviewRequest):
    try:
        html = await fetch_html(str(data.url))
    except httpx.HTTPError as error:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {error}") from error

    parsed = parse_html(html)

    return {
        "url": str(data.url),
        **parsed,
    }
