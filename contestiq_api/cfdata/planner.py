"""Recommendation engine and training planner (Phase 05).

Content-based and deterministic: no collaborative filtering, no randomness.
Queues and plans are materialized once per (handle, date) and returned as-is
on repeat requests — a refresh never generates a different plan.

Candidate score = 0.5*quality + 0.3*rating_closeness + 0.2*mapping_weight.
Difficulty targets (relative to the skill-specific shrunk rating, falling back
to the global anchor):
    warmup -200 | review -150 | core -100 | transfer +0 | stretch +100
    then  -100 * recent_struggle  and  +50 * preference_bias.

Hard constraints (enforced during selection):
- never a solved problem, unless the slot is intentional review AND the solve
  is older than 21 days;
- never a problem attempted in the last 21 days (review included);
- never a problem the user's feedback suppressed (bad_problem/already_seen/too_easy);
- max 2 items from the same top-level skill, max 1 from the same leaf skill
  (review excluded), max 1 from the same contest, at least 2 distinct
  top-level skills in queues of 4-5;
- no stretch slot while recent struggle is high (downgraded to transfer);
- no leaf-skill target while its parent skill is a severe likely_weakness
  (prerequisite readiness: the parent is recommended instead).
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Any

from contestiq_api.cfdata import profiles as profiles_mod
from contestiq_api.cfdata import store
from contestiq_api.cfdata import weakness
from contestiq_api.versions import TAXONOMY_VERSION

DAY_SECONDS = 86400
RECENT_ATTEMPT_DAYS = 21
HIGH_STRUGGLE = 0.5
# Minimum items a daily queue should contain when the catalog/skill map has
# any unused candidate at all — prevents prolific users (many episodes, most
# of the near-target pool already solved/attempted) from seeing an empty
# queue purely because their *preferred* skills ran out of candidates.
MIN_QUEUE_FLOOR = 2

MODE_OFFSETS = {
    "review_or_warmup": -150,
    "calibration": -100,
    "core_repair": -100,
    "underexposed_exploration": -50,
    "transfer": 0,
    "stretch": 100,
}

QUEUE_TEMPLATES = {
    3: ["review_or_warmup", "core_repair", "transfer_or_stretch"],
    4: ["review_or_warmup", "core_repair", "core_repair", "transfer_or_stretch"],
    5: ["review_or_warmup", "core_repair", "core_repair", "transfer_or_stretch", "transfer_or_stretch"],
}

PLAN_7 = [
    (1, "Calibration + easy repair", [("review_or_warmup", 0), ("core_repair", -50)]),
    (2, "Core repair", [("core_repair", 0), ("core_repair", 0)]),
    (3, "Review + transfer", [("review_or_warmup", 0), ("transfer", 0)]),
    (4, "Harder repair", [("core_repair", 50), ("core_repair", 50)]),
    (5, "Interleaving", [("core_repair", 0), ("transfer", 0)]),
    (6, "Stretch / contest-style", [("stretch", 0), ("transfer", 0)]),
    (7, "Checkpoint + report", [("review_or_warmup", 0)]),
]

PLAN_14 = PLAN_7 + [
    (8, "Transfer focus", [("transfer", 0), ("core_repair", 0)]),
    (9, "Stretch", [("stretch", 0), ("transfer", 0)]),
    (10, "Repair consolidation", [("core_repair", 0), ("transfer", 0)]),
    (11, "Stretch + review", [("stretch", 0), ("review_or_warmup", 0)]),
    (12, "Mixed transfer", [("transfer", 0), ("transfer", 0)]),
    (13, "Contest-style stretch", [("stretch", 0), ("core_repair", 50)]),
    (14, "Checkpoint + verification readiness", [("review_or_warmup", 0)]),
]

REPAIR_STATUSES = {"likely_weakness", "possible_weakness"}
REVIEW_STATUSES = {"strength", "likely_strength", "maintenance_needed", "historical_weakness_recent_improvement"}


def top_level(skill_id: str) -> str:
    return skill_id.split(".", 1)[0]


# ─── Selection state (hard constraints) ──────────────────────────────────────


class SelectionState:
    def __init__(self, allow_min_top_levels: int = 2) -> None:
        self.used_problems: set[str] = set()
        self.contest_counts: dict[Any, int] = {}
        self.top_level_counts: dict[str, int] = {}
        self.leaf_used: set[str] = set()
        self.allow_min_top_levels = allow_min_top_levels

    def violates(self, problem: dict[str, Any], skill_id: str, mode: str) -> bool:
        if problem["problem_key"] in self.used_problems:
            return True
        if self.contest_counts.get(problem["contest_id"], 0) >= 1:
            return True
        if self.top_level_counts.get(top_level(skill_id), 0) >= 2:
            return True
        if "." in skill_id and skill_id in self.leaf_used and mode != "review_or_warmup":
            return True
        return False

    def commit(self, problem: dict[str, Any], skill_id: str) -> None:
        self.used_problems.add(problem["problem_key"])
        self.contest_counts[problem["contest_id"]] = self.contest_counts.get(problem["contest_id"], 0) + 1
        tl = top_level(skill_id)
        self.top_level_counts[tl] = self.top_level_counts.get(tl, 0) + 1
        if "." in skill_id:
            self.leaf_used.add(skill_id)


# ─── World loading ───────────────────────────────────────────────────────────


def _load_world(handle: str) -> dict[str, Any]:
    canonical = store.canonical_handle(handle)
    prof = profiles_mod.get_profiles(canonical)
    if not prof:
        profiles_mod.build_profiles(canonical)
        prof = profiles_mod.get_profiles(canonical)
    with store.connect() as conn:
        episodes = [dict(row) for row in conn.execute(
            "SELECT problem_id, eventual_ac, last_submission_at FROM problem_episodes WHERE handle = ?",
            (canonical,),
        ).fetchall()]
        candidates = [dict(row) for row in conn.execute(
            "SELECT p.problem_key, p.contest_id, p.rating, p.name, m.skill_id, m.weight"
            " FROM problems p JOIN problem_skill_map m ON m.problem_id = p.problem_key"
            " WHERE m.taxonomy_version = ?",
            (TAXONOMY_VERSION,),
        ).fetchall()]
    cutoff = max((ep["last_submission_at"] or 0 for ep in episodes), default=0)
    solved, recent = {}, set()
    for ep in episodes:
        if ep["eventual_ac"]:
            solved[ep["problem_id"]] = ep["last_submission_at"] or 0
        age_days = (cutoff - (ep["last_submission_at"] or cutoff)) / DAY_SECONDS
        if age_days <= RECENT_ATTEMPT_DAYS:
            recent.add(ep["problem_id"])
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for row in candidates:
        by_skill.setdefault(row["skill_id"], []).append(row)
    return {
        "handle": canonical,
        "profiles": prof,
        "cutoff": cutoff,
        "solved": solved,
        "recently_attempted": recent,
        "candidates_by_skill": by_skill,
        "suppressed": profiles_mod.suppressed_problems(canonical),
    }


def _recent_struggle(profiles: dict[str, dict[str, Any]], skill_ids: list[str]) -> float:
    if not skill_ids:
        return 0.0
    parts = []
    for skill_id in skill_ids:
        p = profiles.get(skill_id)
        if p is None:
            continue
        parts.append(min(1.0, p["recent_failures_28d"] / 4.0) * 0.7 + p["frustration_score"] * 0.3)
    return round(sum(parts) / len(parts), 3) if parts else 0.0


def _no_profiles_warning(handle: str) -> str:
    """Distinguish "this handle never ran weakness analysis" from "analysis ran
    but produced zero skill profiles" (e.g. the global problem catalog / skill
    map was empty or unmapped at analysis time). The two need different fixes —
    the first needs the user to analyze, the second needs an ops/catalog fix —
    so collapsing them into one message is misleading and was the direct cause
    of premium users with real submission history seeing "sync more history
    first" while an analysis run already existed.
    """
    if weakness.latest_run_id(handle) is None:
        return "no_analysis_run_found_run_weakness_analyze_first"
    return "analysis_found_but_no_skill_profiles_available_check_problem_catalog"


def _prerequisite_ready(skill_id: str, profiles: dict[str, dict[str, Any]]) -> bool:
    if "." not in skill_id:
        return True
    parent = profiles.get(top_level(skill_id))
    if parent is None:
        return True
    return not (parent["status"] == "likely_weakness" and (parent["severity"] or 0) >= 55)


def _skill_lineup(profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Rank skills for each slot role, applying prerequisite readiness."""
    repair = sorted(
        (p for p in profiles.values() if p["status"] in REPAIR_STATUSES),
        key=lambda p: (-(p["severity"] or 0) * (p["confidence"] or 0), -(p["severity"] or 0), p["skill_id"]),
    )
    repair_ids: list[str] = []
    for p in repair:
        skill_id = p["skill_id"]
        if not _prerequisite_ready(skill_id, profiles):
            skill_id = top_level(skill_id)  # prerequisite first: recommend the parent
        if skill_id not in repair_ids:
            repair_ids.append(skill_id)

    review = sorted(
        (p for p in profiles.values() if p["status"] in REVIEW_STATUSES),
        key=lambda p: (p["review_due_at"] is None, p["review_due_at"] or 0, p["skill_id"]),
    )
    review_ids = [p["skill_id"] for p in review]

    underexposed_ids = sorted(p["skill_id"] for p in profiles.values() if p["status"] == "underexposed")
    calibration_ids = sorted(p["skill_id"] for p in profiles.values() if p["status"] == "calibration_needed")
    strong_ids = sorted(
        (p for p in profiles.values() if p["status"] in ("strength", "likely_strength")),
        key=lambda p: (-(p["skill_rating_shrunk"] or 0), p["skill_id"]),
    )
    return {
        "repair": repair_ids,
        "review": review_ids,
        "underexposed": underexposed_ids,
        "calibration": calibration_ids,
        "strong": [p["skill_id"] for p in strong_ids],
        "any": sorted(profiles),
    }


