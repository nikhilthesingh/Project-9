#!/usr/bin/env python3
"""
Custom DevSecOps Gate: AI Prompt Injection & Hardcoded System Prompt Scanner
Scans Python source files for hardcoded SYSTEM_PROMPT secrets and unsafe injection patterns.
"""
import os
import re
import sys

# Required pattern lists for DevSecOps Gate 4
SYSTEM_PROMPT_PATTERNS = [
    r'SYSTEM_PROMPT\s*=\s*["\'].*?(?:API_KEY|password|secret|TECHCORP-ADMIN-KEY).*?["\']',
    r'SYSTEM_PROMPT\s*=\s*["\']You are TechCorp.*?["\']',
    r'role["\']\s*:\s*["\']system["\']\s*,\s*["\']content["\']\s*:\s*["\'][^"\']{20,}["\']'
]

INJECTION_PHRASES = [
    r'ignore\s+previous\s+instructions',
    r'pretend\s+you\s+are\s+DAN',
    r'act\s+as\s+if\s+you\s+have\s+no\s+restrictions',
    r'bypass\s+all\s+safety\s+filters',
    r'UNVALIDATED_PROMPT_CONCATENATION'
]


def scan_file(filepath: str) -> list:
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return findings

    for line_num, line in enumerate(lines, start=1):
        for pat in SYSTEM_PROMPT_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                findings.append(
                    f"[FAIL] {filepath}:{line_num} -> Hardcoded System Prompt / Secret Pattern matched: {pat}"
                )
        for phrase in INJECTION_PHRASES:
            if re.search(phrase, line, re.IGNORECASE):
                findings.append(
                    f"[FAIL] {filepath}:{line_num} -> Unsafe Injection Phrase matched: {phrase}"
                )
    return findings


def main():
    print("=== Gate 4: Running Custom AI Prompt Injection & System Prompt Scanner ===")
    all_findings = []
    for root, _, files in os.walk("."):
        if ".git" in root or "venv" in root or "ai-lab" in root:
            continue
        for file in files:
            if file.endswith(".py") and file != "inject_scanner.py":
                path = os.path.join(root, file)
                all_findings.extend(scan_file(path))

    if all_findings:
        print(f"\n[!] Custom AI Security Scanner detected {len(all_findings)} violation(s):")
        for item in all_findings:
            print(f"  {item}")
        sys.exit(1)

    print("[+] PASS: No hardcoded system prompts or prompt injection patterns found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
