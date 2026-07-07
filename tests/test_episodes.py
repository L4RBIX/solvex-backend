"""Problem episode builder tests — deterministic, no live Codeforces."""

import json

import pytest

from contestiq_api.cfdata import episodes, store


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)


BASE_TIME = 1700000000


def make_submission(sid, problem_key, verdict, *, offset=0, rating=1400, participant="PRACTICE", passed=5,
                    contest_id=200, index="B", tags=("dp",), handle="Epi-User"):
    return {
        "id": sid,
        "contestId": contest_id,
        "creationTimeSeconds": BASE_TIME + offset,
        "relativeTimeSeconds": 2147483647,
        "problem": {
            "contestId": contest_id,
            "index": index,
            "name": f"Problem {problem_key}",
            **({"rating": rating} if rating is not None else {}),
            "tags": list(tags),
        },
        "author": {"members": [{"handle": handle}], "participantType": participant},
        "programmingLanguage": "GNU C++17",
        "verdict": verdict,
        "passedTestCount": passed,
        "timeConsumedMillis": 100,
        "memoryConsumedBytes": 1024,
    }


def seed(handle="Epi-User", submissions=(), rating_history=(), user_rating=1500):
    store.upsert_user({"handle": handle, "rating": user_rating, "maxRating": 1600, "rank": "specialist"})
    store.upsert_rating_history(handle, list(rating_history))
    store.upsert_submissions(handle, list(submissions))


def rebuild(handle="Epi-User"):
    return episodes.rebuild_episodes(handle)


def get(problem_key, handle="Epi-User"):
    episode = episodes.get_episode(handle, problem_key)
    assert episode is not None
    return episode


# ─── Episode collapsing and statuses ─────────────────────────────────────────


def test_multiple_submissions_become_one_episode():
    seed(submissions=[
        make_submission(1, "200B", "WRONG_ANSWER", offset=0, passed=3),
        make_submission(2, "200B", "WRONG_ANSWER", offset=600, passed=7),
        make_submission(3, "200B", "OK", offset=1200, passed=40),
    ])
    result = rebuild()
    assert result["episodes"] == 1
    ep = get("200B")
    assert ep["total_submissions"] == 3
    assert ep["failed_before_ac"] == 2
    assert ep["final_status"] == "solved_with_friction"
    assert ep["eventual_ac"] is True
    assert ep["first_submission_id"] == 1
    assert ep["first_ac_submission_id"] == 3
    assert ep["first_attempt_at"] == BASE_TIME
    assert ep["first_ac_at"] == BASE_TIME + 1200
    assert ep["last_submission_at"] == BASE_TIME + 1200
    assert ep["verdict_sequence"] == ["WRONG_ANSWER", "WRONG_ANSWER", "OK"]
    assert ep["passed_test_progression"] == [3, 7, 40]


def test_ac_first_try_is_clean_solve():
    seed(submissions=[make_submission(1, "200B", "OK")])
    rebuild()
    ep = get("200B")
    assert ep["final_status"] == "clean_solve"
    assert ep["failed_before_ac"] == 0
    assert ep["eventual_ac"] is True


def test_abandoned_episode_without_ac():
    seed(submissions=[
        make_submission(1, "200B", "WRONG_ANSWER", offset=0),
        make_submission(2, "200B", "TIME_LIMIT_EXCEEDED", offset=300),
    ])
    rebuild()
    ep = get("200B")
    assert ep["final_status"] == "abandoned"
    assert ep["eventual_ac"] is False
    assert ep["first_ac_submission_id"] is None
    assert ep["first_ac_at"] is None
    assert ep["failed_before_ac"] == 2


def test_delayed_ac_is_weaker_evidence():
    seed(submissions=[
        make_submission(1, "200B", "WRONG_ANSWER", offset=0),
        make_submission(2, "200B", "OK", offset=100 * 3600),  # 100 h later
    ])
    rebuild()
    assert get("200B")["final_status"] == "delayed_ac"


def test_friction_within_threshold_is_not_delayed():
    seed(submissions=[
        make_submission(1, "200B", "WRONG_ANSWER", offset=0),
        make_submission(2, "200B", "OK", offset=71 * 3600),
    ])
    rebuild()
    assert get("200B")["final_status"] == "solved_with_friction"


def test_separate_problems_get_separate_episodes():
    seed(submissions=[
        make_submission(1, "200B", "OK", contest_id=200, index="B"),
        make_submission(2, "300C", "WRONG_ANSWER", contest_id=300, index="C"),
    ])
    result = rebuild()
    assert result["episodes"] == 2
    assert result["final_status_counts"] == {"clean_solve": 1, "abandoned": 1}


# ─── Rating anchor and bands ─────────────────────────────────────────────────


def test_rating_anchor_uses_latest_history_before_episode():
    history = [
        {"contestId": 10, "newRating": 1300, "oldRating": 1200, "ratingUpdateTimeSeconds": BASE_TIME - 5000},
        {"contestId": 11, "newRating": 1350, "oldRating": 1300, "ratingUpdateTimeSeconds": BASE_TIME - 100},
        {"contestId": 12, "newRating": 1900, "oldRating": 1350, "ratingUpdateTimeSeconds": BASE_TIME + 9999},
    ]
    seed(submissions=[make_submission(1, "200B", "OK", rating=1400)], rating_history=history)
    rebuild()
    ep = get("200B")
    assert ep["user_rating_at_time"] == 1350  # latest before, never the future one
    assert ep["rating_anchor_source"] == "rating_history"
    assert ep["rating_gap"] == 50
    assert ep["rating_band"] == "on_level"


