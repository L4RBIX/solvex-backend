from __future__ import annotations

import json
import re
from typing import Any


BANNED_PUBLIC_PHRASES = [
    "verified skill",
    "proves your skill",
    "mastered",
    "guaranteed improvement",
    "authenticity confirmed",
    "independent solving confirmed",
    "cheating detected",
    "exact mastery",
    "optimal plan",
]

_PROOF_OF_SKILL_RE = re.compile(r"(?<!not\s)(?<!no\s)(?<!without\s)proof of skill")


def unsafe_public_phrases(text: str) -> list[str]:
    lowered = text.lower()
    found = [phrase for phrase in BANNED_PUBLIC_PHRASES if phrase in lowered]
    if _PROOF_OF_SKILL_RE.search(lowered):
        found.append("proof of skill")
    return sorted(set(found))


def assert_safe_public_text(text: str) -> None:
    found = unsafe_public_phrases(text)
    if found:
        raise AssertionError(f"Unsafe public wording found: {', '.join(found)}")


def scan_public_payload(payload: dict[str, Any]) -> None:
    assert_safe_public_text(json.dumps(payload, ensure_ascii=False))
