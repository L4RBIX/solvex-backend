"""Skill taxonomy v1 and the problem-skill map.

Codeforces tags are WEAK SEEDS, not proof of fine-grained skills. The rules
here therefore:
- map broad tags to top-level skills only;
- allow a leaf-skill suggestion per tag, but any leaf mapping whose confidence
  is below LEAF_CONFIDENCE_THRESHOLD falls back to its parent skill;
- send unmapped tags and unmappable problems to mapping_review_queue for
  human review instead of guessing.

Everything is versioned by taxonomy_version so mappings can be rebuilt and
compared across versions.
"""

from __future__ import annotations

import json
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.versions import TAXONOMY_VERSION

LEAF_CONFIDENCE_THRESHOLD = 0.7

TOP_LEVEL_SKILLS: dict[str, str] = {
    "implementation": "Implementation",
    "math": "Math",
    "number_theory": "Number Theory",
    "combinatorics": "Combinatorics",
    "greedy": "Greedy",
    "constructive": "Constructive",
    "binary_search": "Binary Search",
    "graphs": "Graphs",
    "trees": "Trees",
    "dynamic_programming": "Dynamic Programming",
    "data_structures": "Data Structures",
    "strings": "Strings",
    "geometry": "Geometry",
    "brute_force": "Brute Force",
    "bitmasks": "Bitmasks",
    "games": "Games",
    "probability": "Probability",
    "flows": "Flows",
}

LEAF_SKILLS: dict[str, str] = {
    "graphs.dfs_bfs": "DFS / BFS",
    "graphs.shortest_paths": "Shortest Paths",
    "graphs.dsu": "Disjoint Set Union",
    "graphs.toposort": "Topological Sort",
    "graphs.scc": "Strongly Connected Components",
    "graphs.mst": "Minimum Spanning Tree",
    "trees.traversal": "Tree Traversal",
    "trees.binary_lifting": "Binary Lifting",
    "trees.lca": "Lowest Common Ancestor",
    "trees.tree_dp": "Tree DP",
    "dynamic_programming.basic": "Basic DP",
    "dynamic_programming.knapsack": "Knapsack DP",
    "dynamic_programming.bitmask": "Bitmask DP",
    "dynamic_programming.tree_dp": "Tree DP",
    "dynamic_programming.interval": "Interval DP",
    "dynamic_programming.sequence": "Sequence DP",
    "data_structures.fenwick": "Fenwick Tree",
    "data_structures.segment_tree": "Segment Tree",
    "data_structures.lazy_segment_tree": "Lazy Segment Tree",
    "data_structures.sparse_table": "Sparse Table",
    "data_structures.priority_queue": "Priority Queue",
    "data_structures.set_map": "Set / Map",
    "math.modular_arithmetic": "Modular Arithmetic",
    "math.combinatorics": "Combinatorics (Math)",
    "math.gcd_lcm": "GCD / LCM",
    "math.primes_sieve": "Primes / Sieve",
    "math.probability_expected_value": "Probability / Expected Value",
    "strings.kmp": "KMP",
    "strings.z_function": "Z-Function",
    "strings.trie": "Trie",
    "strings.hashing": "String Hashing",
    "constructive.invariant": "Invariants",
    "constructive.parity": "Parity Arguments",
    "constructive.greedy_construction": "Greedy Construction",
}


def parent_of(skill_id: str) -> str | None:
    return skill_id.split(".", 1)[0] if "." in skill_id else None


