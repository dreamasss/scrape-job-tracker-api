from collections.abc import Callable
from typing import Annotated

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

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

router = APIRouter(prefix="/jobs", tags=["jobs"])

DBSession = Annotated[Session, Depends(get_db)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
StatusFilter = Annotated[str | None, Query()]

SessionFactory = Callable[[], Session]

VALID_JOB_STATUSES = {"pending", "success", "failed"}


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
) -> ScrapeJobRead:
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
) -> dict[str, int | list[ScrapeJob]]:
    query = select(ScrapeJob)

    if status is not None:
        if status not in VALID_JOB_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid job status")

        query = query.where(ScrapeJob.status == status)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    jobs = (
        db.execute(query.order_by(ScrapeJob.id.desc()).limit(limit).offset(offset))
        .scalars()
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": jobs,
    }


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


@router.get("/{job_id}", response_model=ScrapeJobRead)
def get_scrape_job(
    job_id: int,
    db: DBSession,
) -> ScrapeJob:
    job = db.get(ScrapeJob, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")

    return job
