"""Gamification (Phase G1) tests: XP, levels, streak, daily goal, badges.

Covers both the pure compute layer (`contestiq_api.gamification`) with
directly-constructed event histories, and the HTTP contract
(`/api/v1/gamification/*`) through the FastAPI TestClient.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from contestiq_api import gamification, product_events
from contestiq_api.cfdata import store

ADMIN_KEY = "gamification-admin-key"
HANDLE = "Gamer-One"


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    yield


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client, handle=None, plan=None):
    user = client.post("/api/v1/admin/users", json={"handle": handle}, headers=admin()).json()
    if plan:
        client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement", json={"plan": plan}, headers=admin())
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def _insert_event(event_type: str, subject: str, *, day: dt.date, properties: dict | None = None) -> None:
    """Directly insert a product_event with a controlled UTC date, bypassing
    `product_events.track()`'s real-clock `_now()` so streak/XP tests can
    construct exact multi-day histories."""
    created_at = dt.datetime.combine(day, dt.time(12, 0), tzinfo=dt.timezone.utc).isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO product_events (event_id, event_type, subject, properties, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), event_type, subject, json.dumps(properties or {}), created_at),
        )


def _days_ago(n: int, today: dt.date | None = None) -> dt.date:
    today = today or dt.date.today()
    return today - dt.timedelta(days=n)


# ─── Streak: only meaningful actions ─────────────────────────────────────────


def test_streak_does_not_count_page_views():
    # "page_view"-style events are not even part of the allow-list, so the
    # write path itself rejects them — they can never enter product_events.
    with pytest.raises(AssertionError):
        product_events.track("page_view", "handle:x")
    with pytest.raises(AssertionError):
        product_events.track("opened_analyze_page", "handle:x")
    with pytest.raises(AssertionError):
        product_events.track("dashboard_refresh", "handle:x")

    # Defense in depth: even if a non-meaningful event type slipped into the
    # events list handed to the compute layer, it must not count.
    today = dt.date.today()
    events = [
        {"event_type": "page_view", "created_at": today.isoformat() + "T00:00:00+00:00"},
        {"event_type": "copilot_message_sent", "created_at": today.isoformat() + "T00:01:00+00:00"},
    ]
    streak = gamification.compute_streak(events, today=today)
    assert streak == {"current": 0, "longest": 0, "last_active_date": None, "today_completed": False}


def test_streak_counts_meaningful_product_events():
    subject = "handle:streaker"
    today = dt.date.today()
    for n in (3, 2, 1, 0):  # 4 consecutive active days ending today
        _insert_event("first_queue_generated" if n == 3 else "daily_queue_generated", subject, day=_days_ago(n, today))
    events = product_events.events_for(subject)
    streak = gamification.compute_streak(events, today=today)
    assert streak["current"] == 4
    assert streak["longest"] == 4
    assert streak["today_completed"] is True
    assert streak["last_active_date"] == today.isoformat()


def test_streak_grace_period_when_today_not_yet_active():
    subject = "handle:grace"
    today = dt.date.today()
    _insert_event("daily_queue_generated", subject, day=_days_ago(2, today))
    _insert_event("daily_queue_generated", subject, day=_days_ago(1, today))
    events = product_events.events_for(subject)
    streak = gamification.compute_streak(events, today=today)
    assert streak["current"] == 2  # still alive: yesterday was active, today isn't over
    assert streak["today_completed"] is False


def test_streak_breaks_after_a_full_skipped_day():
    subject = "handle:broken"
    today = dt.date.today()
    _insert_event("daily_queue_generated", subject, day=_days_ago(5, today))
    _insert_event("daily_queue_generated", subject, day=_days_ago(4, today))
    # gap: days_ago(3) and (2) skipped entirely
    _insert_event("daily_queue_generated", subject, day=_days_ago(1, today))
    events = product_events.events_for(subject)
    streak = gamification.compute_streak(events, today=today)
    assert streak["current"] == 1  # only yesterday counts toward the live streak
    assert streak["longest"] == 2  # the earlier 2-day run is still the longest on record


# ─── XP calculation & daily cap ───────────────────────────────────────────────


def test_xp_calculation_sums_distinct_action_types():
    subject = "handle:xp-calc"
    day = dt.date.today()
    _insert_event("first_analysis_completed", subject, day=day)  # +20
    _insert_event("feedback_submitted", subject, day=day)  # +5
    _insert_event("plan_started", subject, day=day)  # +15
    events = product_events.events_for(subject)
    assert gamification.compute_xp_total(events, daily_cap=1000) == 40


def test_xp_repeating_one_action_same_day_only_counts_once():
    subject = "handle:xp-repeat"
    day = dt.date.today()
    for _ in range(5):
        _insert_event("feedback_submitted", subject, day=day)
    events = product_events.events_for(subject)
    # 5 feedback events in one day still contribute feedback's +5 XP once,
    # not 25 — a single action type cannot be farmed by repetition.
    assert gamification.compute_xp_total(events, daily_cap=1000) == 5


def test_daily_xp_cap_limits_total_regardless_of_actions():
    subject = "handle:xp-cap"
    day = dt.date.today()
    for event_type in ("first_analysis_completed", "verification_attempted", "premium_conversion", "weekly_report_generated"):
        _insert_event(event_type, subject, day=day)  # raw sum = 20+25+50+20 = 115
    events = product_events.events_for(subject)
    assert gamification.compute_xp_total(events, daily_cap=1000) == 115
    assert gamification.compute_xp_total(events, daily_cap=50) == 50  # free-tier cap wins
    assert gamification.compute_xp_total(events, daily_cap=150) == 115  # under premium cap, uncapped


def test_free_and_premium_daily_caps_differ():
    subject = "handle:plan-diff"
    day = dt.date.today()
    for event_type in ("first_analysis_completed", "verification_attempted", "premium_conversion"):
        _insert_event(event_type, subject, day=day)  # raw = 20+25+50 = 95
    events = product_events.events_for(subject)

    free_snapshot = gamification.build_snapshot(subject, "free", events)
    premium_snapshot = gamification.build_snapshot(subject, "premium_student", events)
    assert free_snapshot["xp_total"] == 50  # capped
    assert premium_snapshot["xp_total"] == 95  # under the 150 premium cap
    assert free_snapshot["xp_total"] < premium_snapshot["xp_total"]

    team_snapshot = gamification.build_snapshot(subject, "team", events)
    event_snapshot = gamification.build_snapshot(subject, "event", events)
    admin_snapshot = gamification.build_snapshot(subject, "admin", events)
    assert team_snapshot["xp_total"] == event_snapshot["xp_total"] == admin_snapshot["xp_total"] == 95


# ─── Level formula ─────────────────────────────────────────────────────────


def test_level_thresholds_match_spec_anchors():
    assert gamification.level_threshold(1) == 0
    assert gamification.level_threshold(2) == 100
    assert gamification.level_threshold(3) == 250
    assert gamification.level_threshold(4) == 500
    assert gamification.level_threshold(5) == 900


def test_level_thresholds_keep_increasing_deterministically_past_5():
    thresholds = [gamification.level_threshold(level) for level in range(1, 12)]
    assert thresholds == sorted(thresholds)
    assert len(set(thresholds)) == len(thresholds)  # strictly increasing
    # Same input always produces the same thresholds (deterministic).
    assert [gamification.level_threshold(level) for level in range(1, 12)] == thresholds


def test_level_progress_matches_documented_example():
    progress = gamification.level_progress(340)
    assert gamification.level_for_xp(340) == 3
    assert progress == {"current_level_xp": 250, "next_level_xp": 500, "progress_percent": 36}


# ─── Daily goal ───────────────────────────────────────────────────────────


def test_daily_goal_incomplete_with_only_one_action():
    subject = "handle:goal-one"
    today = dt.date.today()
    _insert_event("first_analysis_completed", subject, day=today)
    events = product_events.events_for(subject)
    goal = gamification.compute_daily_goal(events, today=today)
    assert goal["completed_count"] == 1
    assert goal["required_count"] == 2
    assert goal["completed"] is False


def test_daily_goal_completes_after_two_distinct_categories():
    subject = "handle:goal-two"
    today = dt.date.today()
    _insert_event("first_analysis_completed", subject, day=today)
    _insert_event("daily_queue_generated", subject, day=today)
    events = product_events.events_for(subject)
    goal = gamification.compute_daily_goal(events, today=today)
    assert goal["completed_count"] == 2
    assert goal["completed"] is True
    ids = {item["id"]: item["completed"] for item in goal["items"]}
    assert ids["analysis_completed"] is True
    assert ids["queue_generated"] is True
    assert ids["feedback_submitted"] is False


def test_daily_goal_repeating_one_action_does_not_complete_it():
    subject = "handle:goal-repeat"
    today = dt.date.today()
    for _ in range(4):
        _insert_event("feedback_submitted", subject, day=today)
    events = product_events.events_for(subject)
    goal = gamification.compute_daily_goal(events, today=today)
    assert goal["completed_count"] == 1  # still one category, no matter how many times
    assert goal["completed"] is False


# ─── Badges ───────────────────────────────────────────────────────────────


def test_badges_are_earned_once_and_do_not_double_fire():
    subject = "handle:badge-once"
    day = dt.date.today()
    assert product_events.track("first_analysis_completed", subject, {"run_id": "r1"}) is True
    # A second attempt to fire the same first_* event is rejected by the
    # unique index — proving first-time badges cannot double-fire.
    assert product_events.track("first_analysis_completed", subject, {"run_id": "r2"}) is False

    events = product_events.events_for(subject)
    badges = gamification.compute_badges(events)
    matching = [b for b in badges if b["id"] == "first_analysis"]
    assert len(matching) == 1
    first_earned_at = matching[0]["earned_at"]

    # Recomputing repeatedly must always report the same single badge/timestamp.
    for _ in range(3):
        badges_again = gamification.compute_badges(product_events.events_for(subject))
        again = [b for b in badges_again if b["id"] == "first_analysis"]
        assert len(again) == 1
        assert again[0]["earned_at"] == first_earned_at


def test_streak_badges_earned_at_the_right_milestone():
    subject = "handle:streak-badges"
    today = dt.date.today()
    for n in range(6, -1, -1):  # 7 consecutive active days ending today
        _insert_event("daily_queue_generated", subject, day=_days_ago(n, today))
    events = product_events.events_for(subject)
    badges = {b["id"]: b for b in gamification.compute_badges(events)}
    assert "three_day_streak" in badges
    assert "seven_day_streak" in badges
    # three_day milestone must land on day 3 of the run (days_ago(4)), not day 7.
    assert badges["three_day_streak"]["earned_at"].startswith(_days_ago(4, today).isoformat())
    assert badges["seven_day_streak"]["earned_at"].startswith(_days_ago(0, today).isoformat())


def test_all_v1_badges_defined_and_absent_without_qualifying_events():
    events: list = []
    badges = gamification.compute_badges(events)
    assert badges == []
    expected_ids = {
        "first_analysis", "first_queue", "feedback_loop", "three_day_streak",
        "seven_day_streak", "first_weekly_report", "first_verification_attempt", "beta_premium",
    }
    assert {b["id"] for b in gamification.BADGE_DEFS} == expected_ids


# ─── HTTP contract ────────────────────────────────────────────────────────


def test_gamification_me_response_contract(client):
    response = client.get(f"/api/v1/gamification/me?handle={HANDLE}")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
        "subject", "plan", "xp_total", "level", "level_progress", "streak", "daily_goal", "badges",
    }
    assert data["subject"] == f"handle:{HANDLE.lower()}"
    assert data["plan"] == "free"
    assert data["xp_total"] == 0
    assert data["level"] == 1
    assert set(data["level_progress"].keys()) == {"current_level_xp", "next_level_xp", "progress_percent"}
    assert set(data["streak"].keys()) == {"current", "longest", "last_active_date", "today_completed"}
    assert set(data["daily_goal"].keys()) == {"date", "completed", "completed_count", "required_count", "items"}
    assert data["badges"] == []


def test_gamification_me_anonymous_free_subject_works(client):
    response = client.get(f"/api/v1/gamification/me?handle={HANDLE}")
    assert response.status_code == 200
    assert response.json()["plan"] == "free"


def test_gamification_me_without_handle_or_token_returns_empty_snapshot(client):
    response = client.get("/api/v1/gamification/me")
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == "anonymous"
    assert data["xp_total"] == 0
    assert data["badges"] == []


def test_gamification_me_token_premium_subject_works(client):
    user = make_user(client, handle=HANDLE, plan="premium_student")
    response = client.get("/api/v1/gamification/me", headers=bearer(user))
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "premium_student"
    assert data["subject"] == f"user:{user['user_id']}"


def test_gamification_merges_handle_and_linked_user_events(client):
    user = make_user(client, handle=HANDLE, plan="premium_student")  # premium_conversion tracked as user:<id>
    client.post(
        f"/api/v1/weakness/{HANDLE}/analyze", headers=admin()
    )  # first_analysis_completed tracked as handle:<handle>

    response = client.get(f"/api/v1/gamification/me?handle={HANDLE}", headers=bearer(user))
    assert response.status_code == 200
    data = response.json()
    badge_ids = {b["id"] for b in data["badges"]}
    assert "beta_premium" in badge_ids  # from the user:<id> alias
    assert "first_analysis" in badge_ids  # from the handle:<handle> alias
    assert data["plan"] == "premium_student"


def test_gamification_streak_endpoint_shape(client):
    response = client.get(f"/api/v1/gamification/streak?handle={HANDLE}")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"subject", "streak"}
    assert set(data["streak"].keys()) == {"current", "longest", "last_active_date", "today_completed"}


def test_gamification_daily_goal_endpoint_shape(client):
    response = client.get(f"/api/v1/gamification/daily-goal?handle={HANDLE}")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"subject", "daily_goal"}
    assert len(data["daily_goal"]["items"]) == 6


def test_gamification_badges_endpoint_shape(client):
    response = client.get(f"/api/v1/gamification/badges?handle={HANDLE}")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"subject", "badges"}
    assert isinstance(data["badges"], list)


def test_gamification_recompute_is_admin_gated(client):
    assert client.post("/api/v1/gamification/recompute", json={"handle": HANDLE}).status_code == 403
    response = client.post("/api/v1/gamification/recompute", json={"handle": HANDLE}, headers=admin())
    assert response.status_code == 200
    assert response.json()["subject"] == f"handle:{HANDLE.lower()}"


def test_gamification_recompute_requires_a_target(client):
    response = client.post("/api/v1/gamification/recompute", json={}, headers=admin())
    assert response.status_code == 422


def test_gamification_response_has_no_secrets_admin_or_payment_data(client):
    user = make_user(client, handle=HANDLE, plan="premium_student")
    response = client.get(f"/api/v1/gamification/me?handle={HANDLE}", headers=bearer(user))
    raw = json.dumps(response.json()).lower()
    forbidden = [
        "api_token", "token_hash", "password", "secret", "admin_api_key",
        "billing_api_key", "webhook", "payment", "card", "email",
        "hidden_tests", "checker_ref", "source_code",
    ]
    for word in forbidden:
        assert word not in raw, f"forbidden field/word leaked into gamification response: {word}"


def test_gamification_api_failure_mode_is_graceful_for_invalid_handle(client):
    # Too-short handle fails the same validate_handle() every other v1 endpoint
    # uses — the important behavior is a clean 4xx, not a 500 or a crash.
    response = client.get("/api/v1/gamification/me?handle=a")
    assert response.status_code in (400, 422)


# ─── Integration with real endpoints (events fire correctly) ────────────────


def test_daily_queue_generated_event_fires_once_per_day_not_per_call(client):
    from contestiq_api.cfdata import episodes, taxonomy, weakness

    handle = "queue-gamer"
    submissions = []
    sid = 0
    for i in range(10):
        sid += 1
        submissions.append({
            "id": sid, "contestId": 500 + i, "creationTimeSeconds": 1700000000 - i * 86400,
            "problem": {"contestId": 500 + i, "index": "A", "name": f"P{i}", "rating": 1400, "tags": ["greedy"]},
            "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"},
            "programmingLanguage": "GNU C++17", "verdict": "OK",
            "passedTestCount": 3, "timeConsumedMillis": 50, "memoryConsumedBytes": 100,
        })
    store.upsert_user({"handle": handle, "rating": 1400})
    store.upsert_submissions(handle, submissions)
    problems = {f"{500 + i}A": submissions[i]["problem"] for i in range(10)}
    for i in range(10):
        problems[f"{7000 + i}B"] = {"contestId": 7000 + i, "index": "B", "name": f"greedy {i}",
                                     "rating": 1200 + i * 20, "tags": ["greedy"]}
    store.save_problemset_snapshot({"problems": list(problems.values()), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    episodes.rebuild_episodes(handle)
    weakness.analyze_handle_weakness(handle)

    client.post("/api/v1/recommendations/daily", json={"handle": handle, "queue_date": "2026-07-07"}, headers=admin())
    client.post("/api/v1/recommendations/daily", json={"handle": handle, "queue_date": "2026-07-07"}, headers=admin())
    client.post("/api/v1/recommendations/daily", json={"handle": handle, "queue_date": "2026-07-07"}, headers=admin())

    events = product_events.events_for(f"handle:{handle}")
    daily_fires = [e for e in events if e["event_type"] == "daily_queue_generated"]
    assert len(daily_fires) == 1  # reused same-day calls never re-fire it
