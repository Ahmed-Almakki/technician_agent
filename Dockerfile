FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

COPY src/ ./src/
COPY app/ ./app/

# Set the environment variable to ensure python uses the uv virtual environment
ENV PATH="/app/.venv/bin:$PATH"

