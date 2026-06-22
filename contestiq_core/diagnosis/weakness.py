from __future__ import annotations

from collections import defaultdict

from contestiq_core.config import MODEL_THRESHOLDS
from contestiq_core.diagnosis.confidence import confidence_band, confidence_score
from contestiq_core.diagnosis.explanations import weakness_explanation
from contestiq_core.models import SkillEvidence, SkillScore, WeaknessSnapshot
from contestiq_core.taxonomy.skills import all_skills

LIKELY_MIN_CONFIDENCE = MODEL_THRESHOLDS.likely_needs_work_confidence_threshold
LIKELY_MIN_N_EFF = MODEL_THRESHOLDS.likely_needs_work_n_eff_threshold
LIKELY_MIN_DISTINCT_PROBLEMS = MODEL_THRESHOLDS.likely_needs_work_distinct_problem_threshold
LIMITED_TECHNIQUE_MIN_N_EFF = 2.0
LIMITED_TECHNIQUE_MIN_DISTINCT = 2


def _success_rate(evidence: list[SkillEvidence]) -> float | None:
    if not evidence:
        return None
    positives = sum(1 for item in evidence if item.outcome == "positive")
    mixed = sum(1 for item in evidence if item.outcome == "mixed")
    return round((positives + 0.45 * mixed) / len(evidence), 3)


