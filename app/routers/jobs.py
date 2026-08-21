import csv
from collections.abc import Callable
from datetime import date, datetime, time
from io import StringIO
from typing import Annotated

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_admin_api_key
from app.database import get_db
from app.models import ScrapeJob
from app.schemas import (
    ScrapeJobCreate,
    ScrapeJobListResponse,
    ScrapeJobRead,
    ScrapeJobStatsResponse,
)
from app.services.fetcher import fetch_html
from app.services.parser import parse_html
from app.services.rate_limiter import RateLimit
from app.services.url_safety import validate_public_url

router = APIRouter(prefix="/jobs", tags=["jobs"])

DBSession = Annotated[Session, Depends(get_db)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
StatusFilter = Annotated[str | None, Query()]
SortByQuery = Annotated[str, Query()]
SortOrderQuery = Annotated[str, Query()]
UrlContainsFilter = Annotated[str | None, Query()]
CreatedFromFilter = Annotated[str | None, Query()]
CreatedToFilter = Annotated[str | None, Query()]
AdminApiKeyHeader = Annotated[str | None, Header(alias="X-API-Key")]

SessionFactory = Callable[[], Session]

VALID_JOB_STATUSES = {"pending", "success", "failed"}
VALID_SORT_FIELDS = {
    "id": ScrapeJob.id,
    "created_at": ScrapeJob.created_at,
}
VALID_SORT_ORDERS = {"asc", "desc"}


def require_admin_api_key(x_api_key: AdminApiKeyHeader = None) -> None:
    expected_api_key = get_admin_api_key()

    if not expected_api_key:
        return

    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


AdminAuth = Annotated[None, Depends(require_admin_api_key)]


def parse_datetime_filter(
    value: str, field_name: str, end_of_day: bool = False
) -> datetime:
    try:
        if len(value) == 10:
            parsed_date = date.fromisoformat(value)
            parsed_time = time.max if end_of_day else time.min
            return datetime.combine(parsed_date, parsed_time)

        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}. Use YYYY-MM-DD or ISO datetime.",
        ) from exc


def apply_job_filters(
    query,
    status: str | None,
    url_contains: str | None,
    created_from: str | None,
    created_to: str | None,
):
    if status is not None:
        if status not in VALID_JOB_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid job status")

        query = query.where(ScrapeJob.status == status)

    if url_contains is not None:
        query = query.where(ScrapeJob.url.ilike(f"%{url_contains}%"))

    if created_from is not None:
        query = query.where(
            ScrapeJob.created_at >= parse_datetime_filter(created_from, "created_from")
        )

    if created_to is not None:
        query = query.where(
            ScrapeJob.created_at
            <= parse_datetime_filter(
                created_to,
                "created_to",
                end_of_day=True,
            )
        )

    return query


async def process_scrape_job(
    job_id: int,
    url: str,
    session_factory: SessionFactory,
) -> None:
    db = session_factory()

    try:
        job = db.get(ScrapeJob, job_id)

        if job is None:
            return

        try:
            html = await fetch_html(url)
            parsed = parse_html(html)
        except httpx.HTTPError as exc:
            job.status = "failed"
            job.error_message = str(exc)
        else:
            job.status = "success"
            job.title = parsed["title"]
            job.h1 = parsed["h1"]
            job.meta_description = parsed["meta_description"]
            job.links_count = parsed["links_count"]
            job.error_message = None

        db.commit()
    finally:
        db.close()


@router.post("", response_model=ScrapeJobRead, status_code=status.HTTP_201_CREATED)
def create_scrape_job(
    job_in: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    db: DBSession,
    _rate_limit: RateLimit,
) -> ScrapeJobRead:
    validate_public_url(str(job_in.url))

    job = ScrapeJob(
        url=str(job_in.url),
        status="pending",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    job_response = ScrapeJobRead.model_validate(job)

    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db.get_bind(),
    )

    background_tasks.add_task(
        process_scrape_job,
        job.id,
        job.url,
        session_factory,
    )

    return job_response


@router.get("", response_model=ScrapeJobListResponse)
def list_scrape_jobs(
    db: DBSession,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusFilter = None,
    url_contains: UrlContainsFilter = None,
    created_from: CreatedFromFilter = None,
    created_to: CreatedToFilter = None,
    sort_by: SortByQuery = "id",
    sort_order: SortOrderQuery = "desc",
) -> dict[str, int | str | list[ScrapeJob]]:
    query = apply_job_filters(
        select(ScrapeJob),
        status,
        url_contains,
        created_from,
        created_to,
    )

    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if sort_order not in VALID_SORT_ORDERS:
        raise HTTPException(status_code=400, detail="Invalid sort order")

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    sort_column = VALID_SORT_FIELDS[sort_by]
    order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    jobs = (
        db.execute(query.order_by(order_expression).limit(limit).offset(offset))
        .scalars()
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "items": jobs,
    }


@router.get("/export.csv")
def export_scrape_jobs(
    db: DBSession,
    status: StatusFilter = None,
    url_contains: UrlContainsFilter = None,
    created_from: CreatedFromFilter = None,
    created_to: CreatedToFilter = None,
    sort_by: SortByQuery = "id",
    sort_order: SortOrderQuery = "desc",
) -> Response:
    query = apply_job_filters(
        select(ScrapeJob),
        status,
        url_contains,
        created_from,
        created_to,
    )

    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if sort_order not in VALID_SORT_ORDERS:
        raise HTTPException(status_code=400, detail="Invalid sort order")

    sort_column = VALID_SORT_FIELDS[sort_by]
    order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    jobs = db.execute(query.order_by(order_expression)).scalars().all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "id",
            "url",
            "status",
            "title",
            "h1",
            "meta_description",
            "links_count",
            "error_message",
            "created_at",
        ]
    )

    for job in jobs:
        writer.writerow(
            [
                job.id,
                job.url,
                job.status,
                job.title,
                job.h1,
                job.meta_description,
                job.links_count,
                job.error_message,
                job.created_at.isoformat(),
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scrape_jobs.csv"},
    )


@router.get("/stats", response_model=ScrapeJobStatsResponse)
def get_scrape_job_stats(db: DBSession) -> dict[str, int]:
    rows = db.execute(
        select(ScrapeJob.status, func.count()).group_by(ScrapeJob.status)
    ).all()

    counts = {status: count for status, count in rows}

    pending = counts.get("pending", 0)
    success = counts.get("success", 0)
    failed = counts.get("failed", 0)

    return {
        "total": pending + success + failed,
        "pending": pending,
        "success": success,
        "failed": failed,
    }


@router.post(
    "/{job_id}/retry",
    response_model=ScrapeJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_scrape_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: DBSession,
    _admin_auth: AdminAuth,
) -> ScrapeJobRead:
    job = db.get(ScrapeJob, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")

    job.status = "pending"
    job.title = None
    job.h1 = None
    job.meta_description = None
    job.links_count = None
    job.error_message = None

    db.commit()
    db.refresh(job)

    job_response = ScrapeJobRead.model_validate(job)

    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db.get_bind(),
    )

    background_tasks.add_task(
        process_scrape_job,
        job.id,
        job.url,
        session_factory,
    )

    return job_response


@router.get("/{job_id}", response_model=ScrapeJobRead)
def get_scrape_job(
    job_id: int,
    db: DBSession,
) -> ScrapeJob:
    job = db.get(ScrapeJob, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scrape_job(
    job_id: int,
    db: DBSession,
    _admin_auth: AdminAuth,
) -> Response:
    job = db.get(ScrapeJob, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")

    db.delete(job)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
