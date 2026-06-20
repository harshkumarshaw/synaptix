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