# CF tag → [(skill_id, weight, confidence)]. Leaf targets below the confidence
# threshold fall back to their parent at build time — broad tags like "dp" or
# "trees" deliberately carry a low-confidence leaf suggestion so the fallback
# rule documents intent without pretending precision.
TAG_RULES: dict[str, list[tuple[str, float, float]]] = {
    "implementation": [("implementation", 1.0, 0.6)],
    "math": [("math", 1.0, 0.5)],
    "number theory": [("number_theory", 1.0, 0.85)],
    "combinatorics": [("combinatorics", 1.0, 0.85)],
    "greedy": [("greedy", 1.0, 0.7)],
    "constructive algorithms": [("constructive", 1.0, 0.75)],
    "binary search": [("binary_search", 1.0, 0.85)],
    "graphs": [("graphs", 1.0, 0.8)],
    "dfs and similar": [("graphs.dfs_bfs", 1.0, 0.75)],
    "shortest paths": [("graphs.shortest_paths", 1.0, 0.85)],
    "dsu": [("graphs.dsu", 1.0, 0.85)],
    "trees": [("trees.traversal", 1.0, 0.55)],  # broad tag → falls back to "trees"
    "dp": [("dynamic_programming.basic", 1.0, 0.5)],  # broad tag → falls back to parent
    "data structures": [("data_structures", 1.0, 0.7)],
    "strings": [("strings", 1.0, 0.85)],
    "string suffix structures": [("strings", 1.0, 0.6)],
    "hashing": [("strings.hashing", 0.7, 0.75), ("data_structures", 0.3, 0.4)],
    "geometry": [("geometry", 1.0, 0.9)],
    "brute force": [("brute_force", 1.0, 0.5)],
    "bitmasks": [("bitmasks", 1.0, 0.8)],
    "games": [("games", 1.0, 0.9)],
    "probabilities": [("probability", 1.0, 0.85)],
    "flows": [("flows", 1.0, 0.9)],
    "graph matchings": [("graphs", 0.6, 0.5), ("flows", 0.4, 0.5)],
    "divide and conquer": [("dynamic_programming", 0.5, 0.35), ("binary_search", 0.5, 0.35)],
    "two pointers": [("implementation", 1.0, 0.35)],
    "sortings": [("implementation", 1.0, 0.4)],
    "chinese remainder theorem": [("number_theory", 1.0, 0.8)],
    "matrices": [("math", 1.0, 0.55)],
    "fft": [("math", 1.0, 0.5)],
    "ternary search": [("binary_search", 1.0, 0.5)],
    "shortest paths and similar": [("graphs.shortest_paths", 1.0, 0.8)],
    "expression parsing": [("strings", 1.0, 0.5)],
    "meet-in-the-middle": [("brute_force", 1.0, 0.6)],
    "interactive": [],  # meta tag: no skill signal
    "*special": [],  # meta tag: no skill signal
    "schedules": [("greedy", 1.0, 0.4)],
    "2-sat": [("graphs.scc", 1.0, 0.75)],
}

_META_TAGS = {tag for tag, rules in TAG_RULES.items() if not rules}


def all_skill_ids() -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {
        skill_id: {"display_name": name, "parent_id": None, "level": 0}
        for skill_id, name in TOP_LEVEL_SKILLS.items()
    }
    for skill_id, name in LEAF_SKILLS.items():
        skills[skill_id] = {"display_name": name, "parent_id": parent_of(skill_id), "level": 1}
    return skills


def seed_taxonomy(version: str = TAXONOMY_VERSION) -> dict[str, Any]:
    """Insert taxonomy v1. Idempotent: re-seeding replaces the same version."""
    skills = all_skill_ids()
    now = store._now()
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO taxonomy_versions (version, description, skill_count, created_at) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(version) DO UPDATE SET description=excluded.description, skill_count=excluded.skill_count",
            (version, "Seed taxonomy: 18 top-level skills, 34 leaf skills. CF tags are weak seeds only.", len(skills), now),
        )
        conn.execute("DELETE FROM skill_taxonomy WHERE taxonomy_version = ?", (version,))
        conn.executemany(
            "INSERT INTO skill_taxonomy (skill_id, taxonomy_version, parent_id, display_name, level) VALUES (?, ?, ?, ?, ?)",
            [
                (skill_id, version, meta["parent_id"], meta["display_name"], meta["level"])
                for skill_id, meta in skills.items()
            ],
        )
    return {"version": version, "skills": len(skills)}


def get_taxonomy(version: str = TAXONOMY_VERSION) -> dict[str, Any]:
    with store.connect() as conn:
        version_row = conn.execute("SELECT * FROM taxonomy_versions WHERE version = ?", (version,)).fetchone()
        rows = conn.execute(
            "SELECT * FROM skill_taxonomy WHERE taxonomy_version = ? ORDER BY level, skill_id", (version,)
        ).fetchall()
    return {
        "version": dict(version_row) if version_row else None,
        "skills": [dict(row) for row in rows],
    }


