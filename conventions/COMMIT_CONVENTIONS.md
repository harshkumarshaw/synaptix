# Commit Conventions — Synaptix

Conventional Commits format.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Type

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code restructure without behaviour change |
| `perf` | Performance improvement |
| `test` | Adding or modifying tests |
| `build` | Build system / dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance, no production code change |
| `revert` | Reverting a previous commit |

## Scope (Required)

Use the service or module name:
- `auth`, `attendance`, `exam`, `logbook`, `clinical`, `crmi`
- `db`, `infra`, `tests`, `docs`
- `mobile`, `web`

## Subject

- Imperative mood ("add" not "added")
- Lowercase
- No period at end
- Max 72 characters

## Body

- Explain WHY, not what (code shows what)
- Wrap at 80 characters
- Reference NMC regulations, audit IDs, or issue numbers

## Footer

- `Refs:` — references to audits, issues, NMC sections
- `BREAKING CHANGE:` — for breaking API/schema changes
- `Co-authored-by:` — for agent attribution

## Examples

### Feature

```
feat(attendance): add two-threshold eligibility check for MBBS

NMC CBME 2019/2023 mandates 75% theory and 80% practical attendance
as separate thresholds. Previously the system used a single 75%
threshold which incorrectly passed students with insufficient
practical attendance.

This affects:
- Attendance Engine: separate calculation per category
- Hall Ticket eligibility: both thresholds must pass independently
- At-risk student detection: alerts now consider both thresholds

Refs: AUDIT-G1, NMC GMER 2019 §11.1
Co-authored-by: backend-agent <02@synaptix.local>
```

### Fix

```
fix(logbook): preserve faculty feedback during offline merge

Field-level merge was overwriting faculty_feedback when student
edited activity_description from another device. Now uses
field-level diff with separate ownership per field group.

Refs: AUDIT-D4
Co-authored-by: mobile-agent <04@synaptix.local>
```

### Breaking Change

```
feat(api)!: migrate /attendance/check to v2 with two-threshold response

BREAKING CHANGE: Response structure changed.
- v1: { passing: bool, attendance_pct: float }
- v2: { theory: { passing: bool, pct: float }, practical: { passing: bool, pct: float } }

v1 endpoint deprecated with sunset header. Will be removed 2027-06-18.

Refs: AUDIT-G1
Co-authored-by: backend-agent <02@synaptix.local>
```

### Documentation

```
docs(architecture): add ADR for service grouping decision

Decision to group 49 modules into 12 deployable services documented
in DECISIONS.md. Includes rationale, alternatives considered, and
migration path to per-service deployment if needed at scale.

Refs: FEASIBILITY-2.3
Co-authored-by: architect-agent <01@synaptix.local>
```

## Branch Naming

- `feature/{module}-{description}` — new features
- `fix/{module}-{description}` — bug fixes
- `chore/{description}` — maintenance
- `docs/{description}` — docs-only changes

Examples:
- `feature/attendance-two-threshold`
- `fix/logbook-offline-merge`
- `chore/update-dependencies`

## Pre-commit Hook

The hook at `scripts/pre-commit-hook.ps1` enforces:
- Conventional Commits format
- Lint passes (ruff, eslint)
- Tests pass (pytest, vitest)
- NMC compliance tests pass (HARD FAIL)
- Coverage manifest satisfied
- Documentation updated
- No hardcoded secrets

Bypass only with `git commit --no-verify` and ONLY with explicit human approval. Document the bypass in `docs/INCIDENT_LOG.md`.
