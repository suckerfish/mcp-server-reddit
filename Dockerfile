FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.15

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN uv pip install --system --no-cache .

RUN adduser --disabled-password --gecos '' --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf -o /dev/null -w '%{http_code}' http://localhost:8080/mcp | grep -q '405' || exit 1

CMD ["python", "-m", "mcp_server_reddit", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]
