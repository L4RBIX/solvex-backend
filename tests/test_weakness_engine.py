"""Weakness engine golden tests — synthetic profile archetypes, no live Codeforces."""

import math

import pytest

from contestiq_api.cfdata import episodes, store, taxonomy, weakness


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)


NOW = 1700000000  # data cutoff anchor
DAY = 86400
HANDLE = "Golden-User"


def submission(sid, contest_id, index, verdict, *, days_ago=1, rating=1400, tags=("dp",), participant="PRACTICE"):
    return {
        "id": sid,
        "contestId": contest_id,
        "creationTimeSeconds": NOW - days_ago * DAY,
        "problem": {
            "contestId": contest_id,
            "index": index,
            "name": f"P{contest_id}{index}",
            **({"rating": rating} if rating is not None else {}),
            "tags": list(tags),
        },
        "author": {"members": [{"handle": HANDLE}], "participantType": participant},
        "programmingLanguage": "GNU C++17",
        "verdict": verdict,
        "passedTestCount": 5,
        "timeConsumedMillis": 100,
        "memoryConsumedBytes": 1024,
    }


def setup_world(submissions, *, user_rating=1500, catalog_extra=()):
    """Seed user + submissions + problems catalog, build map + episodes."""
    store.upsert_user({"handle": HANDLE, "rating": user_rating})
    store.upsert_submissions(HANDLE, submissions)
    problems = {}
    for sub in submissions:
        p = sub["problem"]
        key = f"{p['contestId']}{p['index']}"
        problems[key] = {"contestId": p["contestId"], "index": p["index"], "name": p["name"],
                         **({"rating": p["rating"]} if p.get("rating") is not None else {}), "tags": p["tags"]}
    for extra in catalog_extra:
        problems[f"{extra['contestId']}{extra['index']}"] = extra
    store.save_problemset_snapshot({"problems": list(problems.values()), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    episodes.rebuild_episodes(HANDLE)


def analyze():
    return weakness.analyze_handle_weakness(HANDLE)


def skill(result, skill_id):
    match = [s for s in result["skills"] if s["skill_id"] == skill_id]
    assert match, f"skill {skill_id} not in result: {[s['skill_id'] for s in result['skills']]}"
    return match[0]


def solved_problem(sid_base, contest_id, index, *, days_ago, tags, rating=1400, fails=0):
    """One episode: `fails` failed attempts then AC."""
    subs = []
    for i in range(fails):
        subs.append(submission(sid_base + i, contest_id, index, "WRONG_ANSWER",
                               days_ago=days_ago, rating=rating, tags=tags))
    subs.append(submission(sid_base + fails, contest_id, index, "OK",
                           days_ago=days_ago, rating=rating, tags=tags))
    return subs


def failed_problem(sid_base, contest_id, index, *, days_ago, tags, rating=1400, fails=3):
    return [
        submission(sid_base + i, contest_id, index, "WRONG_ANSWER", days_ago=days_ago, rating=rating, tags=tags)
        for i in range(fails)
    ]


# ─── Formula units ───────────────────────────────────────────────────────────


def test_recency_weight_formula():
    assert weakness.recency_weight(0, 180) == 1.0
    assert weakness.recency_weight(180, 180) == pytest.approx(0.5)
    assert weakness.recency_weight(360, 180) == pytest.approx(0.25)


def test_shrunk_success_rate_formula():
    assert weakness.shrunk_success_rate(0, 0) == pytest.approx(0.5)  # prior only
    assert weakness.shrunk_success_rate(10, 10) == pytest.approx(11.5 / 13.0)


def test_attempt_efficiency_formula():
    assert weakness.attempt_efficiency(True, 0) == pytest.approx(1.0)
    assert weakness.attempt_efficiency(True, 2) == pytest.approx(1 / (1 + math.log(3)))
    assert weakness.attempt_efficiency(False, 3) == pytest.approx(0.35 / (1 + math.log(4)))


# ─── Golden archetypes ───────────────────────────────────────────────────────


def test_low_data_never_high_confidence_weakness():
    # One failed dp episode: must not be called a weakness.
    setup_world(failed_problem(1, 100, "A", days_ago=5, tags=("dp",), fails=4))
    result = analyze()
    dp = skill(result, "dynamic_programming")
    assert dp["status"] in {"insufficient_evidence", "underexposed"}
    assert dp["confidence"] < 0.3
    assert "small_sample_size" in dp["warnings"]


def test_strong_skill_archetype():
    subs = []
    for i in range(12):
        subs += solved_problem(100 + i * 10, 200 + i, "A", days_ago=3 + i, tags=("shortest paths",), rating=1550, fails=0)
    setup_world(subs, user_rating=1500)
    result = analyze()
    sp = skill(result, "graphs.shortest_paths")
    assert sp["status"] == "strength"
    assert sp["confidence"] >= 0.6
    assert sp["severity"] < 40
    assert sp["estimated_skill_rating"] >= 1500


def test_likely_weakness_with_many_failed_episodes():
    subs = []
    for i in range(10):
        subs += failed_problem(1000 + i * 10, 300 + i, "B", days_ago=2 + i, tags=("shortest paths",), rating=1500, fails=3)
    # A couple of solved easier ones so it's not pure zero.
    subs += solved_problem(2000, 400, "C", days_ago=4, tags=("shortest paths",), rating=1200, fails=2)
    setup_world(subs, user_rating=1600)
    result = analyze()
    sp = skill(result, "graphs.shortest_paths")
    assert sp["status"] == "likely_weakness"
    assert sp["severity"] >= 55
    assert sp["confidence"] >= 0.55
    assert sp["estimated_skill_rating"] < 1600
    assert sp["evidence"]["solved"] == 1
    assert sp["evidence"]["episodes"] == 11


def test_repeated_submissions_count_once_with_friction():
    # 8 WA + 1 AC on the SAME problem = one episode, not eight failures.
    subs = solved_problem(1, 100, "A", days_ago=3, tags=("number theory",), fails=8)
    setup_world(subs)
    result = analyze()
    nt = skill(result, "number_theory")
    assert nt["evidence"]["episodes"] == 1
    assert nt["evidence"]["solved"] == 1
    assert nt["evidence"]["avg_failed_before_ac"] == 8
    assert nt["status"] in {"insufficient_evidence", "underexposed"}  # one episode is never enough


def test_old_failures_matter_less_than_recent():
    # Recency is anchored to the user's newest submission (reproducible cutoff),
    # so both worlds share a fresh dp episode to pin the cutoff at ~now, and
    # only the geometry failures differ in age.
    anchor = solved_problem(9000, 990, "Z", days_ago=1, tags=("dp",), fails=0)
    old_fail_subs, recent_fail_subs = list(anchor), list(anchor)
    for i in range(8):
        old_fail_subs += failed_problem(1000 + i * 10, 300 + i, "B", days_ago=700 + i, tags=("geometry",), rating=1500)
        recent_fail_subs += failed_problem(5000 + i * 10, 500 + i, "C", days_ago=3 + i, tags=("geometry",), rating=1500)

    setup_world(old_fail_subs, user_rating=1500)
    old_result = analyze()
    old_geo = skill(old_result, "geometry")

    # Fresh isolated world for the recent-failure twin.
    with store.connect() as conn:
        conn.execute("DELETE FROM problem_episodes")
        conn.execute("DELETE FROM cf_submissions_normalized")
        conn.execute("DELETE FROM cf_submissions_raw")
    setup_world(recent_fail_subs, user_rating=1500)
    recent_result = analyze()
    recent_geo = skill(recent_result, "geometry")

    assert recent_geo["evidence"]["weighted_episodes"] > old_geo["evidence"]["weighted_episodes"]
    assert recent_geo["severity"] > old_geo["severity"]
    assert recent_geo["confidence"] > old_geo["confidence"]
    assert "stale_evidence" in old_geo["warnings"]


def test_recent_improvement_status():
    subs = []
    for i in range(6):  # old friction
        subs += failed_problem(1000 + i * 10, 300 + i, "B", days_ago=200 + i, tags=("combinatorics",), rating=1450)
    for i in range(5):  # recent clean successes
        subs += solved_problem(5000 + i * 10, 500 + i, "C", days_ago=5 + i, tags=("combinatorics",), rating=1450, fails=0)
    setup_world(subs, user_rating=1500)
    result = analyze()
    combo = skill(result, "combinatorics")
    assert combo["status"] == "historical_weakness_recent_improvement"
    assert "recent" in combo["explanation"].lower()


def test_ratingless_problems_handled():
    subs = []
    for i in range(6):
        subs += solved_problem(100 + i * 10, 200 + i, "A", days_ago=3 + i, tags=("games",), rating=None, fails=1)
    setup_world(subs)
    result = analyze()
    games = skill(result, "games")
    assert games["estimated_skill_rating"] is None
    assert games["evidence"]["rating_band"] == "unknown"
    assert games["status"] == "calibration_needed"
    assert "no_rated_problems" in games["warnings"]


def test_low_taxonomy_confidence_reduces_confidence():
    # Same episode structure via a weak tag ("math", conf 0.5) vs a strong tag
    # ("number theory", conf 0.85) — weak mapping must yield lower confidence.
    weak_subs, strong_subs = [], []
    for i in range(8):
        weak_subs += solved_problem(100 + i * 10, 200 + i, "A", days_ago=3 + i, tags=("math",), fails=1)
        strong_subs += solved_problem(3000 + i * 10, 600 + i, "D", days_ago=3 + i, tags=("number theory",), fails=1)
    setup_world(weak_subs + strong_subs)
    result = analyze()
    math_skill = skill(result, "math")
    nt_skill = skill(result, "number_theory")
    assert math_skill["confidence"] < nt_skill["confidence"]
    assert math_skill["evidence"]["taxonomy_quality"] < nt_skill["evidence"]["taxonomy_quality"]
    assert "low_taxonomy_confidence" in math_skill["warnings"]


def test_underexposure_relative_to_opportunity():
    # Catalog contains plenty of geometry, user never touches it.
    catalog = [
        {"contestId": 900 + i, "index": "G", "name": f"Geo {i}", "rating": 1400, "tags": ["geometry"]}
        for i in range(10)
    ]
    subs = []
    for i in range(12):
        subs += solved_problem(100 + i * 10, 200 + i, "A", days_ago=3 + i, tags=("dp",), fails=0)
    setup_world(subs, catalog_extra=catalog)
    result = analyze()
    geo = skill(result, "geometry")
    assert geo["status"] == "underexposed"
    assert geo["underexposure"] == 1.0
    assert "underexposed" in geo["explanation"]
    # Forbidden framing must not appear anywhere.
    assert "avoid" not in geo["explanation"].lower()


# ─── Safety of language ──────────────────────────────────────────────────────


def test_no_unsupported_claims_in_any_explanation():
    subs = []
    for i in range(6):
        subs += failed_problem(1000 + i * 10, 300 + i, "B", days_ago=3 + i, tags=("dp",), rating=1500)
    for i in range(6):
        subs += solved_problem(5000 + i * 10, 500 + i, "C", days_ago=3 + i, tags=("greedy",), fails=0)
    setup_world(subs)
    result = analyze()
    import json as _json

    from contestiq_api.safety import scan_public_payload

    scan_public_payload(result)
    text = _json.dumps(result).lower()
    for banned in ["cheat", "editorial", "ai detected", "avoidance", "solve time", "plagiar"]:
        assert banned not in text, f"unsupported claim fragment: {banned}"


# ─── Snapshots ───────────────────────────────────────────────────────────────


def test_snapshot_reproducibility():
    subs = solved_problem(1, 100, "A", days_ago=3, tags=("dp",), fails=2)
    subs += failed_problem(100, 200, "B", days_ago=5, tags=("dp",))
    setup_world(subs)
    first = analyze()
    second = analyze()
    assert first["input_data_hash"] == second["input_data_hash"]
    assert first["data_cutoff_time"] == second["data_cutoff_time"]
    assert first["run_id"] != second["run_id"]  # immutable: new run, not overwrite
    assert first["skills"] == second["skills"]

    stored_first = weakness.get_run(first["run_id"])
    stored_second = weakness.get_run(second["run_id"])
    assert stored_first["skills"] == stored_second["skills"]
    with store.connect() as conn:
        runs = conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
        history = conn.execute("SELECT COUNT(*) FROM user_skill_history").fetchone()[0]
    assert runs == 2
    assert history == 2 * len(first["skills"])


def test_snapshot_stores_version_metadata():
    setup_world(solved_problem(1, 100, "A", days_ago=3, tags=("dp",)))
    result = analyze()
    stored = weakness.get_run(result["run_id"])
    assert stored["analysis_version"] == "ml_core_v0.4"
    assert stored["taxonomy_version"] == "taxonomy_v1"
    assert stored["problem_catalog_version"] == "cf_problemset_v1"
    assert stored["input_data_hash"] == result["input_data_hash"]
    assert stored["data_cutoff_time"] == result["data_cutoff_time"]


def test_problem_evidence_recorded_for_claims():
    subs = []
    for i in range(5):
        subs += failed_problem(1000 + i * 10, 300 + i, "B", days_ago=3 + i, tags=("dp",), rating=1500)
    setup_world(subs)
    result = analyze()
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM analysis_problem_evidence WHERE run_id = ? AND skill_id = 'dynamic_programming'",
            (result["run_id"],),
        ).fetchall()
    assert len(rows) == 5  # every scored episode is traceable
    assert all(row["final_status"] == "abandoned" for row in rows)


# ─── API contract ────────────────────────────────────────────────────────────


def test_api_contract(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import contestiq_api.main as main

    # Contract test runs as an entitled (admin) caller; free-tier shaping is
    # covered separately in tests/test_billing_entitlements.py.
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    client = TestClient(main.app, headers={"X-Admin-Key": "test-admin-key"})
    subs = []
    for i in range(8):
        subs += failed_problem(1000 + i * 10, 300 + i, "B", days_ago=3 + i, tags=("shortest paths",), rating=1550)
    setup_world(subs, user_rating=1500)

    response = client.post(f"/api/v1/weakness/{HANDLE}/analyze")
    assert response.status_code == 200
    data = response.json()
    for field in ("analysis_version", "taxonomy_version", "problem_catalog_version",
                  "generated_at", "data_cutoff_time", "source", "warnings",
                  "run_id", "input_data_hash", "skills"):
        assert field in data

    entry = next(s for s in data["skills"] if s["skill_id"] == "graphs.shortest_paths")
    for field in ("skill_id", "status", "confidence", "severity", "underexposure",
                  "estimated_skill_rating", "estimated_skill_rating_low",
                  "estimated_skill_rating_high", "evidence", "warnings", "explanation"):
        assert field in entry
    for field in ("episodes", "weighted_episodes", "solved", "avg_failed_before_ac",
                  "rating_band", "recent_window_days", "taxonomy_quality"):
        assert field in entry["evidence"]
    assert entry["status"] in weakness.STATUSES

    latest = client.get(f"/api/v1/weakness/{HANDLE}/latest")
    assert latest.status_code == 200
    assert latest.json()["run_id"] == data["run_id"]

    by_id = client.get(f"/api/v1/weakness/runs/{data['run_id']}")
    assert by_id.status_code == 200

    missing = client.get("/api/v1/weakness/nobody-at-all/latest")
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "ANALYSIS_RUN_NOT_FOUND"
