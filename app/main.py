from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routers.jobs import router as jobs_router
from app.routers.scrape import router as scrape_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Scrape Job Tracker API",
    description="Backend API for submitting URLs, scraping page data, and tracking scrape jobs.",
    version="0.2.0",
)

app.include_router(scrape_router)
app.include_router(jobs_router)

DBSession = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return {
        "name": "Scrape Job Tracker API",
        "version": "0.2.0",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check(db: DBSession):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="Database unavailable") from error

    return {
        "status": "ok",
        "database": "ok",
    }