def test_missing_rating_history_falls_back_to_current_rating():
    seed(submissions=[make_submission(1, "200B", "OK", rating=1400)], rating_history=[], user_rating=1500)
    rebuild()
    ep = get("200B")
    assert ep["user_rating_at_time"] == 1500
    assert ep["rating_anchor_source"] == "current_rating"
    assert ep["rating_gap"] == -100


def test_unrated_user_falls_back_to_global_default():
    seed(submissions=[make_submission(1, "200B", "OK", rating=1400)], rating_history=[], user_rating=None)
    rebuild()
    ep = get("200B")
    assert ep["user_rating_at_time"] == 1200
    assert ep["rating_anchor_source"] == "global_default"
    assert ep["rating_gap"] == 200
    assert ep["rating_band"] == "stretch"


def test_ratingless_problem_is_unknown_difficulty():
    seed(submissions=[make_submission(1, "200B", "OK", rating=None)])
    rebuild()
    ep = get("200B")
    assert ep["problem_rating"] is None
    assert ep["rating_gap"] is None
    assert ep["rating_band"] == "unknown_difficulty"


def test_ratingless_submission_uses_problems_table_fallback():
    store.save_problemset_snapshot({
        "problems": [{"contestId": 200, "index": "B", "name": "Problem 200B", "rating": 1800, "tags": ["dp"]}],
        "problemStatistics": [],
    })
    seed(submissions=[make_submission(1, "200B", "OK", rating=None)], user_rating=1500)
    rebuild()
    ep = get("200B")
    assert ep["problem_rating"] == 1800
    assert ep["rating_gap"] == 300
    assert ep["rating_band"] == "stretch"


def test_rating_band_boundaries():
    assert episodes.rating_band(-200) == "consolidation"
    assert episodes.rating_band(-199) == "on_level"
    assert episodes.rating_band(150) == "on_level"
    assert episodes.rating_band(151) == "stretch"
    assert episodes.rating_band(400) == "stretch"
    assert episodes.rating_band(401) == "out_of_band"
    assert episodes.rating_band(None) == "unknown_difficulty"


# ─── Context types ───────────────────────────────────────────────────────────


def test_contest_practice_virtual_context():
    seed(submissions=[
        make_submission(1, "100A", "WRONG_ANSWER", contest_id=100, index="A", participant="CONTESTANT", offset=0),
        make_submission(2, "100A", "OK", contest_id=100, index="A", participant="PRACTICE", offset=600),
        make_submission(3, "200B", "OK", contest_id=200, index="B", participant="VIRTUAL"),
        make_submission(4, "300C", "OK", contest_id=300, index="C", participant="PRACTICE"),
    ])
    rebuild()
    contest_ep = get("100A")
    # First encounter was in a live contest, even though the AC came in practice.
    assert contest_ep["context_type"] == "contest"
    assert contest_ep["participant_type_primary"] in {"CONTESTANT", "PRACTICE"}
    assert get("200B")["context_type"] == "virtual"
    assert get("300C")["context_type"] == "practice"


# ─── Determinism and idempotency ─────────────────────────────────────────────


def test_rebuild_is_deterministic_and_idempotent():
    seed(submissions=[
        make_submission(1, "200B", "WRONG_ANSWER", offset=0),
        make_submission(2, "200B", "OK", offset=600),
    ])
    rebuild()
    first = get("200B")
    rebuild()
    second = get("200B")
    assert first == second
    with store.connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM problem_episodes").fetchone()[0]
    assert count == 1


def test_episode_id_is_stable_and_scoped():
    a = episodes.episode_id_for("Epi-User", "200B")
    assert a == episodes.episode_id_for("epi-user", "200B")  # handle case-insensitive
    assert a != episodes.episode_id_for("epi-user", "200C")
    assert a != episodes.episode_id_for("other-user", "200B")


def test_out_of_order_submissions_produce_same_episode():
    subs = [
        make_submission(1, "200B", "WRONG_ANSWER", offset=0),
        make_submission(2, "200B", "OK", offset=600),
    ]
    seed(submissions=list(reversed(subs)))
    rebuild()
    ep = get("200B")
    assert ep["verdict_sequence"] == ["WRONG_ANSWER", "OK"]
    assert ep["first_submission_id"] == 1


def test_incremental_resync_then_rebuild_updates_episode():
    seed(submissions=[make_submission(1, "200B", "WRONG_ANSWER", offset=0)])
    rebuild()
    assert get("200B")["final_status"] == "abandoned"

    store.upsert_submissions("Epi-User", [make_submission(2, "200B", "OK", offset=600)])
    rebuild()
    ep = get("200B")
    assert ep["final_status"] == "solved_with_friction"
    assert ep["total_submissions"] == 2


# ─── Endpoints ───────────────────────────────────────────────────────────────


def test_episode_endpoints(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import contestiq_api.main as main

    client = TestClient(main.app)
    seed(submissions=[make_submission(1, "200B", "OK")])

    response = client.post("/api/v1/episodes/Epi-User/rebuild")
    assert response.status_code == 200
    assert response.json()["episodes"] == 1

    listing = client.get("/api/v1/episodes/Epi-User")
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] == 1
    assert body["episodes"][0]["final_status"] == "clean_solve"

    empty = client.post("/api/v1/episodes/nobody-here/rebuild")
    assert "warning" in empty.json()
