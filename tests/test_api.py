import importlib
import json

from fastapi.testclient import TestClient

SECURITY_ADMIN_KEY = "legacy-route-security-key"


def _admin_headers():
    return {"X-Admin-Key": SECURITY_ADMIN_KEY}


def _client(tmp_path, monkeypatch, extra_env=None):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONTESTIQ_API_OFFLINE_SAMPLE", "1")
    monkeypatch.setenv("ADMIN_API_KEY", SECURITY_ADMIN_KEY)
    for name in ["APP_ENV", "ENABLE_DEBUG_ENDPOINT", "CORS_ORIGINS", "RATE_LIMIT_ANALYZE_SECONDS"]:
        monkeypatch.delenv(name, raising=False)
    for name, value in (extra_env or {}).items():
        monkeypatch.setenv(name, value)
    import contestiq_api.settings as settings
    import contestiq_api.rate_limit as rate_limit
    import contestiq_api.storage as storage
    import contestiq_api.service as service
    import contestiq_api.workspace as workspace
    import contestiq_api.routes.analysis as analysis_routes
    import contestiq_api.routes.feedback as feedback_routes
    import contestiq_api.routes.health as health_routes
    import contestiq_api.routes.execute as execute_routes
    import contestiq_api.routes.share as share_routes
    import contestiq_api.routes.workspace as workspace_routes
    import contestiq_api.main as main

    importlib.reload(settings)
    importlib.reload(rate_limit)
    importlib.reload(storage)
    importlib.reload(workspace)
    importlib.reload(service)
    importlib.reload(analysis_routes)
    importlib.reload(feedback_routes)
    importlib.reload(health_routes)
    importlib.reload(execute_routes)
    importlib.reload(share_routes)
    importlib.reload(workspace_routes)
    importlib.reload(main)

    return TestClient(main.app)


def _verified_headers(client, handle, *, premium=False):
    user_response = client.post("/api/v1/auth/register")
    assert user_response.status_code == 200
    user = user_response.json()
    admin_headers = {"X-Admin-Key": SECURITY_ADMIN_KEY}
    bound = client.post(
        "/api/v1/admin/handles/bind",
        json={"user_id": user["user_id"], "handle": handle},
        headers=admin_headers,
    )
    assert bound.status_code == 200
    if premium:
        granted = client.post(
            f"/api/v1/admin/users/{user['user_id']}/grant-entitlement",
            json={"plan": "premium_student"},
            headers=admin_headers,
        )
        assert granted.status_code == 200
    return {"Authorization": f"Bearer {user['api_token']}"}


def _route_paths(client):
    # Newer Starlette groups included routers behind `_IncludedRouter` wrapper
    # objects (exposing `original_router` instead of `.path`); recurse through
    # both `.routes` and `.original_router.routes` so this keeps working
    # across Starlette versions.
    def walk(routes):
        paths = set()
        for route in routes:
            path = getattr(route, "path", None)
            if path is not None:
                paths.add(path)
            sub_routes = getattr(route, "routes", None)
            if sub_routes:
                paths |= walk(sub_routes)
            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                paths |= walk(original_router.routes)
        return paths

    return walk(client.app.routes)


