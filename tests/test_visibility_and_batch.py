import json
from pathlib import Path

from contestiq_core.diagnosis.weakness import build_weakness_snapshot
from contestiq_core.evidence.skill_evidence import build_skill_evidence
from contestiq_core.models import NormalizedProblem, UserProblemAttempt
from contestiq_core.pipeline.analyze_handle import build_user_weakness_map
from contestiq_core.pipeline.batch_evaluate import batch_evaluate
from contestiq_core.recommendations.queue import build_daily_queue


def _attempt(problem_key, tags, verdicts=None, rating=1200, has_ac=False):
    verdicts = verdicts or ["WRONG_ANSWER"]
    return UserProblemAttempt(
        problem_key=problem_key,
        problem_name=problem_key,
        attempt_count=len(verdicts),
        has_ac=has_ac,
        verdict_sequence=verdicts,
        attempts_before_ac=(len(verdicts) - 1 if has_ac else None),
        first_submission_time=1700000000,
        first_ac_time=(1700000000 if has_ac else None),
        last_submission_time=1700000000,
        problem_rating=rating,
        problem_tags=tags,
    )


def test_user_facing_limited_evidence_list_is_capped():
    attempts = [
        _attempt("g1", ["geometry"]),
        _attempt("s1", ["strings"]),
        _attempt("t1", ["trees"]),
        _attempt("m1", ["math"]),
        _attempt("ds1", ["data structures"]),
        _attempt("bf1", ["brute force"]),
        _attempt("h1", ["hashing"]),
    ]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    user_map = build_user_weakness_map(scores)
    assert len(user_map["limited_evidence"]) <= 5


def test_sparse_technique_overlays_hidden_from_user_limited_evidence():
    attempts = [_attempt("h1", ["hashing"])]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    hashing = next(score for score in scores if score.skill_id == "hashing")
    assert hashing.public_bucket == "Limited Evidence"
    assert not hashing.user_visible
    assert "Technique overlay" in hashing.visibility_reason


def test_queue_mode_low_evidence_exploration_when_repair_unsafe():
    attempts = [_attempt("geo1", ["geometry"])]
    problems = [
        NormalizedProblem(problem_key="p1", name="Geo", rating=1200, tags=["geometry"], solved_count=1000),
        NormalizedProblem(problem_key="p2", name="Binary", rating=1200, tags=["binary search"], solved_count=1000),
    ]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(problems, attempts, scores, overall_rating=1200)
    assert queue.queue_mode in {"calibration", "low_evidence_exploration"}
    assert queue.queue_mode != "standard"


