# Lightweight runtime image. Build with: make docker-build
# Runtime image for the CLI and, once implemented, the agent and MCP server.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY evals ./evals

RUN pip install --no-cache-dir .

# Default: interactive CLI against the in-memory backend (no LLM key required
# for `search` / `cart` / `orders` subcommands). Override to run the agent or MCP server.
ENTRYPOINT ["harbour-basket"]
CMD ["--help"]
