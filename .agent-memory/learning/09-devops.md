# 09-devops — Learning Memory

Accumulated learnings, patterns, and discoveries.

## Patterns Established

- Always isolate test runs using the correct microservice PYTHONPATH to avoid namespace collision errors under pytest (e.g., `PYTHONPATH=.;services/snx-academic`).
- Include standard Phase 2 tables in `tests/conftest.py` truncation lists to maintain test run isolation.

## Anti-patterns Discovered

- Hardcoded unique identifier fields in test database seeders (like `roll_number='R001'` or static email) cause silent failures during multi-student database seeding under `ON CONFLICT DO NOTHING`. Use dynamic generation or parameterization (e.g. slicing student ID).
- Passing student ID as actor user ID in tests causes `ForeignKeyViolationError` on append-only audit logs since the student is not a registered admin user.

## Useful Code Snippets

- Dynamically unique roll number generation in tests:
  ```python
  "roll": f"R_{str(student_id)[:8]}"
  ```

## Cross-Agent Insights

(None)
