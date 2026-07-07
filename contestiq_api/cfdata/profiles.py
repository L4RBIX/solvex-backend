"""User skill profiles, problem quality scoring, and feedback effects (Phase 05).

Profiles are derived from the latest immutable analysis run plus episode
recency data; feedback mutates only the fields designed for it
(frustration_score, preference_bias) and the per-problem quality stats.

Problem quality:
    Q(p) = 0.30*mapping_confidence + 0.25*feedback_wilson
         + 0.20*solved_count_stability + 0.15*manual_curation
         + 0.10*has_official_rating
    feedback_wilson uses the Wilson lower bound; neutral prior 0.5 with no feedback.
"""

from __future__ import annotations

import json
import math
import uuid
from typing import Any

from contestiq_api.cfdata import store, weakness
from contestiq_api.versions import TAXONOMY_VERSION

DAY_SECONDS = 86400

FEEDBACK_TYPES = {
    "too_easy",
    "too_hard",
    "already_seen",
    "bad_problem",
    "good_problem",
    "solved_independently",
    "solved_with_editorial_self_reported",
    "skipped",
    "abandoned",
}

POSITIVE_FEEDBACK = {"good_problem", "solved_independently"}
NEGATIVE_FEEDBACK = {"bad_problem"}
# Feedback that removes the specific problem from this user's future queues.
SUPPRESSING_FEEDBACK = {"bad_problem", "already_seen", "too_easy"}

REVIEW_INTERVAL_DAYS = {
    "strength": 30,
    "likely_strength": 21,
    "maintenance_needed": 21,
    "historical_weakness_recent_improvement": 10,
    "likely_weakness": 7,
    "possible_weakness": 7,
    "calibration_needed": 14,
    "underexposed": 14,
    "insufficient_evidence": 14,
}


def wilson_lower_bound(positive: int, total: int, z: float = 1.96) -> float:
    if total == 0:
        return 0.5  # neutral prior
    phat = positive / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def build_profiles(handle: str) -> dict[str, Any]:
    """(Re)build user_skill_profiles from the latest analysis run. Idempotent.

    Feedback-owned fields (frustration_score, preference_bias, suppression_until)
    are preserved across rebuilds.
    """
    canonical = store.canonical_handle(handle)
    run_id = weakness.latest_run_id(canonical)
    if run_id is None:
        return {"handle": canonical, "profiles": 0, "analysis_run_id": None}
    run = weakness.get_run(run_id)
    assert run is not None

    with store.connect() as conn:
        episodes = [dict(row) for row in conn.execute(
            "SELECT * FROM problem_episodes WHERE handle = ?", (canonical,)
        ).fetchall()]
        mappings = [dict(row) for row in conn.execute(
            "SELECT problem_id, skill_id, weight FROM problem_skill_map WHERE taxonomy_version = ?",
            (TAXONOMY_VERSION,),
        ).fetchall()]
        existing = {
            row["skill_id"]: dict(row)
            for row in conn.execute("SELECT * FROM user_skill_profiles WHERE handle = ?", (canonical,)).fetchall()
        }

    skills_by_problem: dict[str, list[dict[str, Any]]] = {}
    for row in mappings:
        skills_by_problem.setdefault(row["problem_id"], []).append(row)

    cutoff = run["data_cutoff_time"] or 0
    per_skill: dict[str, dict[str, Any]] = {}
    for ep in episodes:
        for m in skills_by_problem.get(ep["problem_id"], []):
            agg = per_skill.setdefault(m["skill_id"], {
                "delayed": 0, "recent_failures": 0, "last_practiced": None,
            })
            if ep["final_status"] == "delayed_ac":
                agg["delayed"] += 1
            age_days = (cutoff - (ep["last_submission_at"] or cutoff)) / DAY_SECONDS
            if not ep["eventual_ac"] and age_days <= 28:
                agg["recent_failures"] += 1
            last = ep["last_submission_at"]
            if last is not None and (agg["last_practiced"] is None or last > agg["last_practiced"]):
                agg["last_practiced"] = last

    now = store._now()
    with store.connect() as conn:
        for skill in run["skills"]:
            skill_id = skill["skill_id"]
            agg = per_skill.get(skill_id, {"delayed": 0, "recent_failures": 0, "last_practiced": None})
            uncertainty = None
            if skill["estimated_skill_rating_high"] is not None and skill["estimated_skill_rating_low"] is not None:
                uncertainty = (skill["estimated_skill_rating_high"] - skill["estimated_skill_rating_low"]) / 2
            interval_days = REVIEW_INTERVAL_DAYS.get(skill["status"], 14)
            review_due = (
                agg["last_practiced"] + interval_days * DAY_SECONDS if agg["last_practiced"] is not None else None
            )
            prev = existing.get(skill_id, {})
            conn.execute(
                """
                INSERT INTO user_skill_profiles (
                    handle, skill_id, analysis_run_id, global_rating_anchor, skill_rating_raw,
                    skill_rating_shrunk, uncertainty, status, severity, confidence, effective_exposure,
                    attempts, independent_solves, delayed_ac_count, recent_failures_28d,
                    last_practiced_at, review_due_at, frustration_score, preference_bias,
                    suppression_until, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(handle, skill_id) DO UPDATE SET
                    analysis_run_id=excluded.analysis_run_id,
                    global_rating_anchor=excluded.global_rating_anchor,
                    skill_rating_raw=excluded.skill_rating_raw,
                    skill_rating_shrunk=excluded.skill_rating_shrunk,
                    uncertainty=excluded.uncertainty,
                    status=excluded.status,
                    severity=excluded.severity,
                    confidence=excluded.confidence,
                    effective_exposure=excluded.effective_exposure,
                    attempts=excluded.attempts,
                    independent_solves=excluded.independent_solves,
                    delayed_ac_count=excluded.delayed_ac_count,
                    recent_failures_28d=excluded.recent_failures_28d,
                    last_practiced_at=excluded.last_practiced_at,
                    review_due_at=excluded.review_due_at,
                    updated_at=excluded.updated_at
                """,
                (
                    canonical, skill_id, run["run_id"], run["global_rating"],
                    skill["estimated_skill_rating"], skill["estimated_skill_rating"], uncertainty,
                    skill["status"], skill["severity"], skill["confidence"],
                    skill["evidence"].get("weighted_episodes", 0.0),
                    skill["evidence"].get("episodes", 0),
                    skill["evidence"].get("solved", 0),
                    agg["delayed"], agg["recent_failures"],
                    agg["last_practiced"], review_due,
                    prev.get("frustration_score", 0.0), prev.get("preference_bias", 0.0),
                    prev.get("suppression_until"), now,
                ),
            )
    return {"handle": canonical, "profiles": len(run["skills"]), "analysis_run_id": run["run_id"]}


