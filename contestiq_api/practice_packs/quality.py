"""Quality gates for activating practice packs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityThresholds:
    min_tests: int = 8
    min_mutation_score: float = 0.75
    min_oracles: int = 2
    require_sample: bool = True


DEFAULT_THRESHOLDS = QualityThresholds()


def evaluate_quality(
    *,
    test_count: int,
    mutation_score: float,
    oracle_count: int,
    oracles_agree: bool,
    has_sample: bool,
    thresholds: QualityThresholds = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    failures: list[str] = []
    if test_count < thresholds.min_tests:
        failures.append(f"test_count {test_count} < {thresholds.min_tests}")
    if mutation_score + 1e-12 < thresholds.min_mutation_score:
        failures.append(
            f"mutation_score {mutation_score:.3f} < {thresholds.min_mutation_score}"
        )
    if oracle_count < thresholds.min_oracles:
        failures.append(f"oracle_count {oracle_count} < {thresholds.min_oracles}")
    if not oracles_agree:
        failures.append("independent oracles disagree on generated tests")
    if thresholds.require_sample and not has_sample:
        failures.append("official/public sample missing from pack")
    passed = not failures
    return {
        "passed": passed,
        "failures": failures,
        "thresholds": {
            "min_tests": thresholds.min_tests,
            "min_mutation_score": thresholds.min_mutation_score,
            "min_oracles": thresholds.min_oracles,
            "require_sample": thresholds.require_sample,
        },
        "metrics": {
            "test_count": test_count,
            "mutation_score": mutation_score,
            "oracle_count": oracle_count,
            "oracles_agree": oracles_agree,
            "has_sample": has_sample,
        },
    }
