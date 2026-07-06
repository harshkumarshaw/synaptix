# 00-orchestrator — Learning Memory

Accumulated learnings, patterns, and discoveries.

## Patterns Established

- **Testing with NullPool:** When using `pytest-asyncio` with function-scoped tests, connection pooling can lead to `RuntimeError: Event loop is closed` or `ResourceWarning` on test teardown. Configuring the test database engine with `sqlalchemy.pool.NullPool` ensures each session gets a fresh connection and closes it immediately when the session exits, avoiding event loop contamination.
- **Teardown Engine Dispose:** Always add a session-scoped autouse fixture to dispose of the SQLAlchemy engine at the end of the test suite run.

## Anti-patterns Discovered

- **Parameterized SET LOCAL:** Do not parameterize PostgreSQL `SET LOCAL` statements in SQLAlchemy (e.g. `SET LOCAL snx.current_tenant_id = :id`). It raises a syntax error. String interpolation must be used for tenant UUID values in RLS mock settings.

## Useful Code Snippets

```python
# conftest.py NullPool configuration
from sqlalchemy.pool import NullPool
db_session_mod._engine = create_async_engine(
    database_url,
    poolclass=NullPool,
)
```

## Cross-Agent Insights

(None.)

## CI Pipeline Learnings (Session 6)

- **Ruff config deprecation:** Ruff ≥0.4 requires `[tool.ruff.lint]` (not top-level `select`/`ignore`). CI runner downloads the latest pinned ruff version which emits warnings but still fails — migrate fully.
- **FastAPI idiomatic ignores:** The rules `ARG001`, `ARG002`, `B008`, `B904`, `PLC0415`, `PLR2004`, `PLW0603`, `SIM102`, `E501` are all triggered by standard FastAPI patterns (DI injection, Form/File defaults, exception chaining, local imports, SQL strings). Add them to `[tool.ruff.lint]` ignore globally for this project.
- **CI per-service PYTHONPATH:** Microservices each own an `app` namespace. Running `pytest tests/unit` without a service-specific `PYTHONPATH` causes `ModuleNotFoundError: No module named 'app'` for every service except the one whose path is set. Solution: run each service's tests in a separate step with `PYTHONPATH=$GITHUB_WORKSPACE:$GITHUB_WORKSPACE/services/<service-name>`.
- **Coverage accumulation:** Use `--cov-append` in all intermediate steps and `--cov-fail-under=0` so each individual service doesn't fail the build on its own sub-80% slice. Enforce the threshold only on the final combined step.
- **Black `--safe` mode:** If a Python file has a syntax error (e.g. `param: type = default` before `param: type`), `black --safe` cannot parse the AST and reports a fatal error. Fix the Python syntax first, then run formatter.
- **Linux asyncio event loop isolation bug (critical):** On Linux (SelectorEventLoop), pytest-asyncio/anyio gives each test function its own event loop. If you cache a SQLAlchemy `AsyncEngine` or `asyncpg` pool across tests (e.g. `if _engine is None: create_async_engine(...)`), the second test gets a new loop but the engine still holds `Future` objects from the first loop → `RuntimeError: Task got Future attached to a different loop`. Fix: **NEVER cache an async engine across test functions**. Always create `create_async_engine(NullPool)` fresh at the start of each `db_session` fixture and `await engine.dispose()` at teardown. This works on Windows (ProactorEventLoop) which happens to be more lenient about loop reuse. DO NOT test only on Windows.
- **DB-dependent tests in `tests/unit/`:** The unit test directory contains tests that require a live database (they use `db_session`). The CI `unit-tests` job MUST include a `postgres:16` service container to run them. Port mapping: `5436:5432` (matches conftest.py default `SNX_DATABASE_URL`). Run `alembic upgrade head` before pytest to apply all migrations.

