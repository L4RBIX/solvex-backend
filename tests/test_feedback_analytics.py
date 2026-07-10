import importlib
import json

from fastapi.testclient import TestClient

ADMIN_KEY = "feedback-analytics-admin-key"


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _analytics(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import contestiq_api.storage as storage
    import contestiq_api.feedback_analytics as analytics

    importlib.reload(storage)
    importlib.reload(analytics)
    return analytics


def test_summary_no_feedback_when_no_jsonl_files_exist(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    summary = analytics.feedback_summary()
    assert summary["status"] == "no_feedback"
    assert summary["global"]["total_problem_feedback"] == 0
    assert summary["manual_review_flags"][0]["flag"] == "insufficient_feedback_volume"


def test_problem_feedback_summary_by_slot_type(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl",
        [
            {"analysis_id": "a1", "handle": "h", "slot_type": "focused_practice", "anchor_skill": "graphs", "feedback": "good_fit"},
            {"analysis_id": "a1", "handle": "h", "slot_type": "focused_practice", "anchor_skill": "graphs", "feedback": "too_hard"},
            {"analysis_id": "a2", "handle": "h2", "slot_type": "stretch", "anchor_skill": "dp", "feedback": "too_hard"},
        ],
    )
    summary = analytics.feedback_summary()
    assert summary["status"] == "available"
    assert summary["by_slot_type"]["focused_practice"]["count"] == 2
    assert summary["by_slot_type"]["focused_practice"]["good_fit_count"] == 1
    assert summary["by_slot_type"]["focused_practice"]["too_hard_rate"] == 0.5


def test_queue_feedback_summary_counts_global(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "queue_feedback.jsonl",
        [
            {"analysis_id": "a1", "handle": "h", "queue_rating": "good_fit"},
            {"analysis_id": "a2", "handle": "h2", "queue_rating": "too_hard"},
        ],
    )
    summary = analytics.feedback_summary()
    assert summary["global"]["total_queue_feedback"] == 2
    assert summary["global"]["handles_count"] == 2
    assert summary["global"]["analysis_count"] == 2


def test_outcome_summary(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "problem_outcomes.jsonl",
        [
            {"analysis_id": "a1", "handle": "h", "slot_type": "repair", "anchor_skill": "graphs", "outcome": "solved"},
            {"analysis_id": "a1", "handle": "h", "slot_type": "repair", "anchor_skill": "graphs", "outcome": "attempted_but_failed"},
            {"analysis_id": "a1", "handle": "h", "slot_type": "repair", "anchor_skill": "graphs", "outcome": "skipped"},
        ],
    )
    summary = analytics.feedback_summary()
    assert summary["outcomes_by_slot_type"]["repair"]["count"] == 3
    assert summary["outcomes_by_slot_type"]["repair"]["solved_rate"] == 0.3333
    assert summary["outcomes_by_anchor_skill"]["graphs"]["attempted_failed_rate"] == 0.3333


def test_anchor_skill_grouping(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl",
        [
            {"analysis_id": "a1", "handle": "h", "slot_type": "repair", "anchor_skill": "graphs", "feedback": "not_relevant"},
            {"analysis_id": "a2", "handle": "h", "slot_type": "stretch", "anchor_skill": "graphs", "feedback": "good_fit"},
        ],
    )
    summary = analytics.feedback_summary()
    assert summary["by_anchor_skill"]["graphs"]["count"] == 2
    assert summary["by_anchor_skill"]["graphs"]["not_relevant_rate"] == 0.5


def test_manual_flag_high_too_hard_requires_enough_sample(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl",
        [
            {"analysis_id": f"a{i}", "handle": "h", "slot_type": "stretch", "anchor_skill": "graphs", "feedback": "too_hard"}
            for i in range(5)
        ],
    )
    flags = analytics.feedback_summary()["manual_review_flags"]
    assert any(flag["flag"] == "stretch_too_hard_rate_high" for flag in flags)


def test_low_sample_size_prevents_strong_flags(tmp_path, monkeypatch):
    analytics = _analytics(tmp_path, monkeypatch)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl",
        [
            {"analysis_id": f"a{i}", "handle": "h", "slot_type": "stretch", "anchor_skill": "graphs", "feedback": "too_hard"}
            for i in range(4)
        ],
    )
    flags = analytics.feedback_summary()["manual_review_flags"]
    assert any(flag["flag"] == "low_sample_size" for flag in flags)
    assert not any(flag["flag"] == "stretch_too_hard_rate_high" for flag in flags)


def test_feedback_summary_api_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    import contestiq_api.storage as storage
    import contestiq_api.feedback_analytics as analytics
    import contestiq_api.main as main

    importlib.reload(storage)
    importlib.reload(analytics)
    importlib.reload(main)
    _write_jsonl(
        tmp_path / "api_cache" / "feedback" / "problem_feedback.jsonl",
        [{"analysis_id": "a1", "handle": "h", "slot_type": "repair", "anchor_skill": "graphs", "feedback": "good_fit"}],
    )
    client = TestClient(main.app)
    response = client.get("/api/feedback/summary", headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 200
    assert response.json()["status"] == "available"


def test_feedback_summary_markdown_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    import contestiq_api.storage as storage
    import contestiq_api.feedback_analytics as analytics
    import contestiq_api.main as main

    importlib.reload(storage)
    importlib.reload(analytics)
    importlib.reload(main)
    client = TestClient(main.app)
    response = client.get("/api/feedback/summary.md", headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 200
    assert "ContestIQ Feedback Analytics" in response.text