# ─── Candidate picking ───────────────────────────────────────────────────────


def _target_rating(profile: dict[str, Any] | None, mode: str, struggle: float, extra_offset: int = 0) -> int:
    base = None
    if profile is not None:
        base = profile["skill_rating_shrunk"] or profile["global_rating_anchor"]
    base = base or 1200
    bias = profile["preference_bias"] if profile else 0.0
    return int(round(base + MODE_OFFSETS[mode] + extra_offset - 100 * struggle + 50 * bias))


def _pick(
    world: dict[str, Any],
    state: SelectionState,
    skill_id: str,
    mode: str,
    target: int,
    *,
    ignore_diversity: bool = False,
) -> dict[str, Any] | None:
    pool = world["candidates_by_skill"].get(skill_id, [])
    if not pool:
        return None
    is_review = mode == "review_or_warmup"

    def eligible(row: dict[str, Any], window: int | None) -> bool:
        pid = row["problem_key"]
        if pid in world["suppressed"] or pid in world["recently_attempted"]:
            return False
        if pid in world["solved"]:
            if not is_review:
                return False
            solve_age_days = (world["cutoff"] - world["solved"][pid]) / DAY_SECONDS
            if solve_age_days <= RECENT_ATTEMPT_DAYS:
                return False
        # Last-resort fallback pass (see build_daily_queue): still never repeat
        # the exact same problem, but skip the contest/top-level/leaf diversity
        # caps so a prolific user with a near-exhausted pool for their assigned
        # skills can still get a minimum floor of recommendations.
        if pid in state.used_problems:
            return False
        if not ignore_diversity and state.violates(row, skill_id, mode):
            return False
        if window is not None:
            if row["rating"] is None:
                return False
            if abs(row["rating"] - target) > window:
                return False
        return True

    for window in (150, 300, None):  # relaxation ladder; None = any rating/unrated
        shortlist = [row for row in pool if eligible(row, window)]
        if not shortlist:
            continue
        quality = profiles_mod.quality_scores([row["problem_key"] for row in shortlist])
        scored = []
        for row in shortlist:
            closeness = 0.5
            if row["rating"] is not None:
                closeness = 1.0 - min(abs(row["rating"] - target), 400) / 400.0
            q = quality.get(row["problem_key"], 0.0)
            score = 0.5 * q + 0.3 * closeness + 0.2 * row["weight"]
            scored.append((score, q, row))
        scored.sort(key=lambda t: (-t[0], t[2]["problem_key"]))
        score, q, best = scored[0]
        return {"problem": best, "quality": round(q, 4), "score": round(score, 4), "relaxed": window is None}
    return None


