"""Billing, entitlements, paywall, and admin tests (Phase 06)."""

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import episodes, store, taxonomy, weakness
from contestiq_api.cfdata import profiles as profiles_mod

ADMIN_KEY = "test-admin-key"
NOW = 1700000000
DAY = 86400
HANDLE = "Pay-User"


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def admin_headers():
    return {"X-Admin-Key": ADMIN_KEY}


def create_user(client, handle=None, role="user"):
    response = client.post("/api/v1/admin/users", json={"handle": handle, "role": role}, headers=admin_headers())
    assert response.status_code == 200
    return response.json()


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def submission(sid, contest_id, verdict, *, days_ago, rating, tags):
    return {
        "id": sid, "contestId": contest_id, "creationTimeSeconds": NOW - days_ago * DAY,
        "problem": {"contestId": contest_id, "index": "A", "name": f"P{contest_id}A",
                    "rating": rating, "tags": list(tags)},
        "author": {"members": [{"handle": HANDLE}], "participantType": "PRACTICE"},
        "programmingLanguage": "GNU C++17", "verdict": verdict,
        "passedTestCount": 5, "timeConsumedMillis": 100, "memoryConsumedBytes": 1024,
    }


def build_world():
    """dp weakness + greedy strength + wide catalog → >3 skills in the snapshot."""
    subs = []
    sid = 0
    for i in range(8):  # dp failures
        for _ in range(3):
            sid += 1
            subs.append(submission(sid, 300 + i, "WRONG_ANSWER", days_ago=30 + i, rating=1400, tags=("dp",)))
    for i in range(12):  # greedy clean solves
        sid += 1
        subs.append(submission(sid, 500 + i, "OK", days_ago=25 + i, rating=1500, tags=("greedy",)))
    store.upsert_user({"handle": HANDLE, "rating": 1500})
    store.upsert_submissions(HANDLE, subs)
    problems = {}
    for sub in subs:
        p = sub["problem"]
        problems[f"{p['contestId']}A"] = {"contestId": p["contestId"], "index": "A", "name": p["name"],
                                          "rating": p["rating"], "tags": p["tags"]}
    for tag, base in (("dp", 7000), ("greedy", 7100), ("geometry", 7200), ("number theory", 7300)):
        for i in range(12):
            problems[f"{base + i}B"] = {"contestId": base + i, "index": "B", "name": f"{tag} drill {i}",
                                        "rating": 1200 + i * 50, "tags": [tag]}
    store.save_problemset_snapshot({"problems": list(problems.values()), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    episodes.rebuild_episodes(HANDLE)
    weakness.analyze_handle_weakness(HANDLE)
    profiles_mod.build_profiles(HANDLE)


# ─── Backend paywall ─────────────────────────────────────────────────────────


def test_free_user_blocked_from_14_day_plan(client):
    build_world()
    response = client.post("/api/v1/plans/14-day", json={"handle": HANDLE})
    assert response.status_code == 402
    assert response.json()["error_code"] == "PREMIUM_REQUIRED"


def test_free_weakness_map_shows_top_3_only(client):
    build_world()
    response = client.get(f"/api/v1/weakness/{HANDLE}/latest")
    assert response.status_code == 200
    data = response.json()
    assert len(data["skills"]) <= 3
    assert data["locked_skills_count"] >= 1
    assert data["plan"] == "free"


def test_free_daily_queue_is_limited(client):
    build_world()
    response = client.post("/api/v1/recommendations/daily", json={"handle": HANDLE, "queue_date": "2026-07-07"})
    assert response.status_code == 200
    items = response.json()["items"]
    unlocked = [i for i in items if not i.get("locked")]
    locked = [i for i in items if i.get("locked")]
    assert len(unlocked) == 2
    assert locked, "free tier must see locked placeholders"
    assert all("problem_id" not in i for i in locked)


def test_free_plan_preview_only_day_1(client):
    build_world()
    response = client.post("/api/v1/plans/7-day", json={"handle": HANDLE, "start_date": "2026-07-07"})
    assert response.status_code == 200
    days = response.json()["days"]
    assert days[0]["day_number"] == 1 and days[0]["items"]
    for day in days[1:]:
        assert day["locked"] is True
        assert day["items"] == []
        assert day["item_count"] >= 0


def test_premium_user_gets_full_access(client):
    build_world()
    user = create_user(client, handle=HANDLE)
    client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                json={"plan": "premium_student"}, headers=admin_headers())

    full_map = client.get(f"/api/v1/weakness/{HANDLE}/latest", headers=bearer(user)).json()
    assert "locked_skills_count" not in full_map
    assert len(full_map["skills"]) > 3

    queue = client.post("/api/v1/recommendations/daily",
                        json={"handle": HANDLE, "queue_date": "2026-07-07"}, headers=bearer(user)).json()
    assert all(not item.get("locked") for item in queue["items"])

    plan14 = client.post("/api/v1/plans/14-day", json={"handle": HANDLE, "start_date": "2026-07-07"},
                         headers=bearer(user))
    assert plan14.status_code == 200
    assert len(plan14.json()["days"]) == 14
    assert all(not day.get("locked") for day in plan14.json()["days"])


# ─── Grants / revokes ────────────────────────────────────────────────────────


def test_manual_grant_and_revoke_flow(client):
    user = create_user(client, handle="beta-tester")
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "free"

    grant = client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                        json={"plan": "premium_student"}, headers=admin_headers())
    assert grant.status_code == 200
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "premium_student"
    assert me["features"]["plan_14_day"] is True
    assert len(me["grants"]) == 1

    revoke = client.post(f"/api/v1/admin/users/{user['user_id']}/revoke-entitlement",
                         json={"plan": "premium_student"}, headers=admin_headers())
    assert revoke.json()["revoked_grants"] == 1
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "free"


