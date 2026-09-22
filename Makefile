.PHONY: dev test lint gen-api seed migrate reset-demo

dev:
	docker compose up --build

test:
	$(MAKE) -C backend test
	$(MAKE) -C web test

lint:
	$(MAKE) -C backend lint
	$(MAKE) -C web lint

gen-api:
	cd backend && uv run python scripts/export_openapi.py ../web/openapi.json
	$(MAKE) -C web gen-api

seed:
	$(MAKE) -C backend seed

migrate:
	docker compose exec api /app/.venv/bin/alembic upgrade head

reset-demo:
	cd backend && uv run python scripts/reset_demo.py
