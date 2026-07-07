"""SkillTrace verification engine tests (Phase 07) — fake Judge0, no network."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import store
from contestiq_api.skilltrace import events as st_events
from contestiq_api.skilltrace import judge0 as j0

ADMIN_KEY = "test-admin-key"

# Exact hidden-test CONTENT from the seed bank that must never leave the
# backend (event-type names like "hidden_tests_started" are fine to appear).
HIDDEN_MARKERS = ["-1000000000 -1000000000", "999999999 1", "-2000000000", "1000000000\\n0"]


class FakeJudge0Transport:
    def __init__(self):
        self.posts = []       # (url, payload)
        self.next_token = 0
        self.poll_results = {}  # token -> judge0 payload

    def post(self, url, payload, headers):
        self.posts.append((url, payload))
        self.next_token += 1
        return {"token": f"tok-{self.next_token}"}

    def get(self, url, headers):
        token = url.rsplit("/", 1)[-1].split("?")[0]
        return self.poll_results.get(token, {"status": {"id": 2}})


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://fake-judge0")
    fake = FakeJudge0Transport()
    j0.set_adapter(j0.Judge0Adapter(post=fake.post, get=fake.get))
    yield fake
    j0.set_adapter(None)


@pytest.fixture
def fake(_isolated):
    return _isolated


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def make_user(client, role="user", premium=True):
    user = client.post("/api/v1/admin/users", json={"handle": "verify-user", "role": role},
                       headers={"X-Admin-Key": ADMIN_KEY}).json()
    if premium and role == "user":
        client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                    json={"plan": "premium_student"}, headers={"X-Admin-Key": ADMIN_KEY})
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def start(client, user, skill="implementation"):
    response = client.post("/api/v1/verification/sessions", json={"skill_id": skill}, headers=bearer(user))
    assert response.status_code == 200, response.text
    return response.json()


def submission_rows(attempt_kind=None):
    with store.connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT js.* , ea.kind FROM judge0_submissions js JOIN execution_attempts ea"
            " ON ea.attempt_id = js.attempt_id ORDER BY js.created_at, js.test_index").fetchall()]
    if attempt_kind:
        rows = [r for r in rows if r["kind"] == attempt_kind]
    return rows


def callback(client, submission, status_id=3, stdout="ok"):
    payload = {
        "token": submission["judge0_token"],
        "status": {"id": status_id},
        "stdout": base64.b64encode(stdout.encode()).decode(),
        "time": "0.013",
        "memory": 1520,
    }
    return client.put(f"/api/v1/judge0/callback?secret={submission['callback_secret']}", json=payload)


def full_pass_flow(client, user, *, snapshots=3, runs=1, fail_test_index=None):
    """Start → snapshots → run(s) → submit → drive all callbacks."""
    session = start(client, user)
    sid = session["session_id"]
    for i in range(snapshots):
        client.post(f"/api/v1/verification/sessions/{sid}/snapshot",
                    json={"code": f"# thinking v{i}\n"}, headers=bearer(user))
    for _ in range(runs):
        client.post(f"/api/v1/verification/sessions/{sid}/run",
                    json={"language": "python3", "source_code": "print(sum(map(int, input().split())))",
                          "stdin": "2 3"}, headers=bearer(user))
        for sub in submission_rows("run"):
            if sub["submission_status"] == "submitted":
                callback(client, sub)
    submit = client.post(f"/api/v1/verification/sessions/{sid}/submit",
                         json={"language": "python3",
                               "source_code": "print(sum(map(int, input().split())))"},
                         headers=bearer(user))
    assert submit.status_code == 200
    for sub in submission_rows("hidden"):
        status = 4 if fail_test_index is not None and sub["test_index"] == fail_test_index else 3
        callback(client, sub, status_id=status)
    return sid


# ─── Session start + leak protection ─────────────────────────────────────────


def test_start_session_returns_challenge_without_hidden_tests(client):
    user = make_user(client)
    session = start(client, user)
    assert session["challenge"]["statement"]
    assert session["challenge"]["examples"]
    text = json.dumps(session)
    for marker in HIDDEN_MARKERS:
        assert marker not in text, f"hidden test material leaked: {marker}"


def test_session_view_and_events_never_leak_hidden_tests_or_credentials(client, monkeypatch):
    monkeypatch.setenv("JUDGE0_API_KEY", "super-secret-judge0-key")
    user = make_user(client)
    sid = full_pass_flow(client, user)
    view = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(user)).json()
    events_view = client.get(f"/api/v1/verification/sessions/{sid}/events", headers=bearer(user)).json()
    text = json.dumps(view) + json.dumps(events_view)
    for marker in HIDDEN_MARKERS:
        assert marker not in text
    assert "super-secret-judge0-key" not in text
    assert "callback_secret" not in text


def test_session_requires_auth_and_entitlement_limit(client):
    anonymous = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"})
    assert anonymous.status_code == 401

    free_user = make_user(client, premium=False)
    first = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                        headers=bearer(free_user))
    assert first.status_code == 200
    second = client.post("/api/v1/verification/sessions", json={"skill_id": "implementation"},
                         headers=bearer(free_user))
    assert second.status_code == 429  # free plan: 1 verification attempt per week


def test_unknown_skill_has_no_challenge(client):
    user = make_user(client)
    response = client.post("/api/v1/verification/sessions", json={"skill_id": "quantum_sorting"},
                           headers=bearer(user))
    assert response.status_code == 404


# ─── Judge0 adapter behavior ─────────────────────────────────────────────────


def test_run_uses_wait_false_and_safety_limits(client, fake):
    user = make_user(client)
    session = start(client, user)
    response = client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                           json={"language": "python3", "source_code": "print(1)", "stdin": ""},
                           headers=bearer(user))
    assert response.status_code == 200
    url, payload = fake.posts[-1]
    assert "wait=false" in url
    assert "base64_encoded=true" in url
    assert payload["enable_network"] is False
    assert payload["cpu_time_limit"] == j0.CPU_TIME_LIMIT_S
    assert payload["memory_limit"] == j0.MEMORY_LIMIT_KB
    # source is base64, not plaintext
    assert payload["source_code"] == base64.b64encode(b"print(1)").decode()


def test_language_allowlist(client):
    user = make_user(client)
    session = start(client, user)
    response = client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                           json={"language": "java", "source_code": "class A {}", "stdin": ""},
                           headers=bearer(user))
    assert response.status_code == 422


def test_callback_base_embeds_secret(client, fake, monkeypatch):
    monkeypatch.setenv("JUDGE0_CALLBACK_BASE", "https://api.solvex.test")
    user = make_user(client)
    session = start(client, user)
    client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                json={"language": "python3", "source_code": "print(1)", "stdin": ""}, headers=bearer(user))
    _, payload = fake.posts[-1]
    sub = submission_rows("run")[0]
    assert payload["callback_url"] == (
        f"https://api.solvex.test/api/v1/judge0/callback?secret={sub['callback_secret']}"
    )


# ─── Callback handling ───────────────────────────────────────────────────────


def test_callback_updates_attempt_and_is_idempotent(client):
    user = make_user(client)
    session = start(client, user)
    client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                json={"language": "python3", "source_code": "print(1)", "stdin": ""}, headers=bearer(user))
    sub = submission_rows("run")[0]

    first = callback(client, sub)
    assert first.status_code == 200
    assert first.json()["status"] == "processed"
    updated = submission_rows("run")[0]
    assert updated["submission_status"] == "done"
    assert updated["passed"] == 1
    assert updated["callback_received_at"] is not None

    replay = callback(client, sub)
    assert replay.json()["status"] == "already_processed"
    with store.connect() as conn:
        result_events = conn.execute(
            "SELECT COUNT(*) FROM session_events WHERE event_type = 'judge0_result_received'"
        ).fetchone()[0]
    assert result_events == 1  # replay added no ledger events


def test_callback_with_bad_secret_rejected(client):
    user = make_user(client)
    session = start(client, user)
    client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                json={"language": "python3", "source_code": "print(1)", "stdin": ""}, headers=bearer(user))
    response = client.put("/api/v1/judge0/callback?secret=wrong-secret-value",
                          json={"token": "tok-1", "status": {"id": 3}})
    assert response.status_code == 403


def test_callback_token_mismatch_rejected(client):
    user = make_user(client)
    session = start(client, user)
    client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                json={"language": "python3", "source_code": "print(1)", "stdin": ""}, headers=bearer(user))
    sub = submission_rows("run")[0]
    response = client.put(f"/api/v1/judge0/callback?secret={sub['callback_secret']}",
                          json={"token": "tok-spoofed", "status": {"id": 3}})
    assert response.status_code == 403


def test_missed_callback_reconciled_by_polling(client, fake):
    user = make_user(client)
    session = start(client, user)
    client.post(f"/api/v1/verification/sessions/{session['session_id']}/run",
                json={"language": "python3", "source_code": "print(1)", "stdin": ""}, headers=bearer(user))
    sub = submission_rows("run")[0]
    fake.poll_results[sub["judge0_token"]] = {
        "token": sub["judge0_token"], "status": {"id": 3},
        "stdout": base64.b64encode(b"1").decode(), "time": "0.01", "memory": 900,
    }
    result = client.post("/api/v1/verification/reconcile?older_than_seconds=0",
                         headers={"X-Admin-Key": ADMIN_KEY})
    assert result.json()["reconciled"] == 1
    updated = submission_rows("run")[0]
    assert updated["submission_status"] == "done"
    assert updated["polled_at"] is not None


# ─── Event ledger ────────────────────────────────────────────────────────────


def test_event_chain_valid_and_tamper_detectable(client):
    user = make_user(client)
    sid = full_pass_flow(client, user)
    assert st_events.verify_chain(sid) is True

    with store.connect() as conn:
        conn.execute(
            "UPDATE session_events SET payload = '{\"tampered\": true}' WHERE session_id = ? AND seq = 3", (sid,)
        )
    assert st_events.verify_chain(sid) is False


def test_events_are_server_sequenced(client):
    user = make_user(client)
    sid = full_pass_flow(client, user)
    trail = st_events.list_events(sid)
    assert [e["seq"] for e in trail] == list(range(1, len(trail) + 1))
    assert trail[0]["event_type"] == "session_started"
    assert trail[1]["event_type"] == "problem_revealed"
    types = {e["event_type"] for e in trail}
    assert {"code_snapshot", "run_attempt_created", "hidden_tests_started",
            "hidden_tests_completed", "badge_decision_created"} <= types


# ─── Badge policy ────────────────────────────────────────────────────────────


def test_badge_issued_on_pass_with_sufficient_evidence(client):
    user = make_user(client)
    sid = full_pass_flow(client, user, snapshots=3, runs=1)
    view = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(user)).json()
    assert view["session_status"] == "completed"
    assert view["decision"]["decision"] == "issued"
    assert view["decision"]["process_evidence_label"] == "sufficient_process_evidence"
    assert view["badge"]["badge_public_id"]

    badge = client.get(f"/api/v1/badges/{view['badge']['badge_public_id']}")
    assert badge.status_code == 200
    data = badge.json()
    assert data["skill_id"] == "implementation"
    assert data["evidence_label"] == "sufficient_process_evidence"
    text = json.dumps(data).lower()
    for banned in ["cheat", "plagiar", "copied", "ai detected", "source_code", "hidden"]:
        assert banned not in text
    assert set(data) <= {"badge_public_id", "handle", "skill_id", "level", "evidence_label",
                         "badge_status", "issued_at", "interpretation"}


def test_no_badge_when_hidden_tests_fail(client):
    user = make_user(client)
    sid = full_pass_flow(client, user, fail_test_index=1)
    view = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(user)).json()
    assert view["decision"]["decision"] == "not_issued"
    assert "hidden_tests_failed" in view["decision"]["reasons"]
    assert view["badge"] is None
    # No accusations anywhere.
    text = json.dumps(view).lower()
    for banned in ["cheat", "plagiar", "copied", "ai detected"]:
        assert banned not in text


def test_low_evidence_pass_is_confidence_insufficient(client):
    user = make_user(client)
    sid = full_pass_flow(client, user, snapshots=0, runs=0)
    view = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(user)).json()
    assert view["decision"]["decision"] == "manual_review"
    assert view["decision"]["process_evidence_label"] == "verification_confidence_insufficient"
    assert "manual_review_recommended" in view["decision"]["reasons"]
    assert view["badge"] is None
    trail_types = {e["event_type"] for e in st_events.list_events(sid)}
    assert "manual_review_requested" in trail_types


def test_strong_evidence_label(client):
    user = make_user(client)
    sid = full_pass_flow(client, user, snapshots=6, runs=2)
    view = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(user)).json()
    assert view["decision"]["process_evidence_label"] == "strong_process_evidence"
    assert view["decision"]["decision"] == "issued"


# ─── Reports + BOLA ──────────────────────────────────────────────────────────


def test_private_report_owner_only(client):
    owner = make_user(client)
    sid = full_pass_flow(client, owner)
    report_id = client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(owner)).json()["report_id"]

    own = client.get(f"/api/v1/reports/{report_id}", headers=bearer(owner))
    assert own.status_code == 200
    assert own.json()["content"]["decision"] == "issued"
    assert "not claims about cheating" in own.json()["content"]["wording_note"]

    stranger = make_user(client)
    other = client.get(f"/api/v1/reports/{report_id}", headers=bearer(stranger))
    assert other.status_code == 403

    anonymous = client.get(f"/api/v1/reports/{report_id}")
    assert anonymous.status_code == 401


def test_session_bola_protection(client):
    owner = make_user(client)
    session = start(client, owner)
    sid = session["session_id"]
    stranger = make_user(client)

    assert client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(stranger)).status_code == 403
    assert client.post(f"/api/v1/verification/sessions/{sid}/snapshot", json={"code": "x"},
                       headers=bearer(stranger)).status_code == 403
    assert client.post(f"/api/v1/verification/sessions/{sid}/run",
                       json={"language": "python3", "source_code": "print(1)", "stdin": ""},
                       headers=bearer(stranger)).status_code == 403
    assert client.get(f"/api/v1/verification/sessions/{sid}").status_code == 401

    admin = make_user(client, role="admin")
    assert client.get(f"/api/v1/verification/sessions/{sid}", headers=bearer(admin)).status_code == 200


def test_snapshot_content_stored_by_hash_not_in_ledger(client):
    user = make_user(client)
    session = start(client, user)
    sid = session["session_id"]
    secret_code = "print('MY_PRIVATE_DRAFT_CODE')"
    client.post(f"/api/v1/verification/sessions/{sid}/snapshot", json={"code": secret_code}, headers=bearer(user))
    events_view = client.get(f"/api/v1/verification/sessions/{sid}/events", headers=bearer(user)).json()
    assert "MY_PRIVATE_DRAFT_CODE" not in json.dumps(events_view)
    snapshot_event = next(e for e in events_view["events"] if e["event_type"] == "code_snapshot")
    assert snapshot_event["payload_redaction_level"] == "hash_only"
    with store.connect() as conn:
        row = conn.execute("SELECT content FROM code_snapshots WHERE session_id = ?", (sid,)).fetchone()
    assert row["content"] == secret_code
