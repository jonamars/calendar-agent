FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the project requirements
COPY pyproject.toml .

# Install dependencies (this creates a cached layer)
RUN uv sync --no-install-project

# Copy the rest of the application
COPY . .

# Run the application
CMD ["uv", "run", "main.py"]
