#!/usr/bin/env python3
"""Repo secret scan (Phase 09). Exit 1 on findings.

Checks:
1. High-entropy/known-shape secrets in tracked source (backend + frontend).
2. Service-role / backend-only key names referenced anywhere in wope/src
   (the browser bundle must never see them).
3. .env files must not exist inside wope/src or public dirs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO = BACKEND.parent.parent
FRONTEND_SRC = REPO / "wope" / "src"

SECRET_PATTERNS = [
    (re.compile(r"sk_live_[0-9a-zA-Z]{16,}"), "stripe live secret key"),
    (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "API secret key (sk-…)"),
    (re.compile(r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9._-]{40,}"), "JWT (possible service key)"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"), "private key material"),
]

FRONTEND_FORBIDDEN_NAMES = [
    "SUPABASE_SERVICE_KEY",
    "SERVICE_ROLE",
    "JUDGE0_API_KEY",
    "DEEPSEEK_API_KEY",
    "ADMIN_API_KEY",
    "BILLING_API_KEY",
    "BILLING_WEBHOOK_SECRET",
]

SCAN_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml", ".toml", ".md", ".sql"}
SKIP_DIRS = {"node_modules", ".next", "dist", ".git", "__pycache__", ".venv", "api_cache", ".cache", ".pytest_cache"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in SCAN_SUFFIXES and ".env" not in path.name:
            yield path


def main() -> int:
    findings: list[str] = []

    for root in (BACKEND, FRONTEND_SRC):
        if not root.exists():
            continue
        for path in iter_files(root):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(text):
                    findings.append(f"{label}: {path}")

    if FRONTEND_SRC.exists():
        for path in iter_files(FRONTEND_SRC):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name in FRONTEND_FORBIDDEN_NAMES:
                if name in text:
                    findings.append(f"backend-only key name '{name}' referenced in frontend: {path}")
        for env_file in FRONTEND_SRC.rglob(".env*"):
            findings.append(f".env file inside frontend src: {env_file}")

    public_dir = REPO / "wope" / "public"
    if public_dir.exists():
        for env_file in public_dir.rglob(".env*"):
            findings.append(f".env file inside public dir: {env_file}")

    if findings:
        print("SECRET SCAN FAILED:")
        for finding in findings:
            print(f"  - {finding}")
        return 1
    print("Secret scan passed: no service keys in frontend, no secret-shaped strings in source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
