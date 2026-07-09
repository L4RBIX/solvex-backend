"""Recommendation engine and planner tests (Phase 05) — deterministic, no live CF."""

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import episodes, planner, profiles, store, taxonomy, weakness


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)


NOW = 1700000000
DAY = 86400
HANDLE = "Plan-User"
QUEUE_DATE = "2026-07-06"


def submission(sid, contest_id, index, verdict, *, days_ago, rating, tags):
    return {
        "id": sid,
        "contestId": contest_id,
        "creationTimeSeconds": NOW - days_ago * DAY,
        "problem": {"contestId": contest_id, "index": index, "name": f"P{contest_id}{index}",
                    **({"rating": rating} if rating is not None else {}), "tags": list(tags)},
        "author": {"members": [{"handle": HANDLE}], "participantType": "PRACTICE"},
        "programmingLanguage": "GNU C++17",
        "verdict": verdict,
        "passedTestCount": 5, "timeConsumedMillis": 100, "memoryConsumedBytes": 1024,
    }


def failed_episode(sid_base, contest_id, *, days_ago, tags, rating=1500, fails=3):
    return [submission(sid_base + i, contest_id, "A", "WRONG_ANSWER", days_ago=days_ago, rating=rating, tags=tags)
            for i in range(fails)]


def solved_episode(sid_base, contest_id, *, days_ago, tags, rating=1500, fails=0):
    subs = [submission(sid_base + i, contest_id, "A", "WRONG_ANSWER", days_ago=days_ago, rating=rating, tags=tags)
            for i in range(fails)]
    subs.append(submission(sid_base + fails, contest_id, "A", "OK", days_ago=days_ago, rating=rating, tags=tags))
    return subs