def test_expired_grant_does_not_entitle(client):
    user = create_user(client)
    client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                json={"plan": "premium_student", "expires_at": "2020-01-01T00:00:00+00:00"},
                headers=admin_headers())
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "free"


# ─── Beta/demo premium grant by identifier (handle/email lookup) ────────────


def test_admin_can_grant_premium_by_user_id(client):
    user = create_user(client)
    grant = client.post("/api/v1/admin/premium/grant",
                        json={"user_id": user["user_id"], "plan": "premium_student"},
                        headers=admin_headers())
    assert grant.status_code == 200
    assert grant.json()["user_id"] == user["user_id"]
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "premium_student"


def test_admin_can_grant_premium_by_verified_handle(client):
    user = create_user(client)
    bind = client.post("/api/v1/admin/handles/bind",
                       json={"user_id": user["user_id"], "handle": "beta-coder"},
                       headers=admin_headers())
    assert bind.status_code == 200

    grant = client.post("/api/v1/admin/premium/grant",
                        json={"handle": "beta-coder", "plan": "premium_student"},
                        headers=admin_headers())
    assert grant.status_code == 200
    assert grant.json()["user_id"] == user["user_id"]
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "premium_student"


def test_admin_grant_by_unverified_handle_fails_closed(client):
    create_user(client)  # some other unrelated user exists
    grant = client.post("/api/v1/admin/premium/grant",
                        json={"handle": "nobody-verified-this", "plan": "premium_student"},
                        headers=admin_headers())
    assert grant.status_code == 404
    assert grant.json()["error_code"] == "HANDLE_NOT_VERIFIED"


def test_admin_can_grant_premium_by_email(client):
    created = client.post("/api/v1/admin/users", json={"email": "founder-beta@example.com", "role": "user"},
                          headers=admin_headers())
    user = created.json()
    grant = client.post("/api/v1/admin/premium/grant",
                        json={"email": "founder-beta@example.com", "plan": "premium_student"},
                        headers=admin_headers())
    assert grant.status_code == 200
    assert grant.json()["user_id"] == user["user_id"]
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "premium_student"


def test_admin_grant_by_unknown_email_fails_closed(client):
    grant = client.post("/api/v1/admin/premium/grant",
                        json={"email": "nobody@example.com", "plan": "premium_student"},
                        headers=admin_headers())
    assert grant.status_code == 404
    assert grant.json()["error_code"] == "EMAIL_NOT_FOUND"


def test_admin_grant_by_identifier_requires_exactly_one(client):
    user = create_user(client)
    none_provided = client.post("/api/v1/admin/premium/grant", json={"plan": "premium_student"},
                                headers=admin_headers())
    assert none_provided.status_code == 422

    both_provided = client.post(
        "/api/v1/admin/premium/grant",
        json={"user_id": user["user_id"], "handle": "beta-coder", "plan": "premium_student"},
        headers=admin_headers(),
    )
    assert both_provided.status_code == 422


def test_non_admin_cannot_grant_premium_by_identifier(client):
    user = create_user(client)
    forged = client.post("/api/v1/admin/premium/grant",
                         json={"user_id": user["user_id"], "plan": "premium_student"},
                         headers=bearer(user))
    assert forged.status_code == 403
    no_auth = client.post("/api/v1/admin/premium/grant", json={"user_id": user["user_id"], "plan": "premium_student"})
    assert no_auth.status_code == 403
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "free"


