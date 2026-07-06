#!/usr/bin/env python3
"""Verify that documentation has been updated when code changes.

Rules:
1. If services/ or packages/ changed → CHANGELOG.md must be updated
2. If migrations created → MIGRATION_LOG.md must be updated
3. If NMC-related code changed → NMC_COMPLIANCE_LOG.md must be updated
4. Always: sessions/ or HANDOFF_NOTES.md must be updated
"""

import subprocess
import sys
from datetime import date


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def main() -> int:
    files = get_staged_files()
    if not files:
        return 0

    # Skip checks if only docs changed (allows pure-doc commits)
    if all(f.startswith("docs/") or f.endswith(".md") for f in files):
        return 0

    issues = []

    code_changed = any(f.startswith(("services/", "packages/", "frontend-")) for f in files)
    if code_changed:
        # Check CHANGELOG.md updated
        if "docs/CHANGELOG.md" not in files:
            issues.append("Code changed but docs/CHANGELOG.md not updated")

        # Check session log exists for today
        today = date.today().isoformat()
        session_logs = [f for f in files if f.startswith(f"docs/sessions/{today}")]
        if not session_logs:
            issues.append(f"Code changed but no session log for {today} in docs/sessions/")

        # Check HANDOFF_NOTES.md updated
        if "docs/HANDOFF_NOTES.md" not in files:
            issues.append("Code changed but docs/HANDOFF_NOTES.md not updated")

    # Migration check
    migration_changed = any("migrations/versions/" in f for f in files)
    if migration_changed and "docs/MIGRATION_LOG.md" not in files:
        issues.append("Migrations created but docs/MIGRATION_LOG.md not updated")

    # NMC-related code check
    nmc_keywords = [
        "attendance",
        "logbook",
        "crmi",
        "aetcom",
        "electives",
        "next_eligibility",
        "foundation_course",
        "competency",
    ]
    nmc_changed = any(
        any(kw in f.lower() for kw in nmc_keywords) for f in files if f.endswith(".py")
    )
    if nmc_changed and "docs/NMC_COMPLIANCE_LOG.md" not in files:
        issues.append("NMC-related code changed but docs/NMC_COMPLIANCE_LOG.md not updated")

    if issues:
        print("=== DOCUMENTATION NOT UPDATED ===")
        for issue in issues:
            print(f"  - {issue}")
        print("\nUpdate the listed docs and stage them with `git add docs/`.")
        print("Reference: AGENTS.md — Commandment 5")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
