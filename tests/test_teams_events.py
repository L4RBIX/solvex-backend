"""Teams, coaches, orgs, and event screening tests (Phase 08)."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from contestiq_api.cfdata import store
from contestiq_api.skilltrace import judge0 as j0

ADMIN_KEY = "test-admin-key"


class FakeJudge0Transport:
    def __init__(self):
        self.posts = []
        self.next_token = 0

    def post(self, url, payload, headers):
        self.posts.append((url, payload))
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
    j0.set_adapter(j0.Judge0Adapter(post=FakeJudge0Transport().post, get=FakeJudge0Transport().get))
    yield
    j0.set_adapter(None)


@pytest.fixture
def client():
    import contestiq_api.main as main

    return TestClient(main.app)


def make_user(client, handle=None, plan=None, role="user"):
    user = client.post("/api/v1/admin/users", json={"handle": handle, "role": role},
                       headers={"X-Admin-Key": ADMIN_KEY}).json()
    if plan:
        client.post(f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
                    json={"plan": plan}, headers={"X-Admin-Key": ADMIN_KEY})
    return user


def bearer(user):
    return {"Authorization": f"Bearer {user['api_token']}"}


def make_team(client, owner):
    return client.post("/api/v1/teams", json={"name": "CP Club"}, headers=bearer(owner)).json()


def join(client, team_id, owner, member, role="student"):
    invite = client.post(f"/api/v1/teams/{team_id}/invites",
                         json={"member_role": role}, headers=bearer(owner)).json()
    accept = client.post("/api/v1/teams/invites/accept",
                         json={"token": invite["invite_token"]}, headers=bearer(member))
    assert accept.status_code == 200
    return invite


# ─── Teams ───────────────────────────────────────────────────────────────────


def test_team_creation_requires_team_entitlement(client):
    free_user = make_user(client)
    assert client.post("/api/v1/teams", json={"name": "Nope"}, headers=bearer(free_user)).status_code == 402

    coach = make_user(client, plan="team")
    team = make_team(client, coach)
    assert team["role"] == "owner"


def test_invite_accept_flow_and_single_use(client):
    owner = make_user(client, plan="team")
    team = make_team(client, owner)
    student = make_user(client, handle="student-one")

    invite = join(client, team["team_id"], owner, student)
    members = client.get(f"/api/v1/teams/{team['team_id']}/students", headers=bearer(owner)).json()["members"]
    roles = {m["user_id"]: m["member_role"] for m in members}
    assert roles[student["user_id"]] == "student"
    assert roles[owner["user_id"]] == "owner"

    reused = client.post("/api/v1/teams/invites/accept",
                         json={"token": invite["invite_token"]}, headers=bearer(make_user(client)))
    assert reused.status_code == 409


def test_expired_invite_rejected(client):
    owner = make_user(client, plan="team")
    team = make_team(client, owner)
    invite = client.post(f"/api/v1/teams/{team['team_id']}/invites",
                         json={"member_role": "student"}, headers=bearer(owner)).json()
    with store.connect() as conn:
        conn.execute("UPDATE team_invites SET expires_at = '2020-01-01T00:00:00+00:00' WHERE invite_id = ?",
                     (invite["invite_id"],))
    late = client.post("/api/v1/teams/invites/accept",
                       json={"token": invite["invite_token"]}, headers=bearer(make_user(client)))
    assert late.status_code == 410


def test_coach_sees_only_own_team(client):
    owner = make_user(client, plan="team")
    team = make_team(client, owner)
    coach = make_user(client)
    join(client, team["team_id"], owner, coach, role="coach")

    assert client.get(f"/api/v1/teams/{team['team_id']}/students", headers=bearer(coach)).status_code == 200

    outsider = make_user(client, plan="team")  # entitled but NOT a member
    assert client.get(f"/api/v1/teams/{team['team_id']}/students", headers=bearer(outsider)).status_code == 403
    assert client.get(f"/api/v1/teams/{team['team_id']}/dashboard", headers=bearer(outsider)).status_code == 403

    student = make_user(client)
    join(client, team["team_id"], owner, student)
    assert client.get(f"/api/v1/teams/{team['team_id']}/students", headers=bearer(student)).status_code == 403
    assert client.get(f"/api/v1/teams/{team['team_id']}/dashboard", headers=bearer(student)).status_code == 403


def test_assignment_authorization(client):
    owner = make_user(client, plan="team")
    team = make_team(client, owner)
    tid = team["team_id"]
    student_a = make_user(client, handle="stud-a")
    student_b = make_user(client, handle="stud-b")
    join(client, tid, owner, student_a)
    join(client, tid, owner, student_b)

    ok = client.post(f"/api/v1/teams/{tid}/assignments",
                     json={"student_user_id": student_a["user_id"], "kind": "skill_focus",
                           "skill_id": "dynamic_programming", "notes": "Focus on knapsack this week"},
                     headers=bearer(owner))
    assert ok.status_code == 200

    non_member = make_user(client)
    missing = client.post(f"/api/v1/teams/{tid}/assignments",
                          json={"student_user_id": non_member["user_id"], "kind": "skill_focus"},
                          headers=bearer(owner))
    assert missing.status_code == 404  # coach cannot target a non-member

    forbidden = client.post(f"/api/v1/teams/{tid}/assignments",
                            json={"student_user_id": student_b["user_id"], "kind": "problems"},
                            headers=bearer(student_a))
    assert forbidden.status_code == 403  # students cannot assign

    client.post(f"/api/v1/teams/{tid}/assignments",
                json={"student_user_id": student_b["user_id"], "kind": "problems",
                      "problem_ids": ["100A", "200B"]}, headers=bearer(owner))
    own_view = client.get(f"/api/v1/teams/{tid}/assignments", headers=bearer(student_a)).json()["assignments"]
    assert len(own_view) == 1
    assert own_view[0]["student_user_id"] == student_a["user_id"]  # students see own only
    coach_view = client.get(f"/api/v1/teams/{tid}/assignments", headers=bearer(owner)).json()["assignments"]
    assert len(coach_view) == 2


def test_team_dashboard_summarizes_students(client):
    from contestiq_api.cfdata import episodes, taxonomy, weakness

    handle = "dash-student"
    subs = []
    for i in range(8):
        for j in range(3):
            subs.append({
                "id": i * 10 + j, "contestId": 300 + i, "creationTimeSeconds": 1700000000 - i * 86400,
                "problem": {"contestId": 300 + i, "index": "A", "name": f"P{i}", "rating": 1400, "tags": ["dp"]},
                "author": {"members": [{"handle": handle}], "participantType": "PRACTICE"},
                "programmingLanguage": "GNU C++17", "verdict": "WRONG_ANSWER",
                "passedTestCount": 1, "timeConsumedMillis": 10, "memoryConsumedBytes": 100,
            })
    store.upsert_user({"handle": handle, "rating": 1500})
    store.upsert_submissions(handle, subs)
    store.save_problemset_snapshot({"problems": [
        {"contestId": 300 + i, "index": "A", "name": f"P{i}", "rating": 1400, "tags": ["dp"]} for i in range(8)
    ], "problemStatistics": []})
    taxonomy.build_problem_skill_map()
    episodes.rebuild_episodes(handle)
    weakness.analyze_handle_weakness(handle)

    owner = make_user(client, plan="team")
    team = make_team(client, owner)
    student = make_user(client, handle=handle)
    join(client, team["team_id"], owner, student)
    no_data_student = make_user(client, handle="no-data-yet")
    join(client, team["team_id"], owner, no_data_student)

    dashboard = client.get(f"/api/v1/teams/{team['team_id']}/dashboard", headers=bearer(owner)).json()
    assert dashboard["student_count"] == 2
    by_handle = {e["handle"]: e for e in dashboard["students"]}
    with_data = by_handle[handle]
    assert with_data["summary"]["has_analysis"] is True
    assert len(with_data["summary"]["top_weaknesses"]) <= 3
    assert by_handle["no-data-yet"]["summary"]["has_analysis"] is False

    with store.connect() as conn:
        snapshots = conn.execute("SELECT COUNT(*) FROM team_student_snapshots").fetchone()[0]
    assert snapshots == 2
    client.get(f"/api/v1/teams/{team['team_id']}/dashboard", headers=bearer(owner))
    with store.connect() as conn:
        snapshots_after = conn.execute("SELECT COUNT(*) FROM team_student_snapshots").fetchone()[0]
    assert snapshots_after == 2  # at most one snapshot per student per day


# ─── Orgs + events ───────────────────────────────────────────────────────────


def make_org_event(client, organizer):
    org = client.post("/api/v1/orgs", json={"name": "HackFest"}, headers=bearer(organizer)).json()
    event = client.post(f"/api/v1/orgs/{org['org_id']}/events",
                        json={"name": "Screening 2026",
                              "requirements": [{"skill_id": "implementation", "level": 1}]},
                        headers=bearer(organizer)).json()
    return org, event


def test_org_and_event_require_event_entitlement(client):
    free_user = make_user(client)
    assert client.post("/api/v1/orgs", json={"name": "Nope"}, headers=bearer(free_user)).status_code == 402

    organizer = make_user(client, plan="event")
    org, event = make_org_event(client, organizer)
    assert event["requirements"][0]["skill_id"] == "implementation"


def test_applicant_link_lifecycle(client):
    organizer = make_user(client, plan="event")
    _, event = make_org_event(client, organizer)

    link = client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                       json={"display_name": "Alice"}, headers=bearer(organizer)).json()
    assert link["link_token"]

    started = client.post(f"/api/v1/events/links/{link['link_token']}/start")
    assert started.status_code == 200
    body = started.json()
    assert body["api_token"]
    assert body["session"]["challenge"]["statement"]

    reused = client.post(f"/api/v1/events/links/{link['link_token']}/start")
    assert reused.status_code == 409  # single use

    stale = client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                        json={"display_name": "Bob"}, headers=bearer(organizer)).json()
    with store.connect() as conn:
        conn.execute("UPDATE event_verification_links SET expires_at = '2020-01-01T00:00:00+00:00'"
                     " WHERE token_hash = ?", (__import__('hashlib').sha256(stale['link_token'].encode()).hexdigest(),))
    expired = client.post(f"/api/v1/events/links/{stale['link_token']}/start")
    assert expired.status_code == 410


def test_expired_event_blocks_links(client):
    organizer = make_user(client, plan="event")
    _, event = make_org_event(client, organizer)
    with store.connect() as conn:
        conn.execute("UPDATE org_events SET expires_at = '2020-01-01T00:00:00+00:00' WHERE event_id = ?",
                     (event["event_id"],))
    blocked = client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                          json={"display_name": "Late"}, headers=bearer(organizer))
    assert blocked.status_code == 410
    dashboard = client.get(f"/api/v1/events/{event['event_id']}/dashboard", headers=bearer(organizer)).json()
    assert dashboard["event_status"] == "expired"


def test_cross_org_bola_denied(client):
    organizer_a = make_user(client, plan="event")
    _, event_a = make_org_event(client, organizer_a)
    organizer_b = make_user(client, plan="event")
    make_org_event(client, organizer_b)

    assert client.get(f"/api/v1/events/{event_a['event_id']}/dashboard",
                      headers=bearer(organizer_b)).status_code == 403
    assert client.post(f"/api/v1/events/{event_a['event_id']}/applicant-links",
                       json={}, headers=bearer(organizer_b)).status_code == 403
    assert client.get(f"/api/v1/events/{event_a['event_id']}/dashboard").status_code == 401

    other_org_event = client.post(f"/api/v1/orgs/{event_a['org_id']}/events",
                                  json={"name": "Sneaky", "requirements": [{"skill_id": "greedy"}]},
                                  headers=bearer(organizer_b))
    assert other_org_event.status_code == 403


def _complete_applicant(client, link_token):
    """Applicant completes the challenge via the standard SkillTrace endpoints."""
    started = client.post(f"/api/v1/events/links/{link_token}/start").json()
    token_headers = {"Authorization": f"Bearer {started['api_token']}"}
    sid = started["session"]["session_id"]
    for i in range(3):
        client.post(f"/api/v1/verification/sessions/{sid}/snapshot", json={"code": f"# v{i}"}, headers=token_headers)
    code = "print(sum(map(int, input().split())))"
    client.post(f"/api/v1/verification/sessions/{sid}/run",
                json={"language": "python3", "source_code": code, "stdin": "1 2"}, headers=token_headers)
    with store.connect() as conn:
        subs = [dict(r) for r in conn.execute(
            "SELECT js.* FROM judge0_submissions js JOIN execution_attempts ea ON ea.attempt_id = js.attempt_id"
            " WHERE ea.session_id = ? AND js.submission_status = 'submitted'", (sid,)).fetchall()]
    for sub in subs:
        client.put(f"/api/v1/judge0/callback?secret={sub['callback_secret']}",
                   json={"token": sub["judge0_token"], "status": {"id": 3},
                         "stdout": base64.b64encode(b"3").decode(), "time": "0.01", "memory": 100})
    client.post(f"/api/v1/verification/sessions/{sid}/submit",
                json={"language": "python3", "source_code": code}, headers=token_headers)
    with store.connect() as conn:
        subs = [dict(r) for r in conn.execute(
            "SELECT js.* FROM judge0_submissions js JOIN execution_attempts ea ON ea.attempt_id = js.attempt_id"
            " WHERE ea.session_id = ? AND js.submission_status = 'submitted'", (sid,)).fetchall()]
    for sub in subs:
        client.put(f"/api/v1/judge0/callback?secret={sub['callback_secret']}",
                   json={"token": sub["judge0_token"], "status": {"id": 3},
                         "stdout": base64.b64encode(b"ok").decode(), "time": "0.01", "memory": 100})
    return started["applicant_id"]


def test_dashboard_ranks_and_stays_sanitized(client):
    organizer = make_user(client, plan="event")
    _, event = make_org_event(client, organizer)
    done_link = client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                            json={"display_name": "Finisher"}, headers=bearer(organizer)).json()
    applicant_id = _complete_applicant(client, done_link["link_token"])
    client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                json={"display_name": "NeverStarted"}, headers=bearer(organizer))

    dashboard = client.get(f"/api/v1/events/{event['event_id']}/dashboard", headers=bearer(organizer)).json()
    assert dashboard["applicant_count"] == 2
    first, second = dashboard["applicants"]
    assert first["applicant_id"] == applicant_id
    assert first["status"] == "completed"
    assert first["decision"] == "issued"
    assert first["hidden_pass_rate"] == 1.0
    assert first["badge_public_id"]
    assert second["status"] == "invited"

    text = json.dumps(dashboard).lower()
    for banned in ["callback_secret", "source_code", "print(sum", "cheat", "plagiar", "api_token"]:
        assert banned not in text


def test_report_export_requires_scope_and_is_audited(client):
    organizer = make_user(client, plan="event")
    _, event = make_org_event(client, organizer)
    link = client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                       json={"display_name": "Alice"}, headers=bearer(organizer)).json()
    applicant_id = _complete_applicant(client, link["link_token"])

    stranger = make_user(client, plan="event")
    denied = client.get(f"/api/v1/events/{event['event_id']}/applicants/{applicant_id}/report",
                        headers=bearer(stranger))
    assert denied.status_code == 403

    report = client.get(f"/api/v1/events/{event['event_id']}/applicants/{applicant_id}/report",
                        headers=bearer(organizer))
    assert report.status_code == 200
    assert report.json()["report"]["decision"] == "issued"

    with store.connect() as conn:
        exports = conn.execute("SELECT * FROM event_report_exports").fetchall()
        audits = conn.execute(
            "SELECT * FROM admin_audit_logs WHERE action = 'event_report_export'"
        ).fetchall()
    assert len(exports) == 1
    assert exports[0]["exported_by"] == f"user:{organizer['user_id']}"
    assert len(audits) == 1


def test_report_before_completion_not_ready(client):
    organizer = make_user(client, plan="event")
    _, event = make_org_event(client, organizer)
    link = client.post(f"/api/v1/events/{event['event_id']}/applicant-links",
                       json={"display_name": "Slow"}, headers=bearer(organizer)).json()
    started = client.post(f"/api/v1/events/links/{link['link_token']}/start").json()
    response = client.get(
        f"/api/v1/events/{event['event_id']}/applicants/{started['applicant_id']}/report",
        headers=bearer(organizer))
    assert response.status_code == 409
