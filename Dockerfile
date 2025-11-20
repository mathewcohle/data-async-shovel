FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml .python-version ./

# Install dependencies (no src needed for this)
RUN uv sync --no-dev

ENV PYTHONPATH=/app/src
