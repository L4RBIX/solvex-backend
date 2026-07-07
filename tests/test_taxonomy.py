"""Skill taxonomy v1 and problem-skill map tests."""

import pytest

from contestiq_api.cfdata import store, taxonomy


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_PATH", raising=False)


def seed_problems(*problems):
    store.save_problemset_snapshot({"problems": list(problems), "problemStatistics": []})


# ─── Taxonomy seed ───────────────────────────────────────────────────────────


def test_seed_taxonomy_counts_and_hierarchy():
    result = taxonomy.seed_taxonomy()
    assert result == {"version": "taxonomy_v1", "skills": 52}  # 18 top + 34 leaves

    data = taxonomy.get_taxonomy()
    assert data["version"]["skill_count"] == 52
    by_id = {row["skill_id"]: row for row in data["skills"]}
    assert by_id["graphs"]["level"] == 0
    assert by_id["graphs"]["parent_id"] is None
    assert by_id["graphs.dfs_bfs"]["parent_id"] == "graphs"
    assert by_id["graphs.dfs_bfs"]["level"] == 1
    assert by_id["dynamic_programming.knapsack"]["parent_id"] == "dynamic_programming"
    # Every leaf's parent exists as a top-level skill.
    for row in data["skills"]:
        if row["level"] == 1:
            assert by_id[row["parent_id"]]["level"] == 0


def test_reseed_is_idempotent():
    taxonomy.seed_taxonomy()
    taxonomy.seed_taxonomy()
    with store.connect() as conn:
        skills = conn.execute("SELECT COUNT(*) FROM skill_taxonomy WHERE taxonomy_version='taxonomy_v1'").fetchone()[0]
        versions = conn.execute("SELECT COUNT(*) FROM taxonomy_versions").fetchone()[0]
    assert skills == 52
    assert versions == 1


# ─── Tag mapping rules ───────────────────────────────────────────────────────


def test_specific_tag_maps_to_leaf_skill():
    skills, unmapped = taxonomy.map_tags_to_skills(["shortest paths"])
    assert unmapped == []
    assert "graphs.shortest_paths" in skills
    weight, confidence = skills["graphs.shortest_paths"]
    assert confidence >= taxonomy.LEAF_CONFIDENCE_THRESHOLD


def test_broad_tag_falls_back_to_parent_skill():
    # "dp" suggests dynamic_programming.basic at confidence 0.5 — below the
    # threshold, so it must land on the parent, never the leaf.
    skills, _ = taxonomy.map_tags_to_skills(["dp"])
    assert "dynamic_programming" in skills
    assert "dynamic_programming.basic" not in skills

    skills, _ = taxonomy.map_tags_to_skills(["trees"])
    assert "trees" in skills
    assert "trees.traversal" not in skills


def test_multi_skill_mapping_with_weights():
    skills, _ = taxonomy.map_tags_to_skills(["graph matchings"])
    assert set(skills) == {"graphs", "flows"}
    assert skills["graphs"][0] == 0.6
    assert skills["flows"][0] == 0.4


def test_unmapped_tag_is_reported():
    skills, unmapped = taxonomy.map_tags_to_skills(["dp", "quantum computing"])
    assert unmapped == ["quantum computing"]
    assert "dynamic_programming" in skills


def test_meta_tags_are_ignored_silently():
    skills, unmapped = taxonomy.map_tags_to_skills(["interactive", "*special"])
    assert skills == {}
    assert unmapped == []


def test_duplicate_targets_merge():
    # "dfs and similar" → graphs.dfs_bfs (leaf kept), "graphs" → graphs.
    skills, _ = taxonomy.map_tags_to_skills(["dfs and similar", "graphs"])
    assert set(skills) == {"graphs.dfs_bfs", "graphs"}


# ─── Problem skill map build ─────────────────────────────────────────────────


def test_skill_map_build_normalizes_weights_and_marks_primary():
    seed_problems(
        {"contestId": 1, "index": "A", "name": "Mixed", "rating": 1500, "tags": ["dp", "graph matchings"]},
    )
    result = taxonomy.build_problem_skill_map()
    assert result["problems_mapped"] == 1
    mappings = taxonomy.get_problem_skills("1A")
    assert {m["skill_id"] for m in mappings} == {"dynamic_programming", "graphs", "flows"}
    assert abs(sum(m["weight"] for m in mappings) - 1.0) < 1e-6
    primary = [m for m in mappings if m["is_primary"]]
    assert len(primary) == 1
    assert primary[0]["skill_id"] == "dynamic_programming"  # highest raw weight
    assert all(m["mapping_source"] == "cf_tag_rule" for m in mappings)
    assert all(m["taxonomy_version"] == "taxonomy_v1" for m in mappings)
    assert all(m["reviewed_by"] is None for m in mappings)


def test_unmapped_tags_land_in_review_queue():
    seed_problems(
        {"contestId": 2, "index": "B", "name": "Weird", "rating": 1500, "tags": ["dp", "quantum computing"]},
    )
    taxonomy.build_problem_skill_map()
    with store.connect() as conn:
        rows = conn.execute("SELECT * FROM mapping_review_queue").fetchall()
    assert len(rows) == 1
    assert rows[0]["tag"] == "quantum computing"
    assert rows[0]["reason"] == "unmapped_tag"


def test_problem_with_no_mappable_tags_queued_for_review():
    seed_problems(
        {"contestId": 3, "index": "C", "name": "Meta Only", "rating": 1200, "tags": ["interactive"]},
    )
    taxonomy.build_problem_skill_map()
    assert taxonomy.get_problem_skills("3C") == []
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM mapping_review_queue WHERE problem_id='3C'").fetchone()
    assert row["reason"] == "no_skill_mapping"


def test_skill_map_rebuild_is_idempotent():
    seed_problems(
        {"contestId": 1, "index": "A", "name": "Mixed", "rating": 1500, "tags": ["dp", "quantum computing"]},
    )
    taxonomy.build_problem_skill_map()
    taxonomy.build_problem_skill_map()
    with store.connect() as conn:
        mappings = conn.execute("SELECT COUNT(*) FROM problem_skill_map").fetchone()[0]
        queue = conn.execute("SELECT COUNT(*) FROM mapping_review_queue").fetchone()[0]
    assert mappings == 1  # dp → dynamic_programming only
    assert queue == 1


def test_low_confidence_top_level_mapping_is_recorded_not_dropped():
    seed_problems(
        {"contestId": 4, "index": "D", "name": "Mathy", "rating": 1500, "tags": ["math"]},
    )
    taxonomy.build_problem_skill_map()
    mappings = taxonomy.get_problem_skills("4D")
    assert len(mappings) == 1
    assert mappings[0]["skill_id"] == "math"
    assert mappings[0]["confidence"] == 0.5  # honesty preserved: weak seed stays weak


def test_taxonomy_endpoints(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import contestiq_api.main as main

    client = TestClient(main.app)

    missing = client.get("/api/v1/taxonomy")
    assert missing.status_code == 404

    seeded = client.post("/api/v1/taxonomy/seed")
    assert seeded.json() == {"version": "taxonomy_v1", "skills": 52}

    data = client.get("/api/v1/taxonomy").json()
    assert len(data["skills"]) == 52

    seed_problems({"contestId": 1, "index": "A", "name": "P", "rating": 1400, "tags": ["dsu"]})
    client.post("/api/v1/skill-map/rebuild")
    skills = client.get("/api/v1/skill-map/1A").json()["skills"]
    assert skills[0]["skill_id"] == "graphs.dsu"
