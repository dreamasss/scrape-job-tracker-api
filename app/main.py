from fastapi import FastAPI

from app.database import Base, engine
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
