#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify that every edge case catalogued in tests/EDGE_CASES.md has a corresponding test.

Scans EDGE_CASES.md for EC-NNN identifiers and ATT-E/LOG-E/etc edge case IDs,
then checks that they appear in the test codebase.

Exits 0 if all catalogued edge cases have tests.
Exits 1 with detailed gap report if any are missing.

Usage:
    python scripts/verify_edge_case_coverage.py
    python scripts/verify_edge_case_coverage.py --verbose
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EDGE_CASES_FILE = ROOT / "tests" / "EDGE_CASES.md"
COVERAGE_MANIFEST = ROOT / "tests" / "COVERAGE_MANIFEST.yaml"
TESTS_DIR = ROOT / "tests"


def extract_edge_cases_from_doc(content: str) -> dict[str, str]:
    """Extract edge case IDs and their descriptions from EDGE_CASES.md.

    Supports patterns like:
        ### EC-001: Title
        ### EC-001 Title
        **ID:** EC-001
    Returns dict: EC-ID -> description snippet.
    """
    found: dict[str, str] = {}

    # Match heading-based IDs: ### EC-001: Title  or  ### EC-001 Title
    heading_pattern = re.compile(
        r"^#{2,4}\s+(EC-\d{3}(?:-[A-Z]+)?|[A-Z]+-E\d{3,})[:\s]+(.+)$",
        re.MULTILINE,
    )
    for match in heading_pattern.finditer(content):
        eid = match.group(1).strip()
        desc = match.group(2).strip()
        found[eid] = desc

    # Match inline bold IDs: **EC-001** or **ID:** EC-001
    inline_pattern = re.compile(r"\*\*(?:ID:\s*)?([A-Z]+-E\d{3,}|EC-\d{3})\*\*")
    for match in inline_pattern.finditer(content):
        eid = match.group(1)
        if eid not in found:
            found[eid] = "(no description captured)"

    return found


def extract_edge_cases_from_manifest() -> dict[str, str]:
    """Extract edge case IDs from COVERAGE_MANIFEST.yaml edge_cases sections."""
    if not COVERAGE_MANIFEST.exists():
        return {}

    import yaml  # type: ignore

    with open(COVERAGE_MANIFEST, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    found: dict[str, str] = {}
    for module_name, module_data in manifest.items():
        if not isinstance(module_data, dict):
            continue
        tests = module_data.get("edge_cases", [])
        if not isinstance(tests, list):
            continue
        for test in tests:
            if isinstance(test, dict) and "id" in test:
                tid = test["id"]
                deferred = test.get("deferred_to")
                if deferred:
                    continue  # skip explicitly deferred edge cases
                desc = test.get("description", "(no description)")
                found[tid] = desc
    return found


def find_ids_in_codebase() -> set[str]:
    """Scan test files for edge case ID references."""
    found: set[str] = set()
    # Match EC-NNN or ATT-ENNN or ELEC-ENNN style IDs
    pattern = re.compile(r"\b(EC-\d{3}(?:-[A-Z]+)?|[A-Z]+-E\d{3,})\b")

    for test_file in TESTS_DIR.rglob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in pattern.finditer(content):
            found.add(match.group(1))

    return found


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=== Edge Case Coverage Verification ===")

    # Collect from both EDGE_CASES.md and COVERAGE_MANIFEST
    ec_from_doc: dict[str, str] = {}
    if EDGE_CASES_FILE.exists():
        content = EDGE_CASES_FILE.read_text(encoding="utf-8")
        ec_from_doc = extract_edge_cases_from_doc(content)
        print(f"Edge cases in EDGE_CASES.md: {len(ec_from_doc)}")
    else:
        print(f"WARNING: {EDGE_CASES_FILE} not found — skipping doc-based edge cases")

    ec_from_manifest = extract_edge_cases_from_manifest()
    print(f"Edge cases in COVERAGE_MANIFEST (non-deferred): {len(ec_from_manifest)}")

    # Merge (manifest takes priority for descriptions)
    all_cases = {**ec_from_doc, **ec_from_manifest}
    print(f"Total unique edge cases to verify: {len(all_cases)}")

    if not all_cases:
        print("No edge cases catalogued. Nothing to verify.")
        return 0

    found_in_code = find_ids_in_codebase()

    missing: dict[str, str] = {}
    present: list[str] = []
    for eid, desc in sorted(all_cases.items()):
        if eid in found_in_code:
            present.append(eid)
        else:
            missing[eid] = desc

    print(f"\nCatalogued: {len(all_cases)}")
    print(f"Covered:    {len(present)}")
    print(f"Missing:    {len(missing)}")

    if verbose and present:
        print("\n=== Covered Edge Cases ===")
        for eid in present:
            print(f"  [OK] {eid}: {all_cases[eid]}")

    if missing:
        print("\n=== MISSING EDGE CASE TESTS ===")
        for eid, desc in sorted(missing.items()):
            print(f"  [MISS] {eid}: {desc}")
        print(f"\nBuild FAILED: {len(missing)} edge case(s) have no corresponding test.")
        return 1

    print("\nAll catalogued edge cases have test coverage. Build PROCEEDS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
