.PHONY: dev test-e2e migrate lint format

dev:
	uv run fastapi dev main.py

test-e2e:
	bash app/base/tests/run_all.sh .env.e2e

migrate:
	uv run python scripts/migrate.py upgrade

lint:
	uv run ruff check .

format:
	uv run ruff format .