def _why(skill_profile: dict[str, Any] | None, skill_id: str, mode: str, target: int,
         picked: dict[str, Any], struggle: float) -> str:
    status = skill_profile["status"] if skill_profile else "unknown"
    severity = skill_profile["severity"] if skill_profile else 0
    confidence = skill_profile["confidence"] if skill_profile else 0
    rating = picked["problem"]["rating"]
    parts = [
        f"Selected for {mode} on {skill_id} (status: {status}, severity {severity}, confidence {confidence}).",
        f"Target rating {target}" + (f", problem rated {rating}." if rating is not None else ", problem unrated."),
    ]
    if struggle >= HIGH_STRUGGLE:
        parts.append(f"Difficulty lowered because recent struggle is high ({struggle}).")
    if picked["relaxed"]:
        parts.append("Few candidates matched the target window, so the range was widened.")
    parts.append(f"Problem quality score {picked['quality']}.")
    return " ".join(parts)


# ─── Daily queue ─────────────────────────────────────────────────────────────


def _slot_assignments(lineup: dict[str, Any], template: list[str], struggle: float) -> list[tuple[str, str]]:
    """(mode, skill_id) per slot, honoring diversity and struggle rules."""
    assignments: list[tuple[str, str]] = []
    repair = lineup["repair"] or lineup["calibration"] or lineup["underexposed"] or lineup["any"]
    review_skill = (lineup["review"] or repair or lineup["any"])[0] if (lineup["review"] or repair or lineup["any"]) else None
    repair_idx = 0

    def next_repair(exclude_top: set[str]) -> str | None:
        nonlocal repair_idx
        for i in range(len(repair)):
            candidate = repair[(repair_idx + i) % len(repair)]
            if top_level(candidate) not in exclude_top:
                repair_idx = (repair_idx + i + 1) % len(repair)
                return candidate
        if repair:
            candidate = repair[repair_idx % len(repair)]
            repair_idx += 1
            return candidate
        return None

    used_top: list[str] = []
    for slot_mode in template:
        if slot_mode == "review_or_warmup":
            if review_skill is None:
                continue
            assignments.append(("review_or_warmup", review_skill))
            used_top.append(top_level(review_skill))
        elif slot_mode == "core_repair":
            # Prefer a different top-level than the previous repair slot.
            exclude = {t for t in used_top if used_top.count(t) >= 2}
            prev_repairs = [s for m, s in assignments if m == "core_repair"]
            if prev_repairs:
                exclude = exclude | {top_level(prev_repairs[-1])}
            skill = next_repair(exclude)
            if skill is None:
                continue
            mode = "core_repair" if lineup["repair"] else ("calibration" if lineup["calibration"] else "underexposed_exploration")
            assignments.append((mode, skill))
            used_top.append(top_level(skill))
        else:  # transfer_or_stretch
            if struggle >= HIGH_STRUGGLE:
                mode = "transfer"
                skill = (lineup["underexposed"] or lineup["review"] or repair or lineup["any"])[0] if (lineup["underexposed"] or lineup["review"] or repair or lineup["any"]) else None
                if lineup["underexposed"]:
                    mode = "underexposed_exploration"
            elif lineup["strong"]:
                mode, skill = "stretch", lineup["strong"][0]
            elif lineup["underexposed"]:
                mode, skill = "underexposed_exploration", lineup["underexposed"][0]
            elif repair:
                mode, skill = "transfer", repair[0]
            else:
                skill = None
            if skill is None:
                continue
            assignments.append((mode, skill))
            used_top.append(top_level(skill))

    # At least 2 distinct top-level skills for queues of 4-5.
    if len(assignments) >= 4 and len({top_level(s) for _, s in assignments}) < 2:
        for alt in lineup["any"]:
            if top_level(alt) != top_level(assignments[-1][1]):
                assignments[-1] = (assignments[-1][0], alt)
                break
    return assignments


