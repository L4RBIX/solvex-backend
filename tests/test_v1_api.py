import importlib
import json

import pytest
from fastapi.testclient import TestClient

from contestiq_api.metadata import METADATA_FIELDS


def _client(tmp_path, monkeypatch, extra_env=None):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONTESTIQ_API_OFFLINE_SAMPLE", "1")
    for name in [
        "APP_ENV",
        "ENABLE_DEBUG_ENDPOINT",
        "CORS_ORIGINS",
        "RATE_LIMIT_ANALYZE_SECONDS",
        "DATABASE_PATH",
        "LOG_LEVEL",
        "FEATURE_FLAGS",
    ]:
        monkeypatch.delenv(name, raising=False)
    for name, value in (extra_env or {}).items():
        monkeypatch.setenv(name, value)

    import contestiq_api.rate_limit as rate_limit

    rate_limit.reset_rate_limits()

    import contestiq_api.main as main

    importlib.reload(main)
    return TestClient(main.app)


# ─── Health ──────────────────────────────────────────────────────────────────


def test_v1_health(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "solvex-api"
    assert data["api_version"] == "v1"
    assert data["analysis_version"] == "ml_core_v0.4"
    assert data["taxonomy_version"]
    assert data["problem_catalog_version"]


def test_v1_route_paths_exist(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    paths = {route.path for route in client.app.routes}
    expected = {
        "/api/v1/health",
        "/api/v1/analysis/request",
        "/api/v1/analysis/jobs/{job_id}",
        "/api/v1/analysis/latest/{handle}",
        "/api/v1/compat/analyze/{handle}",
    }
    assert expected.issubset(paths)


def test_request_id_header_present(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/v1/health")
    assert response.headers["X-Request-ID"]
    echoed = client.get("/api/v1/health", headers={"X-Request-ID": "test-req-123"})
    assert echoed.headers["X-Request-ID"] == "test-req-123"


# ─── Analysis request / jobs ─────────────────────────────────────────────────


def test_analysis_request_creates_and_completes_job(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/v1/analysis/request", json={"handle": "sample-user"})
    assert response.status_code == 200
    data = response.json()
    for field in METADATA_FIELDS:
        assert field in data, f"missing metadata field {field}"
    assert data["reused"] is False
    job = data["job"]
    assert job["job_type"] == "analysis"
    assert job["status"] == "success"
    assert job["result_ref"] == "analysis/sample-user"
    assert job["created_at"] and job["started_at"] and job["completed_at"]
    assert data["data_cutoff_time"] is not None
    assert data["source"] == "offline_sample"


def test_analysis_request_reuses_completed_job(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    first = client.post("/api/v1/analysis/request", json={"handle": "reuse-user"}).json()
    second = client.post("/api/v1/analysis/request", json={"handle": "reuse-user"}).json()
    assert second["reused"] is True
    assert second["job"]["job_id"] == first["job"]["job_id"]


def test_analysis_request_force_refresh_creates_new_job(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    first = client.post("/api/v1/analysis/request", json={"handle": "fresh-user"}).json()
    second = client.post(
        "/api/v1/analysis/request", json={"handle": "fresh-user", "force_refresh": True}
    ).json()
    assert second["reused"] is False
    assert second["job"]["job_id"] != first["job"]["job_id"]


def test_analysis_request_idempotency_key_reuses_job(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    first = client.post(
        "/api/v1/analysis/request",
        json={"handle": "idem-user", "force_refresh": True, "idempotency_key": "key-1"},
    ).json()
    second = client.post(
        "/api/v1/analysis/request",
        json={"handle": "idem-user", "force_refresh": True, "idempotency_key": "key-1"},
    ).json()
    assert second["reused"] is True
    assert second["job"]["job_id"] == first["job"]["job_id"]


def test_analysis_request_idempotency_key_header(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    first = client.post(
        "/api/v1/analysis/request",
        json={"handle": "idem-header", "force_refresh": True},
        headers={"Idempotency-Key": "hdr-key"},
    ).json()
    second = client.post(
        "/api/v1/analysis/request",
        json={"handle": "idem-header", "force_refresh": True},
        headers={"Idempotency-Key": "hdr-key"},
    ).json()
    assert second["job"]["job_id"] == first["job"]["job_id"]


def test_job_status_endpoint(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post("/api/v1/analysis/request", json={"handle": "job-user"}).json()
    job_id = created["job"]["job_id"]
    response = client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job"]["job_id"] == job_id
    assert data["job"]["status"] == "success"
    for field in METADATA_FIELDS:
        assert field in data


def test_job_status_not_found(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/v1/analysis/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error_code"] == "JOB_NOT_FOUND"


def test_failed_analysis_marks_job_failed(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    import contestiq_api.routes.v1 as v1
    from contestiq_api.errors import APIError

    def _boom(handle, debug=False, force_refresh=False):
        raise APIError("CODEFORCES_UNAVAILABLE", "down", 502)

    monkeypatch.setattr(v1, "analyze_codeforces_handle", _boom)
    response = client.post(
        "/api/v1/analysis/request", json={"handle": "fail-user", "force_refresh": True}
    )
    assert response.status_code == 502

    from contestiq_api.jobs import find_latest_job

    job = find_latest_job("analysis", {"handle": "fail-user"})
    assert job is not None
    assert job["status"] == "failed"
    assert "CODEFORCES_UNAVAILABLE" in job["error_message"]


def test_invalid_handle_rejected_before_job_creation(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/v1/analysis/request", json={"handle": "bad handle!!"})
    assert response.status_code == 422

    from contestiq_api.jobs import find_latest_job

    assert find_latest_job("analysis", {}) is None


# ─── Latest analysis ─────────────────────────────────────────────────────────


def test_latest_analysis_includes_metadata(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/v1/analysis/request", json={"handle": "latest-user"})
    response = client.get("/api/v1/analysis/latest/latest-user")
    assert response.status_code == 200
    data = response.json()
    for field in METADATA_FIELDS:
        assert field in data
    assert data["handle"] == "latest-user"
    assert "weakness_map_user" in data["analysis"]
    assert "daily_queue" in data["analysis"]
    assert "skill_scores" not in data["analysis"]
    assert data["data_cutoff_time"] == data["analysis"]["created_at"]


def test_latest_analysis_not_found(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/v1/analysis/latest/missing-user")
    assert response.status_code == 404
    assert response.json()["error_code"] == "ANALYSIS_NOT_FOUND"


# ─── Job store unit tests ────────────────────────────────────────────────────


def test_job_store_create_and_get(tmp_path, monkeypatch):
    _client(tmp_path, monkeypatch)
    from contestiq_api import jobs

    job = jobs.create_job("analysis", {"handle": "unit-user"})
    assert job["status"] == "queued"
    assert jobs.get_job(job["id"])["input"] == {"handle": "unit-user"}


def test_job_store_idempotency_conflict_returns_existing(tmp_path, monkeypatch):
    _client(tmp_path, monkeypatch)
    from contestiq_api import jobs

    first = jobs.create_job("analysis", {"handle": "a"}, idempotency_key="dup")
    second = jobs.create_job("analysis", {"handle": "a"}, idempotency_key="dup")
    assert first["id"] == second["id"]


def test_job_store_transitions(tmp_path, monkeypatch):
    _client(tmp_path, monkeypatch)
    from contestiq_api import jobs

    job = jobs.create_job("analysis", {"handle": "t"})
    jobs.mark_running(job["id"])
    assert jobs.get_job(job["id"])["status"] == "running"
    jobs.mark_finished(job["id"], "stale_cache_used", result_ref="analysis/t")
    refreshed = jobs.get_job(job["id"])
    assert refreshed["status"] == "stale_cache_used"
    assert refreshed["completed_at"] is not None


def test_job_store_rejects_invalid_terminal_status(tmp_path, monkeypatch):
    _client(tmp_path, monkeypatch)
    from contestiq_api import jobs

    job = jobs.create_job("analysis", {"handle": "x"})
    with pytest.raises(ValueError):
        jobs.mark_finished(job["id"], "queued")


# ─── Settings ────────────────────────────────────────────────────────────────


def test_settings_new_fields_defaults(monkeypatch):
    for name in ["DATABASE_PATH", "LOG_LEVEL", "FEATURE_FLAGS", "CODEFORCES_RATE_LIMIT_SECONDS", "APP_ENV"]:
        monkeypatch.delenv(name, raising=False)
    import contestiq_api.settings as settings

    importlib.reload(settings)
    parsed = settings.get_settings()
    assert parsed.database_path == "api_cache/backend_jobs.db"
    assert parsed.log_level == "INFO"
    assert parsed.codeforces_rate_limit_seconds == 2.0
    assert parsed.codeforces_max_retries == 3
    assert parsed.feature_flags == frozenset()
    assert parsed.billing_provider == "manual"


def test_settings_feature_flags_parse(monkeypatch):
    monkeypatch.setenv("FEATURE_FLAGS", "SkillTrace, beta_queue ,")
    import contestiq_api.settings as settings

    importlib.reload(settings)
    parsed = settings.get_settings()
    assert parsed.feature_flags == frozenset({"skilltrace", "beta_queue"})
    assert parsed.flag_enabled("SkillTrace")
    assert not parsed.flag_enabled("missing")


def test_settings_invalid_log_level_raises(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "LOUD")
    import contestiq_api.settings as settings

    importlib.reload(settings)
    with pytest.raises(settings.SettingsError):
        settings.get_settings()
    monkeypatch.delenv("LOG_LEVEL")


def test_settings_invalid_app_env_raises(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod-like")
    import contestiq_api.settings as settings

    importlib.reload(settings)
    with pytest.raises(settings.SettingsError):
        settings.get_settings()
    monkeypatch.delenv("APP_ENV")


# ─── Legacy compat adapter ───────────────────────────────────────────────────


def _fixture_user():
    return {
        "handle": "fixture-user",
        "rating": 1400,
        "maxRating": 1500,
        "rank": "specialist",
        "maxRank": "specialist",
        "country": "Kazakhstan",
    }


def _fixture_submissions():
    # Newest-first, as the Codeforces API returns them.
    def sub(sid, cid, index, name, rating, tags, verdict, lang="GNU C++17"):
        return {
            "id": sid,
            "contestId": cid,
            "problem": {"contestId": cid, "index": index, "name": name, "rating": rating, "tags": tags},
            "programmingLanguage": lang,
            "verdict": verdict,
            "creationTimeSeconds": 1700000000 + sid,
        }

    subs = []
    sid = 100
    # Three dp problems with heavy WA friction (one unsolved), meeting tag minimums.
    for cid, solved in ((1, True), (2, True), (3, False)):
        subs.append(sub(sid := sid + 1, cid, "A", f"DP {cid}", 1200, ["dp"], "WRONG_ANSWER"))
        subs.append(sub(sid := sid + 1, cid, "A", f"DP {cid}", 1200, ["dp"], "WRONG_ANSWER"))
        if solved:
            subs.append(sub(sid := sid + 1, cid, "A", f"DP {cid}", 1200, ["dp"], "OK"))
    # Greedy problems solved first try.
    for cid in (10, 11, 12):
        subs.append(sub(sid := sid + 1, cid, "B", f"Greedy {cid}", 1100, ["greedy"], "OK", lang="Python 3"))
    subs.reverse()  # newest first overall
    return subs


def test_legacy_compat_shape_matches_frontend_contract(tmp_path, monkeypatch):
    from contestiq_api.legacy_compat import legacy_analysis

    result = legacy_analysis(_fixture_user(), _fixture_submissions())
    assert set(result) == {
        "handle",
        "profile",
        "summary",
        "diagnosis",
        "frictionAreas",
        "strongTopics",
        "errorBreakdown",
        "ratingComfortZone",
        "recommendedProblems",
        "sevenDayQueue",
    }
    assert result["profile"]["rating"] == 1400
    assert result["profile"]["organization"] == ""
    assert result["summary"]["uniqueSolved"] == 5
    assert result["summary"]["totalSubmissions"] == 11
    assert result["errorBreakdown"]["wrongAnswer"] == 6
    assert len(result["sevenDayQueue"]) == 7
    assert result["sevenDayQueue"][6]["focus"] == "Review & Reinforce"


def test_legacy_compat_finds_dp_friction(tmp_path, monkeypatch):
    from contestiq_api.legacy_compat import legacy_analysis

    result = legacy_analysis(_fixture_user(), _fixture_submissions())
    tags = [area["tag"] for area in result["frictionAreas"]]
    assert "dp" in tags
    dp = next(area for area in result["frictionAreas"] if area["tag"] == "dp")
    assert dp["waCount"] == 6
    assert dp["solved"] == 2
    assert dp["attempted"] == 3
    assert dp["issue"] == "High wrong-answer rate"
    unsolved = [p for p in result["recommendedProblems"] if "unresolved" in p["reason"]]
    assert any(p["name"] == "DP 3" for p in unsolved)


def test_legacy_compat_no_friction_diagnosis(tmp_path, monkeypatch):
    from contestiq_api.legacy_compat import legacy_analysis

    result = legacy_analysis(_fixture_user(), [])
    assert "No significant friction patterns detected" in result["diagnosis"]
    assert result["frictionAreas"] == []
    assert result["ratingComfortZone"] == {"min": 800, "max": 1200, "sweet": 1000}


def test_compat_route_serves_legacy_shape(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    import contestiq_api.routes.v1 as v1

    monkeypatch.setattr(v1, "fetch_user_info", lambda handle: _fixture_user())
    monkeypatch.setattr(v1, "fetch_user_status", lambda handle, count=None: _fixture_submissions())
    response = client.get("/api/v1/compat/analyze/fixture-user")
    assert response.status_code == 200
    data = response.json()
    assert data["handle"] == "fixture-user"
    assert "frictionAreas" in data
    assert "sevenDayQueue" in data
    assert data["_meta"]["analysis_version"] == "ml_core_v0.4"


def test_compat_route_maps_not_found(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    import contestiq_api.routes.v1 as v1
    from contestiq_core.codeforces.client import CodeforcesAPIError

    def _missing(handle):
        raise CodeforcesAPIError("Codeforces handle not found: ghost-user-404")

    monkeypatch.setattr(v1, "fetch_user_info", _missing)
    response = client.get("/api/v1/compat/analyze/ghost-user-404")
    assert response.status_code == 404
    assert response.json()["error_code"] == "CODEFORCES_HANDLE_NOT_FOUND"


def test_legacy_client_maps_http_400_to_comment_without_retry(tmp_path, monkeypatch):
    """QA regression (2026-07-08): Codeforces answers HTTP 400 for unknown
    handles; the client must surface the comment (containing 'not found')
    immediately instead of retrying and reporting 'unavailable'."""
    monkeypatch.chdir(tmp_path)
    import contestiq_core.codeforces.client as legacy_client

    calls = {"n": 0}

    class FakeResponse:
        status_code = 400

        @staticmethod
        def json():
            return {"status": "FAILED", "comment": "handles: User with handle ghost-x not found"}

        @staticmethod
        def raise_for_status():
            raise AssertionError("raise_for_status must not be reached for HTTP 400")

    def fake_get(url, params=None, timeout=None):
        calls["n"] += 1
        return FakeResponse()

    monkeypatch.setattr(legacy_client.requests, "get", fake_get)
    with pytest.raises(legacy_client.CodeforcesAPIError, match="not found"):
        legacy_client.fetch_user_info("ghost-x")
    assert calls["n"] == 1  # no retries for a bad request
