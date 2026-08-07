"""Practice pack checkers, oracles, quality gates, and 11A regression."""

from __future__ import annotations

import json

from contestiq_api.practice_packs.checkers import (
    exact_match,
    float_match,
    outputs_match,
    tokens_match,
)
from contestiq_api.practice_packs.classify import (
    AUTO_PACK_POSSIBLE,
    REVIEW_PACK_POSSIBLE,
    UNSUPPORTED,
    classify_problem,
)
from contestiq_api.practice_packs.oracles import (
    ORACLE_REGISTRY,
    _oracle_11a_greedy,
    _oracle_11a_math,
    build_candidate_pack,
)
from contestiq_api.practice_packs.pipeline import upsert_practice_pack
from contestiq_api.cfdata import store


def test_checkers_exact_tokens_float():
    assert exact_match("3\n", "3")
    assert tokens_match("YES\n", "YES")
    assert tokens_match("a  b\n", "a b")
    assert float_match("0.1\n", "0.1000001\n")
    assert not float_match("0.1\n", "0.2\n")
    assert outputs_match("YES\n", "yes\n", checker_type="tokens_ci")


def test_classify_supportability():
    assert classify_problem(is_interactive=True) == UNSUPPORTED
    assert classify_problem(io_mode="file") == UNSUPPORTED
    assert (
        classify_problem(has_oracle=True, display_ready=True, io_mode="stdio")
        == AUTO_PACK_POSSIBLE
    )
    assert (
        classify_problem(has_oracle=False, display_ready=True, io_mode="stdio")
        == REVIEW_PACK_POSSIBLE
    )


def test_11a_oracles_agree_on_sample_and_edges():
    cases = [
        "4 2\n1 3 3 2\n",
        "3 5\n10 10 10\n",
        "5 1\n1 2 3 4 5\n",
        "4 1\n5 5 4 10\n",
    ]
    for stdin in cases:
        assert _oracle_11a_greedy(stdin) == _oracle_11a_math(stdin)
    assert _oracle_11a_greedy("4 2\n1 3 3 2\n").strip() == "3"


def test_11a_pack_passes_quality_and_kills_mutants():
    pack = build_candidate_pack("11A")
    assert pack["problem_id"] == "11A"
    assert pack["quality_report"]["passed"] is True
    assert pack["mutation_score"] >= 0.75
    assert pack["test_count"] >= 8
    assert any(t["input"].startswith("4 2") for t in pack["judge_tests"])
    # Wrong mutants must not match expected on every test.
    from contestiq_api.practice_packs.oracles import (
        _mut_11a_floor_div,
        _mut_11a_no_update,
        _mut_11a_plus_one,
        _mut_11a_strict_less,
    )

    for mutant in (
        _mut_11a_strict_less,
        _mut_11a_no_update,
        _mut_11a_floor_div,
        _mut_11a_plus_one,
    ):
        killed = False
        for test in pack["judge_tests"]:
            if mutant(test["input"]).strip() != test["expected_output"].strip():
                killed = True
                break
        assert killed, "mutant survived the 11A pack"


def test_all_registry_packs_pass_quality_gates():
    failed = []
    for problem_id in sorted(ORACLE_REGISTRY):
        try:
            pack = build_candidate_pack(problem_id)
        except Exception as exc:  # noqa: BLE001
            failed.append((problem_id, str(exc)))
            continue
        if not pack["quality_report"]["passed"]:
            failed.append((problem_id, pack["quality_report"]["failures"]))
    assert failed == []


def test_upsert_practice_pack_and_submit_capable(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "packs.sqlite3"))
    monkeypatch.setenv("CONTESTIQ_API_OFFLINE_SAMPLE", "1")
    # Reset settings cache if any
    import contestiq_api.settings as settings

    settings.get_settings.cache_clear() if hasattr(settings.get_settings, "cache_clear") else None
    from importlib import reload

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
    from contestiq_api.practice_packs.pipeline import problem_has_active_pack

    # Avoid re-seeding entire registry (other problems missing).
    import contestiq_api.practice_packs.pipeline as pipeline

    pipeline._auto_packs_seeded = True
    assert problem_has_active_pack("11A") is True

    # Hidden tests must not appear in public content helper.
    public = store.get_active_public_problem_content("11A")
    blob = json.dumps(public or {})
    assert "judge_tests" not in blob
    for test in pack["judge_tests"]:
        # Public helper historically may include samples only; ensure private stdin not leaked wholesale.
        if test["input"] not in {s["input"] for s in pack["sample_tests"]}:
            assert test["input"] not in blob