def _fill_queue_floor(
    world: dict[str, Any],
    state: SelectionState,
    lineup: dict[str, Any],
    struggle: float,
    items: list[dict[str, Any]],
    floor: int,
) -> int:
    """Last-resort top-up: if normal slot assignment (which targets specific
    skills and enforces contest/top-level/leaf diversity) yields fewer than
    `floor` items, widen the search to any mapped skill and ignore diversity
    caps — but never relax the solved/recently-attempted/suppressed exclusions
    and never repeat an already-picked problem. This only fires for the rare
    case where the catalog and skill map exist but a heavy submission history
    has exhausted the closest matches for the user's specific weak skills.
    Returns the number of items added.
    """
    added = 0
    if len(items) >= floor:
        return added
    ordered_skills = list(dict.fromkeys(lineup["any"] + sorted(world["candidates_by_skill"])))
    # Repeat full passes over every mapped skill (not just one pick each) —
    # each successful pick removes exactly one problem from its pool via
    # state.used_problems, so a skill with several untouched candidates (e.g.
    # a heavy user's one never-practiced tag) can fill the whole floor by
    # itself. Stop once a full pass adds nothing, to guarantee termination.
    progress = True
    while len(items) < floor and progress:
        progress = False
        for skill_id in ordered_skills:
            if len(items) >= floor:
                break
            profile = world["profiles"].get(skill_id)
            target = _target_rating(profile, "transfer", struggle, 0)
            picked = _pick(world, state, skill_id, "transfer", target, ignore_diversity=True)
            if picked is None:
                continue
            state.commit(picked["problem"], skill_id)
            items.append({
                "item_id": str(uuid.uuid4()),
                "slot": len(items) + 1,
                "mode": "transfer",
                "problem_id": picked["problem"]["problem_key"],
                "problem_name": picked["problem"]["name"],
                "skill_id": skill_id,
                "target_rating": target,
                "problem_rating": picked["problem"]["rating"],
                "quality_score": picked["quality"],
                "final_score": picked["score"],
                "why_selected": _why(profile, skill_id, "transfer", target, picked, struggle)
                + " Fallback pick: broadened beyond the usual variety limits because your"
                " recent history had exhausted the closest matches.",
                "item_status": "proposed",
            })
            added += 1
            progress = True
    return added