def get_profiles(handle: str) -> dict[str, dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM user_skill_profiles WHERE handle = ?", (store.canonical_handle(handle),)
        ).fetchall()
    return {row["skill_id"]: dict(row) for row in rows}


# ─── Problem quality ─────────────────────────────────────────────────────────


def _solved_count_stability(solved_count: int | None) -> float:
    if not solved_count or solved_count <= 0:
        return 0.0
    return min(1.0, math.log10(solved_count + 1) / 5.0)


def quality_scores(problem_ids: list[str]) -> dict[str, float]:
    """Q(p) for a batch of problems."""
    if not problem_ids:
        return {}
    placeholders = ", ".join("?" for _ in problem_ids)
    with store.connect() as conn:
        confidence = {
            row["problem_id"]: row["c"]
            for row in conn.execute(
                f"SELECT problem_id, MAX(confidence) AS c FROM problem_skill_map"
                f" WHERE taxonomy_version = ? AND problem_id IN ({placeholders}) GROUP BY problem_id",
                [TAXONOMY_VERSION, *problem_ids],
            ).fetchall()
        }
        stats = {
            row["problem_key"]: row["solved_count"]
            for row in conn.execute(
                f"SELECT problem_key, solved_count FROM problem_statistics WHERE problem_key IN ({placeholders})",
                problem_ids,
            ).fetchall()
        }
        quality_rows = {
            row["problem_id"]: dict(row)
            for row in conn.execute(
                f"SELECT * FROM problem_quality_stats WHERE problem_id IN ({placeholders})", problem_ids
            ).fetchall()
        }
        rated = {
            row["problem_key"]: row["rating"] is not None
            for row in conn.execute(
                f"SELECT problem_key, rating FROM problems WHERE problem_key IN ({placeholders})", problem_ids
            ).fetchall()
        }

    scores: dict[str, float] = {}
    for pid in problem_ids:
        q = quality_rows.get(pid)
        wilson = q["feedback_wilson"] if q and q["feedback_wilson"] is not None else 0.5
        curation = q["manual_curation"] if q else 0.5
        scores[pid] = round(
            0.30 * confidence.get(pid, 0.0)
            + 0.25 * wilson
            + 0.20 * _solved_count_stability(stats.get(pid))
            + 0.15 * curation
            + 0.10 * (1.0 if rated.get(pid) else 0.0),
            4,
        )
    return scores


# ─── Feedback ────────────────────────────────────────────────────────────────


