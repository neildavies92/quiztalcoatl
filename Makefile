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

DOCKER_IMAGE ?= quiztalcoatl:local
DOCKER_TEST_IMAGE ?= quiztalcoatl:test
DOCKER_SMOKE_DIR ?= output/container-smoke

.PHONY: docker-build docker-check docker-smoke

docker-build:
	docker build --target runtime --tag $(DOCKER_IMAGE) .

docker-check:
	docker build --target test --tag $(DOCKER_TEST_IMAGE) .
	docker run --rm --network none $(DOCKER_TEST_IMAGE)
	docker run --rm --network none $(DOCKER_TEST_IMAGE) uv run --locked mypy --strict scripts/container_acceptance.py
	docker run --rm --network none $(DOCKER_TEST_IMAGE) make smoke

docker-smoke:
	python3 scripts/container_acceptance.py --image $(DOCKER_IMAGE) --output $(DOCKER_SMOKE_DIR)