def build_daily_queue(
    handle: str, queue_date: str | None = None, size: int = 4, force: bool = False
) -> dict[str, Any]:
    canonical = store.canonical_handle(handle)
    queue_date = queue_date or dt.date.today().isoformat()
    size = max(3, min(5, size))

    if not force:
        existing = _get_queue_run(canonical, queue_date)
        if existing is not None:
            return {**existing, "reused": True}

    world = _load_world(canonical)
    if not world["profiles"]:
        return {"handle": canonical, "queue_date": queue_date, "items": [],
                "warnings": [_no_profiles_warning(canonical)], "reused": False}

    lineup = _skill_lineup(world["profiles"])
    struggle = _recent_struggle(world["profiles"], lineup["repair"][:3] or lineup["any"][:3])
    state = SelectionState()
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    for slot, (mode, skill_id) in enumerate(_slot_assignments(lineup, QUEUE_TEMPLATES[size], struggle), start=1):
        profile = world["profiles"].get(skill_id)
        extra = 0
        target = _target_rating(profile, mode, struggle, extra)
        picked = _pick(world, state, skill_id, mode, target)
        if picked is None:
            warnings.append(f"no_candidate_for_slot_{slot}_{skill_id}")
            continue
        state.commit(picked["problem"], skill_id)
        items.append({
            "item_id": str(uuid.uuid4()),
            "slot": slot,
            "mode": mode,
            "problem_id": picked["problem"]["problem_key"],
            "problem_name": picked["problem"]["name"],
            "skill_id": skill_id,
            "target_rating": target,
            "problem_rating": picked["problem"]["rating"],
            "quality_score": picked["quality"],
            "final_score": picked["score"],
            "why_selected": _why(profile, skill_id, mode, target, picked, struggle),
            "item_status": "proposed",
        })

    if len(items) < MIN_QUEUE_FLOOR:
        added = _fill_queue_floor(world, state, lineup, struggle, items, floor=MIN_QUEUE_FLOOR)
        if added:
            warnings.append("fallback_expanded_pool_used")

    if not items:
        warnings.append("insufficient_candidates")

    analysis_run_id = next(iter(world["profiles"].values()))["analysis_run_id"] if world["profiles"] else None
    run = {
        "run_id": str(uuid.uuid4()),
        "handle": canonical,
        "analysis_run_id": analysis_run_id,
        "queue_date": queue_date,
        "recent_struggle": struggle,
        "warnings": warnings,
        "created_at": store._now(),
    }
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO recommendation_runs (run_id, handle, analysis_run_id, queue_date, recent_struggle, warnings, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run["run_id"], canonical, analysis_run_id, queue_date, struggle,
             json.dumps(warnings, ensure_ascii=False), run["created_at"]),
        )
        for item in items:
            conn.execute(
                "INSERT INTO recommendation_items (item_id, run_id, slot, mode, problem_id, skill_id,"
                " target_rating, problem_rating, quality_score, final_score, why_selected, item_status)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item["item_id"], run["run_id"], item["slot"], item["mode"], item["problem_id"], item["skill_id"],
                 item["target_rating"], item["problem_rating"], item["quality_score"], item["final_score"],
                 item["why_selected"], item["item_status"]),
            )
    return {**run, "items": items, "reused": False}


