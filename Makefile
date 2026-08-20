.PHONY: install test lint format format-check check run docker-up docker-down docker-logs

install:
	pip install -r requirements.txt

test:
	python -m pytest -q

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

check:
	ruff check .
	ruff format --check .
	python -m pytest -q

run:
	uvicorn app.main:app --reload

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api
