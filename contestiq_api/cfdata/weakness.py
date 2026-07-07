"""Evidence-based weakness engine (Phase 04).

Everything is computed from problem episodes × problem_skill_map — never from
raw submissions (repeated submissions cannot overcount) and never from claims
the data cannot support (no solve-time, cheating, editorial, or avoidance
inference; runtime/memory are not weakness signals).

All recency math is anchored to data_cutoff_time (the newest submission in the
data), NOT wall-clock time, so a run is reproducible from its snapshot.

Formulas
--------
recency weight        w = 2 ** (-age_days / half_life)
                      half-lives: ability 180 d, exposure 365 d, improvement 90 d
shrunk success rate   (alpha + weighted_solved) / (alpha + beta + weighted_total),
                      alpha = beta = 1.5
attempt efficiency    solved:   1 / (1 + ln(1 + failed_before_ac))
                      unsolved: 0.35 / (1 + ln(1 + failed_attempts))
rating estimate       weighted mean of per-episode anchors
                      (clean: rating+100, friction/delayed: rating, abandoned: rating-150),
                      shrunk toward global rating with strength K_SHRINK = 6
uncertainty           300 / sqrt(1 + n_eff_rated) + 50
confidence            sample_factor * (0.35 + 0.65 * quality)
                      sample_factor = n_eff / (n_eff + 6)
                      quality = 0.3*rating_coverage + 0.4*taxonomy_quality + 0.3*mean_recency
severity (0-100)      (0.45*ability_gap + 0.40*friction + 0.15*mean_recency)
                      * 100 * (0.6 + 0.4*confidence)
underexposure         max(0, (opportunity_share - exposure_share) / opportunity_share)
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.cfdata.episodes import GLOBAL_DEFAULT_RATING
from contestiq_api.versions import ANALYSIS_VERSION, PROBLEM_CATALOG_VERSION, TAXONOMY_VERSION

ALPHA = 1.5
BETA = 1.5
HALF_LIFE_ABILITY_DAYS = 180.0
HALF_LIFE_EXPOSURE_DAYS = 365.0
HALF_LIFE_IMPROVEMENT_DAYS = 90.0
K_SHRINK = 6.0
SAMPLE_K = 6.0
DAY_SECONDS = 86400.0

MIN_EVIDENCE_N_EFF = 1.5
UNDEREXPOSED_THRESHOLD = 0.6
LIKELY_WEAKNESS_SEVERITY = 55
LIKELY_WEAKNESS_CONFIDENCE = 0.55
POSSIBLE_WEAKNESS_SEVERITY = 40
POSSIBLE_WEAKNESS_CONFIDENCE = 0.35

STATUSES = (
    "strength",
    "likely_strength",
    "likely_weakness",
    "possible_weakness",
    "underexposed",
    "insufficient_evidence",
    "historical_weakness_recent_improvement",
    "maintenance_needed",
    "calibration_needed",
)


def recency_weight(age_days: float, half_life_days: float) -> float:
    return 2.0 ** (-max(age_days, 0.0) / half_life_days)


def shrunk_success_rate(weighted_solved: float, weighted_total: float) -> float:
    return (ALPHA + weighted_solved) / (ALPHA + BETA + weighted_total)


def attempt_efficiency(solved: bool, failed_attempts: int) -> float:
    if solved:
        return 1.0 / (1.0 + math.log(1.0 + failed_attempts))
    return 0.35 / (1.0 + math.log(1.0 + failed_attempts))


def _episode_rating_anchor(episode: dict[str, Any]) -> float | None:
    rating = episode.get("problem_rating")
    if rating is None:
        return None
    status = episode["final_status"]
    if status == "clean_solve":
        return rating + 100.0
    if status in ("solved_with_friction", "delayed_ac"):
        return float(rating)
    return rating - 150.0  # abandoned


def _load_inputs(handle: str) -> dict[str, Any]:
    canonical = store.canonical_handle(handle)
    with store.connect() as conn:
        episodes = [dict(row) for row in conn.execute(
            "SELECT * FROM problem_episodes WHERE handle = ?", (canonical,)
        ).fetchall()]
        mappings = [dict(row) for row in conn.execute(
            "SELECT problem_id, skill_id, weight, confidence FROM problem_skill_map WHERE taxonomy_version = ?",
            (TAXONOMY_VERSION,),
        ).fetchall()]
        user = conn.execute("SELECT rating FROM cf_users WHERE handle = ?", (canonical,)).fetchone()
        taxonomy_rows = conn.execute(
            "SELECT skill_id, parent_id FROM skill_taxonomy WHERE taxonomy_version = ?", (TAXONOMY_VERSION,)
        ).fetchall()
    map_by_problem: dict[str, list[dict[str, Any]]] = {}
    for row in mappings:
        map_by_problem.setdefault(row["problem_id"], []).append(row)
    if user and user["rating"] is not None:
        global_rating, rating_source = int(user["rating"]), "cf_users"
    else:
        global_rating, rating_source = GLOBAL_DEFAULT_RATING, "global_default"
    return {
        "handle": canonical,
        "episodes": episodes,
        "map_by_problem": map_by_problem,
        "global_rating": global_rating,
        "global_rating_source": rating_source,
        "taxonomy_skills": {row["skill_id"]: row["parent_id"] for row in taxonomy_rows},
    }


def _opportunity_shares(map_by_problem: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
    """Each skill's share of the mapped problem catalog (the training opportunity)."""
    totals: dict[str, float] = {}
    for rows in map_by_problem.values():
        for row in rows:
            totals[row["skill_id"]] = totals.get(row["skill_id"], 0.0) + row["weight"]
    grand_total = sum(totals.values())
    if grand_total <= 0:
        return {}
    return {skill: total / grand_total for skill, total in totals.items()}


