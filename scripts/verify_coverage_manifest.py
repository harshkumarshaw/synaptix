#!/usr/bin/env python3
"""Verify that every test ID in COVERAGE_MANIFEST.yaml exists in test files.

Exits 0 if all required tests are present.
Exits 1 with detailed report if any are missing.

Run pre-commit:
    python scripts/verify_coverage_manifest.py
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / "tests" / "COVERAGE_MANIFEST.yaml"
TESTS_DIR = ROOT / "tests"


def find_test_ids_in_codebase() -> set[str]:
    """Scan test files for test IDs in docstrings, comments, or test names."""
    found = set()
    # Pattern: any X-NNN or X-NNN-NNN identifier
    pattern = re.compile(r"\b([A-Z]+-[A-Z]*-?\d{3,})\b")

    for test_file in TESTS_DIR.rglob("test_*.py"):
        content = test_file.read_text(encoding="utf-8")
        for match in pattern.finditer(content):
            found.add(match.group(1))

    return found


def get_required_test_ids() -> dict[str, list[str]]:
    """Read COVERAGE_MANIFEST and extract all required (non-deferred) test IDs."""
    with open(MANIFEST) as f:
        manifest = yaml.safe_load(f)

    required: dict[str, list[str]] = {}
    deferred_count = 0
    deferred_by_target: dict[str, int] = {}

    for module_name, module_data in manifest.items():
        if not isinstance(module_data, dict):
            continue
        ids: list[str] = []
        for category in [
            "critical_tests",
            "nmc_compliance_tests",
            "compliance_tests",
            "edge_cases",
            "offline_sync_tests",
        ]:
            tests = module_data.get(category, [])
            if not isinstance(tests, list):
                continue
            for test in tests:
                if isinstance(test, dict) and "id" in test:
                    deferred_to = test.get("deferred_to")
                    if deferred_to:
                        # Count deferrals but don't include in required
                        deferred_count += 1
                        deferred_by_target[deferred_to] = deferred_by_target.get(deferred_to, 0) + 1
                        continue
                    ids.append(test["id"])
        if ids:
            required[module_name] = ids

    if deferred_count:
        print(f"Deferred tests (excluded from required): {deferred_count}")
        for target in sorted(deferred_by_target.keys()):
            print(f"  -> {target}: {deferred_by_target[target]} tests")

    return required


def main() -> int:
    if not MANIFEST.exists():
        print(f"ERROR: Manifest not found at {MANIFEST}")
        return 1

    print("=== Coverage Manifest Verification ===")

    required = get_required_test_ids()

    # Filter by command-line arguments if specified (e.g. verify_coverage_manifest.py workflow_engine)
    if len(sys.argv) > 1:
        target_modules = sys.argv[1:]
        required = {k: v for k, v in required.items() if k in target_modules}
        if not required:
            print(f"ERROR: None of the specified modules {target_modules} found in manifest.")
            return 1

    found = find_test_ids_in_codebase()

    total_required = sum(len(ids) for ids in required.values())
    total_found = 0
    missing = {}

    for module, ids in required.items():
        module_missing = [tid for tid in ids if tid not in found]
        module_found = len(ids) - len(module_missing)
        total_found += module_found
        if module_missing:
            missing[module] = module_missing

    coverage_pct = (total_found / total_required * 100) if total_required else 100

    print(f"\nRequired tests: {total_required}")
    print(f"Implemented:    {total_found}")
    print(f"Missing:        {total_required - total_found}")
    print(f"Coverage:       {coverage_pct:.1f}%")

    if missing:
        print("\n=== MISSING TESTS ===\n")
        for module, ids in missing.items():
            print(f"\n  {module}:")
            for tid in ids:
                print(f"    - {tid}")
        print("\nBuild FAILED. Implement missing tests or escalate.")
        return 1

    print("\nAll required tests implemented. Build PROCEEDS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
