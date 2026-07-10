"""Phase 10 launch readiness tests: first-money e2e, onboarding events,
weekly reports, support workflows, launch dashboard."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from contestiq_api import handles, product_events
from contestiq_api.cfdata import episodes, store, taxonomy, weakness
from contestiq_api.skilltrace import judge0 as j0

ADMIN_KEY = "launch-admin-key"
NOW = 1700000000
DAY = 86400
HANDLE = "Launch-User"


class FakeJudge0:
    def __init__(self):
        self.next_token = 0

    def post(self, url, payload, headers):
        self.next_token += 1
        return {"token": f"tok-{self.next_token}"}

    def get(self, url, headers):
        return {"status": {"id": 2}}


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://fake-judge0")
    fake = FakeJudge0()
    j0.set_adapter(j0.Judge0Adapter(post=fake.post, get=fake.get))
    yield
    j0.set_adapter(None)


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def admin():
    return {"X-Admin-Key": ADMIN_KEY}


def make_user(client, handle=None, plan=None):
    user = client.post("/api/v1/admin/users", json={"handle": handle}, headers=admin()).json()
    if plan:
        client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                    json={"plan": plan}, headers=admin())
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def submission(sid, contest_id, verdict, *, days_ago, rating=1400, tags=("dp",)):
    return {
        "id": sid, "contestId": contest_id, "creationTimeSeconds": NOW - days_ago * DAY,
        "problem": {"contestId": contest_id, "index": "A", "name": f"P{contest_id}",
                    "rating": rating, "tags": list(tags)},
        "author": {"members": [{"handle": HANDLE}], "participantType": "PRACTICE"},
        "programmingLanguage": "GNU C++17", "verdict": verdict,
        "passedTestCount": 3, "timeConsumedMillis": 50, "memoryConsumedBytes": 100,
    }


def build_world(extra_solves=0):
    subs = []
    sid = 0
    for i in range(8):
        for _ in range(3):
            sid += 1
            subs.append(submission(sid, 300 + i, "WRONG_ANSWER", days_ago=20 + i))
    for i in range(10 + extra_solves):
        sid += 1
        subs.append(submission(sid, 500 + i, "OK", days_ago=5 + i, rating=1500, tags=("greedy",)))
    store.upsert_user({"handle": HANDLE, "rating": 1500})
    store.upsert_submissions(HANDLE, subs)
    problems = {f"{s['problem']['contestId']}A": s["problem"] for s in subs}
    for tag, base in (("dp", 7000), ("greedy", 7100)):
        for i in range(12):
            problems[f"{base + i}B"] = {"contestId": base + i, "index": "B", "name": f"{tag} d{i}",
                                        "rating": 1250 + i * 40, "tags": [tag]}
    store.save_problemset_snapshot({"problems": list(problems.values()), "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    episodes.rebuild_episodes(HANDLE)
    weakness.analyze_handle_weakness(HANDLE)


# ─── First-money e2e ─────────────────────────────────────────────────────────


def test_first_paid_user_end_to_end_without_code_changes(client):
    build_world()
    user = make_user(client, handle=HANDLE)
    # Weekly report is SolveX-account data (security hotfix): the caller must
    # be the VERIFIED owner of the handle, not merely have it set on file.
    handles.admin_bind(user["user_id"], HANDLE)

    # 1) Free: blocked from premium features.
    assert client.post("/api/v1/plans/14-day", json={"handle": HANDLE},
                       headers=bearer(user)).status_code == 402
    assert client.get(f"/api/v1/weekly-report/{HANDLE}", headers=bearer(user)).status_code == 402

    # 2) Checkout (manual beta) creates a pending payment/invoice reference.
    checkout = client.post("/api/v1/billing/checkout", json={"plan": "premium_student"},
                           headers=bearer(user)).json()
    assert checkout["status"] == "pending_manual_payment"

    # 3) Payment confirmation via webhook activates the entitlement.
    hook = client.post("/api/v1/billing/webhook/manual",
                       json={"event_id": "launch-evt-1", "type": "payment.completed",
                             "payment_id": checkout["payment_id"]}, headers=admin())
    assert hook.json()["result"] == "granted:premium_student"

    # 4) Premium features now work end-to-end.
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "premium_student"
    plan14 = client.post("/api/v1/plans/14-day", json={"handle": HANDLE, "start_date": "2026-07-07"},
                         headers=bearer(user))
    assert plan14.status_code == 200 and len(plan14.json()["days"]) == 14
    weekly = client.get(f"/api/v1/weekly-report/{HANDLE}", headers=bearer(user))
    assert weekly.status_code == 200

    # 5) Refund/dispute: payment refunded AND plan revoked.
    refund = client.post(f"/api/v1/admin/payments/{checkout['payment_id']}/refund", headers=admin())
    assert refund.json()["payment_status"] == "refunded"
    assert refund.json()["revoked_grants"] == 1
    me = client.get("/api/v1/me/entitlements", headers=bearer(user)).json()
    assert me["plan"] == "free"
    assert client.post("/api/v1/plans/14-day", json={"handle": HANDLE},
                       headers=bearer(user)).status_code == 402


def test_team_and_event_buyers_can_be_served(client):
    coach = make_user(client, plan="team")
    team = client.post("/api/v1/teams", json={"name": "Paid Club"}, headers=bearer(coach))
    assert team.status_code == 200

    organizer = make_user(client, plan="event")
    org = client.post("/api/v1/orgs", json={"name": "Paid Org"}, headers=bearer(organizer))
    assert org.status_code == 200
    event = client.post(f"/api/v1/orgs/{org.json()['org_id']}/events",
                        json={"name": "Paid Screening", "requirements": [{"skill_id": "implementation"}]},
                        headers=bearer(organizer))
    assert event.status_code == 200


# ─── Onboarding events ───────────────────────────────────────────────────────


def test_onboarding_events_fire_and_first_events_are_once(client):
    build_world()
    client.post(f"/api/v1/weakness/{HANDLE}/analyze", headers=admin())
    client.post(f"/api/v1/weakness/{HANDLE}/analyze", headers=admin())
    assert product_events.count("first_analysis_completed") == 1  # once per handle

    client.post("/api/v1/recommendations/daily",
                json={"handle": HANDLE, "queue_date": "2026-07-07"}, headers=admin())
    assert product_events.count("first_queue_generated") == 1

    plan = client.post("/api/v1/plans/7-day", json={"handle": HANDLE, "start_date": "2026-07-07"},
                       headers=admin()).json()
    assert product_events.count("plan_started") == 1

    queue = client.get(f"/api/v1/recommendations/today?handle={HANDLE}", headers=admin())
    # feedback event
    today = client.post("/api/v1/recommendations/daily",
                        json={"handle": HANDLE, "queue_date": "2026-07-07"}, headers=admin()).json()
    item_id = today["items"][0]["item_id"]
    feedback_user = make_user(client)
    handles.admin_bind(feedback_user["user_id"], HANDLE)
    client.post(
        f"/api/v1/recommendations/{item_id}/feedback",
        json={"feedback_type": "good_problem"},
        headers=bearer(feedback_user),
    )
    assert product_events.count("feedback_submitted") == 1

    user = make_user(client, handle=HANDLE, plan="premium_student")
    assert product_events.count("premium_conversion") == 1
    client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"}, headers=bearer(user))
    assert product_events.count("verification_attempted") == 1


# ─── Weekly report ───────────────────────────────────────────────────────────


def test_weekly_report_compares_runs_and_is_idempotent(client):
    from contestiq_api import weekly

    build_world()
    # Second run with more solved episodes → some improvement signal.
    extra = [submission(900 + i, 800 + i, "OK", days_ago=1, rating=1400, tags=("dp",)) for i in range(6)]
    store.upsert_submissions(HANDLE, extra)
    episodes.rebuild_episodes(HANDLE)
    weakness.analyze_handle_weakness(HANDLE)

    report = weekly.generate_weekly_report(HANDLE)
    assert report["status"] == "available"
    assert report["previous_analysis_run_id"] is not None
    assert report["episode_count_change"] == 6
    assert isinstance(report["improvements"], list)
    assert len(report["next_week_focus"]) <= 3
    assert "not claims about mastery" in report["safe_interpretation"]

    again = weekly.generate_weekly_report(HANDLE)
    with store.connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM weekly_reports WHERE handle = ?", (HANDLE.lower(),)).fetchone()[0]
    assert count == 1  # same week replaces, never duplicates
    assert again["week_start"] == report["week_start"]


def test_weekly_report_batch_job_and_premium_gate(client):
    build_world()
    result = client.post("/api/v1/admin/jobs/weekly-reports", headers=admin()).json()
    assert result["reports_generated"] == 1

    # Security hotfix: auth is required before anything else — an
    # unauthenticated caller never even reaches the premium-plan check.
    anonymous = client.get(f"/api/v1/weekly-report/{HANDLE}")
    assert anonymous.status_code == 401

    # A different handle for the free-plan check — handle_owners allows only
    # one verified owner per handle, and HANDLE is bound to `premium` below.
    free_owner = make_user(client, handle="Launch-User-Free")
    handles.admin_bind(free_owner["user_id"], "Launch-User-Free")
    gated = client.get("/api/v1/weekly-report/Launch-User-Free", headers=bearer(free_owner))
    assert gated.status_code == 402  # premium feature, verified owner but free plan

    premium = make_user(client, plan="premium_student")
    unverified = client.get(f"/api/v1/weekly-report/{HANDLE}", headers=bearer(premium))
    assert unverified.status_code == 403  # premium plan but NOT the verified owner of this handle
    handles.admin_bind(premium["user_id"], HANDLE)
    response = client.get(f"/api/v1/weekly-report/{HANDLE}", headers=bearer(premium))
    assert response.status_code == 200
    assert response.json()["handle"] == HANDLE.lower()


def test_weekly_report_first_baseline(client):
    build_world()  # single analysis run
    premium = make_user(client, plan="premium_student")
    handles.admin_bind(premium["user_id"], HANDLE)
    report = client.get(f"/api/v1/weekly-report/{HANDLE}", headers=bearer(premium)).json()
    assert report["status"] == "first_report_baseline"


# ─── Support workflows ───────────────────────────────────────────────────────


def _issue_badge(client, user):
    session = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                          headers=bearer(user)).json()
    sid = session["session_id"]
    for i in range(3):
        client.post(f"/api/v1/verification/sessions/{sid}/snapshot", json={"code": f"# {i}"}, headers=bearer(user))
    code = "print(sum(map(int, input().split())))"
    client.post(f"/api/v1/verification/sessions/{sid}/run",
                json={"language": "python3", "source_code": code, "stdin": "1 2"}, headers=bearer(user))
    client.post(f"/api/v1/verification/sessions/{sid}/submit",
                json={"language": "python3", "source_code": code}, headers=bearer(user))
    with store.connect() as conn:
        subs = [dict(r) for r in conn.execute(
            "SELECT * FROM judge0_submissions WHERE submission_status = 'submitted'").fetchall()]
    for sub in subs:
        client.put(f"/api/v1/judge0/callback?secret={sub['callback_secret']}",
                   json={"token": sub["judge0_token"], "status": {"id": 3},
                         "stdout": base64.b64encode(b"3").decode()})
    view = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(user)).json()
    return view["badge"]["badge_public_id"]


def test_badge_revocation_flow(client):
    user = make_user(client, handle="badge-holder", plan="premium_student")
    badge_id = _issue_badge(client, user)
    assert client.get(f"/api/v1/badges/{badge_id}").json()["badge_status"] == "active"

    revoked = client.post(f"/api/v1/admin/badges/{badge_id}/revoke", headers=admin())
    assert revoked.json()["badge_status"] == "revoked"
    public = client.get(f"/api/v1/badges/{badge_id}").json()
    assert public["badge_status"] == "revoked"

    log = client.get("/api/v1/admin/audit-log", headers=admin()).json()["entries"]
    assert any(e["action"] == "revoke_badge" and e["target"] == badge_id for e in log)


def test_leaked_challenge_no_longer_assigned(client):
    user = make_user(client, plan="premium_student")
    session = client.post("/api/v1/verification/sessions", json={"skill_id": "greedy"},
                          headers=bearer(user)).json()
    challenge_id = session["challenge"]["challenge_id"]

    client.post(f"/api/v1/admin/challenges/{challenge_id}/mark-leaked", headers=admin())
    # greedy has only one seed challenge → no active challenge remains.
    another = make_user(client, plan="premium_student")
    blocked = client.post("/api/v1/verification/sessions", json={"skill_id": "greedy"},
                          headers=bearer(another))
    assert blocked.status_code == 404
    assert blocked.json()["error_code"] == "NO_CHALLENGE_AVAILABLE"


def test_user_export_and_deletion(client):
    user = make_user(client, handle="delete-me", plan="premium_student")
    badge_id = _issue_badge(client, user)

    export = client.get(f"/api/v1/admin/users/{user['user_id']}/export", headers=admin()).json()
    assert export["user"]["user_id"] == user["user_id"]
    assert "token_hash" not in export["user"]
    assert len(export["entitlement_grants"]) == 1
    assert len(export["verification_sessions"]) == 1
    assert export["session_events_count"] > 0

    deleted = client.delete(f"/api/v1/admin/users/{user['user_id']}", headers=admin()).json()
    assert deleted["status"] == "deleted"
    assert client.get("/api/v1/me/entitlements", headers=bearer(user)).status_code == 401  # token dead
    assert client.get(f"/api/v1/badges/{badge_id}").status_code == 404  # badge rows removed
    with store.connect() as conn:
        for table, column in [("verification_sessions", "user_id"), ("entitlement_grants", "user_id"),
                              ("payments", "user_id"), ("private_reports", "user_id")]:
            assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?",
                                (user["user_id"],)).fetchone()[0] == 0

    log = client.get("/api/v1/admin/audit-log", headers=admin()).json()["entries"]
    assert any(e["action"] == "delete_user" for e in log)
    assert any(e["action"] == "export_user_data" for e in log)


def test_failed_sync_support_flow(client, monkeypatch):
    job = store.create_sync_job("full", "broken-handle")
    store.mark_sync_running(job["id"])
    store.finish_sync_job(job["id"], "failed", error_message="codeforces exploded")

    listing = client.get("/api/v1/admin/jobs?status=failed", headers=admin()).json()
    assert any(j["id"] == job["id"] for j in listing["sync_jobs"])

    # Admin resolves with a forced resync (fake CF world).
    from contestiq_api.cfdata import sync as cf_sync
    from contestiq_api.cfdata.client import CircuitBreaker, CodeforcesClient, GlobalRateLimiter, TransportResponse

    def ok_transport(url, params, timeout):
        endpoint = url.rsplit("/", 1)[-1]
        payloads = {
            "user.info": [{"handle": "broken-handle", "rating": 1200}],
            "user.rating": [],
            "user.status": [],
        }
        return TransportResponse(200, {"status": "OK", "result": payloads[endpoint]})

    monkeypatch.setattr(cf_sync, "CodeforcesClient", lambda: CodeforcesClient(
        transport=ok_transport, rate_limiter=GlobalRateLimiter(0.0, clock=lambda: 0.0, sleep=lambda s: None),
        breaker=CircuitBreaker(failure_threshold=100), sleep=lambda s: None, rng=lambda: 0.0))
    resync = client.post("/api/v1/admin/resync/broken-handle", headers=admin())
    assert resync.status_code == 200
    assert resync.json()["job"]["status"] == "success"


# ─── Launch dashboard ────────────────────────────────────────────────────────


def test_launch_dashboard_counts(client):
    build_world()
    client.post(f"/api/v1/weakness/{HANDLE}/analyze", headers=admin())
    client.post("/api/v1/recommendations/daily", json={"handle": HANDLE, "queue_date": "2026-07-07"},
                headers=admin())
    user = make_user(client, handle=HANDLE, plan="premium_student")

    dashboard = client.get("/api/v1/admin/launch-dashboard", headers=admin()).json()
    assert dashboard["signup_count"] == 1
    assert dashboard["handle_connected"] == 1
    assert dashboard["analysis_completed"] >= 2  # build_world + endpoint run
    assert dashboard["queues_generated"] == 1
    assert dashboard["premium_conversions"] == 1
    assert dashboard["active_premium_users"] == 1
    assert dashboard["free_to_premium_conversion"] == 1.0
    for key in ("paid_churn_users", "team_invites_accepted", "event_applicant_completion_rate",
                "badge_issuance_rate", "seven_day_retention_subjects", "recommendation_feedback"):
        assert key in dashboard

    assert client.get("/api/v1/admin/launch-dashboard").status_code == 403  # admin only