def _rating_band_label(ratings: list[int]) -> str:
    if not ratings:
        return "unknown"
    low = int(min(ratings) // 100 * 100)
    high = int(math.ceil(max(ratings) / 100) * 100)
    if low == high:
        high += 100
    return f"{low}-{high}"


def _input_data_hash(inputs: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "handle": inputs["handle"],
            "episodes": sorted(ep["episode_hash"] for ep in inputs["episodes"]),
            "skill_map": sorted(
                (pid, row["skill_id"], row["weight"], row["confidence"])
                for pid, rows in inputs["map_by_problem"].items()
                for row in rows
            ),
            "global_rating": inputs["global_rating"],
            "analysis_version": ANALYSIS_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _classify(
    n_eff: float,
    underexposure: float,
    opportunity: float,
    severity: int,
    confidence: float,
    success_rate: float,
    rating_coverage: float,
    estimate: int | None,
    global_rating: int,
    improvement: bool,
) -> str:
    if n_eff < MIN_EVIDENCE_N_EFF:
        if underexposure >= 0.5 and opportunity > 0.01:
            return "underexposed"
        return "insufficient_evidence"
    if underexposure >= UNDEREXPOSED_THRESHOLD and n_eff < 3.0:
        return "underexposed"
    if improvement:
        return "historical_weakness_recent_improvement"
    if severity >= LIKELY_WEAKNESS_SEVERITY and confidence >= LIKELY_WEAKNESS_CONFIDENCE:
        return "likely_weakness"
    if severity >= POSSIBLE_WEAKNESS_SEVERITY and confidence >= POSSIBLE_WEAKNESS_CONFIDENCE:
        return "possible_weakness"
    if rating_coverage < 0.3:
        return "calibration_needed"
    if (
        success_rate >= 0.75
        and confidence >= 0.6
        and estimate is not None
        and estimate >= global_rating - 100
    ):
        return "strength"
    if success_rate >= 0.65 and confidence >= 0.4:
        return "likely_strength"
    return "maintenance_needed"


def _explanation(skill_id: str, status: str, ev: dict[str, Any], global_rating: int) -> str:
    """Every sentence here states only what the evidence dict contains."""
    name = skill_id.replace("_", " ").replace(".", " → ")
    base = (
        f"{ev['solved']} of {ev['episodes']} mapped problem episodes were eventually solved "
        f"(recency-weighted evidence: {ev['weighted_episodes']})."
    )
    if status == "insufficient_evidence":
        return f"Too few mapped episodes for {name} to say anything reliable. {base}"
    if status == "underexposed":
        return (
            f"{name} appears underexposed relative to how often it occurs in the problem catalog. "
            f"{base} This is an exposure observation, not a weakness claim."
        )
    if status == "likely_weakness":
        return (
            f"Evidence suggests {name} is below your current global level: {base} "
            f"Average failed attempts before AC: {ev['avg_failed_before_ac']}. "
            f"Estimated skill rating {ev['estimated_skill_rating']} vs global {global_rating}."
        )
    if status == "possible_weakness":
        return (
            f"Some friction signals in {name}, but evidence is not strong enough for a firm call. {base} "
            f"Average failed attempts before AC: {ev['avg_failed_before_ac']}."
        )
    if status == "historical_weakness_recent_improvement":
        return (
            f"Older {name} episodes showed friction, but recent episodes succeed more often. {base} "
            "Recent evidence is weighted higher than old failures."
        )
    if status == "strength":
        return f"{name} shows consistent solved episodes at or above your level. {base}"
    if status == "likely_strength":
        return f"{name} leans strong on current evidence, with room for more data. {base}"
    if status == "calibration_needed":
        return (
            f"Most {name} episodes lack problem ratings, so difficulty cannot be anchored. {base} "
            "Solving a few rated problems would calibrate this skill."
        )
    return f"{name} looks stable; occasional practice keeps evidence fresh. {base}"


def _skill_score(
    skill_id: str,
    contributions: list[dict[str, Any]],
    cutoff: int,
    global_rating: int,
    opportunity: float,
    exposure_share: float,
) -> dict[str, Any]:
    n_eff = sum(c["w"] for c in contributions)
    weighted_solved = sum(c["w"] for c in contributions if c["solved"])
    success_rate = shrunk_success_rate(weighted_solved, n_eff)

    eff_num = sum(c["w"] * c["efficiency"] for c in contributions)
    efficiency_mean = eff_num / n_eff if n_eff > 0 else 0.0

    mapping_weight_total = sum(c["mapping_weight"] for c in contributions)
    mean_recency = n_eff / mapping_weight_total if mapping_weight_total > 0 else 0.0
    taxonomy_quality = (
        sum(c["w"] * c["mapping_confidence"] for c in contributions) / n_eff if n_eff > 0 else 0.0
    )

    rated = [c for c in contributions if c["rating_anchor"] is not None]
    rated_weight = sum(c["w"] for c in rated)
    rating_coverage = rated_weight / n_eff if n_eff > 0 else 0.0

    if rated:
        raw_mean = sum(c["w"] * c["rating_anchor"] for c in rated) / rated_weight
        estimate = (rated_weight * raw_mean + K_SHRINK * global_rating) / (rated_weight + K_SHRINK)
        uncertainty = 300.0 / math.sqrt(1.0 + rated_weight) + 50.0
        estimate_int = int(round(estimate))
        low, high = int(round(estimate - uncertainty)), int(round(estimate + uncertainty))
    else:
        estimate_int, low, high = None, None, None

    sample_factor = n_eff / (n_eff + SAMPLE_K)
    quality = 0.3 * rating_coverage + 0.4 * taxonomy_quality + 0.3 * mean_recency
    confidence = round(sample_factor * (0.35 + 0.65 * quality), 2)

    gap = 0.0
    if estimate_int is not None:
        gap = min(max((global_rating - estimate_int) / 400.0, 0.0), 1.0)
    friction = 0.6 * (1.0 - success_rate) + 0.4 * (1.0 - efficiency_mean)
    severity = int(round((0.45 * gap + 0.40 * friction + 0.15 * mean_recency) * 100 * (0.6 + 0.4 * confidence)))

    underexposure = 0.0
    if opportunity > 0:
        underexposure = round(max(0.0, (opportunity - exposure_share) / opportunity), 2)

    # Recent-improvement check (90-day window, unweighted-by-recency inside windows).
    recent, older = [], []
    for c in contributions:
        (recent if c["age_days"] <= 90.0 else older).append(c)
    improvement = False
    recent_w = sum(c["mapping_weight"] for c in recent)
    older_w = sum(c["mapping_weight"] for c in older)
    if recent_w >= 2.0 and older_w >= 3.0:
        older_success = shrunk_success_rate(sum(c["mapping_weight"] for c in older if c["solved"]), older_w)
        recent_success = shrunk_success_rate(sum(c["mapping_weight"] for c in recent if c["solved"]), recent_w)
        improvement = older_success <= 0.45 and recent_success >= 0.65

    episodes_count = len(contributions)
    solved_count = sum(1 for c in contributions if c["solved"])
    failed_counts = [c["failed_before_ac"] for c in contributions]
    avg_failed = round(sum(failed_counts) / episodes_count, 1) if episodes_count else 0.0

    status = _classify(
        n_eff, underexposure, opportunity, severity, confidence, success_rate,
        rating_coverage, estimate_int, global_rating, improvement,
    )

    warnings: list[str] = []
    if n_eff < 3:
        warnings.append("small_sample_size")
    elif n_eff < 6:
        warnings.append("moderate_sample_size")
    if 0 < rating_coverage < 0.5:
        warnings.append("low_rating_coverage")
    elif rating_coverage == 0 and episodes_count:
        warnings.append("no_rated_problems")
    if taxonomy_quality < 0.6:
        warnings.append("low_taxonomy_confidence")
    if mean_recency < 0.3 and episodes_count:
        warnings.append("stale_evidence")
    if episodes_count and (mapping_weight_total / episodes_count) < 0.5:
        warnings.append("mixed_problem_tags")

    evidence = {
        "episodes": episodes_count,
        "weighted_episodes": round(n_eff, 2),
        "solved": solved_count,
        "failed_or_abandoned": episodes_count - solved_count,
        "avg_failed_before_ac": avg_failed,
        "success_rate_shrunk": round(success_rate, 3),
        "attempt_efficiency": round(efficiency_mean, 3),
        "rating_band": _rating_band_label([c["problem_rating"] for c in contributions if c["problem_rating"] is not None]),
        "rating_coverage": round(rating_coverage, 2),
        "recent_window_days": int(HALF_LIFE_ABILITY_DAYS),
        "taxonomy_quality": round(taxonomy_quality, 2),
        "mean_recency_weight": round(mean_recency, 3),
        "context_breakdown": _context_breakdown(contributions),
        "rating_bands": _band_breakdown(contributions),
        "exposure_share": round(exposure_share, 4),
        "opportunity_share": round(opportunity, 4),
    }

    return {
        "skill_id": skill_id,
        "status": status,
        "confidence": confidence,
        "severity": severity,
        "underexposure": underexposure,
        "estimated_skill_rating": estimate_int,
        "estimated_skill_rating_low": low,
        "estimated_skill_rating_high": high,
        "evidence": evidence,
        "warnings": warnings,
        "explanation": _explanation(skill_id, status, {**evidence, "estimated_skill_rating": estimate_int}, global_rating),
        "_contributions": contributions,
    }


def _context_breakdown(contributions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in contributions:
        counts[c["context_type"] or "other"] = counts.get(c["context_type"] or "other", 0) + 1
    return counts


def _band_breakdown(contributions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in contributions:
        counts[c["rating_band"]] = counts.get(c["rating_band"], 0) + 1
    return counts


def analyze_handle_weakness(handle: str) -> dict[str, Any]:
    """Run the weakness engine and persist an immutable snapshot."""
    inputs = _load_inputs(handle)
    episodes = inputs["episodes"]
    map_by_problem = inputs["map_by_problem"]
    global_rating = inputs["global_rating"]

    cutoff = max((ep["last_submission_at"] or 0 for ep in episodes), default=None)

    # Per-skill episode contributions.
    by_skill: dict[str, list[dict[str, Any]]] = {}
    exposure_totals: dict[str, float] = {}
    exposure_grand_total = 0.0
    for ep in episodes:
        skill_rows = map_by_problem.get(ep["problem_id"], [])
        age_days = ((cutoff or 0) - (ep["last_submission_at"] or cutoff or 0)) / DAY_SECONDS
        ability_recency = recency_weight(age_days, HALF_LIFE_ABILITY_DAYS)
        exposure_recency = recency_weight(age_days, HALF_LIFE_EXPOSURE_DAYS)
        solved = bool(ep["eventual_ac"])
        for row in skill_rows:
            w = ability_recency * row["weight"]
            by_skill.setdefault(row["skill_id"], []).append(
                {
                    "episode_id": ep["episode_id"],
                    "problem_id": ep["problem_id"],
                    "w": w,
                    "mapping_weight": row["weight"],
                    "mapping_confidence": row["confidence"],
                    "recency": ability_recency,
                    "age_days": age_days,
                    "solved": solved,
                    "failed_before_ac": ep["failed_before_ac"],
                    "efficiency": attempt_efficiency(solved, ep["failed_before_ac"]),
                    "rating_anchor": _episode_rating_anchor(ep),
                    "problem_rating": ep["problem_rating"],
                    "rating_band": ep["rating_band"],
                    "context_type": ep["context_type"],
                    "final_status": ep["final_status"],
                }
            )
            exposure_totals[row["skill_id"]] = exposure_totals.get(row["skill_id"], 0.0) + exposure_recency * row["weight"]
            exposure_grand_total += exposure_recency * row["weight"]

    opportunity = _opportunity_shares(map_by_problem)

    run_warnings: list[str] = []
    if not episodes:
        run_warnings.append("no_episodes_found_run_sync_and_rebuild_first")
    if not opportunity:
        run_warnings.append("problem_skill_map_empty_underexposure_unavailable")
    if inputs["global_rating_source"] == "global_default":
        run_warnings.append("global_rating_defaulted")

    # Score every skill with episodes, plus top-level skills that are notably
    # underexposed (only when the user has enough overall activity to compare).
    skills_to_score = set(by_skill)
    if len(episodes) >= 10:
        for skill_id, share in opportunity.items():
            parent = inputs["taxonomy_skills"].get(skill_id, "missing")
            if parent is None and share >= 0.03 and skill_id not in by_skill:
                skills_to_score.add(skill_id)

    scores = []
    for skill_id in sorted(skills_to_score):
        contributions = by_skill.get(skill_id, [])
        exposure_share = (
            exposure_totals.get(skill_id, 0.0) / exposure_grand_total if exposure_grand_total > 0 else 0.0
        )
        if contributions:
            scores.append(
                _skill_score(skill_id, contributions, cutoff or 0, global_rating, opportunity.get(skill_id, 0.0), exposure_share)
            )
        else:
            underexposure = 1.0 if opportunity.get(skill_id, 0.0) > 0 else 0.0
            evidence = {
                "episodes": 0, "weighted_episodes": 0.0, "solved": 0, "failed_or_abandoned": 0,
                "avg_failed_before_ac": 0.0, "success_rate_shrunk": shrunk_success_rate(0, 0),
                "attempt_efficiency": 0.0, "rating_band": "unknown", "rating_coverage": 0.0,
                "recent_window_days": int(HALF_LIFE_ABILITY_DAYS), "taxonomy_quality": 0.0,
                "mean_recency_weight": 0.0, "context_breakdown": {}, "rating_bands": {},
                "exposure_share": 0.0, "opportunity_share": round(opportunity.get(skill_id, 0.0), 4),
            }
            scores.append({
                "skill_id": skill_id, "status": "underexposed", "confidence": 0.0,
                "severity": 0, "underexposure": underexposure,
                "estimated_skill_rating": None, "estimated_skill_rating_low": None,
                "estimated_skill_rating_high": None, "evidence": evidence,
                "warnings": ["no_episodes_for_skill"],
                "explanation": _explanation(skill_id, "underexposed", evidence, global_rating),
                "_contributions": [],
            })

    run = {
        "run_id": str(uuid.uuid4()),
        "handle": inputs["handle"],
        "analysis_version": ANALYSIS_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "problem_catalog_version": PROBLEM_CATALOG_VERSION,
        "data_cutoff_time": cutoff,
        "input_data_hash": _input_data_hash(inputs),
        "global_rating": global_rating,
        "global_rating_source": inputs["global_rating_source"],
        "episode_count": len(episodes),
        "created_at": store._now(),
    }
    _persist_run(run, scores, run_warnings)

    return _run_payload(run, scores, run_warnings)


def _persist_run(run: dict[str, Any], scores: list[dict[str, Any]], run_warnings: list[str]) -> None:
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO analysis_runs (run_id, handle, analysis_version, taxonomy_version, problem_catalog_version,"
            " data_cutoff_time, input_data_hash, global_rating, global_rating_source, episode_count, created_at)"
            " VALUES (:run_id, :handle, :analysis_version, :taxonomy_version, :problem_catalog_version,"
            " :data_cutoff_time, :input_data_hash, :global_rating, :global_rating_source, :episode_count, :created_at)",
            run,
        )
        for warning in run_warnings:
            conn.execute(
                "INSERT INTO analysis_warnings (run_id, skill_id, warning) VALUES (?, '*', ?)",
                (run["run_id"], warning),
            )
        for score in scores:
            conn.execute(
                "INSERT INTO analysis_skill_scores (run_id, skill_id, status, confidence, severity, underexposure,"
                " estimated_skill_rating, estimated_skill_rating_low, estimated_skill_rating_high, explanation)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run["run_id"], score["skill_id"], score["status"], score["confidence"], score["severity"],
                    score["underexposure"], score["estimated_skill_rating"], score["estimated_skill_rating_low"],
                    score["estimated_skill_rating_high"], score["explanation"],
                ),
            )
            conn.execute(
                "INSERT INTO analysis_skill_evidence (run_id, skill_id, evidence) VALUES (?, ?, ?)",
                (run["run_id"], score["skill_id"], json.dumps(score["evidence"], ensure_ascii=False)),
            )
            for warning in score["warnings"]:
                conn.execute(
                    "INSERT INTO analysis_warnings (run_id, skill_id, warning) VALUES (?, ?, ?)",
                    (run["run_id"], score["skill_id"], warning),
                )
            top = sorted(score["_contributions"], key=lambda c: -c["w"])[:20]
            for c in top:
                conn.execute(
                    "INSERT INTO analysis_problem_evidence (run_id, skill_id, episode_id, problem_id,"
                    " mapping_weight, recency_weight, final_status, problem_rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        run["run_id"], score["skill_id"], c["episode_id"], c["problem_id"],
                        c["mapping_weight"], round(c["recency"], 6), c["final_status"], c["problem_rating"],
                    ),
                )
            conn.execute(
                "INSERT INTO user_skill_history (handle, skill_id, run_id, status, severity, confidence,"
                " estimated_skill_rating, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run["handle"], score["skill_id"], run["run_id"], score["status"], score["severity"],
                    score["confidence"], score["estimated_skill_rating"], run["created_at"],
                ),
            )


def _run_payload(run: dict[str, Any], scores: list[dict[str, Any]], run_warnings: list[str]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "handle": run["handle"],
        "analysis_version": run["analysis_version"],
        "taxonomy_version": run["taxonomy_version"],
        "problem_catalog_version": run["problem_catalog_version"],
        "data_cutoff_time": run["data_cutoff_time"],
        "input_data_hash": run["input_data_hash"],
        "global_rating": run["global_rating"],
        "episode_count": run["episode_count"],
        "created_at": run["created_at"],
        "run_warnings": run_warnings,
        "skills": [{k: v for k, v in score.items() if not k.startswith("_")} for score in scores],
    }


def get_run(run_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        run = conn.execute("SELECT * FROM analysis_runs WHERE run_id = ?", (run_id,)).fetchone()
        if run is None:
            return None
        scores = conn.execute(
            "SELECT * FROM analysis_skill_scores WHERE run_id = ? ORDER BY skill_id", (run_id,)
        ).fetchall()
        evidence = {
            row["skill_id"]: json.loads(row["evidence"])
            for row in conn.execute("SELECT * FROM analysis_skill_evidence WHERE run_id = ?", (run_id,)).fetchall()
        }
        warnings_rows = conn.execute("SELECT * FROM analysis_warnings WHERE run_id = ?", (run_id,)).fetchall()
    skill_warnings: dict[str, list[str]] = {}
    run_warnings: list[str] = []
    for row in warnings_rows:
        if row["skill_id"] == "*":
            run_warnings.append(row["warning"])
        else:
            skill_warnings.setdefault(row["skill_id"], []).append(row["warning"])
    run_dict = dict(run)
    return {
        **{k: run_dict[k] for k in (
            "run_id", "handle", "analysis_version", "taxonomy_version", "problem_catalog_version",
            "data_cutoff_time", "input_data_hash", "global_rating", "episode_count", "created_at",
        )},
        "run_warnings": sorted(run_warnings),
        "skills": [
            {
                "skill_id": row["skill_id"],
                "status": row["status"],
                "confidence": row["confidence"],
                "severity": row["severity"],
                "underexposure": row["underexposure"],
                "estimated_skill_rating": row["estimated_skill_rating"],
                "estimated_skill_rating_low": row["estimated_skill_rating_low"],
                "estimated_skill_rating_high": row["estimated_skill_rating_high"],
                "evidence": evidence.get(row["skill_id"], {}),
                "warnings": sorted(skill_warnings.get(row["skill_id"], [])),
                "explanation": row["explanation"],
            }
            for row in scores
        ],
    }


def latest_run_id(handle: str) -> str | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT run_id FROM analysis_runs WHERE handle = ? ORDER BY created_at DESC, run_id DESC LIMIT 1",
            (store.canonical_handle(handle),),
        ).fetchone()
    return row["run_id"] if row else None
