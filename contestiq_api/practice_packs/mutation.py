"""Mutation scoring for candidate practice packs (pure-Python, no Judge0)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

OracleFn = Callable[[str], str]


@dataclass(frozen=True)
class MutationResult:
    mutation_count: int
    killed_count: int
    surviving: tuple[str, ...]
    mutation_score: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "mutation_count": self.mutation_count,
            "killed_count": self.killed_count,
            "surviving_mutants": list(self.surviving),
            "mutation_score": self.mutation_score,
        }


def score_mutations(
    tests: list[dict[str, str]],
    *,
    correct: OracleFn,
    mutants: dict[str, OracleFn],
    checker: Callable[[str, str], bool],
) -> MutationResult:
    """A mutant is killed if it disagrees with expected on any test."""
    surviving: list[str] = []
    killed = 0
    for name, mutant in mutants.items():
        killed_this = False
        for test in tests:
            try:
                actual = mutant(test["input"])
            except Exception:
                killed_this = True
                break
            if not checker(actual, test["expected_output"]):
                killed_this = True
                break
            # Also kill if mutant matches expected but correct does not
            # (inconsistent pack) — treated as kill for mutant path.
        if killed_this:
            killed += 1
        else:
            surviving.append(name)
    total = len(mutants)
    score = (killed / total) if total else 0.0
    # Sanity: correct oracle must pass all tests.
    for test in tests:
        if not checker(correct(test["input"]), test["expected_output"]):
            raise ValueError("correct oracle disagrees with pack expected_output")
    return MutationResult(
        mutation_count=total,
        killed_count=killed,
        surviving=tuple(surviving),
        mutation_score=score,
    )
