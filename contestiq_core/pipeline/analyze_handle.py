from __future__ import annotations

import argparse
import json
from pathlib import Path

from contestiq_core.codeforces.client import CodeforcesAPIError, fetch_problemset_problems, fetch_user_rating, fetch_user_status
from contestiq_core.codeforces.normalizer import normalize_problemset, normalize_submissions, rollup_user_problem_attempts
from contestiq_core.config import DEFAULT_OVERALL_RATING
from contestiq_core.diagnosis.explanations import caveats
from contestiq_core.diagnosis.weakness import build_weakness_snapshot
from contestiq_core.evidence.skill_evidence import build_skill_evidence
from contestiq_core.models import NormalizedProblem, NormalizedSubmission
from contestiq_core.recommendations.queue import build_daily_queue
from contestiq_core.storage.json_store import write_json
from contestiq_core.taxonomy.skills import all_skills


def _overall_rating(rating_rows: list[dict]) -> int:
    return rating_rows[-1]["newRating"] if rating_rows else DEFAULT_OVERALL_RATING


def _offline_problemset() -> list[NormalizedProblem]:
    return [
        NormalizedProblem(problem_key="100A", contest_id=100, index="A", name="Repair DP Drill", rating=1200, tags=["dp"], solved_count=4300),
        NormalizedProblem(problem_key="101B", contest_id=101, index="B", name="Binary Search Practice", rating=1300, tags=["binary search"], solved_count=3900),
        NormalizedProblem(problem_key="102C", contest_id=102, index="C", name="Stretch Graph Paths", rating=1500, tags=["shortest paths", "graphs"], solved_count=2100),
        NormalizedProblem(problem_key="103D", contest_id=103, index="D", name="Geometry Sampler", rating=1250, tags=["geometry"], solved_count=1600),
    ]


def _offline_submissions(handle: str) -> list[NormalizedSubmission]:
    raw = [
        {"id": 1, "creationTimeSeconds": 1700000000, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "WRONG_ANSWER", "problem": {"contestId": 1, "index": "A", "name": "Old DP", "rating": 1200, "tags": ["dp"]}},
        {"id": 2, "creationTimeSeconds": 1700000100, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "WRONG_ANSWER", "problem": {"contestId": 1, "index": "A", "name": "Old DP", "rating": 1200, "tags": ["dp"]}},
        {"id": 3, "creationTimeSeconds": 1700000200, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "TIME_LIMIT_EXCEEDED", "problem": {"contestId": 2, "index": "B", "name": "Knapsack Variant", "rating": 1300, "tags": ["dp"]}},
        {"id": 4, "creationTimeSeconds": 1700000300, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "WRONG_ANSWER", "problem": {"contestId": 2, "index": "B", "name": "Knapsack Variant", "rating": 1300, "tags": ["dp"]}},
        {"id": 5, "creationTimeSeconds": 1700000400, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "WRONG_ANSWER", "problem": {"contestId": 3, "index": "C", "name": "Transitions", "rating": 1400, "tags": ["dp"]}},
        {"id": 6, "creationTimeSeconds": 1700000500, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "WRONG_ANSWER", "problem": {"contestId": 3, "index": "C", "name": "Transitions", "rating": 1400, "tags": ["dp"]}},
        {"id": 7, "creationTimeSeconds": 1700000600, "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"}, "programmingLanguage": "GNU C++17", "verdict": "OK", "problem": {"contestId": 4, "index": "D", "name": "Greedy OK", "rating": 1100, "tags": ["greedy"]}},
    ]
    return normalize_submissions(raw)


def _compact_skill(row) -> dict:
    return {
        "skill_id": row.skill_id,
        "display_name": row.display_name,
        "bucket": row.user_visible_bucket,
        "severity_score": row.severity_score,
        "confidence_score": row.confidence_score,
        "confidence_band": row.confidence_band,
        "explanation": row.explanation,
        "visibility_reason": row.visibility_reason,
    }


def build_user_weakness_map(skill_scores) -> dict:
    return {
        "likely_needs_work": [_compact_skill(row) for row in skill_scores if row.user_visible and row.user_visible_bucket == "Likely Needs Work"],
        "watchlist": [_compact_skill(row) for row in skill_scores if row.user_visible and row.user_visible_bucket == "Watchlist"],
        "limited_evidence": [_compact_skill(row) for row in skill_scores if row.user_visible and row.user_visible_bucket == "Limited Evidence"],
    }


def overlay_watchlist_debug(skill_scores) -> list[dict]:
    skills = all_skills()
    rows = []
    for score in skill_scores:
        skill = skills[score.skill_id]
        if skill.kind != "technique" or score.public_bucket != "Watchlist":
            continue
        rows.append(
            {
                "skill_id": score.skill_id,
                "display_name": score.display_name,
                "user_visible": score.user_visible,
                "priority_score": score.priority_score,
                "n_eff": score.n_eff,
                "distinct_problem_count": score.distinct_problem_count,
                "avg_tag_reliability": score.avg_tag_reliability,
                "overlay_visibility_reason": score.visibility_reason,
                "suggested_visibility_change": (
                    "review for domain-backed wording before public display"
                    if score.user_visible
                    else "keep internal unless manual review finds the overlay explanation useful"
                ),
            }
        )
    return rows


