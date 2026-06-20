# snx-auth Service — Multi-stage Dockerfile
# Stage 1: Builder (installs dependencies)
# Stage 2: Production (minimal runtime image)
#
# Build: docker build -t snx-auth:latest .
# Run:   docker run -p 8001:8001 --env-file ../../.env snx-auth:latest

# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first (layer caching)
COPY pyproject.toml .python-version ./
COPY packages/shared/pyproject.toml packages/shared/pyproject.toml
COPY services/snx-auth/pyproject.toml services/snx-auth/pyproject.toml

# Install runtime deps only (no dev tools) into /build/.venv
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

# ── Stage 2: Production ──────────────────────────────────────────────────────
FROM python:3.12-slim AS production

# Security: run as non-root user
RUN groupadd --gid 1001 synaptix && \
    useradd --uid 1001 --gid synaptix --shell /bin/bash --create-home synaptix

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application source
COPY packages/shared /app/packages/shared
COPY services/snx-auth/app /app/services/snx-auth/app

# Set Python path so packages/shared is importable
ENV PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Switch to non-root user
USER synaptix

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

EXPOSE 8001

# Run with uvicorn (production: no --reload)
CMD ["python", "-m", "uvicorn", "services.snx-auth.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "2", \
     "--access-log", \
     "--log-level", "info"]
