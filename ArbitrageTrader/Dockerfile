FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir uvicorn[standard]

# -----------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages \
                    /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ src/
COPY config/ config/
COPY .env.example .env.example

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Default: live scan with dashboard, dry-run (safe).
# Override CMD in docker-compose or at runtime for different modes.
CMD ["python", "-m", "run_live_with_dashboard", \
     "--config", "config/live_config.json", \
     "--iterations", "999999", \
     "--sleep", "30"]