def analyze_handle(handle: str, offline_sample: bool = False, debug: bool = False, max_submissions: int | None = None) -> dict:
    warnings = caveats()
    try:
        if offline_sample:
            raise CodeforcesAPIError("offline sample requested")
        raw_submissions = fetch_user_status(handle, count=max_submissions)
        if max_submissions is not None:
            warnings.append(f"Live Codeforces submission history was capped at the most recent {max_submissions} submissions for evaluation runtime.")
        raw_rating = fetch_user_rating(handle)
        raw_problemset = fetch_problemset_problems()
        submissions = normalize_submissions(raw_submissions)
        problems = normalize_problemset(raw_problemset)
    except CodeforcesAPIError as exc:
        if not offline_sample:
            raise
        warnings.append(f"Used offline sample data because offline sample mode was requested: {exc}")
        raw_rating = []
        submissions = _offline_submissions(handle)
        problems = _offline_problemset()

    overall_rating = _overall_rating(raw_rating)
    attempts = rollup_user_problem_attempts(submissions)
    evidence = build_skill_evidence(attempts, overall_rating=overall_rating)
    weakness_map, skill_scores = build_weakness_snapshot(evidence)
    queue = build_daily_queue(problems, attempts, skill_scores, overall_rating=overall_rating)
    solved = sum(1 for attempt in attempts if attempt.has_ac)

    output = {
        "profile_summary": {
            "handle": handle,
            "overall_rating_prior": overall_rating,
            "normalized_submissions": len(submissions),
            "user_problem_attempts": len(attempts),
            "solved_problem_attempts": solved,
        },
        "data_quality_summary": {
            "source": "Codeforces public API" if not offline_sample else "offline sample",
            "process_data_available": False,
            "sample_size": len(attempts),
        },
        "normalized_history": {
            "submissions": [row.model_dump() for row in submissions[:250]],
            "attempts": [row.model_dump() for row in attempts[:250]],
        },
        "skill_evidence": [row.model_dump() for row in evidence],
        "weakness_map": weakness_map.model_dump(),
        "weakness_map_user": build_user_weakness_map(skill_scores),
        "skill_scores": [row.model_dump() for row in skill_scores],
        "daily_queue": queue.model_dump(),
        "explanations": {
            "safe_wording_policy": "Weakness means current friction evidence, not a trait statement.",
            "caveats": caveats(),
        },
        "warnings": warnings,
    }
    if debug:
        output["debug"] = {
            "skill_diagnostics": [
                {
                    "skill_id": row.skill_id,
                    "severity_score": row.severity_score,
                    "confidence_score": row.confidence_score,
                    "confidence_band": row.confidence_band,
                    "evidence_status": row.evidence_status,
                    "n_eff": row.n_eff,
                    "distinct_problem_count": row.distinct_problem_count,
                    "rating_bucket_count": row.rating_bucket_count,
                    "avg_tag_reliability": row.avg_tag_reliability,
                    "recency_factor": row.recency_factor,
                    "skill_success_rate": row.skill_success_rate,
                    "user_baseline_success_rate": row.user_baseline_success_rate,
                    "success_gap": row.success_gap,
                    "attempts_friction": row.attempts_friction,
                    "repeated_failure": row.repeated_failure,
                    "verdict_friction": row.verdict_friction,
                    "ceiling_gap": row.ceiling_gap,
                    "recent_decline": row.recent_decline,
                    "public_bucket": row.public_bucket,
                    "suppression_reasons": row.suppression_reasons,
                    "repair_eligible": row.repair_eligible,
                    "repair_blocking_reasons": row.repair_blocking_reasons,
                    "meets_confidence_threshold": row.meets_confidence_threshold,
                    "meets_n_eff_threshold": row.meets_n_eff_threshold,
                    "meets_distinct_problem_threshold": row.meets_distinct_problem_threshold,
                    "is_underexposed": row.is_underexposed,
                    "severity_above_repair_threshold": row.severity_above_repair_threshold,
                    "public_bucket_reason": row.public_bucket_reason,
                    "priority_score": row.priority_score,
                    "effective_repair_score": row.effective_repair_score,
                    "focused_practice_eligible": row.focused_practice_eligible,
                    "focused_practice_blocking_reasons": row.focused_practice_blocking_reasons,
                }
                for row in skill_scores
            ],
            "recommendation_debug": [
                {
                    "problem_key": item.problem_key,
                    "anchor_skill": item.anchor_skill,
                    "slot_type": item.slot_type,
                    "final_score": item.final_score,
                    "score_components": item.score_components,
                    "why_selected": item.why_selected,
                    "why_safe_to_recommend": item.why_safe_to_recommend,
                    "repair_confidence_eligible": item.repair_confidence_eligible,
                    "exploration_due_to_limited_evidence": item.exploration_due_to_limited_evidence,
                    "original_codeforces_tags": item.original_codeforces_tags,
                    "mapped_skill_candidates": item.mapped_skill_candidates,
                    "mapping_shares": item.mapping_shares,
                    "tag_reliabilities": item.tag_reliabilities,
                    "why_anchor_skill_was_chosen": item.why_anchor_skill_was_chosen,
                    "alternative_anchor_skills": item.alternative_anchor_skills,
                    "whether_anchor_is_domain_or_overlay": item.whether_anchor_is_domain_or_overlay,
                    "anchor_visibility_level": item.anchor_visibility_level,
                }
                for item in queue.items
            ],
            "public_overlay_watchlist_items": overlay_watchlist_debug(skill_scores),
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--offline-sample", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--max-submissions", type=int, default=None)
    args = parser.parse_args()
    output = analyze_handle(args.handle, offline_sample=args.offline_sample, debug=args.debug, max_submissions=args.max_submissions)
    write_json(args.out, output)
    print(json.dumps({"handle": args.handle, "out": str(Path(args.out).resolve()), "queue_items": len(output["daily_queue"]["items"])}, indent=2))


if __name__ == "__main__":
    main()
