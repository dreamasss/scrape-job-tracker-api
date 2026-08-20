# Scrape Job Tracker API

A FastAPI backend project for submitting URLs, scraping basic page data, and returning structured results.

This project is part of my backend learning portfolio. The goal is to build a practical API that combines Python backend development with web scraping, testing, Docker, and later background jobs.

## Current Features

* FastAPI application
* Health check endpoint
* URL preview scraping endpoint
* HTML parsing service
* Extracts:

  * page title
  * first H1 heading
  * meta description
  * number of links
* Swagger/OpenAPI documentation
* Basic test suite with pytest
* GitHub repository setup

## Tech Stack

* Python
* FastAPI
* Pydantic
* HTTPX
* BeautifulSoup
* Pytest
* Ruff

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

### 3. Run the API

```bash
uvicorn app.main:app --reload
```

Open Swagger docs:

```text
http://localhost:8000/docs
```

## Running Tests

```bash
python -m pytest -q
```

Current expected result:

```text
4 passed
```

## Project Status

This project is in early MVP stage.

Current version includes a working scrape preview endpoint and parser tests.

Planned next steps:

* Add PostgreSQL database
* Add SQLAlchemy models
* Store scrape jobs
* Add job status: pending, success, failed
* Add list and detail endpoints for scrape jobs
* Add Docker Compose
* Add GitHub Actions CI
* Add deployment
* Later: background jobs with Redis/RQ
* Later: Playwright support for JavaScript-heavy websites

## Learning Goals

This project is designed to practice:

* Building APIs with FastAPI
* Structuring backend projects
* Making external HTTP requests
* Parsing HTML
* Handling failed requests
* Writing automated tests
* Preparing a project for Docker, CI/CD, and cloud deployment

## Author

Deividas Gagiskis
