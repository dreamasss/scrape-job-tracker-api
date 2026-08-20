import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

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
        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "ScrapeJobTrackerBot/0.1"},
        ) as client:
            response = await client.get(str(data.url))
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {error}") from error

    parsed = parse_html(response.text)

    return {
        "url": str(data.url),
        **parsed,
    }
