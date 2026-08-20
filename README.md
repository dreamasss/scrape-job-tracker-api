# Scrape Job Tracker API

A FastAPI backend project for submitting URLs, scraping basic page data, storing scrape jobs, and returning structured results.

This project is part of my backend learning portfolio. The goal is to build a practical API that combines Python backend development with web scraping, databases, testing, Docker, CI, and cloud-ready infrastructure.

## Current Features

* FastAPI application
* Health check endpoint
* Database health check endpoint
* URL preview scraping endpoint
* Database-backed scrape job endpoints
* SQLite support for local development
* PostgreSQL support through Docker Compose
* SQLAlchemy database models
* HTML parsing service
* External page fetching service
* Extracts:

  * page title
  * first H1 heading
  * meta description
  * number of links
* Saved scrape job status:

  * pending
  * success
  * failed
* Job listing with:

  * pagination metadata
  * limit / offset
  * status filtering
* Swagger/OpenAPI documentation
* Automated tests with pytest
* Ruff linting and formatting checks
* GitHub Actions CI
* Dockerfile
* Docker Compose setup with API + PostgreSQL
* Makefile for common development commands

## Tech Stack

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* SQLite
* PostgreSQL
* HTTPX
* BeautifulSoup
* Pytest
* Ruff
* Docker
* Docker Compose
* GitHub Actions
* Make

## API Endpoints

### Root

```http
GET /
```

Returns basic API information.

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

Fetches a URL, parses the page, saves the result in the database, and returns the created scrape job.

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

### 3. Run the API locally

```bash
uvicorn app.main:app --reload
```

Open Swagger docs:

```text
http://localhost:8000/docs
```

By default, the app uses a local SQLite database:

```text
scrape_jobs.db
```

## Running with Docker Compose

Build and start the API with PostgreSQL:

```bash
docker compose up --build
```

This starts:

* `api` — FastAPI application
* `db` — PostgreSQL database

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
docker compose down
```

## Makefile Commands

Run database migrations:

```bash
make migrate
```

Install dependencies:

```bash
make install
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
15 passed
```

The tests use an isolated in-memory SQLite database and mocked HTML fetching, so they do not depend on the real internet.

## Code Quality

Run all checks:

```bash
make check
```

This runs:

* Ruff linting
* Ruff formatting check
* pytest test suite

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

* dependency installation
* Ruff linting
* Ruff formatting check
* pytest test suite

## Project Status

This project is in MVP stage.

Current version includes:

* working scrape preview endpoint
* database-backed scrape job endpoints
* parser service
* fetcher service
* SQLite local development setup
* Docker Compose PostgreSQL setup
* API health check
* database health check
* pagination metadata for job listing
* job status filtering
* automated test suite
* Ruff code quality checks
* GitHub Actions CI
* Makefile development commands

Planned next steps:

* Add better error handling
* Add request timeout configuration
* Add database migrations with Alembic
* Add production deployment
* Add environment configuration notes
* Later: background jobs with Redis/RQ
* Later: Playwright support for JavaScript-heavy websites
* Later: monitoring/logging basics

## Learning Goals

This project is designed to practice:

* Building APIs with FastAPI
* Structuring backend projects
* Making external HTTP requests
* Parsing HTML
* Saving results in a database
* Working with SQLAlchemy models
* Designing paginated API responses
* Filtering API results
* Testing API endpoints
* Mocking external HTTP calls in tests
* Running a backend app with Docker Compose
* Using PostgreSQL in a containerized environment
* Adding linting and formatting checks
* Setting up GitHub Actions CI
* Creating simple development workflow commands with Makefile
* Preparing a project for deployment and cloud infrastructure

## Author

Deividas Gagiskis
