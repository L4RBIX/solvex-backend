"""Phase 09 security/observability audit tests.

Consolidates the cross-cutting production requirements: BOLA denials,
throttles, secret hygiene in logs, metrics visibility, trace propagation,
and production settings validation. Object-specific BOLA tests also live in
test_skilltrace.py and test_teams_events.py.
"""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from contestiq_api import metrics, throttle
from contestiq_api.cfdata import store
from contestiq_api.skilltrace import judge0 as j0

ADMIN_KEY = "test-admin-key-security"


class FakeTransport:
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
    fake = FakeTransport()
    j0.set_adapter(j0.Judge0Adapter(post=fake.post, get=fake.get))
    metrics.reset()
    yield
    j0.set_adapter(None)


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def make_user(client, plan=None, role="user", handle=None):
    user = client.post("/api/v1/admin/users", json={"handle": handle, "role": role},
                       headers={"X-Admin-Key": ADMIN_KEY}).json()
    if plan:
        client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                    json={"plan": plan}, headers={"X-Admin-Key": ADMIN_KEY})
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


# ─── BOLA: cross-user object access ──────────────────────────────────────────


def test_cross_user_verification_and_report_access_denied(client):
    owner = make_user(client, plan="premium_student")
    session = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                          headers=bearer(owner)).json()
    sid = session["session_id"]

    attacker = make_user(client, plan="premium_student")
    assert client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(attacker)).status_code == 403
    assert client.get(f"/api/v1/verification/sessions/{sid}/events", headers=bearer(attacker)).status_code == 403
    assert client.post(f"/api/v1/verification/sessions/{sid}/submit",
                       json={"language": "python3", "source_code": "print(1)"},
                       headers=bearer(attacker)).status_code == 403


def test_cross_team_and_cross_org_denied(client):
    coach_a = make_user(client, plan="team")
    team = client.post("/api/v1/teams", json={"name": "Team A"}, headers=bearer(coach_a)).json()
    coach_b = make_user(client, plan="team")
    assert client.get(f"/api/v1/teams/{team['team_id']}/dashboard", headers=bearer(coach_b)).status_code == 403

    org_a = make_user(client, plan="event")
    org = client.post("/api/v1/orgs", json={"name": "Org A"}, headers=bearer(org_a)).json()
    event = client.post(f"/api/v1/orgs/{org['org_id']}/events",
                        json={"name": "Event A", "requirements": [{"skill_id": "greedy"}]},
                        headers=bearer(org_a)).json()
    org_b = make_user(client, plan="event")
    assert client.get(f"/api/v1/events/{event['event_id']}/dashboard", headers=bearer(org_b)).status_code == 403


def test_admin_surfaces_denied_to_non_admin(client):
    user = make_user(client, plan="premium_student")
    for method, path in [
        ("get", "/api/v1/admin/users?query=x"),
        ("get", "/api/v1/admin/jobs"),
        ("get", "/api/v1/admin/audit-log"),
        ("post", "/api/v1/admin/resync/somehandle"),
        ("get", "/api/v1/metrics"),
        ("post", "/api/v1/verification/reconcile"),
    ]:
        response = getattr(client, method)(path, headers=bearer(user))
        assert response.status_code == 403, f"{path} not protected: {response.status_code}"
        anonymous = getattr(client, method)(path)
        assert anonymous.status_code in (401, 403), f"{path} open to anonymous"


def test_uuid_secrecy_not_relied_on_for_reports(client):
    """Knowing a report_id is not enough — ownership is enforced."""
    import base64

    owner = make_user(client, plan="premium_student")
    session = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                          headers=bearer(owner)).json()
    sid = session["session_id"]
    client.post(f"/api/v1/verification/sessions/{sid}/snapshot", json={"code": "x"}, headers=bearer(owner))
    client.post(f"/api/v1/verification/sessions/{sid}/snapshot", json={"code": "xy"}, headers=bearer(owner))
    client.post(f"/api/v1/verification/sessions/{sid}/run",
                json={"language": "python3", "source_code": "print(1)", "stdin": ""}, headers=bearer(owner))
    with store.connect() as conn:
        subs = [dict(r) for r in conn.execute("SELECT * FROM judge0_submissions").fetchall()]
    for sub in subs:
        client.put(f"/api/v1/judge0/callback?secret={sub['callback_secret']}",
                   json={"token": sub["judge0_token"], "status": {"id": 3},
                         "stdout": base64.b64encode(b"1").decode()})
    client.post(f"/api/v1/verification/sessions/{sid}/submit",
                json={"language": "python3", "source_code": "print(1)"}, headers=bearer(owner))
    with store.connect() as conn:
        subs = [dict(r) for r in conn.execute(
            "SELECT * FROM judge0_submissions WHERE submission_status = 'submitted'").fetchall()]
    for sub in subs:
        client.put(f"/api/v1/judge0/callback?secret={sub['callback_secret']}",
                   json={"token": sub["judge0_token"], "status": {"id": 3},
                         "stdout": base64.b64encode(b"1").decode()})
    report_id = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(owner)).json()["report_id"]
    assert report_id

    attacker = make_user(client)
    assert client.get(f"/api/v1/reports/{report_id}", headers=bearer(attacker)).status_code == 403
    assert client.get(f"/api/v1/reports/{report_id}").status_code == 401


