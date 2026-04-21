# syntax=docker/dockerfile:1.7

# Build stage ------------------------------------------------------------------
FROM python:3.12-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY anita ./anita

RUN uv build --wheel --out-dir /dist

# Runtime stage ----------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user for safer execution
RUN useradd --create-home --shell /bin/bash anita
USER anita
WORKDIR /home/anita

COPY --from=build /dist/*.whl /tmp/
RUN pip install --user --no-cache-dir /tmp/*.whl 'anita-anki[elevenlabs]' \
    && rm /tmp/*.whl

ENV PATH="/home/anita/.local/bin:${PATH}"

ENTRYPOINT ["anita"]
CMD ["--help"]
