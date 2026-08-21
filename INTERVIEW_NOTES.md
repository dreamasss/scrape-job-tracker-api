# Interview Notes — Scrape Job Tracker API

## 30 second pitch

I built a FastAPI backend called Scrape Job Tracker API. It lets users submit URLs, creates background scraping jobs, extracts basic page metadata like title, first H1, meta description and link count, then stores the results in PostgreSQL.

The project includes Docker, Alembic migrations, GitHub Actions CI, pytest tests, live Render deployment, Swagger docs, a small /demo frontend, CSV export, admin API key protection, URL safety checks, rate limiting, and production smoke tests.

## 1–2 minute explanation

This is a backend portfolio project where I wanted to build something closer to a real production API, not just simple CRUD.

A user submits a URL through the API or demo UI. The backend creates a scrape job in the database with pending status and then processes the URL in a FastAPI background task. When the scraping finishes, the job becomes either success or failed.

For successful jobs, the API stores page metadata: title, first H1, meta description, links count, created_at, status, and error message if failed.

The API supports listing jobs with pagination, sorting, status filters, URL search and created date filters. I also added CSV export, job stats, retry and delete endpoints.

For production-style improvements, I added Alembic migrations, PostgreSQL, Docker deployment, GitHub Actions, pytest coverage, a live smoke test against the deployed Render service, admin API key protection for retry/delete, URL safety checks to block private/local URLs, and basic in-memory rate limiting.

## Hardest part

The hardest part was making the project feel more production-like instead of only working locally. Deployment added extra problems: environment variables, PostgreSQL connection strings, migrations, health checks and Render-specific behavior.

One real issue was that Render PostgreSQL provided a postgresql:// URL, but SQLAlchemy needed the psycopg driver. I fixed that by normalizing the database URL from postgresql:// to postgresql+psycopg://.

I also replaced automatic Base.metadata.create_all() with Alembic migrations, which is a better production approach.

## Why background jobs?

At first, the API could scrape during the request, but that means the user has to wait until the whole fetch and parse process finishes.

I changed it so POST /jobs creates a database record immediately with pending status and returns 201 Created. Then FastAPI processes the scraping in the background and updates the job to success or failed.

This is closer to how real job processing systems work.

## What I would improve next

The current background jobs use FastAPI BackgroundTasks, which is fine for a portfolio project and small demo. The next improvement would be moving job processing to a real queue system like Celery, RQ, Dramatiq or a managed queue.

I would also replace the in-memory rate limiter with Redis, because in-memory rate limiting only works correctly for a single server instance.
