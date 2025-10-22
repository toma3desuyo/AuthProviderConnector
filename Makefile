.PHONY: install format lint check test migrate create-migrate

install:
	uv sync --frozen

lint:
	PYTHONPATH=src uv run ruff check .

lint-fix:
	PYTHONPATH=src uv run ruff check . --fix

format:
	PYTHONPATH=src uv run ruff check . --fix && uv run ruff format .

check:
	PYTHONPATH=src uv run ruff check . && uv run ruff format --check . && uv run mypy src

test:
	PYTHONPATH=src uv run pytest

migrate:
	@docker compose exec -T api uv run alembic upgrade head

create-migrate:
	@if [ -z "$(m)$(MESSAGE)" ]; then \
		echo "使用方法: make create-migrate m=\"変更内容の説明\""; \
		exit 1; \
	fi
	@echo "[alembic] autogenerate only (no upgrade)"
	@docker compose exec api uv run alembic revision --autogenerate -m "$(if $(m),$(m),$(MESSAGE))" \
	|| { echo "[alembic] migration not created（変更なしの可能性）"; exit 0; }
