FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency definitions and install
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src ./src
COPY README.md ./

# Install the project itself
RUN uv sync --frozen --no-dev

# Set entrypoint
ENTRYPOINT ["/app/.venv/bin/python", "-m", "blogger.main"]
