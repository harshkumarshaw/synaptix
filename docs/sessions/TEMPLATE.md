# Session Log Template

Copy this template when starting a new session. Filename: `YYYY-MM-DD-session-N.md`

---

# Session: YYYY-MM-DD — Session N

**Agent:** {agent-id} {agent-name}
**Start time:** HH:MM IST
**End time:** HH:MM IST
**Duration:** X minutes

## Session Start Declaration

```
SESSION START — Agent: {agent-id} {agent-name}
Read: AGENTS.md ✓, MASTER_SPEC ✓, CURRENT_FOCUS ✓, my agent spec ✓, my learning ✓, my incidents ✓, HANDOFF_NOTES ✓
Task: <what you understand the task to be>
Approach: <your approach>
```

## Task

What were you asked to do?

## Context

What was the state of the system when you started?

## Work Performed

### Files Modified
- `path/to/file1.py` — what changed
- `path/to/file2.py` — what changed

### Tests Added
- `tests/.../test_X.py::test_Y` — covers EC-NNN
- ...

### Commits Made
- `abc123` — feat(module): description
- ...

## Commands Run

```bash
# Every command, in chronological order
[10:05] pytest tests/unit/auth/
[10:08] alembic upgrade head
...
```

## Decisions Made

(If any architectural decisions — also add to DECISIONS.md)

## Issues Encountered

- Bug found: BUG-NNN (added to BUG_LOG.md)
- Blocker: ...
- Unexpected: ...

## Tests Run

- Unit: X/Y passing
- Integration: X/Y passing
- Compliance: X/Y passing
- Coverage: X% (target: Y%)

## Session End Declaration

```
SESSION END — Agent: {agent-id} {agent-name}
Duration: ~X minutes
Files modified: <count>
Tests added: <count>
Tests passing: X/Y
Commits made: <count>
Documentation updated: ✓
Memory updated: ✓
Next session should: <brief instruction>
```

## Next Session Should...

What should the next agent know or do?

(Copied to HANDOFF_NOTES.md at session end.)
