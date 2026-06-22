from __future__ import annotations

from contestiq_core.models import SkillMapping


REJECTED_TAGS = {"interactive"}
NOISY_UNUSED_TAGS = {"implementation"}

TAG_MAPPINGS: dict[str, list[tuple[str, str, float, float]]] = {
    "dp": [("dynamic_programming", "domain", 1.0, 0.92)],
    "graphs": [("graphs", "domain", 1.0, 0.82)],
    "shortest paths": [("graphs", "domain", 1.0, 0.95)],
    "trees": [("trees", "domain", 1.0, 0.95)],
    "data structures": [("data_structures", "domain", 1.0, 0.84)],
    "dsu": [("data_structures", "domain", 0.58, 0.86), ("graphs", "domain", 0.42, 0.78)],
    "binary search": [("binary_search", "technique", 0.7, 0.9), ("sequence_search", "domain", 0.3, 0.7)],
    "two pointers": [("sequence_search", "domain", 0.5, 0.78), ("two_pointers", "technique", 0.5, 0.9)],
    "math": [("math_number_theory", "domain", 1.0, 0.48)],
    "number theory": [("math_number_theory", "domain", 1.0, 0.88)],
    "greedy": [("greedy_constructive", "domain", 1.0, 0.72)],
    "constructive algorithms": [("greedy_constructive", "domain", 1.0, 0.76)],
    "strings": [("strings", "domain", 1.0, 0.86)],
    "hashing": [("hashing", "technique", 0.65, 0.86), ("strings", "domain", 0.35, 0.74)],
    "geometry": [("geometry", "domain", 1.0, 0.92)],
    "bitmasks": [("bitmasks", "technique", 0.55, 0.86), ("advanced_sparse", "domain", 0.45, 0.62)],
    "divide and conquer": [("divide_and_conquer", "technique", 1.0, 0.86)],
    "meet-in-the-middle": [("meet_in_the_middle", "technique", 1.0, 0.9)],
    "matrices": [("matrices", "technique", 1.0, 0.86)],
    "brute force": [("sequence_search", "domain", 1.0, 0.28)],
}


def map_cf_tags(tags: list[str]) -> list[SkillMapping]:
    mappings: list[SkillMapping] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized in REJECTED_TAGS or normalized in NOISY_UNUSED_TAGS:
            continue
        for skill_id, kind, share, reliability in TAG_MAPPINGS.get(normalized, []):
            mappings.append(
                SkillMapping(
                    skill_id=skill_id,
                    kind=kind,  # type: ignore[arg-type]
                    mapping_share=share,
                    tag_reliability=reliability,
                    source_tag=tag,
                )
            )
    return mappings
