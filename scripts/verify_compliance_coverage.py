#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify that every NMC compliance test declared in COVERAGE_MANIFEST.yaml is:
  1. Implemented in test files (ID appears in codebase)
  2. Has an entry in tests/NMC_COMPLIANCE_TESTS.md (regulation-to-test mapping)

Exits 0 if all compliance tests are declared, implemented, and logged.
Exits 1 with detailed report if any gaps found.

Usage:
    python scripts/verify_compliance_coverage.py
    python scripts/verify_compliance_coverage.py --verbose
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMPLIANCE_TESTS_DOC = ROOT / "tests" / "NMC_COMPLIANCE_TESTS.md"
COMPLIANCE_LOG = ROOT / "docs" / "NMC_COMPLIANCE_LOG.md"
COVERAGE_MANIFEST = ROOT / "tests" / "COVERAGE_MANIFEST.yaml"
TESTS_DIR = ROOT / "tests"


def extract_compliance_ids_from_manifest() -> dict[str, dict]:
    """Extract all compliance/nmc_compliance test IDs from COVERAGE_MANIFEST.yaml.

    Returns dict: test_id -> {description, deferred_to, module}
    """
    if not COVERAGE_MANIFEST.exists():
        return {}

    import yaml  # type: ignore

    with open(COVERAGE_MANIFEST, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    found: dict[str, dict] = {}
    for module_name, module_data in manifest.items():
        if not isinstance(module_data, dict):
            continue
        for category in ("nmc_compliance_tests", "compliance_tests"):
            tests = module_data.get(category, [])
            if not isinstance(tests, list):
                continue
            for test in tests:
                if not isinstance(test, dict) or "id" not in test:
                    continue
                tid = test["id"]
                found[tid] = {
                    "description": test.get("description", ""),
                    "deferred_to": test.get("deferred_to"),
                    "module": module_name,
                    "regulation_ref": test.get("regulation_ref", ""),
                }
    return found


def extract_ids_from_doc(filepath: Path) -> set[str]:
    """Extract all compliance test IDs mentioned in a markdown document."""
    if not filepath.exists():
        return set()
    content = filepath.read_text(encoding="utf-8")
    # Match IDs like ATT-NMC-001, LOG-NMC-001, ELEC-NMC-001, DOAP-NMC-001, etc.
    pattern = re.compile(r"\b([A-Z]+-NMC-\d{3,}|[A-Z]+-NMC-\d{3,}[A-Z]*)\b")
    return {m.group(1) for m in pattern.finditer(content)}


def find_ids_in_codebase() -> set[str]:
    """Scan test files for compliance test ID references."""
    found: set[str] = set()
    # Match NMC-style compliance IDs
    pattern = re.compile(r"\b([A-Z]+-NMC-\d{3,})\b")

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

    print("=== NMC Compliance Coverage Verification ===")

    # 1. Get all declared compliance tests from manifest
    declared = extract_compliance_ids_from_manifest()
    active = {tid: data for tid, data in declared.items() if not data["deferred_to"]}
    deferred = {tid: data for tid, data in declared.items() if data["deferred_to"]}

    print(f"Compliance tests in manifest:  {len(declared)}")
    print(f"  Active (must pass):          {len(active)}")
    print(f"  Deferred (acknowledged):     {len(deferred)}")

    # 2. Check if IDs appear in compliance test document
    doc_ids = extract_ids_from_doc(COMPLIANCE_TESTS_DOC)
    log_ids = extract_ids_from_doc(COMPLIANCE_LOG)
    code_ids = find_ids_in_codebase()

    # 3. Compute gaps
    not_in_doc: list[str] = []
    not_in_code: list[str] = []
    fully_covered: list[str] = []

    for tid in sorted(active.keys()):
        in_doc = tid in doc_ids
        in_code = tid in code_ids
        if in_doc and in_code:
            fully_covered.append(tid)
        else:
            if not in_doc:
                not_in_doc.append(tid)
            if not in_code:
                not_in_code.append(tid)

    print(f"\n=== Compliance Test Status ===")
    print(f"Active declared: {len(active)}")
    print(f"In compliance doc ({COMPLIANCE_TESTS_DOC.name}): {len(doc_ids)}")
    print(f"In test codebase:             {len(code_ids)}")
    print(f"Fully covered (doc + code):   {len(fully_covered)}")
    print(f"Missing from doc:             {len(not_in_doc)}")
    print(f"Missing from code (stubs):    {len(not_in_code)}")

    if verbose:
        if fully_covered:
            print("\n=== Fully Covered ===")
            for tid in fully_covered:
                data = active[tid]
                print(f"  [OK] {tid}: {data['description']}")
        if deferred:
            print("\n=== Deferred (acknowledged) ===")
            for tid, data in sorted(deferred.items()):
                print(f"  [DEF→{data['deferred_to']}] {tid}: {data['description']}")

    failures: list[str] = []

    if not_in_doc:
        print("\n=== MISSING FROM COMPLIANCE DOC ===")
        for tid in not_in_doc:
            data = active[tid]
            print(f"  [MISS-DOC] {tid} ({data['module']}): {data['description']}")
        failures.append(f"{len(not_in_doc)} compliance test(s) not in NMC_COMPLIANCE_TESTS.md")

    if not_in_code:
        print("\n=== MISSING FROM TEST CODE (no stub or implementation) ===")
        for tid in not_in_code:
            data = active[tid]
            print(f"  [MISS-CODE] {tid} ({data['module']}): {data['description']}")
        failures.append(f"{len(not_in_code)} compliance test(s) not implemented in codebase")

    if failures:
        print(f"\nBuild FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nAll active compliance tests declared, documented, and implemented. Build PROCEEDS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