def test_health_endpoint(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "contestiq-api"
    assert data["model_version"] == "ml_core_v0.4"
    # Judge0 flags depend on the local .env; assert presence and type only.
    assert isinstance(data["judge0_configured"], bool)
    assert isinstance(data["judge0_reachable"], bool)


def test_existing_route_paths_are_preserved(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    expected = {
        "/api/health",
        "/api/execute",
        "/api/analyze",
        "/api/analysis/{handle}",
        "/api/analysis/{handle}/weakness-map",
        "/api/analysis/{handle}/daily-queue",
        "/api/analysis/{handle}/debug",
        "/api/analysis/{handle}/progress",
        "/api/analysis/{handle}/history",
        "/api/analysis/{handle}/weekly-report",
        "/api/analysis/{handle}/weekly-report.md",
        "/api/analysis/{handle}/share",
        "/api/share/{share_id}",
        "/api/share/{share_id}.md",
        "/api/feedback/problem",
        "/api/outcome/problem",
        "/api/feedback/queue",
        "/api/feedback/summary",
        "/api/feedback/summary.md",
        "/api/workspace/handles",
        "/api/workspace/handles/{handle}",
        "/api/workspace/dashboard",
    }
    assert expected.issubset(_route_paths(client))


def test_execute_rejects_unsupported_language(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/execute",
        json={"language": "javascript", "source_code": "console.log('hi')", "stdin": ""},
    )
    assert response.status_code == 422
    assert response.json() == {
        "status": "failed",
        "error_code": "unsupported_language",
        "message": "Unsupported language. This MVP supports only C++17 and Python 3.",
    }


def test_execute_supported_language_ids_are_mvp_only():
    from contestiq_api.routes.execute import _LANGUAGE_IDS

    assert _LANGUAGE_IDS == {"cpp17": 54, "python3": 71}


def test_settings_defaults(monkeypatch):
    for name in ["APP_ENV", "ENABLE_DEBUG_ENDPOINT", "CORS_ORIGINS", "RATE_LIMIT_ANALYZE_SECONDS"]:
        monkeypatch.delenv(name, raising=False)
    import contestiq_api.settings as settings

    importlib.reload(settings)
    parsed = settings.get_settings()
    assert parsed.app_env == "development"
    assert parsed.enable_debug_endpoint is True
    assert parsed.rate_limit_analyze_seconds == 0
    assert "http://localhost:5173" in parsed.cors_origins


def test_custom_cors_origins_parse(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, http://localhost:3000 ")
    import contestiq_api.settings as settings

    importlib.reload(settings)
    assert settings.get_settings().cors_origins == ["https://app.example.com", "http://localhost:3000"]


def test_production_settings_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ADMIN_API_KEY", "prod-admin-key-0123456789")  # production requires it (Phase 09)
    monkeypatch.delenv("ENABLE_DEBUG_ENDPOINT", raising=False)
    monkeypatch.delenv("RATE_LIMIT_ANALYZE_SECONDS", raising=False)
    import contestiq_api.settings as settings

    importlib.reload(settings)
    parsed = settings.get_settings()
    assert parsed.enable_debug_endpoint is False
    assert parsed.rate_limit_analyze_seconds == 30


def test_cors_origins_are_loaded_from_settings(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, {"CORS_ORIGINS": "https://app.example.com"})
    response = client.options(
        "/api/health",
        headers={"Origin": "https://app.example.com", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_analyze_and_retrieve_public_analysis(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/analyze", json={"handle": "sample-user", "debug": False, "force_refresh": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["handle"] == "sample-user"
    assert data["model_version"] == "ml_core_v0.4"
    assert "profile_summary" in data
    assert "weakness_map_user" in data
    assert "daily_queue" in data

    retrieved = client.get("/api/analysis/sample-user")
    assert retrieved.status_code == 200
    assert retrieved.json()["analysis_id"] == data["analysis_id"]


def test_cached_old_model_version_is_invalidated(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_analysis

    save_analysis(
        "stale-user",
        {
            "status": "completed",
            "analysis_id": "old-analysis",
            "handle": "stale-user",
            "model_version": "ml_core_v0.3",
            "profile_summary": {},
            "data_quality_summary": {},
            "weakness_map_user": {"likely_needs_work": [], "watchlist": [], "limited_evidence": []},
            "daily_queue": {"queue_mode": "calibration", "items": []},
            "warnings": [],
        },
    )
    response = client.post("/api/analyze", json={"handle": "stale-user", "debug": False, "force_refresh": False})
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "ml_core_v0.4"
    assert data["analysis_id"] != "old-analysis"


def test_force_refresh_overwrites_stale_cached_analysis(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import analysis_path, save_analysis

    save_analysis(
        "refresh-user",
        {
            "status": "completed",
            "analysis_id": "old-refresh",
            "handle": "refresh-user",
            "model_version": "ml_core_v0.3",
            "profile_summary": {},
            "data_quality_summary": {},
            "weakness_map_user": {"likely_needs_work": [], "watchlist": [], "limited_evidence": []},
            "daily_queue": {"queue_mode": "calibration", "items": []},
            "warnings": [],
        },
    )
    response = client.post("/api/analyze", json={"handle": "refresh-user", "debug": False, "force_refresh": True})
    assert response.status_code == 200
    stored = json.loads(analysis_path("refresh-user").read_text(encoding="utf-8"))
    assert stored["model_version"] == "ml_core_v0.4"
    assert stored["analysis_id"] == response.json()["analysis_id"]
    assert stored["analysis_id"] != "old-refresh"


def test_health_and_analyze_model_versions_match(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    health = client.get("/api/health").json()
    analysis = client.post("/api/analyze", json={"handle": "version-user", "debug": False, "force_refresh": True}).json()
    assert health["model_version"] == analysis["model_version"] == "ml_core_v0.4"


def test_weakness_map_and_daily_queue_endpoints(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "queue-user", "debug": False, "force_refresh": True})

    weakness = client.get("/api/analysis/queue-user/weakness-map")
    assert weakness.status_code == 200
    assert set(weakness.json()) == {"handle", "weakness_map_user", "warnings"}

    queue = client.get("/api/analysis/queue-user/daily-queue")
    assert queue.status_code == 200
    assert set(queue.json()) == {"handle", "daily_queue", "warnings"}
    assert "queue_mode" in queue.json()["daily_queue"]


def test_debug_endpoint_when_debug_analysis_available(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "debug-user", "debug": True, "force_refresh": True})
    response = client.get("/api/analysis/debug-user/debug")
    assert response.status_code == 200
    data = response.json()
    assert "debug" in data
    assert "skill_scores" in data
    assert "repair_candidate_count" in data["daily_queue"]


def test_debug_endpoint_blocked_when_disabled(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, {"ENABLE_DEBUG_ENDPOINT": "false"})
    client.post("/api/analyze", json={"handle": "debug-blocked", "debug": True, "force_refresh": True})
    response = client.get("/api/analysis/debug-blocked/debug")
    assert response.status_code == 403
    data = response.json()
    assert data == {
        "status": "failed",
        "error_code": "DEBUG_ENDPOINT_DISABLED",
        "message": "Debug endpoint is disabled in this environment.",
    }
    assert "skill_scores" not in json.dumps(data)


def test_analyze_rate_limit_triggers_when_enabled(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, {"RATE_LIMIT_ANALYZE_SECONDS": "30"})
    first = client.post("/api/analyze", json={"handle": "rate-one", "debug": False, "force_refresh": True})
    second = client.post("/api/analyze", json={"handle": "rate-two", "debug": False, "force_refresh": True})
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error_code"] == "RATE_LIMITED"


def test_analyze_rate_limit_disabled_by_default(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    first = client.post("/api/analyze", json={"handle": "no-rate-one", "debug": False, "force_refresh": True})
    second = client.post("/api/analyze", json={"handle": "no-rate-two", "debug": False, "force_refresh": True})
    assert first.status_code == 200
    assert second.status_code == 200


def test_analyze_rate_limit_does_not_affect_unrelated_endpoints(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, {"RATE_LIMIT_ANALYZE_SECONDS": "30"})
    client.post("/api/analyze", json={"handle": "limited-user", "debug": False, "force_refresh": True})
    health = client.get("/api/health")
    workspace = client.get("/api/workspace/handles", headers=_admin_headers())
    assert health.status_code == 200
    assert workspace.status_code == 200


def test_invalid_handle_validation(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/analyze", json={"handle": "bad handle!", "debug": False})
    assert response.status_code == 422


def test_public_response_strips_internal_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/analyze", json={"handle": "safe-user", "debug": False, "force_refresh": True})
    data = response.json()
    forbidden = {
        "skill_scores",
        "skill_evidence",
        "normalized_history",
        "debug",
        "weakness_map",
    }
    assert forbidden.isdisjoint(data)
    queue_forbidden = {
        "repair_candidate_count",
        "focused_practice_candidate_count",
        "maintenance_candidate_count",
        "stretch_candidate_count",
        "exploration_candidate_count",
    }
    assert queue_forbidden.isdisjoint(data["daily_queue"])
    for item in data["daily_queue"]["items"]:
        assert "score_components" not in item
        assert "repair_blocking_reasons" not in item
        assert "focused_practice_blocking_reasons" not in item
        assert "debug_anchor" not in item.get("risk_flags", [])


def test_queue_items_include_frontend_explanation_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/analyze", json={"handle": "explain-user", "debug": False, "force_refresh": True})
    item = response.json()["daily_queue"]["items"][0]
    required = {
        "problem_key",
        "problem_name",
        "rating",
        "tags",
        "slot_type",
        "anchor_skill",
        "final_score",
        "explanation",
        "why_this_problem",
        "why_this_skill",
        "why_this_slot",
        "difficulty_reason",
        "safety_note",
        "risk_flags",
    }
    assert required.issubset(item)
    assert "score_components" not in item


def test_analysis_not_found(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/analysis/missing-user")
    assert response.status_code == 404
    assert response.json()["error_code"] == "ANALYSIS_NOT_FOUND"


def test_feedback_problem_endpoint_saves_jsonl(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    payload = {
        "analysis_id": "a1",
        "handle": "feed-user",
        "problem_key": "1869B",
        "slot_type": "focused_practice",
        "anchor_skill": "graphs",
        "feedback": "good_fit",
        "comment": "This looked relevant",
    }
    response = client.post(
        "/api/feedback/problem", json=payload, headers=_verified_headers(client, payload["handle"])
    )
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    assert (tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl").exists()


def test_outcome_endpoint_saves_jsonl(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    payload = {
        "analysis_id": "a1",
        "handle": "outcome-user",
        "problem_key": "1869B",
        "slot_type": "focused_practice",
        "anchor_skill": "graphs",
        "outcome": "attempted_but_failed",
        "comment": "Could not finish",
    }
    response = client.post(
        "/api/outcome/problem", json=payload, headers=_verified_headers(client, payload["handle"])
    )
    assert response.status_code == 200
    assert (tmp_path / "api_cache" / "feedback" / "problem_outcomes.jsonl").exists()


def test_queue_feedback_endpoint_saves_jsonl(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    payload = {
        "analysis_id": "a1",
        "handle": "queue-feed-user",
        "queue_rating": "good_fit",
        "comment": "The plan felt useful",
    }
    response = client.post(
        "/api/feedback/queue", json=payload, headers=_verified_headers(client, payload["handle"])
    )
    assert response.status_code == 200
    assert (tmp_path / "api_cache" / "feedback" / "queue_feedback.jsonl").exists()


def test_invalid_feedback_value_is_rejected(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    payload = {
        "analysis_id": "a1",
        "handle": "feed-user",
        "problem_key": "1869B",
        "slot_type": "focused_practice",
        "anchor_skill": "graphs",
        "feedback": "perfect_mastery",
    }
    response = client.post(
        "/api/feedback/problem", json=payload, headers=_verified_headers(client, payload["handle"])
    )
    assert response.status_code == 422


def test_legacy_feedback_mutations_require_auth_and_verified_ownership(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    problem_payload = {
        "analysis_id": "victim-analysis",
        "handle": "victim-handle",
        "problem_key": "1869B",
        "slot_type": "focused_practice",
        "anchor_skill": "graphs",
        "feedback": "good_fit",
    }
    outcome_payload = {**problem_payload, "outcome": "solved"}
    outcome_payload.pop("feedback")
    queue_payload = {
        "analysis_id": "victim-analysis",
        "handle": "victim-handle",
        "queue_rating": "good_fit",
    }

    assert client.post("/api/feedback/problem", json=problem_payload).status_code == 401
    assert client.post("/api/outcome/problem", json=outcome_payload).status_code == 401
    assert client.post("/api/feedback/queue", json=queue_payload).status_code == 401

    attacker_headers = _verified_headers(client, "attacker-handle")
    spoof = client.post("/api/feedback/problem", json=problem_payload, headers=attacker_headers)
    assert spoof.status_code == 403
    assert spoof.json()["error_code"] == "HANDLE_NOT_VERIFIED"
    assert not (tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl").exists()


def test_analyze_saves_progress_snapshot(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post("/api/analyze", json={"handle": "snap-user", "debug": False, "force_refresh": True})
    analysis_id = response.json()["analysis_id"]
    assert (tmp_path / "api_cache" / "snapshots" / "snap-user" / f"{analysis_id}.json").exists()


def test_progress_not_enough_history_with_one_snapshot(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "progress-one", "debug": False, "force_refresh": True})
    response = client.get("/api/analysis/progress-one/progress")
    assert response.status_code == 200
    assert response.json()["status"] == "not_enough_history"


def test_progress_compares_two_snapshots(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    first = client.post("/api/analyze", json={"handle": "progress-two", "debug": False, "force_refresh": True}).json()
    second = client.post("/api/analyze", json={"handle": "progress-two", "debug": False, "force_refresh": True}).json()
    response = client.get("/api/analysis/progress-two/progress")
    data = response.json()
    assert data["status"] == "available"
    assert data["latest_analysis_id"] == second["analysis_id"]
    assert data["previous_analysis_id"] == first["analysis_id"]
    assert "queue_mode_changed" in data["summary"]


def _snapshot(analysis_id, created_at, queue_mode="maintenance_stretch", watchlist=None, limited=None, likely=None):
    return {
        "status": "completed",
        "analysis_id": analysis_id,
        "handle": "history-user",
        "model_version": "ml_core_v0.4",
        "created_at": created_at,
        "weakness_map_user": {
            "likely_needs_work": [{"skill_id": skill} for skill in (likely or [])],
            "watchlist": [{"skill_id": skill} for skill in (watchlist or [])],
            "limited_evidence": [{"skill_id": skill} for skill in (limited or [])],
        },
        "daily_queue": {
            "queue_mode": queue_mode,
            "items": [
                {
                    "slot_type": "focused_practice",
                    "anchor_skill": "graphs",
                    "problem_key": "100A",
                    "problem_name": "Graph Focus",
                    "rating": 1200,
                }
            ],
        },
        "warnings": [],
    }


def test_history_endpoint_not_found_without_snapshots(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/analysis/no-history/history")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_history_endpoint_returns_snapshots_newest_first(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("old", "2026-06-01T00:00:00+00:00", "calibration"))
    save_snapshot("history-user", _snapshot("new", "2026-06-08T00:00:00+00:00", "focused_practice"))
    response = client.get("/api/analysis/history-user/history")
    data = response.json()
    assert data["status"] == "available"
    assert data["count"] == 2
    assert [item["analysis_id"] for item in data["items"]] == ["new", "old"]
    assert "debug" not in data["items"][0]


def test_weekly_report_not_enough_history_with_one_snapshot(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("only", "2026-06-08T00:00:00+00:00"))
    response = client.get(
        "/api/analysis/history-user/weekly-report",
        headers=_verified_headers(client, "history-user", premium=True),
    )
    data = response.json()
    assert data["status"] == "not_enough_history"
    assert data["safe_interpretation"] == "ContestIQ needs at least two saved analyses to build a weekly report."


def test_legacy_weekly_reports_require_auth_owner_and_entitlement(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    json_path = "/api/analysis/private-weekly/weekly-report"
    markdown_path = "/api/analysis/private-weekly/weekly-report.md"

    assert client.get(json_path).status_code == 401
    assert client.get(markdown_path).status_code == 401

    free_owner = _verified_headers(client, "private-weekly")
    assert client.get(json_path, headers=free_owner).status_code == 402

    different_owner = _verified_headers(client, "different-weekly", premium=True)
    spoof = client.get(json_path, headers=different_owner)
    assert spoof.status_code == 403
    assert spoof.json()["error_code"] == "HANDLE_NOT_VERIFIED"


def test_weekly_report_compares_latest_and_baseline(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("baseline", "2026-06-01T00:00:00+00:00", "maintenance_stretch", watchlist=["dp"]))
    save_snapshot("history-user", _snapshot("latest", "2026-06-08T00:00:00+00:00", "focused_practice", watchlist=["graphs"], limited=["geometry"]))
    response = client.get(
        "/api/analysis/history-user/weekly-report",
        headers=_verified_headers(client, "history-user", premium=True),
    )
    data = response.json()
    assert data["status"] == "available"
    assert data["latest_analysis_id"] == "latest"
    assert data["baseline_analysis_id"] == "baseline"
    assert data["summary"]["queue_mode_changed"]
    assert data["summary"]["watchlist_added"] == ["graphs"]
    assert data["summary"]["watchlist_removed"] == ["dp"]


def test_weekly_report_includes_current_training_focus(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("baseline", "2026-06-01T00:00:00+00:00"))
    save_snapshot("history-user", _snapshot("latest", "2026-06-08T00:00:00+00:00"))
    data = client.get(
        "/api/analysis/history-user/weekly-report",
        headers=_verified_headers(client, "history-user", premium=True),
    ).json()
    focus = data["summary"]["current_training_focus"]
    assert focus == [
        {
            "slot_type": "focused_practice",
            "anchor_skill": "graphs",
            "problem_key": "100A",
            "problem_name": "Graph Focus",
            "rating": 1200,
        }
    ]


def test_weekly_report_does_not_expose_internal_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    snap = _snapshot("baseline", "2026-06-01T00:00:00+00:00")
    snap["debug"] = {"secret": True}
    snap["skill_scores"] = [{"skill_id": "graphs"}]
    save_snapshot("history-user", snap)
    save_snapshot("history-user", _snapshot("latest", "2026-06-08T00:00:00+00:00"))
    headers = _verified_headers(client, "history-user", premium=True)
    text = json.dumps(client.get("/api/analysis/history-user/weekly-report", headers=headers).json()).lower()
    assert "skill_scores" not in text
    assert "secret" not in text


def test_weekly_report_safe_wording_avoids_banned_phrases(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("baseline", "2026-06-01T00:00:00+00:00"))
    save_snapshot("history-user", _snapshot("latest", "2026-06-08T00:00:00+00:00"))
    headers = _verified_headers(client, "history-user", premium=True)
    text = json.dumps(client.get("/api/analysis/history-user/weekly-report", headers=headers).json()).lower()
    banned = ["you improved", "you mastered", "proves your skill", "verified", "guaranteed"]
    assert all(phrase not in text for phrase in banned)
    from contestiq_api.safety import scan_public_payload

    scan_public_payload(client.get("/api/analysis/history-user/weekly-report", headers=headers).json())


def test_weekly_report_markdown_endpoint(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("baseline", "2026-06-01T00:00:00+00:00"))
    save_snapshot("history-user", _snapshot("latest", "2026-06-08T00:00:00+00:00"))
    response = client.get(
        "/api/analysis/history-user/weekly-report.md",
        headers=_verified_headers(client, "history-user", premium=True),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# ContestIQ Weekly Training Report" in response.text


def test_existing_analyze_response_shape_still_public_safe(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    data = client.post("/api/analyze", json={"handle": "shape-user", "debug": False, "force_refresh": True}).json()
    assert "skill_scores" not in data
    assert "normalized_history" not in data
    assert "daily_queue" in data


def test_feedback_analytics_endpoint_still_works(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/feedback/summary", headers={"X-Admin-Key": SECURITY_ADMIN_KEY})
    assert response.status_code == 200
    assert response.json()["status"] in {"available", "no_feedback"}


def test_feedback_summaries_are_admin_only(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert client.get("/api/feedback/summary").status_code == 403
    assert client.get("/api/feedback/summary.md").status_code == 403

    user_headers = _verified_headers(client, "summary-user")
    assert client.get("/api/feedback/summary", headers=user_headers).status_code == 403
    assert client.get("/api/feedback/summary.md", headers=user_headers).status_code == 403


def test_create_share_link_from_existing_analysis(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    analysis = client.post("/api/analyze", json={"handle": "share-user", "debug": True, "force_refresh": True}).json()
    assert client.post("/api/analysis/share-user/share").status_code == 401
    response = client.post(
        "/api/analysis/share-user/share",
        headers=_verified_headers(client, "share-user"),
    )
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "created"
    assert data["handle"] == "share-user"
    assert data["analysis_id"] == analysis["analysis_id"]
    assert data["public_url_path"] == f"/api/share/{data['share_id']}"


def test_create_share_returns_analysis_not_found(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/analysis/no-share/share",
        headers=_verified_headers(client, "no-share"),
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "ANALYSIS_NOT_FOUND"


def test_public_share_endpoint_returns_report(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "share-report", "debug": True, "force_refresh": True})
    share = client.post(
        "/api/analysis/share-report/share",
        headers=_verified_headers(client, "share-report"),
    ).json()
    response = client.get(f"/api/share/{share['share_id']}")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "available"
    assert data["report_type"] == "shareable_training_report"
    assert data["public_report"]["handle"] == "share-report"


def test_share_markdown_endpoint_returns_text_plain(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "share-md", "debug": False, "force_refresh": True})
    share = client.post(
        "/api/analysis/share-md/share",
        headers=_verified_headers(client, "share-md"),
    ).json()
    response = client.get(f"/api/share/{share['share_id']}.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# ContestIQ Shareable Training Report" in response.text


def test_build_public_report_strips_internal_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    analysis = client.post("/api/analyze", json={"handle": "sanitize-user", "debug": True, "force_refresh": True}).json()
    analysis["feedback_logs"] = [{"x": 1}]
    analysis["outcomes"] = [{"x": 2}]
    from contestiq_api.share import build_public_report

    report = build_public_report(analysis)
    text = json.dumps(report).lower()
    forbidden = [
        "debug",
        "skill_scores",
        "skill_evidence",
        "normalized_history",
        "raw submissions",
        "feedback_logs",
        "outcomes",
        "repair_blocking_reasons",
        "focused_practice_blocking_reasons",
        "candidate_count",
        "score_components",
    ]
    assert all(term not in text for term in forbidden)


def test_public_share_does_not_include_private_or_internal_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "private-share", "debug": True, "force_refresh": True})
    share = client.post(
        "/api/analysis/private-share/share",
        headers=_verified_headers(client, "private-share"),
    ).json()
    report = client.get(f"/api/share/{share['share_id']}").json()["public_report"]
    text = json.dumps(report).lower()
    forbidden = [
        "debug",
        "skill_scores",
        "skill_evidence",
        "normalized_history",
        "feedback",
        "outcome",
        "repair_blocking_reasons",
        "focused_practice_blocking_reasons",
    ]
    assert all(term not in text for term in forbidden)


def test_public_share_safe_wording_avoids_banned_terms(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "wording-share", "debug": False, "force_refresh": True})
    share = client.post(
        "/api/analysis/wording-share/share",
        headers=_verified_headers(client, "wording-share"),
    ).json()
    text = json.dumps(client.get(f"/api/share/{share['share_id']}").json()).lower()
    banned = [
        "verified",
        "proved skill",
        "mastered",
        "guaranteed",
        "authenticity confirmed",
        "independent solving confirmed",
    ]
    assert all(term not in text for term in banned)
    from contestiq_api.safety import scan_public_payload

    scan_public_payload(client.get(f"/api/share/{share['share_id']}").json())


def test_public_analyze_response_passes_safety_scan(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    data = client.post("/api/analyze", json={"handle": "safety-analyze", "debug": False, "force_refresh": True}).json()
    from contestiq_api.safety import scan_public_payload

    scan_public_payload(data)


def test_share_markdown_passes_safety_scan(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "safety-md", "debug": False, "force_refresh": True})
    share = client.post(
        "/api/analysis/safety-md/share",
        headers=_verified_headers(client, "safety-md"),
    ).json()
    markdown = client.get(f"/api/share/{share['share_id']}.md").text
    from contestiq_api.safety import assert_safe_public_text

    assert_safe_public_text(markdown)


def test_share_not_found_error(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/share/missing-share-id")
    assert response.status_code == 404
    assert response.json()["error_code"] == "SHARE_NOT_FOUND"


def test_share_does_not_change_existing_analyze_response(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    data = client.post("/api/analyze", json={"handle": "unchanged-share", "debug": False, "force_refresh": True}).json()
    assert "weakness_map_user" in data
    assert "daily_queue" in data
    assert "skill_scores" not in data
    assert "normalized_history" not in data


def test_weekly_report_still_works_after_share_routes(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from contestiq_api.storage import save_snapshot

    save_snapshot("history-user", _snapshot("baseline", "2026-06-01T00:00:00+00:00"))
    save_snapshot("history-user", _snapshot("latest", "2026-06-08T00:00:00+00:00"))
    response = client.get(
        "/api/analysis/history-user/weekly-report",
        headers=_verified_headers(client, "history-user", premium=True),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "available"


def test_workspace_manual_save_handle(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert client.get("/api/workspace/handles").status_code == 403
    response = client.post(
        "/api/workspace/handles",
        json={"handle": "tourist", "notes": "Strong baseline test"},
        headers=_admin_headers(),
    )
    data = response.json()
    assert response.status_code == 200
    assert data["handle"] == "tourist"
    assert data["notes"] == "Strong baseline test"
    assert data["latest_analysis_id"] is None
    assert (tmp_path / "api_cache" / "workspace" / "saved_handles.json").exists()


def test_workspace_lists_saved_handles(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/workspace/handles", json={"handle": "tourist"}, headers=_admin_headers())
    client.post("/api/workspace/handles", json={"handle": "benq"}, headers=_admin_headers())
    response = client.get("/api/workspace/handles", headers=_admin_headers())
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "available"
    assert data["count"] == 2
    assert {item["handle"] for item in data["items"]} == {"tourist", "benq"}


def test_workspace_delete_saved_handle_only(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    analysis = client.post("/api/analyze", json={"handle": "delete-me", "debug": False, "force_refresh": True}).json()
    share = client.post(
        "/api/analysis/delete-me/share",
        headers=_verified_headers(client, "delete-me"),
    ).json()
    response = client.delete("/api/workspace/handles/delete-me", headers=_admin_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert client.get("/api/workspace/handles", headers=_admin_headers()).json()["count"] == 0
    assert (tmp_path / "api_cache" / "analyses" / "delete-me.json").exists()
    assert (tmp_path / "api_cache" / "shares" / f"{share['share_id']}.json").exists()
    assert client.get("/api/analysis/delete-me").json()["analysis_id"] == analysis["analysis_id"]


def test_analyze_auto_upserts_workspace_handle(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    analysis = client.post("/api/analyze", json={"handle": "auto-save", "debug": False, "force_refresh": True}).json()
    handles = client.get("/api/workspace/handles", headers=_admin_headers()).json()["items"]
    record = next(item for item in handles if item["handle"] == "auto-save")
    assert record["latest_analysis_id"] == analysis["analysis_id"]
    assert record["latest_analysis_created_at"] == analysis["created_at"]
    assert record["latest_queue_mode"] == analysis["daily_queue"]["queue_mode"]
    assert record["latest_model_version"] == "ml_core_v0.4"


def test_share_creation_updates_workspace_latest_share_id(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "share-workspace", "debug": False, "force_refresh": True})
    share = client.post(
        "/api/analysis/share-workspace/share",
        headers=_verified_headers(client, "share-workspace"),
    ).json()
    record = client.get("/api/workspace/handles", headers=_admin_headers()).json()["items"][0]
    assert record["handle"] == "share-workspace"
    assert record["latest_share_id"] == share["share_id"]


def test_workspace_dashboard_returns_saved_handles(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "dash-user", "debug": False, "force_refresh": True})
    response = client.get("/api/workspace/dashboard", headers=_admin_headers())
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "available"
    assert data["handles_count"] == 1
    assert data["items"][0]["handle"] == "dash-user"
    assert data["items"][0]["has_history"] is True
    assert "verification" in data["safe_interpretation"]
    assert "verified user" not in json.dumps(data).lower()


def test_workspace_invalid_handle_rejected(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/workspace/handles",
        json={"handle": "bad handle!"},
        headers=_admin_headers(),
    )
    assert response.status_code == 422


def test_workspace_does_not_expose_debug_internal_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "workspace-safe", "debug": True, "force_refresh": True})
    data = client.get("/api/workspace/dashboard", headers=_admin_headers()).json()
    text = json.dumps(data).lower()
    forbidden = ["skill_scores", "normalized_history", "repair_blocking_reasons", "focused_practice_blocking_reasons"]
    assert all(term not in text for term in forbidden)


def test_existing_analyze_response_remains_frontend_safe_after_workspace(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    data = client.post("/api/analyze", json={"handle": "workspace-shape", "debug": False, "force_refresh": True}).json()
    assert "skill_scores" not in data
    assert "normalized_history" not in data
    assert "daily_queue" in data


def test_existing_share_endpoints_still_work_after_workspace(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/api/analyze", json={"handle": "workspace-share", "debug": False, "force_refresh": True})
    share = client.post(
        "/api/analysis/workspace-share/share",
        headers=_verified_headers(client, "workspace-share"),
    ).json()
    response = client.get(f"/api/share/{share['share_id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "available"