def record_feedback(item_id: str, feedback_type: str, comment: str | None = None) -> dict[str, Any]:
    """Store feedback for a queue or plan item and apply its effects."""
    if feedback_type not in FEEDBACK_TYPES:
        raise ValueError(f"Unknown feedback type: {feedback_type}")

    with store.connect() as conn:
        item = conn.execute(
            "SELECT ri.item_id, ri.problem_id, ri.skill_id, rr.handle FROM recommendation_items ri"
            " JOIN recommendation_runs rr ON rr.run_id = ri.run_id WHERE ri.item_id = ?",
            (item_id,),
        ).fetchone()
        if item is None:
            item = conn.execute(
                "SELECT tpi.item_id, tpi.problem_id, tpi.skill_id, tp.handle FROM training_plan_items tpi"
                " JOIN training_plans tp ON tp.plan_id = tpi.plan_id WHERE tpi.item_id = ?",
                (item_id,),
            ).fetchone()
        if item is None:
            return {"status": "item_not_found"}
        item = dict(item)

        feedback_id = str(uuid.uuid4())
        now = store._now()
        conn.execute(
            "INSERT INTO recommendation_feedback (feedback_id, item_id, handle, problem_id, feedback_type, comment, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (feedback_id, item_id, item["handle"], item["problem_id"], feedback_type, comment, now),
        )

        item_status = {
            "solved_independently": "solved",
            "solved_with_editorial_self_reported": "solved_with_editorial_self_reported",
            "skipped": "skipped",
            "abandoned": "abandoned",
        }.get(feedback_type, "feedback_received")
        conn.execute("UPDATE recommendation_items SET item_status = ? WHERE item_id = ?", (item_status, item_id))
        conn.execute("UPDATE training_plan_items SET item_status = ? WHERE item_id = ?", (item_status, item_id))

        # Problem-level quality stats.
        if feedback_type in POSITIVE_FEEDBACK or feedback_type in NEGATIVE_FEEDBACK:
            positive = 1 if feedback_type in POSITIVE_FEEDBACK else 0
            conn.execute(
                "INSERT INTO problem_quality_stats (problem_id, feedback_positive, feedback_negative, updated_at)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(problem_id) DO UPDATE SET"
                " feedback_positive = feedback_positive + excluded.feedback_positive,"
                " feedback_negative = feedback_negative + excluded.feedback_negative,"
                " updated_at = excluded.updated_at",
                (item["problem_id"], positive, 1 - positive, now),
            )
            row = conn.execute(
                "SELECT feedback_positive, feedback_negative FROM problem_quality_stats WHERE problem_id = ?",
                (item["problem_id"],),
            ).fetchone()
            wilson = wilson_lower_bound(row["feedback_positive"], row["feedback_positive"] + row["feedback_negative"])
            conn.execute(
                "UPDATE problem_quality_stats SET feedback_wilson = ? WHERE problem_id = ?",
                (round(wilson, 4), item["problem_id"]),
            )

        # Skill-level effects.
        if feedback_type in ("too_hard", "abandoned"):
            delta = 0.25 if feedback_type == "too_hard" else 0.15
            conn.execute(
                "UPDATE user_skill_profiles SET frustration_score = MIN(1.0, frustration_score + ?), updated_at = ?"
                " WHERE handle = ? AND skill_id = ?",
                (delta, now, item["handle"], item["skill_id"]),
            )
        elif feedback_type == "too_easy":
            conn.execute(
                "UPDATE user_skill_profiles SET preference_bias = MIN(1.0, preference_bias + 0.2), updated_at = ?"
                " WHERE handle = ? AND skill_id = ?",
                (now, item["handle"], item["skill_id"]),
            )
        elif feedback_type == "solved_independently":
            conn.execute(
                "UPDATE user_skill_profiles SET frustration_score = MAX(0.0, frustration_score - 0.1), updated_at = ?"
                " WHERE handle = ? AND skill_id = ?",
                (now, item["handle"], item["skill_id"]),
            )

    return {
        "status": "saved",
        "feedback_id": feedback_id,
        "item_id": item_id,
        "problem_id": item["problem_id"],
        "feedback_type": feedback_type,
    }


def suppressed_problems(handle: str) -> set[str]:
    """Problems this user's feedback removed from future recommendations."""
    placeholders = ", ".join("?" for _ in SUPPRESSING_FEEDBACK)
    with store.connect() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT problem_id FROM recommendation_feedback"
            f" WHERE handle = ? AND feedback_type IN ({placeholders})",
            [store.canonical_handle(handle), *sorted(SUPPRESSING_FEEDBACK)],
        ).fetchall()
    return {row["problem_id"] for row in rows}
