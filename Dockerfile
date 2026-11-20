# syntax=docker/dockerfile:1
# Container image for remote (streamable-HTTP) deployment.
#
# Used by:
#   - IBM Code Engine (deploy/ibm/)
#   - cloud.gov (docker image path) and any other container host
#
# The server serves MCP over streamable-HTTP at :8080/mcp with a health check
# at :8080/health. app.py auto-selects HTTP because PORT is set below.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PORT=8080

WORKDIR /app

# Install uv (fast, reproducible installs).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first for better layer caching.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

# PORT=8080 (set above) makes app.py run HTTP on that port automatically.
CMD ["python", "-m", "example_server.app"]
