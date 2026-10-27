ARG PYTHON_IMAGE=python:3.12.16-slim-bookworm@sha256:6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.11.19@sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6

FROM ${UV_IMAGE} AS uv

FROM ${PYTHON_IMAGE} AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    QUIZTALCOATL_FONT_DIR=/usr/share/fonts/truetype/dejavu \
    HOME=/tmp
RUN apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 install --yes --no-install-recommends \
        ffmpeg fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip uninstall --yes pip \
    && rm -rf /root/.cache \
    && groupadd --gid 10001 quiztalcoatl \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /tmp quiztalcoatl \
    && mkdir /work && chown 10001:10001 /work

FROM base AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable --no-cache

FROM base AS test
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 install --yes --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*
ENV UV_PROJECT_ENVIRONMENT=/opt/testvenv UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
WORKDIR /app
COPY --chown=10001:10001 . .
RUN uv sync --locked --no-cache && chown 10001:10001 /app
ENV PATH=/opt/testvenv/bin:$PATH UV_OFFLINE=1 UV_CACHE_DIR=/tmp/uv-cache
USER 10001:10001
CMD ["make", "check"]

FROM base AS runtime
COPY --from=build /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /work
USER 10001:10001
ENTRYPOINT ["quiztalcoatl"]
CMD ["--help"]
