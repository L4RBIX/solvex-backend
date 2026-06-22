from contestiq_core.diagnosis.weakness import build_weakness_snapshot
from contestiq_core.evidence.skill_evidence import build_skill_evidence
from contestiq_core.models import NormalizedProblem, UserProblemAttempt
from contestiq_core.recommendations.candidates import candidate_pool
from contestiq_core.recommendations.queue import build_daily_queue
from contestiq_core.recommendations.scoring import score_candidate
from contestiq_core.taxonomy.tag_mapping import map_cf_tags


def _attempt(problem_key, tags, verdicts, rating=1200, has_ac=False):
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


def _high_confidence_attempts():
    friction = [_attempt(f"dp{idx}", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1400) for idx in range(7)]
    baseline = [_attempt(f"gr{idx}", ["greedy"], ["OK"], 1100 + (idx % 3) * 100, has_ac=True) for idx in range(9)]
    return friction + baseline


def _problems():
    return [
        NormalizedProblem(problem_key="dp0", contest_id=1, index="A", name="Solved Or Attempted DP", rating=1200, tags=["dp"], solved_count=1000),
        NormalizedProblem(problem_key="10A", contest_id=10, index="A", name="Repair DP", rating=1200, tags=["dp"], solved_count=3000),
        NormalizedProblem(problem_key="11A", contest_id=11, index="A", name="Maintain Greedy", rating=1250, tags=["greedy"], solved_count=2500),
        NormalizedProblem(problem_key="12A", contest_id=12, index="A", name="Stretch Greedy", rating=1450, tags=["greedy"], solved_count=2000),
        NormalizedProblem(problem_key="13A", contest_id=13, index="A", name="Explore Geo", rating=1200, tags=["geometry"], solved_count=1500),
    ]


def test_solved_problems_are_excluded_from_recommendations():
    attempts = _high_confidence_attempts()
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(_problems(), attempts, scores, overall_rating=1200)
    solved = {attempt.problem_key for attempt in attempts if attempt.has_ac}
    assert solved.isdisjoint({item.problem_key for item in queue.items})


def test_previously_attempted_unsolved_problems_are_strongly_penalized():
    attempts = _high_confidence_attempts()
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    dp = next(score for score in scores if score.skill_id == "dynamic_programming")
    mapping = map_cf_tags(["dp"])[0]
    problem = NormalizedProblem(problem_key="x", name="X", rating=1200, tags=["dp"], solved_count=3000)
    fresh_score, fresh = score_candidate(problem, mapping, dp, "repair", 1200, previously_attempted=False)
    attempted_score, attempted = score_candidate(problem, mapping, dp, "repair", 1200, previously_attempted=True)
    assert attempted["RecentRepeatPenalty"] == 1.0
    assert attempted_score <= fresh_score - 0.07


def test_repair_slot_cannot_use_low_confidence_weakness():
    attempts = [_attempt(f"dp{idx}", ["dp"], ["WRONG_ANSWER", "WRONG_ANSWER"], 1200) for idx in range(3)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    candidates = candidate_pool(_problems(), attempts, scores, "repair", overall_rating=1200)
    assert candidates == []


def test_exploration_slot_is_used_for_underexposed_skills():
    attempts = [_attempt("geo1", ["geometry"], ["WRONG_ANSWER"], 1200)]
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(_problems(), attempts, scores, overall_rating=1200)
    assert any(item.slot_type == "exploration" for item in queue.items)
    assert all(
        item.exploration_due_to_limited_evidence
        for item in queue.items
        if item.slot_type == "exploration"
    )


def test_daily_queue_debug_fields_and_slots_when_repair_is_supported():
    attempts = _high_confidence_attempts()
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(_problems(), attempts, scores, overall_rating=1200)
    slots = [item.slot_type for item in queue.items]
    assert "repair" in slots
    assert "stretch" in slots
    assert any(slot in {"maintenance", "exploration"} for slot in slots)
    assert all(item.anchor_skill == item.target_skill for item in queue.items)
    assert all(item.why_selected and item.why_safe_to_recommend for item in queue.items)
    repair = next(item for item in queue.items if item.slot_type == "repair")
    assert repair.repair_confidence_eligible
    assert queue.queue_mode == "standard"


def test_hard_repair_takes_priority_over_focused_practice():
    attempts = _high_confidence_attempts()
    _, scores = build_weakness_snapshot(build_skill_evidence(attempts, now=1700000100))
    queue = build_daily_queue(_problems(), attempts, scores, overall_rating=1200)
    assert queue.items[0].slot_type == "repair"
    assert queue.queue_mode == "standard"
