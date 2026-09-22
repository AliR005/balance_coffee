.PHONY: test lint seed

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy app

seed:
	uv run python scripts/seed.py
