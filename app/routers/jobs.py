import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScrapeJob
from app.schemas import ScrapeJobCreate, ScrapeJobRead
from app.services.fetcher import fetch_html
from app.services.parser import parse_html

router = APIRouter(prefix="/jobs", tags=["jobs"])

VALID_JOB_STATUSES = {"pending", "success", "failed"}


@router.post("", response_model=ScrapeJobRead, status_code=status.HTTP_201_CREATED)
async def create_scrape_job(data: ScrapeJobCreate, db: Session = Depends(get_db)):
    job = ScrapeJob(url=str(data.url), status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        html = await fetch_html(str(data.url))
        parsed = parse_html(html)

        job.status = "success"
        job.title = parsed["title"]
        job.h1 = parsed["h1"]
        job.meta_description = parsed["meta_description"]
        job.links_count = parsed["links_count"]
        job.error_message = None
    except httpx.HTTPError as error:
        job.status = "failed"
        job.error_message = str(error)

    db.commit()
    db.refresh(job)

    return job


@router.get("", response_model=list[ScrapeJobRead])
def list_scrape_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(ScrapeJob)

    if status_filter is not None:
        if status_filter not in VALID_JOB_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid job status")

        query = query.where(ScrapeJob.status == status_filter)

    jobs = db.execute(
        query.order_by(ScrapeJob.id.desc()).limit(limit).offset(offset)
    ).scalars().all()

    return jobs


@router.get("/{job_id}", response_model=ScrapeJobRead)
def get_scrape_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ScrapeJob, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")

    return job
