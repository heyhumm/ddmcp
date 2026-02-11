# Dockerfile for ddmcp MCP server (HTTP mode)

FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies and the package itself
RUN uv sync --frozen
RUN uv pip install -e .

# Expose MCP HTTP port
EXPOSE 8000

# Set environment variables (override these when running)
ENV DD_API_KEY=""
ENV DD_APP_KEY=""
ENV DD_SITE="us5"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run in HTTP mode for network access
# Use the venv python to ensure package is found
CMD [".venv/bin/python", "-m", "ddmcp.http_server"]