def test_queue_mode_not_standard_without_repair_safe_skills():
    attempts = [_attempt(f"dp{i}", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1200) for i in range(3)]
    problems = [NormalizedProblem(problem_key="p1", name="DP", rating=1200, tags=["dp"], solved_count=1000)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(problems, attempts, scores, overall_rating=1200)
    assert all(item.slot_type != "repair" for item in queue.items)
    assert queue.queue_mode != "standard"


def test_queue_mode_not_low_evidence_when_sufficient_history_and_zero_limited_evidence():
    attempts = [
        _attempt(f"g{i}", ["greedy"], ["OK"], 1200 + (i % 3) * 100, has_ac=True)
        for i in range(35)
    ]
    problems = [
        NormalizedProblem(problem_key="m1", name="Maintain", rating=1250, tags=["greedy"], solved_count=2000),
        NormalizedProblem(problem_key="s1", name="Stretch", rating=1400, tags=["greedy"], solved_count=1500),
    ]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(problems, attempts, scores, overall_rating=1200)
    assert queue.has_sufficient_history
    assert queue.visible_limited_evidence_count == 0
    assert queue.queue_mode != "low_evidence_exploration"


def test_zero_repair_items_alone_does_not_imply_low_evidence_exploration():
    attempts = [
        _attempt(f"g{i}", ["greedy"], ["OK"], 1200, has_ac=True)
        for i in range(30)
    ]
    problems = [NormalizedProblem(problem_key="m1", name="Maintain", rating=1200, tags=["greedy"], solved_count=2000)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(problems, attempts, scores, overall_rating=1200)
    assert queue.repair_candidate_count == 0
    assert queue.queue_mode in {"maintenance_stretch", "no_repair_needed"}


def test_sufficient_history_no_repair_safe_skill_gets_maintenance_stretch_mode():
    attempts = [
        _attempt(f"g{i}", ["greedy"], ["OK"], 1200, has_ac=True)
        for i in range(40)
    ]
    problems = [
        NormalizedProblem(problem_key="m1", name="Maintain", rating=1200, tags=["greedy"], solved_count=2000),
        NormalizedProblem(problem_key="s1", name="Stretch", rating=1400, tags=["greedy"], solved_count=1500),
    ]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(problems, attempts, scores, overall_rating=1200)
    assert queue.has_sufficient_history
    assert queue.repair_candidate_count == 0
    assert queue.queue_mode == "maintenance_stretch"


def test_batch_evaluation_handles_errors_and_creates_summaries(tmp_path, monkeypatch):
    handles = tmp_path / "handles.txt"
    handles.write_text("ok\nbad\n", encoding="utf-8")
    out_dir = tmp_path / "eval"

    def fake_analyze(handle, offline_sample=False, debug=False, max_submissions=None):
        if handle == "bad":
            raise RuntimeError("forced failure")
        return {
            "profile_summary": {
                "handle": handle,
                "overall_rating_prior": 1200,
                "normalized_submissions": 1,
                "user_problem_attempts": 1,
                "solved_problem_attempts": 0,
            },
            "weakness_map_user": {"likely_needs_work": [], "watchlist": [], "limited_evidence": []},
            "daily_queue": {"queue_mode": "calibration", "mode": "calibration", "items": []},
            "warnings": [],
        }

    monkeypatch.setattr("contestiq_core.pipeline.batch_evaluate.analyze_handle", fake_analyze)
    batch_evaluate(handles, out_dir, debug=True)
    assert (out_dir / "eval_summary.json").exists()
    assert (out_dir / "eval_summary.md").exists()
    summary = json.loads((out_dir / "eval_summary.json").read_text(encoding="utf-8"))
    assert len(summary["handles"]) == 2
    bad = next(row for row in summary["handles"] if row["handle"] == "bad")
    assert bad["pipeline_error"] == "forced failure"
    assert (out_dir / "ok_output.json").exists()
    assert (out_dir / "bad_debug.json").exists()
    assert "Top 5 repair blocking reasons" in (out_dir / "eval_summary.md").read_text(encoding="utf-8")


def test_queue_items_include_mapping_debug():
    attempts = [_attempt(f"g{i}", ["greedy"], ["OK"], 1200, has_ac=True) for i in range(30)]
    problems = [NormalizedProblem(problem_key="m1", name="Maintain", rating=1200, tags=["greedy", "math"], solved_count=2000)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(problems, attempts, scores, overall_rating=1200)
    assert queue.items
    item = queue.items[0]
    assert item.original_codeforces_tags == ["greedy", "math"]
    assert item.mapped_skill_candidates
    assert item.mapping_shares
    assert item.tag_reliabilities
    assert item.why_anchor_skill_was_chosen


def test_repair_blocking_reasons_populated_when_not_eligible():
    attempts = [_attempt("geo1", ["geometry"])]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    geometry = next(score for score in scores if score.skill_id == "geometry")
    assert not geometry.repair_eligible
    assert geometry.repair_blocking_reasons


def test_underexposed_skill_cannot_become_focused_practice():
    attempts = [_attempt("geo1", ["geometry"])]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    geometry = next(score for score in scores if score.skill_id == "geometry")
    assert not geometry.focused_practice_eligible
    assert geometry.focused_practice_blocking_reasons


def test_noisy_overlay_cannot_become_focused_practice():
    attempts = [_attempt(f"hash{i}", ["hashing"], ["WRONG_ANSWER", "OK"], 1200) for i in range(8)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    hashing = next(score for score in scores if score.skill_id == "hashing")
    assert not hashing.focused_practice_eligible
    assert "focused practice is limited to domain skills in v1" in hashing.focused_practice_blocking_reasons
