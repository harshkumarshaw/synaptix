# Dependency Log

Every npm/pip/cargo package added, with reason and security audit.

## Format

```markdown
### DEP-NNN: [package-name]

**Added:** YYYY-MM-DD
**Agent:** {agent-id}
**Package:** name@version
**Ecosystem:** Python / npm / Flutter / Other

**Reason:**
Why this dependency? What problem does it solve?

**Alternatives Considered:**
What else was evaluated?

**Security Audit:**
- npm audit / pip-audit / etc. result
- Known CVEs: ...
- License: MIT / Apache / etc.

**Impact:**
What does this add to the bundle size / runtime?
```

## Approved Dependencies

(Starts with core dependencies in docker-compose and pyproject.toml.)
