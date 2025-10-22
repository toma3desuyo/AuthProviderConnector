.PHONY: format lint check migrate create-migrate

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

format:
	uv run ruff check . --fix && uv run ruff format .

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
