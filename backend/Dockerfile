FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install system dependencies (ffmpeg required by some LiveKit/Deepgram plugins)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Download models
RUN python main.py download-files

# Switch to non-root user
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Default command will be overridden by docker-compose for the specific service (API vs Agent)
CMD ["python", "main.py", "dev"]
