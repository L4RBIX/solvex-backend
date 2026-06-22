from contestiq_core.models import SkillCategory


DOMAIN_SKILLS = {
    "sequence_search": "Sequence Search",
    "greedy_constructive": "Greedy / Constructive",
    "math_number_theory": "Math / Number Theory",
    "data_structures": "Data Structures",
    "graphs": "Graphs",
    "trees": "Trees",
    "dynamic_programming": "Dynamic Programming",
    "strings": "Strings",
    "geometry": "Geometry",
    "advanced_sparse": "Advanced / Sparse",
}

TECHNIQUE_OVERLAYS = {
    "binary_search": "Binary Search",
    "two_pointers": "Two Pointers",
    "prefix_sums": "Prefix Sums",
    "bitmasks": "Bitmasks",
    "divide_and_conquer": "Divide and Conquer",
    "meet_in_the_middle": "Meet in the Middle",
    "hashing": "Hashing",
    "matrices": "Matrices",
}


def all_skills() -> dict[str, SkillCategory]:
    skills = {
        skill_id: SkillCategory(skill_id=skill_id, display_name=name, kind="domain")
        for skill_id, name in DOMAIN_SKILLS.items()
    }
    skills.update(
        {
            skill_id: SkillCategory(skill_id=skill_id, display_name=name, kind="technique")
            for skill_id, name in TECHNIQUE_OVERLAYS.items()
        }
    )
    return skills