def _get_queue_run(handle: str, queue_date: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        run = conn.execute(
            "SELECT * FROM recommendation_runs WHERE handle = ? AND queue_date = ? ORDER BY created_at DESC LIMIT 1",
            (handle, queue_date),
        ).fetchone()
        if run is None:
            return None
        items = conn.execute(
            "SELECT * FROM recommendation_items WHERE run_id = ? ORDER BY slot", (run["run_id"],)
        ).fetchall()
    payload = dict(run)
    payload["warnings"] = json.loads(payload["warnings"])
    payload["items"] = [dict(item) for item in items]
    return payload


def get_today_queue(handle: str) -> dict[str, Any] | None:
    return _get_queue_run(store.canonical_handle(handle), dt.date.today().isoformat())


# ─── Plans ───────────────────────────────────────────────────────────────────


def build_plan(handle: str, plan_type: str, start_date: str | None = None, force: bool = False) -> dict[str, Any]:
    assert plan_type in ("7_day", "14_day")
    canonical = store.canonical_handle(handle)
    start_date = start_date or dt.date.today().isoformat()

    if not force:
        existing = _find_plan(canonical, plan_type, start_date)
        if existing is not None:
            return {**get_plan(existing), "reused": True}

    world = _load_world(canonical)
    if not world["profiles"]:
        # start_date must always be present: the frontend renders
        # `Starts ${plan.start_date}` unconditionally once a plan object comes
        # back, so omitting it here previously rendered "Starts undefined".
        return {"handle": canonical, "plan_type": plan_type, "start_date": start_date, "days": [],
                "warnings": [_no_profiles_warning(canonical)], "reused": False}

    lineup = _skill_lineup(world["profiles"])
    struggle = _recent_struggle(world["profiles"], lineup["repair"][:3] or lineup["any"][:3])
    template = PLAN_7 if plan_type == "7_day" else PLAN_14

    plan_id = str(uuid.uuid4())
    analysis_run_id = next(iter(world["profiles"].values()))["analysis_run_id"]
    state = SelectionState()  # plan-wide: no duplicate problems across days
    rotation = {"repair": 0, "review": 0, "strong": 0, "underexposed": 0}

    def rotate(kind: str, fallback: list[str]) -> str | None:
        skills = lineup[kind] or fallback
        if not skills:
            return None
        skill = skills[rotation[kind] % len(skills)] if kind in rotation else skills[0]
        if kind in rotation:
            rotation[kind] += 1
        return skill

    days_payload = []
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO training_plans (plan_id, handle, plan_type, analysis_run_id, start_date, plan_status, created_at)"
            " VALUES (?, ?, ?, ?, ?, 'active', ?)",
            (plan_id, canonical, plan_type, analysis_run_id, start_date, store._now()),
        )
        for day_number, theme, slots in template:
            conn.execute(
                "INSERT INTO training_plan_days (plan_id, day_number, theme) VALUES (?, ?, ?)",
                (plan_id, day_number, theme),
            )
            day_items = []
            # Contest constraint applies within a day, not across the plan.
            state.contest_counts = {}
            state.top_level_counts = {}
            state.leaf_used = set()
            for slot, (mode, extra) in enumerate(slots, start=1):
                if mode == "stretch" and struggle >= HIGH_STRUGGLE:
                    mode = "transfer"
                if mode == "core_repair":
                    skill_id = rotate("repair", lineup["calibration"] or lineup["any"])
                elif mode == "review_or_warmup":
                    skill_id = rotate("review", lineup["repair"] or lineup["any"])
                elif mode == "stretch":
                    skill_id = rotate("strong", lineup["repair"] or lineup["any"])
                else:  # transfer
                    skill_id = rotate("underexposed", lineup["review"] or lineup["repair"] or lineup["any"])
                    if skill_id is not None and skill_id in lineup["underexposed"]:
                        mode = "underexposed_exploration"
                if skill_id is None:
                    continue
                profile = world["profiles"].get(skill_id)
                target = _target_rating(profile, mode, struggle, extra)
                picked = _pick(world, state, skill_id, mode, target)
                if picked is None:
                    continue
                state.commit(picked["problem"], skill_id)
                item_id = str(uuid.uuid4())
                why = _why(profile, skill_id, mode, target, picked, struggle)
                conn.execute(
                    "INSERT INTO training_plan_items (item_id, plan_id, day_number, slot, mode, problem_id,"
                    " skill_id, target_rating, problem_rating, why_selected, item_status)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed')",
                    (item_id, plan_id, day_number, slot, mode, picked["problem"]["problem_key"], skill_id,
                     target, picked["problem"]["rating"], why),
                )
                day_items.append({
                    "item_id": item_id, "slot": slot, "mode": mode,
                    "problem_id": picked["problem"]["problem_key"], "skill_id": skill_id,
                    "target_rating": target, "problem_rating": picked["problem"]["rating"],
                    "why_selected": why, "item_status": "proposed",
                })
            days_payload.append({"day_number": day_number, "theme": theme, "items": day_items})

    return {
        "plan_id": plan_id,
        "handle": canonical,
        "plan_type": plan_type,
        "analysis_run_id": analysis_run_id,
        "start_date": start_date,
        "recent_struggle": struggle,
        "days": days_payload,
        "reused": False,
    }


