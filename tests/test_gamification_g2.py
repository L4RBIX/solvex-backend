"""Gamification Phase G2 tests: XP transparency (recent_xp_events), daily and
weekly quests, milestone progress, and badge details (category/rarity).

Design invariants under test:
- recent_xp_events per-event attribution always sums to compute_xp_total
  (same once-per-type-per-day rule, same daily cap), so the breakdown can
  never contradict the headline XP number.
- Quests are progress UI only, derived from the same product_events — they
  award no XP of their own and therefore cannot double-award or bypass caps.
- No raw product_event `properties` payload is ever exposed.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from contestiq_api import gamification, product_events
from contestiq_api.cfdata import store

ADMIN_KEY = "gamification-g2-admin-key"
HANDLE = "Quest-Runner"


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


def _insert_event(event_type: str, subject: str, *, day: dt.date, hour: int = 12,
                  properties: dict | None = None) -> None:
    created_at = dt.datetime.combine(day, dt.time(hour, 0), tzinfo=dt.timezone.utc).isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO product_events (event_id, event_type, subject, properties, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), event_type, subject, json.dumps(properties or {}), created_at),
        )


# UTC date, matching build_snapshot's internal clock (local tz may be a day ahead).
TODAY = dt.datetime.now(dt.timezone.utc).date()
WEEK_START = gamification.week_start_for(TODAY)


# ─── recent_xp_events ─────────────────────────────────────────────────────────


def test_recent_xp_events_shape_and_labels():
    subject = "handle:activity-shape"
    _insert_event("first_analysis_completed", subject, day=TODAY, hour=9)
    _insert_event("daily_queue_generated", subject, day=TODAY, hour=10)
    events = product_events.events_for(subject)

    recent = gamification.compute_recent_xp_events(events, daily_cap=1000)
    assert len(recent) == 2
    # Most recent first.
    assert recent[0]["event_type"] == "daily_queue_generated"
    assert recent[0]["label"] == "Generated today's queue"
    assert recent[0]["xp_awarded"] == 5
    assert recent[0]["daily_cap_applied"] is False
    assert recent[0]["occurred_at"].startswith(TODAY.isoformat())
    assert recent[1]["event_type"] == "first_analysis_completed"
    assert recent[1]["label"] == "Completed first analysis"
    assert recent[1]["xp_awarded"] == 20
    assert set(recent[0].keys()) == {"event_type", "label", "xp_awarded", "occurred_at", "daily_cap_applied"}


def test_recent_xp_events_daily_cap_is_visible():
    subject = "handle:activity-cap"
    # Free cap = 50. premium_conversion (50) exhausts it; the later analysis
    # event awards 0 and must be flagged as cap-limited.
    _insert_event("premium_conversion", subject, day=TODAY, hour=8)
    _insert_event("first_analysis_completed", subject, day=TODAY, hour=9)
    events = product_events.events_for(subject)

    recent = gamification.compute_recent_xp_events(events, daily_cap=50)
    by_type = {e["event_type"]: e for e in recent}
    assert by_type["premium_conversion"]["xp_awarded"] == 50
    assert by_type["premium_conversion"]["daily_cap_applied"] is False
    assert by_type["first_analysis_completed"]["xp_awarded"] == 0
    assert by_type["first_analysis_completed"]["daily_cap_applied"] is True


def test_recent_xp_events_partial_cap_award_is_flagged():
    subject = "handle:activity-partial"
    # 20 + 25 = 45 already awarded; premium_conversion (raw 50) only gets 5.
    _insert_event("first_analysis_completed", subject, day=TODAY, hour=8)
    _insert_event("verification_attempted", subject, day=TODAY, hour=9)
    _insert_event("premium_conversion", subject, day=TODAY, hour=10)
    events = product_events.events_for(subject)

    recent = gamification.compute_recent_xp_events(events, daily_cap=50)
    premium = next(e for e in recent if e["event_type"] == "premium_conversion")
    assert premium["xp_awarded"] == 5
    assert premium["daily_cap_applied"] is True


def test_recent_xp_events_repeat_same_day_awards_zero_without_cap_flag():
    subject = "handle:activity-repeat"
    _insert_event("feedback_submitted", subject, day=TODAY, hour=8)
    _insert_event("feedback_submitted", subject, day=TODAY, hour=9)
    events = product_events.events_for(subject)

    recent = gamification.compute_recent_xp_events(events, daily_cap=50)
    assert recent[0]["xp_awarded"] == 0  # the repeat (most recent)
    assert recent[0]["daily_cap_applied"] is False  # anti-farming rule, not the cap
    assert recent[1]["xp_awarded"] == 5


def test_recent_xp_events_sum_matches_xp_total():
    subject = "handle:activity-sum"
    for n, event_type in enumerate(
        ("first_analysis_completed", "daily_queue_generated", "feedback_submitted",
         "premium_conversion", "weekly_report_generated")
    ):
        _insert_event(event_type, subject, day=TODAY - dt.timedelta(days=n % 2), hour=8 + n)
    events = product_events.events_for(subject)

    for cap in (50, 150, 1000):
        recent = gamification.compute_recent_xp_events(events, daily_cap=cap, limit=100)
        assert sum(e["xp_awarded"] for e in recent) == gamification.compute_xp_total(events, daily_cap=cap)


def test_recent_xp_events_limited_to_last_ten():
    subject = "handle:activity-limit"
    for n in range(15):
        _insert_event("daily_queue_generated", subject, day=TODAY - dt.timedelta(days=n))
    events = product_events.events_for(subject)
    recent = gamification.compute_recent_xp_events(events, daily_cap=50)
    assert len(recent) == 10
    # Most recent first: entry 0 is today.
    assert recent[0]["occurred_at"].startswith(TODAY.isoformat())


def test_recent_xp_events_do_not_expose_event_properties():
    subject = "handle:activity-secrets"
    _insert_event("premium_conversion", subject, day=TODAY,
                  properties={"provider_ref": "internal-billing-id-123", "amount": 999})
    events = product_events.events_for(subject)
    recent = gamification.compute_recent_xp_events(events, daily_cap=50)
    raw = json.dumps(recent)
    assert "internal-billing-id-123" not in raw
    assert "properties" not in raw
    assert "999" not in raw


# ─── Daily quests ─────────────────────────────────────────────────────────────


def test_daily_quests_computed_from_product_events():
    subject = "handle:daily-quests"
    _insert_event("daily_queue_generated", subject, day=TODAY, hour=9)
    _insert_event("feedback_submitted", subject, day=TODAY, hour=10)
    _insert_event("weekly_report_generated", subject, day=TODAY - dt.timedelta(days=1))  # yesterday: must not count
    events = product_events.events_for(subject)

    quests = gamification.compute_daily_quests(events, today=TODAY)
    assert quests["date"] == TODAY.isoformat()
    assert quests["total_count"] == 6
    assert quests["completed_count"] == 2
    by_id = {q["id"]: q for q in quests["quests"]}
    assert by_id["generate_queue_today"]["completed"] is True
    assert by_id["generate_queue_today"]["completed_at"].startswith(TODAY.isoformat())
    assert by_id["submit_feedback_today"]["completed"] is True
    assert by_id["view_weekly_report_today"]["completed"] is False  # yesterday's report doesn't count today
    assert by_id["view_weekly_report_today"]["completed_at"] is None
    assert set(by_id) == {
        "complete_analysis_today", "generate_queue_today", "submit_feedback_today",
        "view_weekly_report_today", "start_plan_today", "attempt_verification_today",
    }


def test_daily_quests_empty_history():
    quests = gamification.compute_daily_quests([], today=TODAY)
    assert quests["completed_count"] == 0
    assert all(not q["completed"] for q in quests["quests"])


# ─── Weekly quests ────────────────────────────────────────────────────────────


def test_weekly_quests_computed_from_product_events():
    subject = "handle:weekly-quests"
    # Two distinct active days this week with queue events.
    _insert_event("daily_queue_generated", subject, day=WEEK_START, hour=9)
    _insert_event("daily_queue_generated", subject, day=TODAY, hour=9)
    _insert_event("weekly_report_generated", subject, day=TODAY, hour=10)
    events = product_events.events_for(subject)

    weekly = gamification.compute_weekly_quests(events, today=TODAY)
    assert weekly["week_start"] == WEEK_START.isoformat()
    assert weekly["total_count"] == 5
    by_id = {q["id"]: q for q in weekly["quests"]}

    expected_days = len({WEEK_START, TODAY})  # 1 if today IS week start, else 2
    assert by_id["active_3_days_this_week"]["progress"] == expected_days
    assert by_id["active_3_days_this_week"]["target"] == 3
    assert by_id["active_3_days_this_week"]["completed"] is False
    assert by_id["complete_3_queues_this_week"]["progress"] == expected_days
    assert by_id["complete_weekly_report"]["completed"] is True
    assert by_id["complete_weekly_report"]["progress"] == 1
    assert by_id["submit_3_feedback_this_week"]["progress"] == 0
    assert by_id["attempt_one_verification"]["completed"] is False


def test_weekly_quests_regenerating_same_day_queue_does_not_farm_progress():
    subject = "handle:weekly-farm"
    for _ in range(5):
        _insert_event("daily_queue_generated", subject, day=TODAY)
    events = product_events.events_for(subject)
    weekly = gamification.compute_weekly_quests(events, today=TODAY)
    by_id = {q["id"]: q for q in weekly["quests"]}
    assert by_id["complete_3_queues_this_week"]["progress"] == 1  # distinct days, not raw calls
    assert by_id["active_3_days_this_week"]["progress"] == 1


def test_weekly_quests_ignore_last_weeks_events():
    subject = "handle:weekly-window"
    _insert_event("daily_queue_generated", subject, day=WEEK_START - dt.timedelta(days=1))
    events = product_events.events_for(subject)
    weekly = gamification.compute_weekly_quests(events, today=TODAY)
    assert all(q["progress"] == 0 for q in weekly["quests"])


def test_quests_do_not_award_xp():
    """Quests are UI only: completing every daily+weekly quest changes XP only
    through the underlying product events, never additionally."""
    subject = "handle:no-double-award"
    for event_type in ("first_analysis_completed", "daily_queue_generated", "feedback_submitted",
                       "weekly_report_generated", "plan_started", "verification_attempted"):
        _insert_event(event_type, subject, day=TODAY)
    events = product_events.events_for(subject)

    snapshot = gamification.build_snapshot(subject, "premium_student", events)
    assert snapshot["daily_quests"]["completed_count"] == 6
    # XP == the plain event-rule sum (20+5+5+20+15+25 = 90), nothing extra for quests.
    assert snapshot["xp_total"] == gamification.compute_xp_total(events, daily_cap=150) == 90


# ─── Badge details ────────────────────────────────────────────────────────────


def test_badge_details_include_category_rarity_and_earned_at():
    subject = "handle:badge-details"
    _insert_event("first_analysis_completed", subject, day=TODAY)
    _insert_event("premium_conversion", subject, day=TODAY)
    events = product_events.events_for(subject)

    badges = {b["id"]: b for b in gamification.compute_badges(events)}
    assert badges["first_analysis"]["category"] == "onboarding"
    assert badges["first_analysis"]["rarity"] == "common"
    assert badges["first_analysis"]["earned_at"].startswith(TODAY.isoformat())
    assert badges["beta_premium"]["category"] == "premium"
    assert badges["beta_premium"]["rarity"] == "rare"


def test_all_badge_defs_have_valid_category_and_rarity():
    valid_categories = {"onboarding", "consistency", "verification", "premium"}
    valid_rarities = {"common", "uncommon", "rare"}
    for badge in gamification.BADGE_DEFS:
        assert badge["category"] in valid_categories, badge["id"]
        assert badge["rarity"] in valid_rarities, badge["id"]


# ─── Milestones ───────────────────────────────────────────────────────────────


def test_milestones_progress_is_correct():
    subject = "handle:milestones"
    # 120 XP today under the premium cap: 20 + 50 + 25 + 20 + 5 = 120.
    for event_type in ("first_analysis_completed", "premium_conversion", "verification_attempted",
                       "weekly_report_generated", "daily_queue_generated"):
        _insert_event(event_type, subject, day=TODAY)
    events = product_events.events_for(subject)

    snapshot = gamification.build_snapshot(subject, "premium_student", events)
    assert snapshot["xp_total"] == 120
    milestones = {m["id"]: m for m in snapshot["milestones"]}

    assert milestones["next_level"]["label"] == "Reach Level 3"
    assert milestones["next_level"]["progress"] == 120
    assert milestones["next_level"]["target"] == 250

    assert milestones["next_streak_badge"]["label"] == "Reach a 3-day streak"
    assert milestones["next_streak_badge"]["progress"] == 1
    assert milestones["next_streak_badge"]["target"] == 3

    # Daily goal is already complete (5 categories today) so it is omitted.
    assert "next_daily_goal" not in milestones

    # First incomplete weekly quest surfaces as the weekly milestone.
    assert milestones["next_weekly_quest"]["target"] >= 1


def test_milestones_include_daily_goal_when_incomplete():
    subject = "handle:milestone-goal"
    _insert_event("daily_queue_generated", subject, day=TODAY)  # 1 of 2 goal categories
    events = product_events.events_for(subject)
    snapshot = gamification.build_snapshot(subject, "free", events)
    milestones = {m["id"]: m for m in snapshot["milestones"]}
    assert milestones["next_daily_goal"]["progress"] == 1
    assert milestones["next_daily_goal"]["target"] == 2


def test_milestones_streak_target_moves_to_seven_after_three():
    subject = "handle:milestone-streak"
    for n in (2, 1, 0):
        _insert_event("daily_queue_generated", subject, day=TODAY - dt.timedelta(days=n))
    events = product_events.events_for(subject)
    snapshot = gamification.build_snapshot(subject, "free", events)
    streak_milestone = next(m for m in snapshot["milestones"] if m["id"] == "next_streak_badge")
    assert streak_milestone["label"] == "Reach a 7-day streak"
    assert streak_milestone["progress"] == 3
    assert streak_milestone["target"] == 7


# ─── HTTP contract ────────────────────────────────────────────────────────────


def test_me_includes_g2_fields_and_stays_backward_compatible(client):
    user = make_user(client)
    response = client.get("/api/v1/gamification/me", headers=bearer(user))
    assert response.status_code == 200
    data = response.json()
    # G1 fields untouched.
    for key in ("subject", "plan", "xp_total", "level", "level_progress", "streak", "daily_goal", "badges"):
        assert key in data
    # G2 fields present.
    assert data["recent_xp_events"] == []
    assert data["daily_quests"]["total_count"] == 6
    assert data["weekly_quests"]["total_count"] == 5
    assert isinstance(data["milestones"], list)
    assert data["milestones"][0]["id"] == "next_level"


def test_gamification_g2_endpoints_require_auth(client):
    assert client.get("/api/v1/gamification/me").status_code == 401
    assert client.get("/api/v1/gamification/activity").status_code == 401
    assert client.get("/api/v1/gamification/quests").status_code == 401


def test_activity_endpoint_shape(client):
    user = make_user(client)
    response = client.get("/api/v1/gamification/activity", headers=bearer(user))
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"subject", "recent_xp_events"}


def test_quests_endpoint_shape(client):
    user = make_user(client)
    response = client.get("/api/v1/gamification/quests", headers=bearer(user))
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"subject", "daily_quests", "weekly_quests", "milestones"}
    assert {q["id"] for q in data["daily_quests"]["quests"]} == {
        "complete_analysis_today", "generate_queue_today", "submit_feedback_today",
        "view_weekly_report_today", "start_plan_today", "attempt_verification_today",
    }
    assert {q["id"] for q in data["weekly_quests"]["quests"]} == {
        "active_3_days_this_week", "complete_3_queues_this_week", "submit_3_feedback_this_week",
        "complete_weekly_report", "attempt_one_verification",
    }


def test_premium_token_user_gets_g2_fields(client):
    user = make_user(client, handle=HANDLE, plan="premium_student")
    response = client.get("/api/v1/gamification/me", headers=bearer(user))
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "premium_student"
    # premium_conversion fired on grant → appears in the XP breakdown.
    types = {e["event_type"] for e in data["recent_xp_events"]}
    assert "premium_conversion" in types


def test_invalid_token_does_not_crash_g2_response(client):
    response = client.get(
        "/api/v1/gamification/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    # Current auth behavior must remain unchanged: invalid bearer tokens return
    # a clean 401 (same as /api/v1/me/entitlements), not a 500 or crash.
    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "INVALID_TOKEN"


def test_g2_response_has_no_secrets_admin_or_payment_data(client):
    user = make_user(client, handle=HANDLE, plan="premium_student")
    response = client.get("/api/v1/gamification/me", headers=bearer(user))
    raw = json.dumps(response.json()).lower()
    forbidden = [
        "api_token", "token_hash", "password", "secret", "admin_api_key",
        "billing_api_key", "webhook", "payment", "card", "email",
        "hidden_tests", "checker_ref", "source_code", "properties",
        user["api_token"].lower(),
    ]
    for word in forbidden:
        assert word not in raw, f"forbidden field/word leaked into G2 gamification response: {word}"
