from collections import defaultdict

from contestiq_core.taxonomy.tag_mapping import map_cf_tags


def test_tag_mapping_rejects_noisy_and_maps_fractionally():
    mappings = map_cf_tags(["dsu", "implementation", "interactive"])
    assert {m.skill_id for m in mappings} == {"data_structures", "graphs"}
    assert round(sum(m.mapping_share for m in mappings), 2) == 1.0
    assert all(m.tag_reliability > 0 for m in mappings)


def test_two_pointers_maps_domain_and_overlay():
    mappings = map_cf_tags(["two pointers"])
    assert {m.skill_id for m in mappings} == {"sequence_search", "two_pointers"}


def test_noisy_tags_have_low_reliability_or_are_rejected():
    implementation = map_cf_tags(["implementation"])
    noisy = map_cf_tags(["math", "brute force"])
    assert implementation == []
    assert noisy
    assert all(mapping.tag_reliability < 0.5 for mapping in noisy)


def test_multi_tag_problem_uses_fractional_evidence_not_full_credit():
    mappings = map_cf_tags(["dsu", "two pointers"])
    shares_by_tag = defaultdict(float)
    for mapping in mappings:
        shares_by_tag[mapping.source_tag] += mapping.mapping_share
    assert shares_by_tag["dsu"] == 1.0
    assert shares_by_tag["two pointers"] == 1.0
    assert any(mapping.mapping_share < 1.0 for mapping in mappings)
