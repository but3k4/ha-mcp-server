FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock LICENSE ./
COPY ha_mcp/ ./ha_mcp/
RUN uv sync --frozen --no-dev

EXPOSE 8765

ENV TRANSPORT=sse \
    PORT=8765 \
    LOG_LEVEL=WARNING

CMD ["/app/.venv/bin/ha-mcp"]
