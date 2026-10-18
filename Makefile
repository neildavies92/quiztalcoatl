.PHONY: setup format lint typecheck test check smoke

setup:
	@echo "Requires uv and Make. Install FFmpeg/ffprobe separately; see README.md."
	uv sync --locked

format:
	uv run --locked ruff format .

lint:
	uv run --locked ruff check .

typecheck:
	uv run --locked mypy

test:
	uv run --locked pytest -m "not smoke"

check:
	uv run --locked ruff format --check .
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

smoke:
	uv run --locked pytest -m smoke