def _severity_components(evidence: list[SkillEvidence], baseline_success_rate: float | None = None) -> dict[str, float]:
    if not evidence:
        return {
            "success_gap": 0.0,
            "attempts_friction": 0.0,
            "repeated_failure": 0.0,
            "verdict_friction": 0.0,
            "ceiling_gap": 0.0,
            "recent_decline": 0.0,
        }
    skill_success = _success_rate(evidence) or 0.0
    baseline = baseline_success_rate if baseline_success_rate is not None else skill_success
    total = len(evidence)
    repeated_failure = sum(1 for item in evidence if item.outcome == "friction" and len(item.verdicts) >= 2) / total
    wa_friction = sum(1 for item in evidence if "WRONG_ANSWER" in item.verdicts) / total
    hard_negative = [item for item in evidence if item.outcome == "friction" and item.difficulty_weight > 1.05]
    recent_items = sorted(evidence, key=lambda item: item.recency_weight, reverse=True)[: max(1, total // 2)]
    recent_avg = sum(item.evidence_value for item in recent_items) / len(recent_items)
    overall_avg = sum(item.evidence_value for item in evidence) / total
    return {
        "success_gap": max(0.0, baseline - skill_success),
        "attempts_friction": min(1.0, sum(max(0.0, 1.0 - item.attempt_modifier) for item in evidence) / total),
        "repeated_failure": repeated_failure,
        "verdict_friction": wa_friction,
        "ceiling_gap": min(1.0, len(hard_negative) / total),
        "recent_decline": max(0.0, min(1.0, overall_avg - recent_avg)),
    }


def severity_score(
    evidence: list[SkillEvidence],
    baseline_success_rate: float | None = None,
) -> tuple[float, dict[str, float]]:
    components = _severity_components(evidence, baseline_success_rate)
    severity = (
        0.40 * components["success_gap"]
        + 0.20 * components["attempts_friction"]
        + 0.15 * components["repeated_failure"]
        + 0.10 * components["verdict_friction"]
        + 0.10 * components["ceiling_gap"]
        + 0.05 * components["recent_decline"]
    )
    return round(max(0.0, min(1.0, severity)), 3), components


def _public_bucket(severity: float, confidence: float, n_eff: float, distinct: int) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if n_eff <= 0 or distinct == 0:
        return "Limited Evidence", "none", ["no mapped Codeforces evidence for this skill"]
    if n_eff < LIKELY_MIN_N_EFF:
        reasons.append("effective sample size below public weakness threshold")
    if distinct < LIKELY_MIN_DISTINCT_PROBLEMS:
        reasons.append("distinct problem count below public weakness threshold")
    if confidence < LIKELY_MIN_CONFIDENCE:
        reasons.append("confidence below public weakness threshold")

    underexposed = n_eff < 2.0 or distinct < 2
    if underexposed:
        return "Limited Evidence", "underexposed", reasons or ["underexposed skill evidence"]
    if confidence < 0.35:
        return "Limited Evidence", "underexposed", reasons or ["insufficient confidence"]
    if reasons:
        if severity >= 0.32 or confidence >= 0.35:
            return "Watchlist", "tentative", reasons
        return "Limited Evidence", "underexposed", reasons
    if severity >= 0.48:
        return "Likely Needs Work", "sufficient", []
    if severity >= 0.32 or confidence < 0.55:
        return "Watchlist", "tentative", []
    return "Hidden", "sufficient", []


def _repair_diagnostics(
    public_bucket: str,
    severity: float,
    confidence: float,
    n_eff: float,
    distinct: int,
    evidence_status: str,
) -> dict:
    meets_confidence = confidence >= LIKELY_MIN_CONFIDENCE
    meets_n_eff = n_eff >= LIKELY_MIN_N_EFF
    meets_distinct = distinct >= LIKELY_MIN_DISTINCT_PROBLEMS
    underexposed = evidence_status in {"underexposed", "none"} or n_eff < 2.0 or distinct < 2
    severity_ready = severity >= MODEL_THRESHOLDS.repair_severity_threshold
    reasons: list[str] = []
    if public_bucket != "Likely Needs Work":
        reasons.append(f"public bucket is {public_bucket}, not Likely Needs Work")
    if not severity_ready:
        reasons.append("severity below repair threshold")
    if not meets_confidence:
        reasons.append("confidence below repair threshold")
    if not meets_n_eff:
        reasons.append("effective sample size below repair threshold")
    if not meets_distinct:
        reasons.append("distinct problem count below repair threshold")
    if underexposed:
        reasons.append("skill is underexposed")
    repair_eligible = not reasons
    priority = round(severity * confidence, 4)
    return {
        "repair_eligible": repair_eligible,
        "repair_blocking_reasons": reasons,
        "meets_confidence_threshold": meets_confidence,
        "meets_n_eff_threshold": meets_n_eff,
        "meets_distinct_problem_threshold": meets_distinct,
        "is_underexposed": underexposed,
        "severity_above_repair_threshold": severity_ready,
        "public_bucket_reason": "; ".join(reasons) if reasons else "passed public repair thresholds",
        "priority_score": priority,
        "effective_repair_score": priority if repair_eligible else None,
    }


def _focused_practice_diagnostics(
    skill_id: str,
    public_bucket: str,
    severity: float,
    confidence: float,
    n_eff: float,
    distinct: int,
    avg_tag_reliability: float,
    evidence_status: str,
    repair_eligible: bool,
) -> dict:
    skill = all_skills()[skill_id]
    reasons: list[str] = []
    if repair_eligible:
        reasons.append("hard repair already eligible")
    if severity < MODEL_THRESHOLDS.focused_practice_severity_threshold:
        reasons.append("severity below focused practice threshold")
    if confidence < MODEL_THRESHOLDS.focused_practice_confidence_threshold:
        reasons.append("confidence below focused practice threshold")
    if n_eff < MODEL_THRESHOLDS.focused_practice_n_eff_threshold:
        reasons.append("effective sample size below focused practice threshold")
    if distinct < MODEL_THRESHOLDS.focused_practice_distinct_problem_threshold:
        reasons.append("distinct problem count below focused practice threshold")
    if avg_tag_reliability < MODEL_THRESHOLDS.focused_practice_min_avg_tag_reliability:
        reasons.append("average tag reliability below focused practice threshold")
    if evidence_status in {"underexposed", "none"} or n_eff <= 0 or distinct < 2:
        reasons.append("skill is underexposed or lacks meaningful mapped evidence")
    if skill.kind != "domain":
        reasons.append("focused practice is limited to domain skills in v1")
    if public_bucket == "Limited Evidence":
        reasons.append("limited evidence is routed to exploration, not focused practice")
    return {
        "focused_practice_eligible": not reasons,
        "focused_practice_blocking_reasons": reasons,
    }


def _apply_visibility(scores: list[SkillScore]) -> None:
    skills = all_skills()
    for score in scores:
        score.user_visible = False
        score.user_visible_bucket = None
        score.visibility_reason = "Hidden from compact user-facing map; available in debug diagnostics."

    likely = sorted([s for s in scores if s.public_bucket == "Likely Needs Work"], key=lambda s: s.severity * s.confidence, reverse=True)[:3]
    for score in likely:
        score.user_visible = True
        score.user_visible_bucket = "Likely Needs Work"
        score.visibility_reason = "Visible because it passed public friction thresholds and the max-3 cap."

    watchlist_candidates = [s for s in scores if s.public_bucket == "Watchlist"]
    domain_watchlist = [s for s in watchlist_candidates if skills[s.skill_id].kind == "domain"]
    overlay_watchlist = [
        s
        for s in watchlist_candidates
        if skills[s.skill_id].kind == "technique"
        and s.n_eff >= 6.0
        and s.distinct_problem_count >= 4
        and s.avg_tag_reliability >= 0.7
        and s.priority_score >= 0.2
    ]
    watchlist = sorted(domain_watchlist, key=lambda s: s.severity * s.confidence, reverse=True)
    if len(watchlist) < 3:
        watchlist.extend(sorted(overlay_watchlist, key=lambda s: s.severity * s.confidence, reverse=True))
    watchlist = watchlist[:3]
    for score in watchlist:
        score.user_visible = True
        score.user_visible_bucket = "Watchlist"
        score.visibility_reason = "Visible as cautious watchlist evidence within the max-3 cap."

    for score in watchlist_candidates:
        if score.user_visible:
            continue
        if skills[score.skill_id].kind == "technique":
            score.visibility_reason = "Technique overlay watchlist kept internal unless it has strong, meaningful evidence and a useful user-facing explanation."
        else:
            score.visibility_reason = "Watchlist cap reached; retained for debug diagnostics."

    limited_candidates = [s for s in scores if s.public_bucket == "Limited Evidence"]
    domain_limited = [s for s in limited_candidates if skills[s.skill_id].kind == "domain" and s.n_eff > 0]
    technique_limited = [
        s
        for s in limited_candidates
        if skills[s.skill_id].kind == "technique"
        and s.n_eff >= LIMITED_TECHNIQUE_MIN_N_EFF
        and s.distinct_problem_count >= LIMITED_TECHNIQUE_MIN_DISTINCT
    ]
    limited = sorted(domain_limited, key=lambda s: (s.n_eff, s.distinct_problem_count), reverse=True)
    if len(limited) < 5:
        limited.extend(sorted(technique_limited, key=lambda s: (s.n_eff, s.distinct_problem_count), reverse=True))
    for score in limited[:5]:
        score.user_visible = True
        score.user_visible_bucket = "Limited Evidence"
        score.visibility_reason = "Visible as limited evidence within the max-5 cap."

    for score in limited_candidates:
        if score.user_visible:
            continue
        if skills[score.skill_id].kind == "technique":
            score.visibility_reason = "Technique overlay has too little meaningful evidence for user-facing limited-evidence display."
        else:
            score.visibility_reason = "Limited-evidence list cap reached; retained for debug diagnostics."


def build_weakness_snapshot(evidence: list[SkillEvidence]) -> tuple[WeaknessSnapshot, list[SkillScore]]:
    grouped: dict[str, list[SkillEvidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.skill_id].append(item)

    skills = all_skills()
    scores: list[SkillScore] = []
    baseline_success = _success_rate(evidence)
    for skill_id, skill in skills.items():
        rows = grouped.get(skill_id, [])
        severity, severity_components = severity_score(rows, baseline_success)
        confidence, confidence_components = confidence_score(rows)
        distinct = int(confidence_components["distinct_problem_count"])
        n_eff = confidence_components["n_eff"]
        public_bucket, evidence_status, suppression_reasons = _public_bucket(severity, confidence, n_eff, distinct)
        repair_debug = _repair_diagnostics(public_bucket, severity, confidence, n_eff, distinct, evidence_status)
        focused_debug = _focused_practice_diagnostics(
            skill_id,
            public_bucket,
            severity,
            confidence,
            n_eff,
            distinct,
            confidence_components["average_tag_reliability"],
            evidence_status,
            repair_debug["repair_eligible"],
        )
        skill_success = _success_rate(rows)
        components = {
            **severity_components,
            **{f"confidence_{k}": v for k, v in confidence_components.items()},
        }
        scores.append(
            SkillScore(
                skill_id=skill_id,
                display_name=skill.display_name,
                severity=severity,
                confidence=confidence,
                category=public_bucket,  # type: ignore[arg-type]
                sample_size=len(rows),
                distinct_problems=distinct,
                explanation=weakness_explanation(skill_id, public_bucket),
                components=components,
                severity_score=severity,
                confidence_score=confidence,
                confidence_band=confidence_band(confidence),
                evidence_status=evidence_status,  # type: ignore[arg-type]
                n_eff=round(n_eff, 3),
                distinct_problem_count=distinct,
                rating_bucket_count=int(confidence_components["rating_bucket_count"]),
                avg_tag_reliability=round(confidence_components["average_tag_reliability"], 3),
                recency_factor=round(confidence_components["recency"], 3),
                skill_success_rate=skill_success,
                user_baseline_success_rate=baseline_success,
                success_gap=round(severity_components["success_gap"], 3),
                attempts_friction=round(severity_components["attempts_friction"], 3),
                repeated_failure=round(severity_components["repeated_failure"], 3),
                verdict_friction=round(severity_components["verdict_friction"], 3),
                ceiling_gap=round(severity_components["ceiling_gap"], 3),
                recent_decline=round(severity_components["recent_decline"], 3),
                public_bucket=public_bucket,  # type: ignore[arg-type]
                suppression_reasons=suppression_reasons,
                internal_bucket=public_bucket,  # type: ignore[arg-type]
                **repair_debug,
                **focused_debug,
            )
        )

    _apply_visibility(scores)
    likely = sorted([s for s in scores if s.public_bucket == "Likely Needs Work"], key=lambda s: s.severity * s.confidence, reverse=True)[:3]
    likely_ids = {s.skill_id for s in likely}
    watchlist = [
        s
        for s in scores
        if s.public_bucket == "Watchlist" or (s.public_bucket == "Likely Needs Work" and s.skill_id not in likely_ids)
    ]
    snapshot = WeaknessSnapshot(
        likely_needs_work=likely,
        watchlist=sorted(watchlist, key=lambda s: s.severity * s.confidence, reverse=True),
        limited_evidence=sorted([s for s in scores if s.public_bucket == "Limited Evidence"], key=lambda s: s.display_name),
        hidden=sorted([s for s in scores if s.public_bucket == "Hidden"], key=lambda s: s.display_name),
    )
    return snapshot, scores