def _find_plan(handle: str, plan_type: str, start_date: str) -> str | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT plan_id FROM training_plans WHERE handle = ? AND plan_type = ? AND start_date = ?"
            " AND plan_status = 'active' ORDER BY created_at DESC LIMIT 1",
            (handle, plan_type, start_date),
        ).fetchone()
    return row["plan_id"] if row else None


def get_plan(plan_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        plan = conn.execute("SELECT * FROM training_plans WHERE plan_id = ?", (plan_id,)).fetchone()
        if plan is None:
            return None
        days = conn.execute(
            "SELECT * FROM training_plan_days WHERE plan_id = ? ORDER BY day_number", (plan_id,)
        ).fetchall()
        items = conn.execute(
            "SELECT * FROM training_plan_items WHERE plan_id = ? ORDER BY day_number, slot", (plan_id,)
        ).fetchall()
    items_by_day: dict[int, list[dict[str, Any]]] = {}
    for item in items:
        items_by_day.setdefault(item["day_number"], []).append(dict(item))
    return {
        "plan_id": plan_id,
        "handle": plan["handle"],
        "plan_type": plan["plan_type"],
        "analysis_run_id": plan["analysis_run_id"],
        "start_date": plan["start_date"],
        "plan_status": plan["plan_status"],
        "days": [
            {"day_number": day["day_number"], "theme": day["theme"], "items": items_by_day.get(day["day_number"], [])}
            for day in days
        ],
    }