def map_tags_to_skills(tags: list[str]) -> tuple[dict[str, tuple[float, float]], list[str]]:
    """Apply tag rules with leaf→parent fallback.

    Returns ({skill_id: (weight, confidence)}, unmapped_tags). Duplicate
    targets merge by summing weights and keeping the highest confidence.
    """
    merged: dict[str, tuple[float, float]] = {}
    unmapped: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized in _META_TAGS:
            continue
        rules = TAG_RULES.get(normalized)
        if rules is None:
            unmapped.append(normalized)
            continue
        for skill_id, weight, confidence in rules:
            target = skill_id
            if parent_of(skill_id) is not None and confidence < LEAF_CONFIDENCE_THRESHOLD:
                target = parent_of(skill_id) or skill_id
            prev = merged.get(target)
            if prev is None:
                merged[target] = (weight, confidence)
            else:
                merged[target] = (prev[0] + weight, max(prev[1], confidence))
    return merged, unmapped


def build_problem_skill_map(
    problem_ids: list[str] | None = None, version: str = TAXONOMY_VERSION
) -> dict[str, Any]:
    """(Re)build problem_skill_map from the problems table. Idempotent per version."""
    seed_taxonomy(version)
    now = store._now()
    with store.connect() as conn:
        if problem_ids is None:
            problems = conn.execute("SELECT problem_key, tags FROM problems").fetchall()
        else:
            placeholders = ", ".join("?" for _ in problem_ids)
            problems = conn.execute(
                f"SELECT problem_key, tags FROM problems WHERE problem_key IN ({placeholders})", problem_ids
            ).fetchall()

        mapped_problems = 0
        total_mappings = 0
        review_items = 0
        for problem in problems:
            problem_id = problem["problem_key"]
            tags = json.loads(problem["tags"] or "[]")
            skills, unmapped = map_tags_to_skills(tags)

            conn.execute(
                "DELETE FROM problem_skill_map WHERE problem_id = ? AND taxonomy_version = ?",
                (problem_id, version),
            )
            if skills:
                total_weight = sum(weight for weight, _ in skills.values())
                primary = max(skills.items(), key=lambda kv: (kv[1][0], kv[1][1], kv[0]))[0]
                for skill_id, (weight, confidence) in skills.items():
                    conn.execute(
                        """
                        INSERT INTO problem_skill_map
                            (problem_id, skill_id, taxonomy_version, weight, confidence, mapping_source, is_primary)
                        VALUES (?, ?, ?, ?, ?, 'cf_tag_rule', ?)
                        """,
                        (
                            problem_id,
                            skill_id,
                            version,
                            round(weight / total_weight, 6),
                            confidence,
                            1 if skill_id == primary else 0,
                        ),
                    )
                mapped_problems += 1
                total_mappings += len(skills)
            elif tags:
                conn.execute(
                    "INSERT INTO mapping_review_queue (problem_id, tag, reason, taxonomy_version, created_at)"
                    " VALUES (?, '*', 'no_skill_mapping', ?, ?)"
                    " ON CONFLICT(problem_id, tag, taxonomy_version) DO NOTHING",
                    (problem_id, version, now),
                )
                review_items += 1
            for tag in unmapped:
                conn.execute(
                    "INSERT INTO mapping_review_queue (problem_id, tag, reason, taxonomy_version, created_at)"
                    " VALUES (?, ?, 'unmapped_tag', ?, ?)"
                    " ON CONFLICT(problem_id, tag, taxonomy_version) DO NOTHING",
                    (problem_id, tag, version, now),
                )
                review_items += 1

    return {
        "taxonomy_version": version,
        "problems_seen": len(problems),
        "problems_mapped": mapped_problems,
        "mappings": total_mappings,
        "review_queue_items": review_items,
    }


def get_problem_skills(problem_id: str, version: str = TAXONOMY_VERSION) -> list[dict[str, Any]]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM problem_skill_map WHERE problem_id = ? AND taxonomy_version = ? ORDER BY weight DESC, skill_id",
            (problem_id, version),
        ).fetchall()
    result = []
    for row in rows:
        mapping = dict(row)
        mapping["is_primary"] = bool(mapping["is_primary"])
        result.append(mapping)
    return result
