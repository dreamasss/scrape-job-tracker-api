# Scrape Job Tracker API

A FastAPI backend project for submitting URLs, scraping basic page data, storing scrape jobs, and returning structured results.

This project is part of my backend learning portfolio. The goal is to build a practical API that combines Python backend development with web scraping, databases, testing, Docker, CI/CD, and cloud-ready infrastructure.

## Live Demo

API: https://scrape-job-tracker-api-v2.onrender.com

Swagger docs: https://scrape-job-tracker-api-v2.onrender.com/docs

Database health check: https://scrape-job-tracker-api-v2.onrender.com/health/db

> Note: this project is deployed on a free Render instance, so the first request after inactivity may take some time to wake up.

## Current Features

- FastAPI application
- Health check endpoint
- Database health check endpoint
- URL preview scraping endpoint
- Database-backed scrape job endpoints
- SQLite support for local development
- PostgreSQL support through Docker Compose and Render
- SQLAlchemy database models
- Alembic database migrations
- Environment-based fetch configuration
- HTML parsing service
- External page fetching service
- Extracts:
  - page title
  - first H1 heading
  - meta description
  - number of links
- Saved scrape job status:
  - pending
  - success
  - failed
- Job listing with:
  - pagination metadata
  - limit / offset
  - status filtering
- Swagger/OpenAPI documentation
- Automated tests with pytest
- Ruff linting and formatting checks
- GitHub Actions CI
- Dockerfile
- Docker Compose setup with API + PostgreSQL
- Makefile for common development commands
- Smoke test script for checking a real running API
- Production deployment on Render

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLite
- PostgreSQL
- HTTPX
- BeautifulSoup
- Pytest
- Ruff
- Docker
- Docker Compose
- GitHub Actions
- Render
- Make

## API Endpoints

### Root

```http
GET /
```

Returns basic API information.

Example response:

```json
{
  "name": "Scrape Job Tracker API",
  "version": "0.2.0",
  "status": "ok",
  "docs": "/docs",
  "health": "/health"
}
```

### Health Check

```http
GET /health
```

Checks if the API is running.

Example response:

```json
{
  "status": "ok"
}
```

### Database Health Check

```http
GET /health/db
```

Checks if the API can connect to the database.

Example response:

```json
{
  "status": "ok",
  "database": "ok"
}
```

### Scrape Preview

```http
POST /scrape/preview
```

Fetches a URL and returns parsed page data without saving it as a scrape job.

Example request:

```json
{
  "url": "https://example.com"
}
```

Example response:

```json
{
  "url": "https://example.com/",
  "title": "Example Domain",
  "h1": "Example Domain",
  "meta_description": null,
  "links_count": 1
}
```

### Create Scrape Job

```http
POST /jobs
```

Creates a scrape job with `pending` status, returns it immediately, and processes the URL in a FastAPI background task. When processing finishes, the job is updated to `success` or `failed`.

Example request:

```json
{
  "url": "https://example.com"
}
```

Example response:

```json
{
  "id": 1,
  "url": "https://example.com/",
  "status": "success",
  "title": "Example Domain",
  "h1": "Example Domain",
  "meta_description": null,
  "links_count": 1,
  "error_message": null,
  "created_at": "2026-08-20T12:00:00"
}
```

### List Scrape Jobs

```http
GET /jobs
```

Returns saved scrape jobs with pagination metadata.

Optional query parameters:

```text
limit=50
offset=0
status=success
```

Examples:

```http
GET /jobs?limit=10&offset=0
GET /jobs?status=success
GET /jobs?status=failed
```

Example response:

```json
{
  "total": 2,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": 2,
      "url": "https://example.org/",
      "status": "success",
      "title": "Example Page",
      "h1": "Main heading",
      "meta_description": "Example description",
      "links_count": 2,
      "error_message": null,
      "created_at": "2026-08-20T12:05:00"
    },
    {
      "id": 1,
      "url": "https://example.com/",
      "status": "success",
      "title": "Example Domain",
      "h1": "Example Domain",
      "meta_description": null,
      "links_count": 1,
      "error_message": null,
      "created_at": "2026-08-20T12:00:00"
    }
  ]
}
```

