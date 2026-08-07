"""Output checkers for SolveX practice/PvP packs.

Packs must declare checker_type. Constructive / multi-answer problems must use
a verifier (custom) — never raw string equality.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any


CheckerFn = Callable[[str, str], bool]


def _normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def exact_match(actual: str, expected: str) -> bool:
    """Line-rstrip exact compare (legacy Judge0 path)."""

    def lines(s: str) -> list[str]:
        return [
            ln.rstrip()
            for ln in _normalize_newlines(s).rstrip("\n").split("\n")
        ]

    return lines(actual) == lines(expected)


def tokens_match(actual: str, expected: str) -> bool:
    """Whitespace-insensitive token compare."""
    return _normalize_newlines(actual).split() == _normalize_newlines(expected).split()


def float_match(actual: str, expected: str, *, rel_eps: float = 1e-6, abs_eps: float = 1e-6) -> bool:
    """Tokenize and compare numeric tokens with tolerance; non-numeric exact."""
    a_toks = _normalize_newlines(actual).split()
    e_toks = _normalize_newlines(expected).split()
    if len(a_toks) != len(e_toks):
        return False
    for a, e in zip(a_toks, e_toks):
        try:
            af = float(a)
            ef = float(e)
        except ValueError:
            if a != e:
                return False
            continue
        if not math.isfinite(af) or not math.isfinite(ef):
            if a != e:
                return False
            continue
        if abs(af - ef) > max(abs_eps, rel_eps * max(1.0, abs(ef))):
            return False
    return True


def case_insensitive_tokens(actual: str, expected: str) -> bool:
    a = [t.casefold() for t in _normalize_newlines(actual).split()]
    e = [t.casefold() for t in _normalize_newlines(expected).split()]
    return a == e


_CHECKERS: dict[str, CheckerFn] = {
    "exact": exact_match,
    "tokens": tokens_match,
    "float": float_match,
    "tokens_ci": case_insensitive_tokens,
}


def get_checker(checker_type: str | None) -> CheckerFn:
    key = (checker_type or "exact").strip().lower()
    if key == "custom":
        raise ValueError("custom checker requires an explicit verifier callable")
    try:
        return _CHECKERS[key]
    except KeyError as exc:
        raise ValueError(f"unsupported checker_type: {checker_type!r}") from exc


def outputs_match(
    actual: str,
    expected: str,
    *,
    checker_type: str | None = "exact",
    verifier: CheckerFn | None = None,
) -> bool:
    if verifier is not None:
        return bool(verifier(actual, expected))
    return get_checker(checker_type)(actual, expected)


def normalize_checker_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "exact"
    key = value.strip().lower()
    if key == "custom":
        return "custom"
    if key not in _CHECKERS and key != "custom":
        return "exact"
    return key
