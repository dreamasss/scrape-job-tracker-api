from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ScrapeJobCreate(BaseModel):
    url: HttpUrl


class ScrapeJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status: str
    title: str | None
    h1: str | None
    meta_description: str | None
    links_count: int | None
    error_message: str | None
    created_at: datetime


class ScrapeJobListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ScrapeJobRead]


class ScrapeJobStatsResponse(BaseModel):
    total: int
    pending: int
    success: int
    failed: int
