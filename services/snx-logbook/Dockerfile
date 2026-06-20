# snx-logbook Service — Multi-stage Dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .python-version ./
COPY packages/shared/pyproject.toml packages/shared/pyproject.toml
COPY services/snx-logbook/pyproject.toml services/snx-logbook/pyproject.toml

RUN uv venv --python 3.12 .venv && \
    uv pip install --no-cache \
        fastapi \
        uvicorn[standard] \
        sqlalchemy[asyncio] \
        asyncpg \
        "pydantic[email]" \
        pydantic-settings \
        "python-jose[cryptography]" \
        "passlib[bcrypt]" \
        pyotp \
        structlog \
        python-multipart \
        python-dotenv

FROM python:3.12-slim AS production

RUN groupadd --gid 1001 synaptix && \
    useradd --uid 1001 --gid synaptix --shell /bin/bash --create-home synaptix

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv
COPY packages/shared /app/packages/shared
COPY services/snx-logbook/app /app/services/snx-logbook/app

ENV PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER synaptix

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8006/health')" || exit 1

EXPOSE 8006

CMD ["python", "-m", "uvicorn", "services.snx-logbook.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8006", \
     "--workers", "2", \
     "--access-log", \
     "--log-level", "info"]
