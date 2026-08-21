from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapeJobCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com",
            }
        }
    )

    url: HttpUrl = Field(
        description="Public URL to scrape. Private and local network URLs are blocked."
    )


class ScrapeJobRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "url": "https://example.com/",
                "status": "success",
                "title": "Example Domain",
                "h1": "Example Domain",
                "meta_description": None,
                "links_count": 1,
                "error_message": None,
                "created_at": "2026-08-20T14:24:53Z",
            }
        },
    )

    id: int = Field(description="Database ID of the scrape job.")
    url: str = Field(description="Submitted URL.")
    status: str = Field(description="Current job status: pending, success, or failed.")
    title: str | None = Field(description="HTML page title, if found.")
    h1: str | None = Field(description="First H1 heading, if found.")
    meta_description: str | None = Field(
        description="Meta description content, if found."
    )
    links_count: int | None = Field(description="Number of links found on the page.")
    error_message: str | None = Field(description="Error message when the job failed.")
    created_at: datetime = Field(description="Timestamp when the job was created.")


class ScrapeJobListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "limit": 50,
                "offset": 0,
                "sort_by": "id",
                "sort_order": "desc",
                "items": [
                    {
                        "id": 1,
                        "url": "https://example.com/",
                        "status": "success",
                        "title": "Example Domain",
                        "h1": "Example Domain",
                        "meta_description": None,
                        "links_count": 1,
                        "error_message": None,
                        "created_at": "2026-08-20T14:24:53Z",
                    }
                ],
            }
        }
    )

    total: int = Field(description="Total matching jobs before pagination.")
    limit: int = Field(description="Maximum number of jobs returned.")
    offset: int = Field(description="Number of jobs skipped.")
    sort_by: str = Field(description="Sort field used for the response.")
    sort_order: str = Field(description="Sort order used for the response.")
    items: list[ScrapeJobRead] = Field(description="Paginated list of scrape jobs.")


class ScrapeJobStatsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 12,
                "pending": 0,
                "success": 11,
                "failed": 1,
            }
        }
    )

    total: int = Field(description="Total number of scrape jobs.")
    pending: int = Field(description="Number of pending jobs.")
    success: int = Field(description="Number of successful jobs.")
    failed: int = Field(description="Number of failed jobs.")
