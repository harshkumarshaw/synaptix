#!/usr/bin/env python3
"""Scan staged files for hardcoded secrets. Block commit if any found."""

import re
import subprocess
import sys

PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI/Anthropic API Key"),
    (r"AC[a-f0-9]{32}", "Twilio Account SID"),
    (r'(password|passwd|pwd)\s*[:=]\s*[\'"][^\'"]+[\'"]', "Hardcoded password"),
    (r'(api_key|apikey|secret)\s*[:=]\s*[\'"][^\'"]+[\'"]', "Hardcoded API key/secret"),
    (r"-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", "Private key"),
]

ALLOWED_FILES = {
    ".env.example",
    "CODING_STANDARDS.md",
    "check_secrets.py",
    "ERROR_HANDLING.md",
    "AOIP_MASTER_SPEC_v5.md",  # contains regex examples
}


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def main() -> int:
    files = get_staged_files()
    if not files:
        return 0

    issues = []
    for file_path in files:
        path_parts = file_path.split("/")
        if any(p in ALLOWED_FILES for p in path_parts):
            continue
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (FileNotFoundError, IsADirectoryError):
            continue

        for pattern, desc in PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                issues.append((file_path, line_num, desc, match.group()[:30]))

    if issues:
        print("=== HARDCODED SECRETS DETECTED ===")
        for path, line, desc, snippet in issues:
            print(f"  {path}:{line}  [{desc}]  {snippet}...")
        print("\nCOMMIT BLOCKED. Remove secrets or use environment variables.")
        print("Reference: conventions/CODING_STANDARDS.md — Commandment 4")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