### Get Scrape Job by ID

```http
GET /jobs/{job_id}
```

Returns one saved scrape job by ID.

If the job does not exist, the API returns:

```json
{
  "detail": "Scrape job not found"
}
```

## Environment Configuration

The app can be configured with environment variables.

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/scrape_jobs
FETCH_TIMEOUT_SECONDS=10
USER_AGENT=ScrapeJobTrackerBot/0.1
```

`DATABASE_URL` supports SQLite for local development and PostgreSQL for Docker/Render.

Render may provide PostgreSQL URLs in this format:

```text
postgresql://...
```

The app normalizes that URL internally to use the installed `psycopg` driver.

## Running Locally

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or:

```bash
make install
```

### 3. Run database migrations

```bash
make migrate
```

By default, the app uses a local SQLite database:

```text
scrape_jobs.db
```

### 4. Run the API locally

```bash
make run
```

Or:

```bash
uvicorn app.main:app --reload
```

Open Swagger docs:

```text
http://localhost:8000/docs
```

## Running with Docker Compose

Build and start the API with PostgreSQL:

```bash
docker compose up --build
```

Or:

```bash
make docker-up
```

This starts:

- `api` — FastAPI application
- `db` — PostgreSQL database

The API container runs Alembic migrations before starting the FastAPI server.

Open Swagger docs:

```text
http://localhost:8000/docs
```

Check API health:

```text
http://localhost:8000/health
```

Check database health:

```text
http://localhost:8000/health/db
```

Stop the containers:

```text
Ctrl + C
```

Or run in detached mode:

```bash
docker compose up --build -d
```

Stop detached containers:

```bash
make docker-down
```

Or:

```bash
docker compose down
```

## Makefile Commands

Install dependencies:

```bash
make install
```

Run database migrations:

```bash
make migrate
```

Run tests:

```bash
make test
```

Run Ruff linting:

```bash
make lint
```

Format code:

```bash
make format
```

Check formatting:

```bash
make format-check
```

Run linting, formatting check, and tests:

```bash
make check
```

Run the API locally:

```bash
make run
```

Run smoke test against a running API:

```bash
make smoke
```

Run with Docker Compose:

```bash
make docker-up
```

Stop Docker containers:

```bash
make docker-down
```

Follow API container logs:

```bash
make docker-logs
```

## Running Tests

```bash
python -m pytest -q
```

Or:

```bash
make test
```

Current expected result:

```text
44 passed
```

The tests use an isolated in-memory SQLite database and mocked HTML fetching, so they do not depend on the real internet.

## Smoke Test

A smoke test script is included to check the real running API over HTTP.

Start the API first:

```bash
make run
```

Then, in another terminal:

```bash
make smoke
```

The smoke test checks:

- root endpoint
- API health
- database health
- scrape preview
- create scrape job
- list scrape jobs
- get scrape job by ID

To run the smoke test against the deployed Render service:

```bash
BASE_URL=https://scrape-job-tracker-api-v2.onrender.com make smoke
```

## Code Quality

Run all checks:

```bash
make check
```

This runs:

- Ruff linting
- Ruff formatting check
- pytest test suite

Run Ruff linting manually:

```bash
ruff check .
```

Run Ruff formatting check manually:

```bash
ruff format --check .
```

Format code automatically:

```bash
ruff format .
```

## CI

This project uses GitHub Actions.

On every push and pull request to `main`, CI runs:

- dependency installation
- Ruff linting
- Ruff formatting check
- pytest test suite

## Deployment

The project is deployed on Render using Docker.

Production setup:

- Render Web Service
- Render PostgreSQL database
- Dockerfile-based deployment
- Alembic migrations run before app startup
- `/health/db` used as the health check endpoint

Live endpoints:

```text
https://scrape-job-tracker-api-v2.onrender.com
https://scrape-job-tracker-api-v2.onrender.com/docs
https://scrape-job-tracker-api-v2.onrender.com/health/db
```

## Project Status

This project is in MVP stage.

Current version includes:

- working scrape preview endpoint
- database-backed scrape job endpoints
- parser service
- fetcher service
- environment-based fetch configuration
- SQLite local development setup
- Docker Compose PostgreSQL setup
- Render PostgreSQL deployment
- API health check
- database health check
- Alembic database migrations
- pagination metadata for job listing
- job status filtering
- automated test suite
- smoke test script
- Ruff code quality checks
- GitHub Actions CI
- Makefile development commands
- production deployment on Render

Planned next steps:

- Add better error handling
- Add request retry logic
- Add rate limiting
- Add request history improvements
- Add background jobs with Redis/RQ
- Add Playwright support for JavaScript-heavy websites
- Add monitoring/logging basics

## Learning Goals

This project is designed to practice:

- Building APIs with FastAPI
- Structuring backend projects
- Making external HTTP requests
- Parsing HTML
- Saving results in a database
- Working with SQLAlchemy models
- Managing database changes with Alembic migrations
- Designing paginated API responses
- Filtering API results
- Testing API endpoints
- Mocking external HTTP calls in tests
- Running a backend app with Docker Compose
- Using PostgreSQL in a containerized environment
- Deploying a Docker-based backend API
- Connecting a deployed API to a managed PostgreSQL database
- Adding linting and formatting checks
- Setting up GitHub Actions CI
- Creating simple development workflow commands with Makefile
- Running smoke tests against local and deployed APIs
- Preparing a project for cloud/backend portfolio work

## Author

Deividas Gagiskis

## Admin API Key

Retry and delete endpoints can be protected with an admin API key:

```text
ADMIN_API_KEY=your-secret-key
```

When `ADMIN_API_KEY` is configured, these endpoints require the `X-API-Key` header:

```text
POST /jobs/{job_id}/retry
DELETE /jobs/{job_id}
```

Example:

```bash
curl -X DELETE https://scrape-job-tracker-api-v2.onrender.com/jobs/1 \
  -H "X-API-Key: your-secret-key"