def catalog(tag, contest_base, count=14, rating_base=1150, rating_step=50, shared_contests=False):
    problems = []
    for i in range(count):
        cid = contest_base + (i // 2 if shared_contests else i)
        problems.append({
            "contestId": cid, "index": chr(ord("B") + (i % 2 if shared_contests else 0)),
            "name": f"{tag} drill {i}", "rating": rating_base + i * rating_step, "tags": [tag],
        })
    return problems


def build_world(submissions, extra_catalog, user_rating=1500):
    store.upsert_user({"handle": HANDLE, "rating": user_rating})
    store.upsert_submissions(HANDLE, submissions)
    problems = {}
    for sub in submissions:
        p = sub["problem"]
        problems[f"{p['contestId']}{p['index']}"] = {
            "contestId": p["contestId"], "index": p["index"], "name": p["name"],
            **({"rating": p["rating"]} if p.get("rating") is not None else {}), "tags": p["tags"],
        }
    for p in extra_catalog:
        problems[f"{p['contestId']}{p['index']}"] = p
    store.save_problemset_snapshot({"problems": list(problems.values()), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    episodes.rebuild_episodes(HANDLE)
    weakness.analyze_handle_weakness(HANDLE)
    profiles.build_profiles(HANDLE)


def default_world(recent_failures=False):
    """Weak shortest-paths + dp, strong greedy, underexposed geometry."""
    fail_days = 3 if recent_failures else 35
    subs = []
    for i in range(10):  # graphs.shortest_paths likely weakness
        subs += failed_episode(1000 + i * 10, 300 + i, days_ago=fail_days + i, tags=("shortest paths",), rating=1500)
    for i in range(8):  # dp weakness (different top-level)
        subs += failed_episode(3000 + i * 10, 400 + i, days_ago=fail_days + i, tags=("dp",), rating=1450)
    for i in range(12):  # greedy strength
        subs += solved_episode(5000 + i * 10, 500 + i, days_ago=30 + i, tags=("greedy",), rating=1550)
    extra = (
        catalog("shortest paths", 7000)
        + catalog("dp", 7100)
        + catalog("greedy", 7200, rating_base=1350)
        + catalog("geometry", 7300)
        + catalog("number theory", 7400)
    )
    build_world(subs, extra)


def queue(force=False, size=4, date=QUEUE_DATE):
    return planner.build_daily_queue(HANDLE, queue_date=date, size=size, force=force)


# ─── Queue composition ───────────────────────────────────────────────────────


def test_daily_queue_composition():
    default_world()
    result = queue()
    assert len(result["items"]) == 4
    assert [item["slot"] for item in result["items"]] == [1, 2, 3, 4]
    assert result["items"][0]["mode"] == "review_or_warmup"
    assert result["items"][1]["mode"] == "core_repair"
    assert result["items"][2]["mode"] == "core_repair"
    assert result["items"][3]["mode"] in {"stretch", "transfer", "underexposed_exploration"}
    for item in result["items"]:
        assert item["why_selected"].strip()
        assert item["problem_id"]
        assert item["skill_id"]
    assert result["analysis_run_id"] is not None


def test_queue_size_bounds():
    default_world()
    assert len(queue(size=3)["items"]) == 3
    assert len(queue(size=5, force=True, date="2026-07-07")["items"]) == 5


def test_difficulty_targets_relative_to_skill_rating():
    default_world()
    result = queue()
    prof = profiles.get_profiles(HANDLE)
    for item in result["items"]:
        base = prof[item["skill_id"]]["skill_rating_shrunk"] or prof[item["skill_id"]]["global_rating_anchor"]
        offset = planner.MODE_OFFSETS[item["mode"]]
        expected = base + offset - 100 * result["recent_struggle"] + 50 * prof[item["skill_id"]]["preference_bias"]
        assert item["target_rating"] == int(round(expected))


# ─── Hard constraints ────────────────────────────────────────────────────────


def test_no_solved_or_recently_attempted_problems():
    default_world(recent_failures=True)  # failures 3-12 days ago = recently attempted
    result = queue()
    with store.connect() as conn:
        solved = {r["problem_id"] for r in conn.execute(
            "SELECT problem_id FROM problem_episodes WHERE handle = ? AND eventual_ac = 1", (HANDLE.lower(),))}
        attempted = {r["problem_id"] for r in conn.execute(
            "SELECT problem_id FROM problem_episodes WHERE handle = ?", (HANDLE.lower(),))}
    recent_attempted = attempted  # all fixture episodes are within 21d or solved
    for item in result["items"]:
        assert item["problem_id"] not in solved
        # failures were 3-12 days ago → those problems are excluded
        if item["mode"] != "review_or_warmup":
            assert item["problem_id"] not in recent_attempted


def test_skill_diversity_constraints():
    default_world()
    result = queue()
    top_levels = [planner.top_level(item["skill_id"]) for item in result["items"]]
    assert len(set(top_levels)) >= 2
    for tl in set(top_levels):
        assert top_levels.count(tl) <= 2
    contests = [item["problem_id"] for item in result["items"]]
    contest_ids = []
    with store.connect() as conn:
        for pid in contests:
            row = conn.execute("SELECT contest_id FROM problems WHERE problem_key = ?", (pid,)).fetchone()
            contest_ids.append(row["contest_id"])
    assert len(contest_ids) == len(set(contest_ids))  # max 1 per contest
    leaves = [item["skill_id"] for item in result["items"] if "." in item["skill_id"] and item["mode"] != "review_or_warmup"]
    assert len(leaves) == len(set(leaves))  # max 1 exact subskill


def test_recent_struggle_shifts_difficulty_easier_and_blocks_stretch():
    default_world(recent_failures=True)
    result = queue()
    assert result["recent_struggle"] >= planner.HIGH_STRUGGLE
    assert all(item["mode"] != "stretch" for item in result["items"])
    repair_items = [item for item in result["items"] if item["mode"] == "core_repair"]
    prof = profiles.get_profiles(HANDLE)
    for item in repair_items:
        base = prof[item["skill_id"]]["skill_rating_shrunk"] or prof[item["skill_id"]]["global_rating_anchor"]
        assert item["target_rating"] < base - 100  # struggle pushed below the plain core offset


def test_prerequisite_failure_blocks_leaf_target():
    subs = []
    # Parent "graphs" is a severe likely weakness (failing problems below level)…
    for i in range(12):
        subs += failed_episode(1000 + i * 10, 300 + i, days_ago=3 + i, tags=("graphs",), rating=1450, fails=4)
    # …and the leaf also looks weak.
    for i in range(6):
        subs += failed_episode(4000 + i * 10, 450 + i, days_ago=4 + i, tags=("shortest paths",), rating=1550)
    for i in range(10):
        subs += solved_episode(5000 + i * 10, 500 + i, days_ago=25 + i, tags=("greedy",), rating=1500)
    extra = catalog("graphs", 7000) + catalog("shortest paths", 7100) + catalog("greedy", 7200)
    build_world(subs, extra, user_rating=1600)

    prof = profiles.get_profiles(HANDLE)
    assert prof["graphs"]["status"] == "likely_weakness"
    assert prof["graphs"]["severity"] >= 55

    result = queue()
    targeted = {item["skill_id"] for item in result["items"]}
    assert "graphs.shortest_paths" not in targeted  # leaf blocked while parent is broken
    assert "graphs" in targeted


# ─── Stability / materialization ─────────────────────────────────────────────


def test_daily_queue_is_materialized_and_stable():
    default_world()
    first = queue()
    second = queue()
    assert second["reused"] is True
    assert second["run_id"] == first["run_id"]
    assert [i["problem_id"] for i in second["items"]] == [i["problem_id"] for i in first["items"]]


def test_plans_are_materialized_and_stable():
    default_world()
    first = planner.build_plan(HANDLE, "7_day", start_date=QUEUE_DATE)
    second = planner.build_plan(HANDLE, "7_day", start_date=QUEUE_DATE)
    assert second["reused"] is True
    assert second["plan_id"] == first["plan_id"]


def test_7_day_plan_structure():
    default_world()
    plan = planner.build_plan(HANDLE, "7_day", start_date=QUEUE_DATE)
    assert len(plan["days"]) == 7
    assert plan["days"][0]["theme"] == "Calibration + easy repair"
    assert plan["days"][6]["theme"] == "Checkpoint + report"
    all_items = [item for day in plan["days"] for item in day["items"]]
    assert all_items, "plan must contain items"
    pids = [item["problem_id"] for item in all_items]
    assert len(pids) == len(set(pids))  # no duplicate problems across the plan
    assert all(item["why_selected"].strip() for item in all_items)
    assert plan["analysis_run_id"] is not None


def test_14_day_plan_structure():
    default_world()
    plan = planner.build_plan(HANDLE, "14_day", start_date=QUEUE_DATE)
    assert len(plan["days"]) == 14
    assert plan["days"][13]["theme"] == "Checkpoint + verification readiness"
    week2_modes = {item["mode"] for day in plan["days"][7:] for item in day["items"]}
    assert week2_modes & {"transfer", "stretch", "underexposed_exploration"}


# ─── Feedback loop ───────────────────────────────────────────────────────────


def test_bad_problem_feedback_suppresses_problem():
    default_world()
    result = queue()
    target = result["items"][1]
    feedback = profiles.record_feedback(target["item_id"], "bad_problem")
    assert feedback["status"] == "saved"

    regenerated = queue(force=True)
    assert target["problem_id"] not in [item["problem_id"] for item in regenerated["items"]]

    with store.connect() as conn:
        stats = conn.execute(
            "SELECT * FROM problem_quality_stats WHERE problem_id = ?", (target["problem_id"],)
        ).fetchone()
    assert stats["feedback_negative"] == 1
    assert stats["feedback_wilson"] < 0.5


def test_too_hard_feedback_raises_frustration():
    default_world()
    result = queue()
    target = result["items"][1]
    before = profiles.get_profiles(HANDLE)[target["skill_id"]]["frustration_score"]
    profiles.record_feedback(target["item_id"], "too_hard")
    after = profiles.get_profiles(HANDLE)[target["skill_id"]]["frustration_score"]
    assert after == pytest.approx(before + 0.25)


def test_good_problem_feedback_improves_wilson():
    default_world()
    result = queue()
    target = result["items"][0]
    # Wilson lower bound is conservative: 8/8 positives puts it above the 0.5 prior.
    for _ in range(8):
        profiles.record_feedback(target["item_id"], "good_problem")
    with store.connect() as conn:
        stats = conn.execute(
            "SELECT * FROM problem_quality_stats WHERE problem_id = ?", (target["problem_id"],)
        ).fetchone()
    assert stats["feedback_positive"] == 8
    assert stats["feedback_wilson"] > 0.5


def test_profile_rebuild_preserves_feedback_fields():
    default_world()
    result = queue()
    profiles.record_feedback(result["items"][1]["item_id"], "too_hard")
    skill_id = result["items"][1]["skill_id"]
    profiles.build_profiles(HANDLE)  # rebuild from same analysis snapshot
    assert profiles.get_profiles(HANDLE)[skill_id]["frustration_score"] == pytest.approx(0.25)


# ─── Fallbacks ───────────────────────────────────────────────────────────────


def test_no_candidate_fallback_relaxes_window():
    # Catalog only has problems far above the target ratings.
    subs = []
    for i in range(8):
        subs += failed_episode(1000 + i * 10, 300 + i, days_ago=30 + i, tags=("dp",), rating=1400)
    extra = catalog("dp", 7000, count=4, rating_base=2600, rating_step=100)
    build_world(subs, extra)
    result = queue()
    assert result["items"], "fallback should still produce items"
    assert any("widened" in item["why_selected"] for item in result["items"])


def test_insufficient_candidates_warning_when_catalog_empty():
    subs = []
    for i in range(6):
        subs += failed_episode(1000 + i * 10, 300 + i, days_ago=3 + i, tags=("dp",), rating=1400)
    build_world(subs, extra_catalog=[])  # only the recently-attempted problems exist
    result = queue()
    assert result["items"] == []
    assert "insufficient_candidates" in result["warnings"]


def test_queue_without_analysis_run_warns():
    result = planner.build_daily_queue("nobody-here", queue_date=QUEUE_DATE)
    assert result["items"] == []
    assert "no_analysis_run_found_run_weakness_analyze_first" in result["warnings"]


def test_fallback_fills_queue_floor_when_lineup_skills_exhausted():
    # The user's only profiled skill is "dp", and every dp catalog problem is
    # also a problem they've recently attempted -> zero eligible dp candidates
    # for any slot. A separate skill ("geometry") they've never touched still
    # has fresh candidates in the shared catalog. Regression for: a prolific
    # user's own weak-skill pool being exhausted must not produce an empty
    # queue when other real recommendations exist.
    subs = []
    for i in range(8):
        subs += failed_episode(1000 + i * 10, 300 + i, days_ago=3 + i, tags=("dp",), rating=1400)
    extra = catalog("geometry", 7000, count=4, rating_base=1200, rating_step=50)
    build_world(subs, extra)  # no extra dp catalog: the dp pool is 100% recently-attempted
    result = queue()
    assert len(result["items"]) >= 2
    assert "fallback_expanded_pool_used" in result["warnings"]
    assert all(item["skill_id"] == "geometry" for item in result["items"])


def test_no_profiles_warning_distinguishes_never_analyzed_from_empty_catalog():
    # Never analyzed at all -> generic "run weakness analyze" hint.
    never_analyzed = planner.build_daily_queue("totally-unseen-handle", queue_date=QUEUE_DATE)
    assert never_analyzed["warnings"] == ["no_analysis_run_found_run_weakness_analyze_first"]

    # Analysis *did* run for this handle, but the shared problem catalog / skill
    # map was empty at the time, so it produced zero skill profiles. This is
    # the exact bug behind "593 episodes but an empty queue": the old generic
    # warning told users to re-run analysis when the real problem was an
    # ops-side empty catalog. The warning must say something different.
    subs = failed_episode(2000, 900, days_ago=5, tags=("dp",), rating=1400)
    store.upsert_user({"handle": HANDLE, "rating": 1500})
    store.upsert_submissions(HANDLE, subs)
    store.save_problemset_snapshot({"problems": [], "problemStatistics": []})
    taxonomy.build_problem_skill_map()  # no problems in the catalog -> map stays empty
    episodes.rebuild_episodes(HANDLE)
    weakness.analyze_handle_weakness(HANDLE)
    profiles.build_profiles(HANDLE)

    result = planner.build_daily_queue(HANDLE, queue_date=QUEUE_DATE)
    assert result["items"] == []
    assert result["warnings"] == ["analysis_found_but_no_skill_profiles_available_check_problem_catalog"]

    plan = planner.build_plan(HANDLE, "7_day", start_date=QUEUE_DATE)
    assert plan["days"] == []
    assert plan["start_date"] == QUEUE_DATE  # regression: must never be omitted ("Starts undefined")
    assert plan["warnings"] == ["analysis_found_but_no_skill_profiles_available_check_problem_catalog"]


# ─── API contract ────────────────────────────────────────────────────────────


def test_api_contract(tmp_path, monkeypatch):
    import contestiq_api.main as main

    # Contract test runs as an entitled (admin) caller; free-tier shaping is
    # covered separately in tests/test_billing_entitlements.py.
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    client = TestClient(main.app, headers={"X-Admin-Key": "test-admin-key"})
    default_world()

    created = client.post("/api/v1/recommendations/daily", json={"handle": HANDLE})
    assert created.status_code == 200
    data = created.json()
    for field in ("analysis_version", "taxonomy_version", "generated_at", "run_id",
                  "analysis_run_id", "queue_date", "recent_struggle", "items"):
        assert field in data
    assert 3 <= len(data["items"]) <= 5
    for item in data["items"]:
        for field in ("item_id", "slot", "mode", "problem_id", "skill_id", "target_rating",
                      "problem_rating", "quality_score", "final_score", "why_selected"):
            assert field in item

    today = client.get(f"/api/v1/recommendations/today?handle={HANDLE}")
    assert today.status_code == 200
    assert today.json()["run_id"] == data["run_id"]

    plan7 = client.post("/api/v1/plans/7-day", json={"handle": HANDLE})
    assert plan7.status_code == 200
    plan_id = plan7.json()["plan_id"]
    assert len(plan7.json()["days"]) == 7

    plan14 = client.post("/api/v1/plans/14-day", json={"handle": HANDLE})
    assert len(plan14.json()["days"]) == 14

    fetched = client.get(f"/api/v1/plans/{plan_id}")
    assert fetched.status_code == 200
    assert fetched.json()["plan_id"] == plan_id

    item_id = data["items"][0]["item_id"]
    fb = client.post(f"/api/v1/recommendations/{item_id}/feedback", json={"feedback_type": "good_problem"})
    assert fb.status_code == 200
    assert fb.json()["status"] == "saved"

    bad_type = client.post(f"/api/v1/recommendations/{item_id}/feedback", json={"feedback_type": "hated_it"})
    assert bad_type.status_code == 422

    missing = client.post("/api/v1/recommendations/no-such-item/feedback", json={"feedback_type": "skipped"})
    assert missing.status_code == 404

    no_plan = client.get("/api/v1/plans/00000000-0000-0000-0000-000000000000")
    assert no_plan.status_code == 404
