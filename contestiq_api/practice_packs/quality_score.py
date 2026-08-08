"""Normalized pack quality score (0..100) on top of hard gates."""

from __future__ import annotations

from typing import Any

from contestiq_api.practice_packs.quality import DEFAULT_THRESHOLDS, QualityThresholds, evaluate_quality

# Activation policy (hard gates still required via evaluate_quality.passed).
AUTO_ACTIVATE_MIN = 85
REVIEW_MIN = 75


def compute_quality_score(
    *,
    mutation_score: float,
    test_count: int,
    oracle_count: int,
    oracles_agree: bool,
    has_sample: bool,
    checker_type: str = "exact",
    agreement_ratio: float = 1.0,
    diverse_case_count: int | None = None,
    surviving_mutants: int = 0,
) -> dict[str, Any]:
    """Return quality_score and activation recommendation.

    Hard trust gates remain in evaluate_quality; this score only ranks packs
    that already satisfy (or fail) those gates.
    """
    gate = evaluate_quality(
        test_count=test_count,
        mutation_score=mutation_score,
        oracle_count=oracle_count,
        oracles_agree=oracles_agree,
        has_sample=has_sample,
        thresholds=DEFAULT_THRESHOLDS,
    )

    score = 0.0
    # Oracle agreement (25)
    if oracles_agree:
        score += 25.0 * max(0.0, min(1.0, agreement_ratio))
    # Mutation kill rate (30) — false-AC defense
    score += 30.0 * max(0.0, min(1.0, mutation_score))
    if surviving_mutants > 0 and mutation_score + 1e-12 < 1.0:
        score -= min(10.0, 2.5 * surviving_mutants)
    # Sample inclusion (15)
    if has_sample:
        score += 15.0
    # Test volume / diversity (20)
    volume = min(1.0, test_count / 12.0)
    diversity = min(1.0, (diverse_case_count or test_count) / 10.0)
    score += 12.0 * volume + 8.0 * diversity
    # Checker confidence (10)
    if checker_type in {"exact", "tokens", "tokens_ci"}:
        score += 10.0
    elif checker_type == "float":
        score += 6.0
    else:
        score += 2.0

    score = max(0.0, min(100.0, score))

    if not gate["passed"]:
        recommendation = "reject"
    elif score + 1e-12 >= AUTO_ACTIVATE_MIN:
        recommendation = "auto_activate"
    elif score + 1e-12 >= REVIEW_MIN:
        recommendation = "review_required"
    else:
        recommendation = "reject"

    return {
        "quality_score": round(score, 2),
        "recommendation": recommendation,
        "auto_activate_min": AUTO_ACTIVATE_MIN,
        "review_min": REVIEW_MIN,
        "gate": gate,
    }


def attach_quality_score(quality_report: dict[str, Any], **score_kwargs: Any) -> dict[str, Any]:
    scored = compute_quality_score(**score_kwargs)
    out = dict(quality_report)
    out["quality_score"] = scored["quality_score"]
    out["recommendation"] = scored["recommendation"]
    out["score_policy"] = {
        "auto_activate_min": scored["auto_activate_min"],
        "review_min": scored["review_min"],
    }
    return out
