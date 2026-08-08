"""Regression tests for practice-pack coverage expansion."""

from __future__ import annotations

import json

from contestiq_api.practice_packs.classify import (
    AUTO_HIGH_CONFIDENCE,
    AUTO_POSSIBLE,
    AUTO_PACK_POSSIBLE,
    REVIEW_REQUIRED,
    UNSUPPORTED,
    classify_problem,
)
from contestiq_api.practice_packs.oracles import (
    ORACLE_REGISTRY,
    _classic_specs,
    build_candidate_pack,
)
from contestiq_api.practice_packs.priority import priority_score, rank_candidates
from contestiq_api.practice_packs.quality_score import (
    AUTO_ACTIVATE_MIN,
    compute_quality_score,
)
from contestiq_api.practice_packs.pipeline import upsert_practice_pack
from contestiq_api.cfdata import store


def test_classify_supportability_bands():
    assert classify_problem(is_interactive=True) == UNSUPPORTED
    assert classify_problem(io_mode="file", display_ready=True) == UNSUPPORTED
    assert (
        classify_problem(
            has_oracle=True,
            display_ready=True,
            io_mode="stdio",
            rating=800,
            tags=["math"],
        )
        == AUTO_HIGH_CONFIDENCE
    )
    assert (
        classify_problem(has_oracle=True, display_ready=True, io_mode="stdio", rating=2000)
        == AUTO_POSSIBLE
    )
    assert AUTO_PACK_POSSIBLE == AUTO_POSSIBLE
    assert (
        classify_problem(has_oracle=False, display_ready=True, io_mode="stdio", rating=900)
        == REVIEW_REQUIRED
    )


def test_priority_prefers_popular_beginner_over_hard():
    easy = priority_score(rating=800, solved_count=500000, tags=["math"], has_oracle=True)
    hard = priority_score(rating=1300, solved_count=100, tags=["geometry"])
    assert easy > 0
    assert hard < 0
    ranked = rank_candidates(
        [
            {"problem_id": "B", "rating": 1300, "solved_count": 10, "tags": ["math"]},
            {"problem_id": "A", "rating": 800, "solved_count": 100000, "tags": ["math"]},
        ]
    )
    assert ranked[0]["problem_id"] == "A"


def test_quality_score_auto_vs_review_vs_reject():
    auto = compute_quality_score(
        mutation_score=1.0,
        test_count=12,
        oracle_count=2,
        oracles_agree=True,
        has_sample=True,
        checker_type="exact",
    )
    assert auto["recommendation"] == "auto_activate"
    assert auto["quality_score"] >= AUTO_ACTIVATE_MIN

    reject = compute_quality_score(
        mutation_score=0.5,
        test_count=4,
        oracle_count=1,
        oracles_agree=False,
        has_sample=False,
        checker_type="custom",
        surviving_mutants=2,
    )
    assert reject["recommendation"] == "reject"
    assert reject["gate"]["passed"] is False


def test_classic_registry_packs_auto_activate():
    failed = []
    for spec in _classic_specs():
        pid = spec.problem_id
        try:
            pack = build_candidate_pack(pid)
        except Exception as exc:  # noqa: BLE001
            failed.append((pid, str(exc)))
            continue
        q = pack["quality_report"]
        if not (q.get("passed") and q.get("recommendation") == "auto_activate"):
            failed.append((pid, q.get("failures") or q.get("recommendation")))
    assert failed == []


def test_registry_has_expanded_auto_activate_coverage():
    auto = 0
    for pid in ORACLE_REGISTRY:
        try:
            pack = build_candidate_pack(pid)
        except Exception:
            continue
        q = pack["quality_report"]
        if q.get("passed") and q.get("recommendation") == "auto_activate":
            auto += 1
    # Expansion milestone progress: must be well above the original 24.
    assert auto >= 250
    assert len(ORACLE_REGISTRY) >= auto


def test_generator_determinism_for_11a():
    a = build_candidate_pack("11A", rng_seed=11)
    b = build_candidate_pack("11A", rng_seed=11)
    assert [t["input"] for t in a["judge_tests"]] == [t["input"] for t in b["judge_tests"]]
    assert a["mutation_score"] == b["mutation_score"]


def test_false_ac_mutants_do_not_survive_11a():
    pack = build_candidate_pack("11A")
    surviving = pack["quality_report"]["mutation"]["surviving_mutants"]
    assert surviving == []
    assert pack["mutation_score"] >= 0.75


def test_upsert_stores_quality_score_without_leaking_hidden_tests(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "packs.sqlite3"))
    monkeypatch.setenv("CONTESTIQ_API_OFFLINE_SAMPLE", "1")
    import contestiq_api.settings as settings
    from importlib import reload

    if hasattr(settings.get_settings, "cache_clear"):
        settings.get_settings.cache_clear()
    reload(settings)
    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO problems
            (problem_key, contest_id, problem_index, name, rating, tags, updated_at)
            VALUES ('11A', 11, 'A', 'Increasing Sequence', 900, '[]', ?)
            """,
            (store._now(),),
        )
        conn.commit()

    pack = build_candidate_pack("11A")
    assert upsert_practice_pack(pack, activate=True)
    with store.connect() as conn:
        row = conn.execute(
            "SELECT quality_score, mutation_score, active FROM duel_problem_packs WHERE problem_id='11A' AND active=1"
        ).fetchone()
    assert row is not None
    assert float(row["mutation_score"]) >= 0.75
    public = store.get_active_public_problem_content("11A")
    blob = json.dumps(public or {})
    assert "judge_tests" not in blob
    for test in pack["judge_tests"]:
        if test["input"] not in {s["input"] for s in pack["sample_tests"]}:
            assert test["input"] not in blob
