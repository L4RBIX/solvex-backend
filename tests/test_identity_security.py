"""Critical security fix: a Codeforces handle is PUBLIC data and must never
be treated as authentication.

Before this fix, `?handle=<anything>` (or a body `handle` field) was accepted
as identity for creating/joining PvP duels, reading private leaderboard/
gamification data, and earning XP — anyone could open another person's
handle and act as them. This file is the dedicated regression suite for the
fix: authenticated identity now comes ONLY from a validated bearer token
(auth.require_user / auth.require_user_subject), and a Codeforces handle
carries authorization weight only after explicit ownership verification
(contestiq_api.handles).
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from contestiq_api import handles, product_events
from contestiq_api.cfdata import store, taxonomy

ADMIN_KEY = "identity-security-admin-key"


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


@pytest.fixture
def catalog():
    problems = []
    for i, rating in enumerate([1000, 1100, 1200, 1300, 1400]):
        problems.append({
            "contestId": 9000 + i,
            "index": "A",
            "name": f"Identity Prob {i}",
            "rating": rating,
            "tags": ["greedy" if i % 2 == 0 else "math"],
        })
    store.save_problemset_snapshot({"problems": problems, "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    return problems


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client, handle=None, plan=None):
    user = client.post("/api/v1/admin/users", json={"handle": handle}, headers=admin()).json()
    if plan:
        client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement", json={"plan": plan}, headers=admin())
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def register(client):
    """Self-service account creation — the only way an ordinary end user
    (not an admin) can obtain a bearer token."""
    return client.post("/api/v1/auth/register").json()


# ─── Self-service registration (new — no more admin-only tokens) ────────────


def test_register_returns_a_usable_bearer_token(client):
    user = register(client)
    assert "api_token" in user
    assert "user_id" in user
    me = client.get("/api/v1/auth/me", headers=bearer(user))
    assert me.status_code == 200
    assert me.json()["user_id"] == user["user_id"]
    assert me.json()["handle"] is None
    assert me.json()["handle_verified"] is False


def test_register_does_not_require_or_accept_a_handle_as_identity(client):
    # No endpoint parameter exists for the caller to assert their own handle
    # at registration time — identity starts as a bare, handle-less account.
    response = client.post("/api/v1/auth/register")
    assert response.status_code == 200
    assert response.json().get("handle") is None


def test_invalid_bearer_token_is_rejected(client):
    response = client.get(
        "/api/v1/gamification/me",
        headers={"Authorization": "Bearer invalid-account-token"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


def test_handle_claim_routes_require_authentication(client):
    assert client.post("/api/v1/handles/claim", json={"handle": "auth-required"}).status_code == 401
    assert client.post("/api/v1/handles/claim/missing/verify").status_code == 401
    assert client.get("/api/v1/handles/me").status_code == 401


# ─── 1. Unauthenticated user cannot create/join/start/submit duel ───────────


def test_unauthenticated_cannot_create_duel(client, catalog):
    response = client.post("/api/v1/duels", json={"mode": "rapid_10", "display_name": "Ghost"})
    assert response.status_code == 401


def test_unauthenticated_cannot_join_duel(client, catalog):
    creator = register(client)
    created = client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "Creator"}, headers=bearer(creator)
    ).json()
    response = client.post(
        "/api/v1/duels/join", json={"invite_code": created["invite_code"], "display_name": "Ghost"}
    )
    assert response.status_code == 401


def test_unauthenticated_cannot_ready_start_or_submit_duel(client, catalog):
    creator = register(client)
    challenger = register(client)
    created = client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "Creator"}, headers=bearer(creator)
    ).json()
    client.post(
        "/api/v1/duels/join",
        json={"invite_code": created["invite_code"], "display_name": "Challenger"},
        headers=bearer(challenger),
    )
    duel_id = created["duel_id"]
    assert client.post(f"/api/v1/duels/{duel_id}/ready").status_code == 401
    assert client.post(f"/api/v1/duels/{duel_id}/start").status_code == 401
    assert client.post(
        f"/api/v1/duels/{duel_id}/submit",
        json={"language": "python3", "source_code": "print(1)", "expected_output": "1"},
    ).status_code == 401
    assert client.get(f"/api/v1/duels/{duel_id}").status_code == 401
    assert client.get(f"/api/v1/duels/{duel_id}/state").status_code == 401
    assert client.get(f"/api/v1/duels/{duel_id}/result").status_code == 401
    assert client.post(f"/api/v1/duels/{duel_id}/hint").status_code == 401
    assert client.post(f"/api/v1/duels/{duel_id}/open-arena").status_code == 401
    assert client.get("/api/v1/duels").status_code == 401


# ─── 2. User A cannot act as user B by passing B's handle ───────────────────


def test_creating_duel_with_victims_handle_does_not_impersonate_them(client, catalog):
    """The classic exploit: attacker passes the victim's public CF handle,
    hoping to be treated as them. The route no longer even accepts a handle
    parameter for this purpose — the duel is created under the attacker's
    OWN account regardless of what handle string they attach."""
    victim = make_user(client, handle="famous-cf-grandmaster")
    attacker = register(client)

    response = client.post(
        "/api/v1/duels?handle=famous-cf-grandmaster",
        json={"mode": "rapid_10", "display_name": "famous-cf-grandmaster (totally legit)"},
        headers=bearer(attacker),
    )
    assert response.status_code == 200
    created = response.json()

    detail = client.get(f"/api/v1/duels/{created['duel_id']}", headers=bearer(attacker)).json()
    me = next(p for p in detail["participants"] if p["is_viewer"])
    assert me["handle"] is None  # attacker never verified the victim's handle
    assert me["display_name"].startswith("SolveX Player ")
    assert "famous-cf-grandmaster" not in me["display_name"].lower()
    with store.connect() as conn:
        row = conn.execute(
            "SELECT creator_user_id, creator_handle FROM duel_matches WHERE duel_id = ?", (created["duel_id"],)
        ).fetchone()
    assert row["creator_user_id"] == attacker["user_id"]
    assert row["creator_user_id"] != victim["user_id"]
    assert row["creator_handle"] != "famous-cf-grandmaster"


def test_joining_duel_with_victims_handle_in_body_does_not_impersonate_them(client, catalog):
    creator = register(client)
    victim = make_user(client, handle="another-real-person")
    attacker = register(client)
    created = client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "Creator"}, headers=bearer(creator)
    ).json()

    # Extra "handle" field in the body is not part of the schema anymore —
    # even if sent, it must be ignored for authorization.
    response = client.post(
        "/api/v1/duels/join",
        json={
            "invite_code": created["invite_code"],
            "display_name": "Impersonator",
            "handle": "another-real-person",
        },
        headers=bearer(attacker),
    )
    assert response.status_code == 200
    with store.connect() as conn:
        row = conn.execute(
            "SELECT user_id, handle, display_name FROM duel_participants WHERE duel_id = ? AND role = 'challenger'",
            (created["duel_id"],),
        ).fetchone()
    assert row["user_id"] == attacker["user_id"]
    assert row["user_id"] != victim["user_id"]
    assert row["handle"] != "another-real-person"
    assert row["display_name"] != "Impersonator"

    replay = client.post(
        "/api/v1/duels/join",
        json={
            "invite_code": created["invite_code"],
            "display_name": "A second fake identity",
            "handle": "yet-another-handle",
        },
        headers=bearer(attacker),
    )
    assert replay.status_code == 200
    assert replay.json()["already_member"] is True
    with store.connect() as conn:
        participant_count = conn.execute(
            "SELECT COUNT(*) FROM duel_participants WHERE duel_id = ?",
            (created["duel_id"],),
        ).fetchone()[0]
    assert participant_count == 2


def test_creating_leaderboard_with_victims_handle_does_not_impersonate_them(client):
    victim = make_user(client, handle="leaderboard-victim")
    attacker = register(client)
    response = client.post(
        "/api/v1/leaderboards?handle=leaderboard-victim",
        json={"name": "Impersonation Attempt", "display_name": "Not The Victim"},
        headers=bearer(attacker),
    )
    assert response.status_code == 200
    data = response.json()
    assert "owner_subject" not in data  # internal user ids never cross the API boundary
    with store.connect() as conn:
        owner = conn.execute(
            "SELECT owner_user_id, owner_subject FROM leaderboard_groups WHERE leaderboard_id = ?",
            (data["leaderboard_id"],),
        ).fetchone()
    assert owner["owner_user_id"] == attacker["user_id"]
    assert owner["owner_user_id"] != victim["user_id"]
    assert owner["owner_subject"] == f"user:{attacker['user_id']}"
    with store.connect() as conn:
        member = conn.execute(
            "SELECT display_name FROM leaderboard_members WHERE leaderboard_id = ? AND user_id = ?",
            (data["leaderboard_id"], attacker["user_id"]),
        ).fetchone()
    assert member["display_name"].startswith("SolveX Player ")
    assert member["display_name"] != "Not The Victim"


# ─── 3. User A cannot read user B's private duel state ──────────────────────


def test_user_a_cannot_read_user_b_private_duel_state(client, catalog):
    user_a = register(client)
    user_b = register(client)
    user_b_friend = register(client)

    # B's own private duel — A is not a participant.
    b_duel = client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "B"}, headers=bearer(user_b)
    ).json()
    client.post(
        "/api/v1/duels/join",
        json={"invite_code": b_duel["invite_code"], "display_name": "B's friend"},
        headers=bearer(user_b_friend),
    )

    assert client.get(f"/api/v1/duels/{b_duel['duel_id']}", headers=bearer(user_a)).status_code == 403
    assert client.get(f"/api/v1/duels/{b_duel['duel_id']}/state", headers=bearer(user_a)).status_code == 403
    assert client.post(f"/api/v1/duels/{b_duel['duel_id']}/ready", headers=bearer(user_a)).status_code == 403
    assert client.post(f"/api/v1/duels/{b_duel['duel_id']}/hint", headers=bearer(user_a)).status_code == 403
    assert client.post(
        f"/api/v1/duels/{b_duel['duel_id']}/submit",
        json={"language": "python3", "source_code": "print(1)", "expected_output": "1"},
        headers=bearer(user_a),
    ).status_code == 403

    # Passing B's handle/user_id as a query param must not grant access either
    # — these routes don't even accept such a parameter anymore.
    assert client.get(
        f"/api/v1/duels/{b_duel['duel_id']}?handle=b&user_id={user_b['user_id']}", headers=bearer(user_a)
    ).status_code == 403


# ─── 4. User A cannot read user B's private gamification ────────────────────


def test_user_a_cannot_read_user_b_private_gamification(client):
    user_a = register(client)
    user_b = make_user(client, plan="premium_student")  # generates premium_conversion XP for B

    response = client.get("/api/v1/gamification/me", headers=bearer(user_a))
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == f"user:{user_a['user_id']}"
    assert data["xp_total"] == 0  # none of B's XP leaked to A
    assert data["plan"] == "free"  # not B's premium_student plan

    # No parameter lets A target B's data — extra/unknown query params are
    # simply ignored, never used for identity resolution.
    spoof_attempt = client.get(
        f"/api/v1/gamification/me?handle=whatever&user_id={user_b['user_id']}", headers=bearer(user_a)
    )
    assert spoof_attempt.json()["subject"] == f"user:{user_a['user_id']}"
    assert spoof_attempt.json()["xp_total"] == 0


def test_verified_alias_merges_only_pre_verification_history(client):
    user = register(client)
    handle = "historical-owner"
    product_events.track("first_analysis_completed", f"handle:{handle}")
    handles.admin_bind(user["user_id"], handle)

    # Anyone can still invoke public handle actions. Events written to the
    # public alias after ownership was established must not alter private XP.
    product_events.track("daily_queue_generated", f"handle:{handle}")
    snapshot = client.get("/api/v1/gamification/me", headers=bearer(user)).json()
    assert snapshot["xp_total"] == 20
    assert {event["label"] for event in snapshot["recent_xp_events"]} == {"Completed first analysis"}

    # Authenticated account activity remains eligible.
    product_events.track("daily_queue_generated", f"user:{user['user_id']}")
    snapshot = client.get("/api/v1/gamification/me", headers=bearer(user)).json()
    assert snapshot["xp_total"] == 25


def test_verified_handle_alias_cannot_authorize_legacy_leaderboard_row(client):
    owner = register(client)
    group = client.post(
        "/api/v1/leaderboards",
        json={"name": "Legacy Alias Isolation"},
        headers=bearer(owner),
    ).json()
    outsider = register(client)
    handles.admin_bind(outsider["user_id"], "legacy-member")
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO leaderboard_members"
            " (leaderboard_id, member_subject, user_id, handle, display_name, member_role, joined_at)"
            " VALUES (?, ?, NULL, ?, ?, 'member', ?)",
            (
                group["leaderboard_id"],
                "handle:legacy-member",
                "legacy-member",
                "Legacy Member",
                store._now(),
            ),
        )

    response = client.get(
        f"/api/v1/leaderboards/{group['leaderboard_id']}/weekly",
        headers=bearer(outsider),
    )
    assert response.status_code == 403


# ─── 5. Unverified user cannot earn XP for a public handle ──────────────────


def test_unverified_user_cannot_earn_xp_for_a_public_handle(client):
    famous_handle = "public-figure-handle"
    # Public, unauthenticated analysis of a real CF handle — anyone can do
    # this, and it is intentionally NOT gated (Phase security-hotfix req. 1).
    client.post(f"/api/v1/weakness/{famous_handle}/analyze")

    attacker = register(client)  # never verified famous_handle
    snapshot = client.get("/api/v1/gamification/me", headers=bearer(attacker)).json()
    assert snapshot["xp_total"] == 0
    badge_ids = {b["id"] for b in snapshot["badges"]}
    assert "first_analysis" not in badge_ids


# ─── 6. Verified owner can use their handle ──────────────────────────────────


def test_verified_owner_can_use_their_handle_end_to_end(client):
    user = register(client)
    claim = client.post(
        "/api/v1/handles/claim", json={"handle": "real-owner-handle"}, headers=bearer(user)
    ).json()
    assert claim["already_verified"] is False
    assert claim["verification_code"].startswith("solvex-verify-")

    with patch(
        "contestiq_core.codeforces.client.fetch_user_info",
        return_value={"handle": "real-owner-handle", "organization": claim["verification_code"]},
    ) as fetch_user_info:
        result = client.post(
            f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user)
        )
    assert result.status_code == 200
    assert result.json()["verified"] is True
    assert "verification_code" not in result.json()
    fetch_user_info.assert_called_once_with("real-owner-handle", use_cache=False)

    me = client.get("/api/v1/auth/me", headers=bearer(user)).json()
    assert me["handle"] == "real-owner-handle"
    assert me["handle_verified"] is True
    claims_view = client.get("/api/v1/handles/me", headers=bearer(user)).json()
    assert claims_view["claims"][0]["status"] == handles.STATUS_VERIFIED
    assert "verification_code" not in json.dumps(claims_view)
    assert handles.owner_user_id_for_handle("real-owner-handle") == user["user_id"]
    with store.connect() as conn:
        stored = conn.execute(
            "SELECT status, verification_code FROM handle_claims WHERE claim_id = ?",
            (claim["claim_id"],),
        ).fetchone()
    assert stored["status"] == handles.STATUS_VERIFIED
    assert stored["verification_code"] == ""


def test_verify_fails_when_cf_fetch_errors(client):
    from contestiq_core.codeforces.client import CodeforcesAPIError

    user = register(client)
    claim = client.post("/api/v1/handles/claim", json={"handle": "unreachable-handle"}, headers=bearer(user)).json()
    with patch(
        "contestiq_core.codeforces.client.fetch_user_info",
        side_effect=CodeforcesAPIError("Codeforces handle not found: unreachable-handle"),
    ):
        result = client.post(f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user))
    assert result.status_code == 502


# ─── 7. Duplicate claim rejected ─────────────────────────────────────────────


def test_duplicate_claim_rejected(client):
    owner = register(client)
    handles.admin_bind(owner["user_id"], "contested-handle")  # already verified by owner

    challenger = register(client)
    response = client.post(
        "/api/v1/handles/claim", json={"handle": "contested-handle"}, headers=bearer(challenger)
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "HANDLE_ALREADY_CLAIMED"


def test_second_verified_claim_on_same_handle_rejected_even_mid_flow(client):
    """Even if a second user starts a claim before the first completes, the
    verification step itself must reject once someone else already owns it."""
    first = register(client)
    second = register(client)

    first_claim = client.post(
        "/api/v1/handles/claim", json={"handle": "race-handle"}, headers=bearer(first)
    ).json()
    second_claim_response = client.post(
        "/api/v1/handles/claim", json={"handle": "race-handle"}, headers=bearer(second)
    )
    assert second_claim_response.status_code == 200
    second_claim = second_claim_response.json()
    with patch(
        "contestiq_core.codeforces.client.fetch_user_info",
        return_value={"handle": "race-handle", "organization": first_claim["verification_code"]},
    ):
        assert client.post(
            f"/api/v1/handles/claim/{first_claim['claim_id']}/verify", headers=bearer(first)
        ).status_code == 200

    response = client.post(
        f"/api/v1/handles/claim/{second_claim['claim_id']}/verify", headers=bearer(second)
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "HANDLE_ALREADY_CLAIMED"


# ─── 8. Expired/incorrect verification code rejected ─────────────────────────


def test_incorrect_verification_code_rejected(client):
    user = register(client)
    claim = client.post("/api/v1/handles/claim", json={"handle": "mismatch-handle"}, headers=bearer(user)).json()
    with patch(
        "contestiq_core.codeforces.client.fetch_user_info",
        return_value={"handle": "mismatch-handle", "organization": "not-the-right-code"},
    ):
        response = client.post(f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user))
    assert response.status_code == 422
    assert response.json()["error_code"] == "VERIFICATION_CODE_MISMATCH"
    assert handles.owner_user_id_for_handle("mismatch-handle") is None


def test_expired_verification_code_rejected(client):
    user = register(client)
    claim = client.post("/api/v1/handles/claim", json={"handle": "expired-handle"}, headers=bearer(user)).json()
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE handle_claims SET expires_at = ? WHERE claim_id = ?", (past, claim["claim_id"]))

    with patch(
        "contestiq_core.codeforces.client.fetch_user_info",
        return_value={"handle": "expired-handle", "organization": claim["verification_code"]},
    ):
        response = client.post(f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user))
    assert response.status_code == 410
    assert response.json()["error_code"] == "CLAIM_EXPIRED"
    assert handles.owner_user_id_for_handle("expired-handle") is None
    with store.connect() as conn:
        stored = conn.execute(
            "SELECT status, verification_code FROM handle_claims WHERE claim_id = ?",
            (claim["claim_id"],),
        ).fetchone()
    assert stored["status"] == handles.STATUS_EXPIRED
    assert stored["verification_code"] == ""


def test_handles_me_sweeps_expired_claim_and_verify_does_not_fetch_cf(client):
    user = register(client)
    claim = client.post(
        "/api/v1/handles/claim", json={"handle": "swept-expired-handle"}, headers=bearer(user)
    ).json()
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE handle_claims SET expires_at = ? WHERE claim_id = ?", (past, claim["claim_id"]))

    claims_view = client.get("/api/v1/handles/me", headers=bearer(user)).json()
    assert claims_view["claims"][0]["status"] == handles.STATUS_EXPIRED
    assert "verification_code" not in json.dumps(claims_view)
    with store.connect() as conn:
        stored = conn.execute(
            "SELECT verification_code FROM handle_claims WHERE claim_id = ?", (claim["claim_id"],)
        ).fetchone()
    assert stored["verification_code"] == ""

    with patch("contestiq_core.codeforces.client.fetch_user_info") as fetch_user_info:
        response = client.post(
            f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user)
        )
    assert response.status_code == 410
    assert response.json()["error_code"] == "CLAIM_EXPIRED"
    fetch_user_info.assert_not_called()


def test_starting_replacement_claim_clears_superseded_code(client):
    user = register(client)
    first = client.post(
        "/api/v1/handles/claim", json={"handle": "replacement-handle"}, headers=bearer(user)
    ).json()
    second = client.post(
        "/api/v1/handles/claim", json={"handle": "replacement-handle"}, headers=bearer(user)
    ).json()

    assert second["claim_id"] != first["claim_id"]
    assert second["verification_code"] != first["verification_code"]
    with store.connect() as conn:
        old = conn.execute(
            "SELECT status, verification_code FROM handle_claims WHERE claim_id = ?",
            (first["claim_id"],),
        ).fetchone()
    assert old["status"] == handles.STATUS_SUPERSEDED
    assert old["verification_code"] == ""


def test_verification_code_is_single_use(client):
    """A consumed claim rejects every replay, including by the true owner."""
    user = register(client)
    claim = client.post("/api/v1/handles/claim", json={"handle": "single-use-handle"}, headers=bearer(user)).json()
    with patch(
        "contestiq_core.codeforces.client.fetch_user_info",
        return_value={"handle": "single-use-handle", "organization": claim["verification_code"]},
    ):
        first = client.post(f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user))
        second = client.post(f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(user))
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error_code"] == "CLAIM_ALREADY_USED"

    # A DIFFERENT user replaying the same claim_id must never succeed.
    stranger = register(client)
    replay = client.post(f"/api/v1/handles/claim/{claim['claim_id']}/verify", headers=bearer(stranger))
    assert replay.status_code == 404


def test_live_verification_fetch_neither_reads_nor_writes_public_cache(tmp_path, monkeypatch):
    import contestiq_core.codeforces.client as cf_client

    cache_dir = tmp_path / "public-cf-cache"
    monkeypatch.setattr(cf_client, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(cf_client, "RATE_LIMIT_SECONDS", 0)
    cf_client._last_request_at = 0.0
    cached_path = cf_client._cache_path("user.info", {"handles": "live-only-handle"})
    stale_payload = [{"handle": "live-only-handle", "organization": "stale-code"}]
    cached_path.write_text(json.dumps(stale_payload), encoding="utf-8")

    class LiveResponse:
        status_code = 200

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {
                "status": "OK",
                "result": [{"handle": "live-only-handle", "organization": "live-code"}],
            }

    with patch.object(cf_client.requests, "get", return_value=LiveResponse()) as request:
        profile = cf_client.fetch_user_info("live-only-handle", use_cache=False)

    assert profile["organization"] == "live-code"  # did not read the stale file
    assert json.loads(cached_path.read_text(encoding="utf-8")) == stale_payload  # did not overwrite it
    request.assert_called_once()


# ─── 9. Private leaderboard membership cannot be spoofed ────────────────────


def test_leaderboard_membership_cannot_be_spoofed_by_handle(client):
    owner = register(client)
    created = client.post(
        "/api/v1/leaderboards", json={"name": "Spoof Test", "display_name": "Owner"}, headers=bearer(owner)
    ).json()

    attacker = register(client)
    # No invite code known — passing the owner's handle/user_id must not
    # substitute for one.
    spoof = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}?handle=owner&user_id={owner['user_id']}",
        headers=bearer(attacker),
    )
    assert spoof.status_code == 403

    weekly_spoof = client.get(
        f"/api/v1/leaderboards/{created['leaderboard_id']}/weekly", headers=bearer(attacker)
    )
    assert weekly_spoof.status_code == 403


def test_leaderboard_join_requires_real_invite_not_just_a_handle(client):
    owner = register(client)
    client.post(
        "/api/v1/leaderboards", json={"name": "Invite Required", "display_name": "Owner"}, headers=bearer(owner)
    )
    attacker = register(client)
    response = client.post(
        "/api/v1/leaderboards/join",
        json={"invite_code": "guessed-or-fabricated-code", "display_name": "Attacker"},
        headers=bearer(attacker),
    )
    assert response.status_code == 404


# ─── 10. Premium cannot be obtained by handle spoofing ───────────────────────


def test_premium_features_not_unlocked_by_spoofing_a_premium_handle(client):
    rich_user = make_user(client, handle="premium-account-handle", plan="premium_student")
    free_attacker = register(client)

    entitlements = client.get("/api/v1/me/entitlements", headers=bearer(free_attacker)).json()
    assert entitlements["plan"] == "free"

    # Attacker tries every plausible spoof vector on a premium-gated endpoint.
    blocked = client.post(
        "/api/v1/plans/14-day?handle=premium-account-handle",
        json={"handle": "premium-account-handle"},
        headers=bearer(free_attacker),
    )
    assert blocked.status_code == 402

    still_free = client.get("/api/v1/me/entitlements", headers=bearer(free_attacker)).json()
    assert still_free["plan"] == "free"
    assert still_free["plan"] != "premium_student"


def test_weekly_report_premium_gate_not_bypassed_by_verified_but_free_handle(client):
    free_user = make_user(client, handle="free-verified-handle")
    handles.admin_bind(free_user["user_id"], "free-verified-handle")
    response = client.get(
        "/api/v1/weekly-report/free-verified-handle", headers=bearer(free_user)
    )
    assert response.status_code == 402  # verified ownership alone is not premium


# ─── 11. Existing public analysis still works without login ─────────────────


def test_public_analysis_endpoints_work_without_any_auth(client):
    handle = "public-analysis-handle"
    analyze = client.post(f"/api/v1/weakness/{handle}/analyze")
    assert analyze.status_code == 200
    assert analyze.json()["handle"] == handle.lower()

    queue = client.post("/api/v1/recommendations/daily", json={"handle": handle})
    assert queue.status_code == 200

    plan = client.post("/api/v1/plans/7-day", json={"handle": handle})
    assert plan.status_code == 200


def test_public_invite_preview_works_without_auth(client, catalog):
    creator = register(client)
    created = client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "Creator"}, headers=bearer(creator)
    ).json()
    preview = client.get(f"/api/v1/duels/invite/{created['invite_code']}")
    assert preview.status_code == 200
    assert preview.json()["mode"] == "rapid_10"


# ─── 12. No tokens/secrets/private data exposed ──────────────────────────────


def test_no_tokens_or_secrets_exposed_across_the_new_surface(client, catalog):
    user_a = register(client)
    user_b = register(client)
    duel = client.post(
        "/api/v1/duels", json={"mode": "rapid_10", "display_name": "A"}, headers=bearer(user_a)
    ).json()
    client.post(
        "/api/v1/duels/join",
        json={"invite_code": duel["invite_code"], "display_name": "B"},
        headers=bearer(user_b),
    )
    lb = client.post(
        "/api/v1/leaderboards", json={"name": "Secret Check", "display_name": "A"}, headers=bearer(user_a)
    ).json()
    claim = client.post("/api/v1/handles/claim", json={"handle": "secret-check-handle"}, headers=bearer(user_a)).json()

    payloads = [
        client.get("/api/v1/auth/me", headers=bearer(user_a)).json(),
        client.get(f"/api/v1/duels/{duel['duel_id']}", headers=bearer(user_a)).json(),
        client.get(f"/api/v1/duels/{duel['duel_id']}/state", headers=bearer(user_a)).json(),
        client.get(f"/api/v1/leaderboards/{lb['leaderboard_id']}", headers=bearer(user_a)).json(),
        client.get("/api/v1/gamification/me", headers=bearer(user_a)).json(),
        claim,
        client.get("/api/v1/handles/me", headers=bearer(user_a)).json(),
    ]
    raw = json.dumps(payloads).lower()
    for secret in (
        user_a["api_token"].lower(),
        user_b["api_token"].lower(),
        ADMIN_KEY.lower(),
        "token_hash",
        "admin_api_key",
        "invite_code_hash",
        "judge0_api_key",
        "password",
    ):
        assert secret not in raw, f"forbidden leak: {secret}"


def test_admin_handle_bind_is_audited_and_admin_only(client):
    user = register(client)
    unauth = client.post("/api/v1/admin/handles/bind", json={"user_id": user["user_id"], "handle": "reconciled-handle"})
    assert unauth.status_code == 403

    response = client.post(
        "/api/v1/admin/handles/bind",
        json={"user_id": user["user_id"], "handle": "reconciled-handle"},
        headers=admin(),
    )
    assert response.status_code == 200
    assert response.json()["bound_by"] == "admin_reconciliation"
    log = client.get("/api/v1/admin/audit-log", headers=admin()).json()["entries"]
    assert any(e["action"] == "handle_bind" for e in log)


def test_admin_bind_rejects_existing_owner_without_mutating_loser(client):
    first = register(client)
    second = register(client)
    assert client.post(
        "/api/v1/admin/handles/bind",
        json={"user_id": first["user_id"], "handle": "admin-race-handle"},
        headers=admin(),
    ).status_code == 200

    conflict = client.post(
        "/api/v1/admin/handles/bind",
        json={"user_id": second["user_id"], "handle": "admin-race-handle"},
        headers=admin(),
    )
    assert conflict.status_code == 409
    assert conflict.json()["error_code"] == "HANDLE_ALREADY_CLAIMED"
    assert handles.owner_user_id_for_handle("admin-race-handle") == first["user_id"]
    with store.connect() as conn:
        loser = conn.execute("SELECT handle FROM users WHERE user_id = ?", (second["user_id"],)).fetchone()
    assert loser["handle"] is None


def test_simultaneous_admin_binds_have_exactly_one_winner(client):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from contestiq_api.errors import APIError

    first = register(client)
    second = register(client)
    barrier = Barrier(2)

    def attempt(user_id):
        barrier.wait()
        try:
            handles.admin_bind(user_id, "simultaneous-bind-handle")
            return "bound", user_id
        except APIError as exc:
            return exc.error_code, user_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (first["user_id"], second["user_id"])))

    assert sorted(status for status, _ in outcomes) == ["HANDLE_ALREADY_CLAIMED", "bound"]
    winner = next(user_id for status, user_id in outcomes if status == "bound")
    loser = next(user_id for status, user_id in outcomes if status != "bound")
    assert handles.owner_user_id_for_handle("simultaneous-bind-handle") == winner
    with store.connect() as conn:
        winner_row = conn.execute("SELECT handle FROM users WHERE user_id = ?", (winner,)).fetchone()
        loser_row = conn.execute("SELECT handle FROM users WHERE user_id = ?", (loser,)).fetchone()
    assert winner_row["handle"] == "simultaneous-bind-handle"
    assert loser_row["handle"] is None


def test_admin_bind_and_audit_are_one_transaction(client):
    user = register(client)
    with store.connect() as conn:
        conn.execute(
            "CREATE TRIGGER reject_handle_bind_audit BEFORE INSERT ON admin_audit_logs "
            "WHEN NEW.action = 'handle_bind' BEGIN "
            "SELECT RAISE(ABORT, 'audit write failed'); END"
        )

    with pytest.raises(sqlite3.IntegrityError, match="audit write failed"):
        handles.admin_bind(user["user_id"], "atomic-bind-handle", audit_actor="test-admin")

    assert handles.owner_user_id_for_handle("atomic-bind-handle") is None
    with store.connect() as conn:
        stored_user = conn.execute("SELECT handle FROM users WHERE user_id = ?", (user["user_id"],)).fetchone()
    assert stored_user["handle"] is None


def test_user_export_redacts_claim_codes_and_deletion_removes_identity_rows(client):
    user = register(client)
    pending = client.post(
        "/api/v1/handles/claim", json={"handle": "pending-export-handle"}, headers=bearer(user)
    ).json()
    handles.admin_bind(user["user_id"], "owned-export-handle")

    exported = client.get(f"/api/v1/admin/users/{user['user_id']}/export", headers=admin())
    assert exported.status_code == 200
    payload = exported.json()
    assert len(payload["handle_owners"]) == 1
    assert payload["handle_owners"][0]["handle"] == "owned-export-handle"
    assert len(payload["handle_claims"]) == 1
    assert payload["handle_claims"][0]["verification_code"] == "[REDACTED]"
    assert pending["verification_code"] not in json.dumps(payload)

    deleted = client.delete(f"/api/v1/admin/users/{user['user_id']}", headers=admin())
    assert deleted.status_code == 200
    assert deleted.json()["deleted"]["handle_owners"] == 1
    assert deleted.json()["deleted"]["handle_claims"] == 1
    with store.connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM handle_owners WHERE user_id = ?", (user["user_id"],)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM handle_claims WHERE user_id = ?", (user["user_id"],)
        ).fetchone()[0] == 0
