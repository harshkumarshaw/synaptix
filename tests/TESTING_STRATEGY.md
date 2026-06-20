# Testing Strategy — Synaptix

## Philosophy

In Synaptix, testing is **not optional and not delegated to agent imagination**. Tests are specified BEFORE code is written, in two files that the Testing Agent reads:

1. `tests/COVERAGE_MANIFEST.yaml` — the source of truth for required tests
2. `tests/EDGE_CASES.md` — every edge case must have a test
3. `tests/NMC_COMPLIANCE_TESTS.md` — every regulation must have a test

The Testing Agent does NOT decide which tests to write. It reads these specs and implements every listed test. If a test is missing from the spec, the human supervisor adds it — the agent does not invent.

## Test Pyramid

```
                  /\
                 /  \
                / E2E\          50+ tests, slow, run pre-release
               /------\
              /        \
             /Integration\     800+ tests, medium, run on commit
            /------------\
           /              \
          /  Unit Tests    \   5000+ tests, fast, run on every save
         /------------------\
        /                    \
       / Compliance + Edge   \  200+ tests, HARD-FAIL, run on commit
      /----------------------\
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test single functions/classes in isolation
- All external dependencies mocked
- Run in < 1 second each
- Coverage target: 80% line coverage overall, 95% for critical modules

### Integration Tests (`tests/integration/`)
- Test interactions between components
- Use real PostgreSQL (test database via Docker)
- Mock external services (HIMS, SMS gateway, etc.)
- Run in < 5 seconds each

### Compliance Tests (`tests/compliance/`)
- **HARD-FAIL** — any failure blocks ALL commits
- Maps 1:1 to entries in `NMC_COMPLIANCE_TESTS.md`
- Cannot be modified by code-writing agents
- Only the NMC Compliance Agent can modify these tests

### Edge Case Tests (`tests/edge_cases/` inside relevant unit/integration dirs)
- Maps 1:1 to entries in `EDGE_CASES.md`
- Each test references its EC-XXX ID
- Required for every edge case in the catalogue

### Security Tests (`tests/security/`)
- Tenant isolation verification
- RBAC enforcement
- SQL injection attempts
- JWT tampering attempts
- RLS policy verification
- Hardcoded secret detection

### Load Tests (`tests/load/`)
- Use k6 or Locust
- Simulate Tier 1 (300), Tier 2 (1000), Tier 3 (3000) concurrent users
- Run pre-release, not on every commit

### E2E Tests (`tests/e2e/`)
- Use Playwright (web) and Patrol (mobile)
- Test complete user journeys (see Section 6 of MASTER_SPEC)
- Run nightly, not on every commit

### Mutation Tests (configured in `pyproject.toml`)
- Use `mutmut` for Python
- Target: critical paths only
  - Attendance calculation
  - NExT eligibility
  - Logbook IA contribution
  - Hall ticket eligibility
  - CRMI completion
- Run weekly
- Goal: 80% mutation score on critical paths

## Test Enforcement

### Pre-Commit Hook
```bash
# scripts/pre-commit-hook.ps1 (Windows)
1. Run ruff (Python lint)
2. Run black --check (Python format)
3. Run mypy --strict (Python types)
4. Run eslint (TS/JS lint)
5. Run prettier --check (TS/JS format)
6. Run pytest tests/unit/ (unit tests)
7. Run pytest tests/compliance/ (HARD FAIL)
8. Run python scripts/verify_coverage_manifest.py
9. Run python scripts/check_secrets.py
10. Verify documentation files updated
11. Verify commit message format (Conventional Commits)
```

If ANY step fails, the commit is rejected.

### Coverage Manifest Verification

`scripts/verify_coverage_manifest.py` reads `COVERAGE_MANIFEST.yaml` and scans `tests/`:

```python
# Pseudocode
for module in manifest:
    for test in module.critical_tests + module.edge_cases + module.nmc_compliance_tests:
        if not test_exists_in_codebase(test.id):
            print(f"MISSING TEST: {test.id} - {test.description}")
            exit(1)