def test_premium_grant_by_identifier_is_audited(client):
    user = create_user(client)
    client.post("/api/v1/admin/premium/grant",
               json={"user_id": user["user_id"], "plan": "premium_student"},
               headers=admin_headers())
    log = client.get("/api/v1/admin/audit-log", headers=admin_headers()).json()["entries"]
    entry = next(e for e in log if e["action"] == "grant_entitlement" and e["target"] == user["user_id"])
    assert entry["details"]["resolved_via"] == "user_id"


# ─── Billing / webhooks ──────────────────────────────────────────────────────


def test_manual_checkout_creates_pending_payment(client):
    user = create_user(client, handle="payer")
    checkout = client.post("/api/v1/billing/checkout", json={"plan": "premium_student"}, headers=bearer(user))
    assert checkout.status_code == 200
    data = checkout.json()
    assert data["provider"] == "manual"
    assert data["status"] == "pending_manual_payment"

    billing_view = client.get(f"/api/v1/admin/users/{user['user_id']}/billing", headers=admin_headers()).json()
    assert billing_view["payments"][0]["payment_status"] == "pending"
    assert billing_view["effective_plan"] == "free"


def test_checkout_requires_auth(client):
    response = client.post("/api/v1/billing/checkout", json={"plan": "premium_student"})
    assert response.status_code == 401


def test_webhook_grants_and_is_idempotent(client):
    user = create_user(client, handle="webhook-user")
    checkout = client.post("/api/v1/billing/checkout", json={"plan": "premium_student", "provider": "local"},
                           headers=bearer(user)).json()
    event = {
        "event_id": "evt-001",
        "type": "payment.completed",
        "payment_id": checkout["payment_id"],
        "external_payment_id": "ext-123",
    }
    first = client.post("/api/v1/billing/webhook/local", json=event, headers=admin_headers())
    assert first.status_code == 200
    assert first.json()["status"] == "processed"
    assert first.json()["result"] == "granted:premium_student"

    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "premium_student"

    # Replay: no double processing, no duplicate entitlement.
    second = client.post("/api/v1/billing/webhook/local", json=event, headers=admin_headers())
    assert second.json()["status"] == "already_processed"
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert len(me["grants"]) == 1

    billing_view = client.get(f"/api/v1/admin/users/{user['user_id']}/billing", headers=admin_headers()).json()
    assert billing_view["payments"][0]["payment_status"] == "completed"


def test_webhook_ignores_unknown_event_types(client):
    response = client.post(
        "/api/v1/billing/webhook/local",
        json={"event_id": "evt-x", "type": "customer.updated"},
        headers=admin_headers(),
    )
    assert response.json()["result"].startswith("ignored_event_type")


def test_webhook_cannot_self_grant_or_spoof_payment_identity(client):
    attacker = create_user(client, handle="billing-attacker")
    forged = {
        "event_id": "evt-forged",
        "type": "payment.completed",
        "user_id": attacker["user_id"],
        "plan": "premium_student",
    }
    assert client.post("/api/v1/billing/webhook/manual", json=forged).status_code == 403

    admin_attempt = client.post(
        "/api/v1/billing/webhook/manual", json=forged, headers=admin_headers()
    )
    assert admin_attempt.status_code == 200
    assert admin_attempt.json()["result"] == "error:missing_payment_id"
    me = client.get("/api/v1/me/entitlements", headers=bearer(attacker)).json()
    assert me["plan"] == "free"


def test_external_webhook_fails_closed_without_signature_verification(client):
    response = client.post(
        "/api/v1/billing/webhook/stripe",
        json={"event_id": "evt-stripe", "type": "payment.completed"},
    )
    assert response.status_code == 501
    assert response.json()["error_code"] == "WEBHOOK_VERIFICATION_UNAVAILABLE"


def test_stripe_placeholder_fails_loudly_without_key(client):
    user = create_user(client)
    response = client.post("/api/v1/billing/checkout", json={"plan": "premium_student", "provider": "stripe"},
                           headers=bearer(user))
    assert response.status_code == 501
    assert response.json()["error_code"] == "PROVIDER_NOT_CONFIGURED"


# ─── Admin authorization + audit ─────────────────────────────────────────────


def test_admin_endpoints_require_admin(client):
    assert client.get("/api/v1/admin/users?query=x").status_code == 403
    assert client.get("/api/v1/admin/users?query=x", headers={"X-Admin-Key": "wrong"}).status_code == 403
    user = create_user(client)
    assert client.get("/api/v1/admin/users?query=x", headers=bearer(user)).status_code == 403
    admin_user = create_user(client, role="admin")
    assert client.get("/api/v1/admin/users?query=x", headers=bearer(admin_user)).status_code == 200