# ─── Throttles ───────────────────────────────────────────────────────────────


def test_throttle_returns_429_past_daily_limit(client, monkeypatch):
    monkeypatch.setitem(throttle.DAILY_LIMITS, "badge_view", 3)
    for _ in range(3):
        assert client.get("/api/v1/badges/nonexistent").status_code == 404  # throttled but allowed
    blocked = client.get("/api/v1/badges/nonexistent")
    assert blocked.status_code == 429
    assert blocked.json()["error_code"] == "RATE_LIMITED"


def test_execute_endpoint_throttled(client, monkeypatch):
    monkeypatch.setitem(throttle.DAILY_LIMITS, "execute", 1)
    first = client.post("/api/execute", json={"language": "python3", "source_code": "print(1)", "stdin": ""})
    assert first.status_code in (200, 503)  # depends on judge0 config, but not throttled
    second = client.post("/api/execute", json={"language": "python3", "source_code": "print(1)", "stdin": ""})
    assert second.status_code == 429


def test_webhook_throttled(client, monkeypatch):
    monkeypatch.setitem(throttle.DAILY_LIMITS, "billing_webhook", 2)
    for i in range(2):
        client.post("/api/v1/billing/webhook/local", json={"event_id": f"e{i}", "type": "noop"},
                    headers={"X-Admin-Key": ADMIN_KEY})
    blocked = client.post("/api/v1/billing/webhook/local", json={"event_id": "e9", "type": "noop"},
                          headers={"X-Admin-Key": ADMIN_KEY})
    assert blocked.status_code == 429


# ─── Logging hygiene ─────────────────────────────────────────────────────────


def test_logs_contain_no_secrets_and_are_structured(client, caplog):
    user = make_user(client, plan="premium_student")
    with caplog.at_level(logging.INFO, logger="solvex.api"):
        client.get("/api/v1/me/entitlements", headers={**bearer(user), "X-Admin-Key": ADMIN_KEY})
    assert caplog.records, "access log expected"
    all_logs = " ".join(record.getMessage() for record in caplog.records)
    assert user["api_token"] not in all_logs
    assert ADMIN_KEY not in all_logs
    assert "Authorization" not in all_logs

    http_logs = [r.getMessage() for r in caplog.records if '"event": "http_request"' in r.getMessage()]
    assert http_logs, "structured http_request log expected"
    parsed = json.loads(http_logs[-1])
    for field in ("request_id", "trace_id", "method", "path", "status", "duration_ms"):
        assert field in parsed


def test_trace_id_propagates_end_to_end(client):
    response = client.get("/api/v1/health", headers={"X-Trace-Id": "trace-abc-123"})
    assert response.headers["X-Trace-Id"] == "trace-abc-123"
    assert response.headers["X-Request-ID"]

    # SkillTrace events carry the request id for traceability.
    user = make_user(client, plan="premium_student")
    session = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                          headers={**bearer(user), "X-Request-ID": "req-trace-1"}).json()
    with store.connect() as conn:
        row = conn.execute(
            "SELECT request_id FROM session_events WHERE session_id = ? AND seq = 1",
            (session["session_id"],),
        ).fetchone()
    assert row["request_id"] == "req-trace-1"


# ─── Metrics ─────────────────────────────────────────────────────────────────


def test_metrics_endpoint_reports_traffic_and_latency(client):
    client.get("/api/v1/health")
    client.get("/api/v1/health")
    response = client.get("/api/v1/metrics", headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 200
    body = response.text
    assert "http_requests_total_api_v1_health_2xx 2" in body
    assert "http_request_duration_ms_api_v1_health_p95_ms" in body


def test_analysis_metrics_recorded(client):
    client.post("/api/v1/weakness/some-handle/analyze", headers={"X-Admin-Key": ADMIN_KEY})
    snap = metrics.snapshot()
    assert snap["counters"].get("analysis_runs_total") == 1
    assert "analysis_latency_ms" in snap["latencies"]


# ─── Production settings validation ──────────────────────────────────────────


def test_production_requires_admin_key(monkeypatch):
    import importlib

    import contestiq_api.settings as settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    importlib.reload(settings)
    with pytest.raises(settings.SettingsError, match="ADMIN_API_KEY"):
        settings.get_settings()


def test_production_stripe_requires_webhook_secret(monkeypatch):
    import importlib

    import contestiq_api.settings as settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ADMIN_API_KEY", "prod-admin-key-0123456789")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", "https://example.supabase.co/auth/v1")
    monkeypatch.setenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://example.supabase.co/auth/v1/.well-known/jwks.json")
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    monkeypatch.delenv("BILLING_API_KEY", raising=False)
    monkeypatch.delenv("BILLING_WEBHOOK_SECRET", raising=False)
    importlib.reload(settings)
    with pytest.raises(settings.SettingsError, match="stripe"):
        settings.get_settings()


# ─── Hidden material never public ────────────────────────────────────────────


def test_no_route_exposes_challenge_test_sets(client):
    """No registered route path references hidden test material."""
    import contestiq_api.main as main

    for route in main.app.routes:
        path = getattr(route, "path", "")
        assert "test_set" not in path
        assert "hidden" not in path