```

If any test is missing or skipped (without explicit `@pytest.mark.deferred`), the build fails.

## Test Naming Conventions

```python
# Pattern: test_<scenario>_<expected_outcome>
def test_student_with_exactly_75_percent_theory_attendance_is_eligible():
    ...

def test_student_with_74_99_percent_theory_attendance_is_blocked():
    ...

# Include test ID in docstring
def test_two_faculty_marking_same_student_uses_last_write_wins():
    """Test ID: ATT-E001. See EDGE_CASES.md."""
    ...
```

## Mocking Conventions

```python
# Use pytest fixtures
@pytest.fixture
async def mock_hims_client():
    client = AsyncMock(spec=HIMSClient)
    client.get_patient.return_value = Patient(id="P-001", name="Test")
    return client

# Use respx for HTTP mocking
@respx.mock
async def test_external_api_call():
    respx.get("https://hims.example/api/patient/P-001").respond(
        json={"id": "P-001", "name": "Test"}
    )
    ...
```

## Test Database

Local development uses Docker Compose with a dedicated test database:

```yaml
# docker-compose.test.yml
services:
  postgres-test:
    image: postgres:16
    environment:
      POSTGRES_DB: synaptix_test
      POSTGRES_USER: snx_test
      POSTGRES_PASSWORD: snx_test_pass
    ports:
      - "5433:5432"  # Different port from dev DB
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for speed
```

Each test run:
1. Starts with empty database (or migrations applied to latest)
2. Test creates only data it needs
3. Test cleans up after itself OR uses transaction rollback

## Performance Targets

| Test Type | Target Speed | Max Speed |
|-----------|-------------|-----------|
| Unit | < 100ms | 1s |
| Integration | < 1s | 5s |
| Compliance | < 500ms | 2s |
| E2E | < 30s | 120s |

If any test takes longer than max, it must be optimised or marked `@pytest.mark.slow` and run separately.

## What to Test (Decision Tree)

```
Does the change touch business logic?
├── YES → Unit test required
│         └── Does it touch DB? → Integration test required
└── NO
    └── Is it UI?
        ├── YES → Component test (Vitest/Flutter test)
        │         └── Is it a user journey? → E2E test
        └── NO (infra/config) → Smoke test in CI

Does the change touch NMC rules?
└── YES → Compliance test REQUIRED (HARD FAIL)

Does the change handle an edge case?
└── YES → Edge case test REQUIRED (matches EC-XXX in EDGE_CASES.md)

Does the change affect performance?
└── YES → Load test required pre-release
```

## Anti-Patterns (Forbidden)

```python
# NEVER — testing only happy path
def test_calculate_attendance():
    assert calculate(present=80, total=100) == 80.0
# (no test for 0 sessions, no test for boundary, no test for edge cases)

# NEVER — assertions without messages
assert result.is_eligible  # Why? What was the input?

# NEVER — overly broad mocks
mock = MagicMock()
# Doesn't enforce contract; if real interface changes, test still passes

# NEVER — sleep-based timing
time.sleep(2)  # Flaky; use mocked time

# NEVER — sharing test data between tests
SHARED_STUDENT = create_student()  # Tests become order-dependent
```

## Mutation Testing Setup

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = [
    "services/attendance/business_logic.py",
    "services/exam/eligibility.py",
    "services/logbook/ia_contribution.py",
    "services/crmi/completion.py",
]
runner = "python -m pytest tests/unit -x --tb=no -q"
tests_dir = "tests/unit"
```

Run weekly: `mutmut run`

Review results: `mutmut results`

If mutation score < 80%, add tests until it reaches threshold.

---

*Testing is the safety net for solo-developer + agent development. Without comprehensive tests, the system collapses.*
