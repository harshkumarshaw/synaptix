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