```

## CSV Export

Scrape jobs can be exported as CSV:

```http
GET /jobs/export.csv
```

The export endpoint supports the same filters and sorting as the job list:

```http
GET /jobs/export.csv?status=success
GET /jobs/export.csv?url_contains=example
GET /jobs/export.csv?sort_by=id&sort_order=asc
```

The `/demo` page includes a **Download CSV** button.

## Created Date Filters

Job list and CSV export support filtering by creation date:

```http
GET /jobs?created_from=2026-08-20
GET /jobs?created_to=2026-08-20
GET /jobs?created_from=2026-08-20&created_to=2026-08-21
GET /jobs/export.csv?created_from=2026-08-20&created_to=2026-08-21
```

Supported formats:

```text
YYYY-MM-DD
YYYY-MM-DDTHH:MM:SS
YYYY-MM-DDTHH:MM:SSZ
```

When a date-only value is used for `created_to`, the API treats it as the end of that day.

## Demo UI Features

The `/demo` page includes a small interactive frontend for testing the live API:

```text
create scrape jobs
view job stats
filter and sort jobs
filter jobs by created date
open job details in a modal
retry and delete jobs with admin API key
download filtered results as CSV
use pagination controls with selectable limit
```

## Basic Rate Limiting

Public expensive endpoints are protected by a basic in-memory rate limiter:

```http
POST /jobs
POST /scrape/preview
```

Default limits:

```text
30 requests per 60 seconds per client IP and endpoint
```

The limits can be configured with environment variables:

```text
RATE_LIMIT_MAX_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
```

If the limit is exceeded, the API returns:

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

Note: this is an in-memory limiter, suitable for a small single-instance demo deployment. A real multi-instance production setup would usually use Redis or another shared store.
