from __future__ import annotations

from contestiq_core.models import SkillEvidence


def confidence_score(evidence: list[SkillEvidence]) -> tuple[float, dict[str, float]]:
    if not evidence:
        return 0.0, {
            "n_eff": 0.0,
            "effective_sample_size": 0.0,
            "distinct_problem_factor": 0.0,
            "distinct_problem_count": 0.0,
            "rating_bucket_coverage": 0.0,
            "rating_bucket_count": 0.0,
            "average_tag_reliability": 0.0,
            "recency": 0.0,
            "evidence_diversity": 0.0,
        }
    distinct = {item.problem_key for item in evidence}
    ratings = [item.problem_rating for item in evidence if item.problem_rating is not None]
    buckets = {rating // 200 for rating in ratings}
    outcomes = {item.outcome for item in evidence}
    reliability = sum(item.tag_reliability for item in evidence) / len(evidence)
    recency = sum(item.recency_weight for item in evidence) / len(evidence)
    n_eff = sum(item.mapping_share * item.tag_reliability for item in evidence)
    components = {
        "n_eff": n_eff,
        "effective_sample_size": min(1.0, n_eff / 8.0),
        "distinct_problem_factor": min(1.0, len(distinct) / 6.0),
        "distinct_problem_count": float(len(distinct)),
        "rating_bucket_coverage": min(1.0, len(buckets) / 3.0),
        "rating_bucket_count": float(len(buckets)),
        "average_tag_reliability": reliability,
        "recency": recency,
        "evidence_diversity": min(1.0, len(outcomes) / 3.0),
    }
    score = (
        0.25 * components["effective_sample_size"]
        + 0.20 * components["distinct_problem_factor"]
        + 0.15 * components["rating_bucket_coverage"]
        + 0.20 * components["average_tag_reliability"]
        + 0.10 * components["recency"]
        + 0.10 * components["evidence_diversity"]
    )
    return round(max(0.0, min(1.0, score)), 3), components


def confidence_band(confidence: float) -> str:
    if confidence < 0.35:
        return "insufficient evidence"
    if confidence < 0.55:
        return "tentative / watchlist only"
    if confidence < 0.75:
        return "moderate / likely current friction"
    return "high confidence"
