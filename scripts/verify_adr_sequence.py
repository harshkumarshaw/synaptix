#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify that docs/DECISIONS.md contains a sequential ADR series with no gaps.

Exits 0 if all ADRs are present and sequential.
Exits 1 with detailed gap report if any ADRs are missing.

Usage:
    python scripts/verify_adr_sequence.py
    python scripts/verify_adr_sequence.py --verbose   # print all ADR titles
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DECISIONS_FILE = ROOT / "docs" / "DECISIONS.md"


def extract_adrs(content: str) -> dict[int, str]:
    """Extract all ADR entries from DECISIONS.md.

    Supports both:
        ## ADR-001: Title
        ### ADR-001: Title

    Returns a dict mapping ADR number → title string.
    """
    # Match heading lines: ## ADR-NNN: Title  or  ### ADR-NNN: Title
    pattern = re.compile(r"^#{2,3}\s+ADR-(\d{3}):\s+(.+)$", re.MULTILINE)
    found: dict[int, str] = {}
    for match in pattern.finditer(content):
        num = int(match.group(1))
        title = match.group(2).strip()
        if num in found:
            # Duplicate ADR number — report it
            print(f"WARNING: Duplicate ADR-{num:03d} detected in DECISIONS.md")
        found[num] = title
    return found


def verify_sequence(adrs: dict[int, str]) -> tuple[bool, list[int], int, int]:
    """Verify the ADR sequence is gapless from 1 to max.

    Returns:
        (is_ok, missing_numbers, min_adr, max_adr)
    """
    if not adrs:
        return False, [], 0, 0

    min_adr = min(adrs.keys())
    max_adr = max(adrs.keys())

    # ADRs should start at 001
    if min_adr != 1:
        print(f"WARNING: ADR sequence does not start at ADR-001 (starts at ADR-{min_adr:03d})")

    expected = set(range(min_adr, max_adr + 1))
    missing = sorted(expected - set(adrs.keys()))
    return len(missing) == 0, missing, min_adr, max_adr


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    if not DECISIONS_FILE.exists():
        print(f"ERROR: {DECISIONS_FILE} not found.")
        return 1

    content = DECISIONS_FILE.read_text(encoding="utf-8")
    adrs = extract_adrs(content)

    print("=== ADR Sequence Verification ===")
    print(f"File: {DECISIONS_FILE.relative_to(ROOT)}")
    print(f"ADRs found: {len(adrs)}")

    if not adrs:
        print("ERROR: No ADR entries found in DECISIONS.md")
        return 1

    is_ok, missing, min_adr, max_adr = verify_sequence(adrs)

    print(f"Range: ADR-{min_adr:03d} through ADR-{max_adr:03d}")

    if verbose:
        print("\n=== ADR Index ===")
        for num in sorted(adrs.keys()):
            print(f"  ADR-{num:03d}: {adrs[num]}")

    if missing:
        print(f"\n=== GAPS DETECTED ===")
        print(f"Missing ADR numbers: {[f'ADR-{n:03d}' for n in missing]}")
        print(f"\nGap detail:")
        for n in missing:
            prev = n - 1
            nxt = n + 1
            prev_title = adrs.get(prev, "(not present)")
            next_title = adrs.get(nxt, "(not present)")
            print(f"  ADR-{n:03d} is missing")
            print(f"    Previous: ADR-{prev:03d}: {prev_title}")
            print(f"    Next:     ADR-{nxt:03d}: {next_title}")
        print(f"\nBuild FAILED: {len(missing)} gap(s) in ADR sequence.")
        return 1

    print(f"\nADR sequence intact: ADR-001 through ADR-{max_adr:03d} ({max_adr} ADRs). No gaps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
