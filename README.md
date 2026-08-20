# Scrape Job Tracker API

A FastAPI backend project for submitting URLs, scraping basic page data, storing scrape jobs, and returning structured results.

This project is part of my backend learning portfolio. The goal is to build a practical API that combines Python backend development with web scraping, databases, testing, Docker, and cloud-ready infrastructure.

## Current Features

* FastAPI application
* Health check endpoint
* URL preview scraping endpoint
* Scrape job endpoints
* SQLite support for local development
* PostgreSQL support through Docker Compose
* SQLAlchemy database models
* HTML parsing service
* Extracts:

  * page title
  * first H1 heading
  * meta description
  * number of links
* Saved scrape job status:

  * pending
  * success
  * failed
* Swagger/OpenAPI documentation
* Automated tests with pytest
* Dockerfile
* Docker Compose setup with API + PostgreSQL
* GitHub repository setup

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

Example response:

```json
{
  "status": "ok"
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

Returns all saved scrape jobs, ordered by newest first.

### Get Scrape Job by ID

```http
GET /jobs/{job_id}
```

Returns one saved scrape job by ID.

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

Stop the containers:

```bash
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

## Running Tests

```bash
python -m pytest -q
```

Current expected result:

```text
9 passed
```

The tests use an isolated in-memory SQLite database and mocked HTML fetching, so they do not depend on the real internet.

## Project Status

This project is in MVP stage.

Current version includes:

* working scrape preview endpoint
* database-backed scrape job endpoints
* parser service
* fetcher service
* SQLite local development setup
* Docker Compose PostgreSQL setup
* automated test suite

Planned next steps:

* Add pagination for `/jobs`
* Add filters by job status
* Add better error handling
* Add GitHub Actions CI
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
* Testing API endpoints
* Mocking external HTTP calls in tests
* Running a backend app with Docker Compose
* Preparing a project for CI/CD and cloud deployment

## Author

Deividas Gagiskis