# Use astral-sh/uv for faster dependency management
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-install-project --no-dev

# Final stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Ensure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Install system dependencies (needed for some livekit plugins or audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY . .

# Expose the Flask port
EXPOSE 8080

# Run both the Token Server and the Agent Worker
# We use 'sh -c' to start the server in the background and the agent in the foreground
CMD ["sh", "-c", "python token_server.py & python main.py dev"]
