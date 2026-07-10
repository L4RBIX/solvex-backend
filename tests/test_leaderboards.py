"""Private weekly leaderboards (Phase G3) tests.

Security hotfix: membership is resolved exclusively from bearer tokens
(never a caller-supplied handle) — see tests/test_identity_security.py for
the dedicated spoofing/authorization regression suite.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from contestiq_api import gamification, leaderboards, product_events
from contestiq_api.cfdata import store
from contestiq_api.identity import account_display_name

ADMIN_KEY = "leaderboards-admin-key"


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
        client.post(
            f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
            json={"plan": plan},
            headers=admin(),
        )
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def _insert_event(event_type: str, subject: str, *, day: dt.date, hour: int = 12) -> None:
    created_at = dt.datetime.combine(day, dt.time(hour, 0), tzinfo=dt.timezone.utc).isoformat()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO product_events (event_id, event_type, subject, properties, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), event_type, subject, "{}", created_at),
        )


TODAY = dt.datetime.now(dt.timezone.utc).date()


# ─── Create / membership ──────────────────────────────────────────────────────


def test_create_leaderboard_with_token_owner_becomes_member(client):
    user = make_user(client)
    response = client.post(
        "/api/v1/leaderboards",
        json={"name": "NIS CP Squad", "display_name": "Owner"},
        headers=bearer(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NIS CP Squad"
    assert "leaderboard_id" in data
    assert "invite_code" in data
    assert len(data["invite_code"]) >= 8

    member = leaderboards.is_member(data["leaderboard_id"], user["user_id"])
    assert member is not None
    assert member["member_role"] == "owner"
    assert member["display_name"] == account_display_name({"user_id": user["user_id"]})


def test_create_leaderboard_requires_auth(client):
    response = client.post(
        "/api/v1/leaderboards", json={"name": "No Auth Squad", "display_name": "Ghost"}
    )
    assert response.status_code == 401


def test_owner_can_create_invite(client):
    user = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Invite Test", "display_name": "Owner"},
        headers=bearer(user),
    ).json()
    response = client.post(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/invites",
        json={"expires_in_days": 7},
        headers=bearer(user),
    )
    assert response.status_code == 200
    assert "invite_code" in response.json()


def test_join_with_invite_code(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Join Test", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()
    invite_code = created["invite_code"]

    member = make_user(client)
    response = client.post(
        "/api/v1/leaderboards/join",
        json={"invite_code": invite_code, "display_name": "Member Two"},
        headers=bearer(member),
    )
    assert response.status_code == 200
    assert response.json()["already_member"] is False
    assert leaderboards.is_member(created["leaderboard_id"], member["user_id"]) is not None


def test_join_requires_auth(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Auth Join", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()

    response = client.post(
        "/api/v1/leaderboards/join",
        json={"invite_code": created["invite_code"], "display_name": "Anon Friend"},
    )
    assert response.status_code == 401


def test_invalid_invite_rejected(client):
    user = make_user(client)
    response = client.post(
        "/api/v1/leaderboards/join",
        json={"invite_code": "totally-bogus-code", "display_name": "X"},
        headers=bearer(user),
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "INVITE_INVALID"


# ─── Authorization ────────────────────────────────────────────────────────────


def test_non_member_cannot_view_weekly(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Private", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()

    outsider = make_user(client)
    response = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly",
        headers=bearer(outsider),
    )
    assert response.status_code == 403


def test_weekly_requires_auth(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Auth Weekly", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()
    response = client.get(f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly")
    assert response.status_code == 401


def test_member_can_view_weekly(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Members Only", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()

    response = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly",
        headers=bearer(owner),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Members Only"
    assert "entries" in data
    assert data["viewer_rank"] == 1


def test_list_leaderboards_for_member_only(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Listed", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()

    listed = client.get("/api/v1/leaderboards", headers=bearer(owner)).json()
    assert any(g["leaderboard_id"] == created["leaderboard_id"] for g in listed["leaderboards"])

    outsider = make_user(client)
    assert client.get("/api/v1/leaderboards", headers=bearer(outsider)).json()["leaderboards"] == []


# ─── Weekly scoring ───────────────────────────────────────────────────────────


def test_weekly_ranking_from_product_events(client):
    owner = make_user(client, plan="premium_student")
    member = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Rank Test", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()
    client.post(
        "/api/v1/leaderboards/join",
        json={"invite_code": created["invite_code"], "display_name": "Member"},
        headers=bearer(member),
    )

    _insert_event("first_analysis_completed", f"user:{owner['user_id']}", day=TODAY, hour=9)
    _insert_event("daily_queue_generated", f"user:{owner['user_id']}", day=TODAY, hour=10)
    _insert_event("feedback_submitted", f"user:{member['user_id']}", day=TODAY, hour=9)

    weekly = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly",
        headers=bearer(owner),
    ).json()
    assert len(weekly["entries"]) == 2
    assert weekly["entries"][0]["weekly_xp"] >= weekly["entries"][1]["weekly_xp"]
    assert weekly["entries"][0]["rank"] == 1
    assert weekly["entries"][0]["active_days"] >= 1


def test_legacy_handle_only_rows_do_not_score_public_events(client):
    """Pre-fix rows have no authenticated account owner. Public handle
    telemetry must not change their score inside a private leaderboard."""
    lb_id = str(uuid.uuid4())
    now = store._now()
    week_start = gamification.week_start_for(TODAY)
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO leaderboard_groups (leaderboard_id, name, owner_subject, visibility, active, created_at)"
            " VALUES (?, 'Tie', 'handle:a', 'private', 1, ?)",
            (lb_id, now),
        )
        conn.execute(
            "INSERT INTO leaderboard_members (leaderboard_id, member_subject, handle, display_name, member_role, joined_at)"
            " VALUES (?, 'handle:a', 'a', 'Alpha', 'owner', ?)",
            (lb_id, now),
        )
        conn.execute(
            "INSERT INTO leaderboard_members (leaderboard_id, member_subject, handle, display_name, member_role, joined_at)"
            " VALUES (?, 'handle:b', 'b', 'Beta', 'member', ?)",
            (lb_id, (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=5)).isoformat()),
        )

    # These public handle events are intentionally ignored for legacy rows.
    _insert_event("feedback_submitted", "handle:a", day=TODAY)
    _insert_event("daily_queue_generated", "handle:a", day=TODAY - dt.timedelta(days=1))
    _insert_event("daily_queue_generated", "handle:b", day=TODAY)
    _insert_event("daily_queue_generated", "handle:b", day=TODAY - dt.timedelta(days=1))

    entries = leaderboards._rank_entries(
        [
            {"member_subject": "handle:a", "handle": "a", "display_name": "Alpha", "joined_at": now, "user_id": None},
            {"member_subject": "handle:b", "handle": "b", "display_name": "Beta",
             "joined_at": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=5)).isoformat(), "user_id": None},
        ],
        week_start,
    )
    assert entries[0]["display_name"] == "Alpha"
    assert entries[0]["weekly_xp"] == entries[1]["weekly_xp"] == 0
    assert entries[0]["active_days"] == entries[1]["active_days"] == 0
    assert entries[0]["feedback_count"] == entries[1]["feedback_count"] == 0


def test_page_views_and_copilot_do_not_count(client):
    with pytest.raises(AssertionError):
        product_events.track("page_view", "handle:x")
    stats = gamification.compute_weekly_stats([], "free")
    assert stats["weekly_xp"] == 0
    assert stats["active_days"] == 0


def test_daily_xp_cap_respected_in_weekly_score():
    subject = "handle:cap-user"
    for event_type in ("first_analysis_completed", "premium_conversion", "verification_attempted"):
        _insert_event(event_type, subject, day=TODAY)
    events = product_events.events_for(subject)
    stats = gamification.compute_weekly_stats(events, "free")
    assert stats["weekly_xp"] == 50  # free cap, not 95 raw


# ─── Response safety ──────────────────────────────────────────────────────────


def test_weekly_response_has_no_secrets(client):
    owner = make_user(client, plan="premium_student")
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Safe", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()
    response = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly",
        headers=bearer(owner),
    )
    raw = json.dumps(response.json()).lower()
    forbidden = [
        "api_token", "token_hash", "invite_code_hash", "password", "secret",
        "admin_api_key", "billing", "payment", "email", "properties",
        "hidden_tests", "checker_ref", owner["api_token"].lower(),
    ]
    for word in forbidden:
        assert word not in raw, f"forbidden leak: {word}"


def test_weekly_entries_never_include_other_members_user_id(client):
    """The internal `user_id` field _rank_entries keeps for viewer-matching
    must never reach the HTTP response — even for a peer member's entry."""
    owner = make_user(client)
    member = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "No Leak", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()
    client.post(
        "/api/v1/leaderboards/join",
        json={"invite_code": created["invite_code"], "display_name": "Member"},
        headers=bearer(member),
    )
    weekly = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly", headers=bearer(owner)
    ).json()
    for entry in weekly["entries"]:
        assert "user_id" not in entry


def test_invite_code_hash_not_stored_retrievable(client):
    owner = make_user(client)
    created = client.post(
        "/api/v1/leaderboards",
        json={"name": "Hash", "display_name": "Owner"},
        headers=bearer(owner),
    ).json()
    with store.connect() as conn:
        rows = conn.execute("SELECT invite_code_hash FROM leaderboard_invites").fetchall()
    assert all(r["invite_code_hash"] != created["invite_code"] for r in rows)
    assert all(len(r["invite_code_hash"]) == 64 for r in rows)