def test_invalid_token_rejected(client):
    response = client.get("/api/v1/me/entitlements", headers={"Authorization": "Bearer bogus"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


def test_anonymous_entitlements_are_free(client):
    me = client.get("/api/v1/me/entitlements").json()
    assert me["plan"] == "free"
    assert me["user"] is None
    assert me["features"]["weak_skills_visible"] == 3


def test_every_admin_action_is_audited(client):
    user = create_user(client, handle="audited")
    client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                json={"plan": "premium_student"}, headers=admin_headers())
    client.post(f"/api/v1/admin/users/{user['user_id']}/revoke-entitlement",
                json={"plan": "premium_student"}, headers=admin_headers())
    client.get(f"/api/v1/admin/users/{user['user_id']}/billing", headers=admin_headers())

    log = client.get("/api/v1/admin/audit-log", headers=admin_headers()).json()["entries"]
    actions = [entry["action"] for entry in log]
    for expected in ("create_user", "grant_entitlement", "revoke_entitlement", "view_billing"):
        assert expected in actions
    grant_entry = next(e for e in log if e["action"] == "grant_entitlement")
    assert grant_entry["actor"] == "admin_api_key"
    assert grant_entry["target"] == user["user_id"]


def test_admin_user_search(client):
    created = create_user(client, handle="Findable-User")
    result = client.get("/api/v1/admin/users?query=findable", headers=admin_headers()).json()
    assert any(u["user_id"] == created["user_id"] for u in result["users"])


# ─── Usage limits ────────────────────────────────────────────────────────────


def test_usage_limit_enforced_for_free_tier(client):
    for i in range(3):
        response = client.post(f"/api/v1/weakness/limit-user-{i}/analyze")
        assert response.status_code == 200
    blocked = client.post("/api/v1/weakness/limit-user-x/analyze")
    assert blocked.status_code == 429
    assert blocked.json()["error_code"] == "USAGE_LIMIT_EXCEEDED"


def test_premium_raises_usage_limit(client):
    user = create_user(client)
    client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                json={"plan": "premium_student"}, headers=admin_headers())
    for i in range(5):  # above the free limit of 3
        response = client.post(f"/api/v1/weakness/prem-user-{i}/analyze", headers=bearer(user))
        assert response.status_code == 200


# ─── Admin ops: jobs, resync, snapshots, curation ────────────────────────────


def test_admin_job_listing_and_retry(client, monkeypatch):
    monkeypatch.setenv("CONTESTIQ_API_OFFLINE_SAMPLE", "1")
    from contestiq_api import jobs as backend_jobs

    job = backend_jobs.create_job("analysis", {"handle": "retry-user", "force_refresh": False})
    backend_jobs.mark_running(job["id"])
    backend_jobs.mark_finished(job["id"], "failed", error_message="boom")

    listing = client.get("/api/v1/admin/jobs?status=failed", headers=admin_headers()).json()
    assert any(j["job_id"] == job["id"] for j in listing["backend_jobs"])

    retried = client.post(f"/api/v1/admin/jobs/{job['id']}/retry", headers=admin_headers())
    assert retried.status_code == 200
    assert retried.json()["job"]["status"] == "success"


def test_admin_analysis_snapshot_view(client):
    build_world()
    snapshot = client.get(f"/api/v1/admin/analysis/{HANDLE}/latest", headers=admin_headers())
    assert snapshot.status_code == 200
    assert snapshot.json()["skills"]
    runs = client.get(f"/api/v1/admin/analysis/{HANDLE}/runs", headers=admin_headers()).json()
    assert len(runs["runs"]) == 1


def test_admin_mark_problem_bad_and_edit_skill_map(client):
    build_world()
    marked = client.post("/api/v1/admin/problems/7000B/mark-bad", json={"reason": "broken statement"},
                         headers=admin_headers())
    assert marked.json()["manual_curation"] == 0.0

    edited = client.post(
        "/api/v1/admin/problems/7000B/skill-map",
        json={"skills": [{"skill_id": "dynamic_programming.knapsack", "weight": 0.7, "confidence": 0.9},
                         {"skill_id": "greedy", "weight": 0.3, "confidence": 0.6}]},
        headers=admin_headers(),
    )
    assert edited.status_code == 200
    mappings = taxonomy.get_problem_skills("7000B")
    assert {m["skill_id"] for m in mappings} == {"dynamic_programming.knapsack", "greedy"}
    assert all(m["mapping_source"] == "manual" for m in mappings)

    unknown = client.post(
        "/api/v1/admin/problems/7000B/skill-map",
        json={"skills": [{"skill_id": "not_a_skill", "weight": 1.0, "confidence": 0.9}]},
        headers=admin_headers(),
    )
    assert unknown.status_code == 422
