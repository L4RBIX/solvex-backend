"""Reusable mutation helpers for practice-pack oracles."""

from __future__ import annotations

from collections.abc import Callable

OracleFn = Callable[[str], str]


def mut_floor_instead_of_ceil(solve_ceil: OracleFn) -> OracleFn:
    """Wrap not used directly — kept as documentation hook."""
    return solve_ceil


def general_off_by_one_int(solve: OracleFn, *, delta: int = 1) -> OracleFn:
    def mutant(stdin: str) -> str:
        out = solve(stdin).strip()
        try:
            return f"{int(out) + delta}\n"
        except ValueError:
            return out + "\n"

    return mutant


def general_flip_yes_no(solve: OracleFn) -> OracleFn:
    def mutant(stdin: str) -> str:
        out = solve(stdin).strip().upper()
        if out == "YES":
            return "NO\n"
        if out == "NO":
            return "YES\n"
        return out + "\n"

    return mutant


def general_identity(stdin: str) -> str:
    return stdin if stdin.endswith("\n") else stdin + "\n"


def general_empty(_: str) -> str:
    return "\n"


def general_zero(_: str) -> str:
    return "0\n"


def general_one(_: str) -> str:
    return "1\n"
