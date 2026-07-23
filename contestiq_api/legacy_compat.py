"""Backend port of the legacy frontend analysis (wope/src/lib/cfAnalysis.ts).

The old Next.js /api/analyze route computed its own analysis in TypeScript,
which made the frontend a second source of truth. This module reproduces that
output shape (camelCase, field-for-field) so the Next.js route can become a
thin proxy while the UI keeps rendering unchanged. It is a temporary
compatibility layer: once the UI consumes /api/v1 responses directly, delete
this module together with the proxy route.
"""

from __future__ import annotations

import math
from typing import Any

V_AC = "OK"
V_WA = "WRONG_ANSWER"
V_TLE = "TIME_LIMIT_EXCEEDED"
V_RE = "RUNTIME_ERROR"
V_CE = "COMPILE_ERROR"
V_MLE = "MEMORY_LIMIT_EXCEEDED"

SKIP_TAGS = {"*special", "interactive"}
MIN_PROBLEMS = 3
MIN_SUBS = 5

TAG_COLORS = {
    "constructive algorithms": "#FF4D6D",
    "implementation": "#00F5A0",
    "math": "#FACC15",
    "greedy": "#00D9F5",
    "dp": "#f97316",
    "dynamic programming": "#f97316",
    "data structures": "#a78bfa",
    "graphs": "#00D9F5",
    "trees": "#00F5A0",
    "brute force": "#8A9A96",
    "binary search": "#00D9F5",
    "sorting": "#FACC15",
    "number theory": "#FACC15",
    "strings": "#f97316",
    "geometry": "#a78bfa",
    "dfs and similar": "#00D9F5",
    "games": "#FACC15",
    "shortest paths": "#00D9F5",
    "two pointers": "#00F5A0",
    "bitmasks": "#f97316",
    "combinatorics": "#FACC15",
}

DEFAULT_COLOR = "#8A9A96"


def _tag_color(tag: str) -> str:
    return TAG_COLORS.get(tag.lower(), DEFAULT_COLOR)


def _capitalize(text: str) -> str:
    return " ".join(word[:1].upper() + word[1:] for word in text.split(" "))


def _js_round(value: float) -> int:
    """JS Math.round: round half toward +infinity (Python's round() is banker's)."""
    return math.floor(value + 0.5)


def _problem_key(sub: dict[str, Any]) -> str:
    cid = sub.get("problem", {}).get("contestId") or sub.get("contestId") or 0
    return f"{cid}:{sub.get('problem', {}).get('index')}"


def _build_problem_map(submissions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    problems: dict[str, dict[str, Any]] = {}
    for sub in submissions:
        key = _problem_key(sub)
        problem = sub.get("problem", {})
        if key not in problems:
            problems[key] = {
                "key": key,
                "name": problem.get("name", ""),
                "rating": problem.get("rating"),
                "tags": problem.get("tags", []),
                "subs": [],
                "solved": False,
                "attemptsBeforeAC": 0,
            }
        problems[key]["subs"].append(sub)

    # CF returns submissions newest-first; reverse per-problem for chronological order.
    for ps in problems.values():
        ps["subs"].reverse()
        attempts = 0
        for sub in ps["subs"]:
            attempts += 1
            if sub.get("verdict") == V_AC:
                ps["solved"] = True
                ps["attemptsBeforeAC"] = attempts
                break
    return problems


def legacy_analysis(user: dict[str, Any], submissions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the legacy AnalysisResult shape from raw Codeforces API payloads."""
    problem_map = _build_problem_map(submissions)
    all_problems = list(problem_map.values())

    lang_count: dict[str, int] = {}
    for sub in submissions:
        if sub.get("verdict") == V_AC:
            lang = str(sub.get("programmingLanguage", "")).split(" ")[0]
            lang_count[lang] = lang_count.get(lang, 0) + 1
    main_language = max(lang_count.items(), key=lambda kv: kv[1])[0] if lang_count else "Unknown"

    solved_problems = [p for p in all_problems if p["solved"]]
    unique_solved = len(solved_problems)
    rated_solved = [p for p in solved_problems if isinstance(p["rating"], (int, float)) and p["rating"] > 0]
    avg_solved_rating = (
        _js_round(sum(p["rating"] for p in rated_solved) / len(rated_solved)) if rated_solved else 0
    )

    error_breakdown = {
        "wrongAnswer": 0,
        "timeLimitExceeded": 0,
        "runtimeError": 0,
        "compileError": 0,
        "memoryLimitExceeded": 0,
        "other": 0,
    }
    for sub in submissions:
        verdict = sub.get("verdict")
        if verdict == V_WA:
            error_breakdown["wrongAnswer"] += 1
        elif verdict == V_TLE:
            error_breakdown["timeLimitExceeded"] += 1
        elif verdict == V_RE:
            error_breakdown["runtimeError"] += 1
        elif verdict == V_CE:
            error_breakdown["compileError"] += 1
        elif verdict == V_MLE:
            error_breakdown["memoryLimitExceeded"] += 1
        elif verdict and verdict != V_AC:
            error_breakdown["other"] += 1

    tag_problems: dict[str, list[dict[str, Any]]] = {}
    for ps in all_problems:
        for tag in ps["tags"]:
            if tag in SKIP_TAGS:
                continue
            tag_problems.setdefault(tag, []).append(ps)

    friction_areas: list[dict[str, Any]] = []
    strong_topics: list[dict[str, Any]] = []

    for tag, problems in tag_problems.items():
        if len(problems) < MIN_PROBLEMS:
            continue
        total_subs = sum(len(p["subs"]) for p in problems)
        if total_subs < MIN_SUBS:
            continue

        solved = sum(1 for p in problems if p["solved"])
        attempted = len(problems)
        wa_count = sum(1 for p in problems for s in p["subs"] if s.get("verdict") == V_WA)
        tle_count = sum(1 for p in problems for s in p["subs"] if s.get("verdict") == V_TLE)
        re_count = sum(1 for p in problems for s in p["subs"] if s.get("verdict") == V_RE)

        solved_with_data = [p for p in problems if p["solved"] and p["attemptsBeforeAC"] > 0]
        avg_attempts_before_ac = (
            sum(p["attemptsBeforeAC"] for p in solved_with_data) / len(solved_with_data)
            if solved_with_data
            else 1.0
        )

        solve_rate = solved / attempted
        wa_rate = wa_count / total_subs if total_subs > 0 else 0.0
        tle_rate = tle_count / total_subs if total_subs > 0 else 0.0
        retry_penalty = min((avg_attempts_before_ac - 1) / 4, 1.0)

        friction_score = wa_rate * 40 + tle_rate * 30 + retry_penalty * 20 + (1 - solve_rate) * 10
        if friction_score < 4:
            continue

        confidence = "high" if attempted >= 20 else "medium" if attempted >= 10 else "low"

        if wa_rate > 0.3:
            issue = "High wrong-answer rate"
            action = "Practice systematic edge-case testing"
        elif tle_rate > 0.15:
            issue = "High time-limit rate"
            action = "Review algorithmic complexity and optimize"
        elif avg_attempts_before_ac > 3.5:
            issue = f"Avg {avg_attempts_before_ac:.1f} attempts before AC"
            action = "Plan before coding — reduce submission trial-and-error"
        elif solve_rate < 0.5:
            issue = "Low solve rate"
            action = "Focus on fundamentals for this topic"
        elif wa_rate > 0.18:
            issue = "Elevated WA count"
            action = "Add corner-case checks before each submission"
        else:
            issue = "High retry cost"
            action = "Deliberate practice and pattern review"

        friction_areas.append(
            {
                "tag": tag,
                "solved": solved,
                "attempted": attempted,
                "totalSubmissions": total_subs,
                "waCount": wa_count,
                "tleCount": tle_count,
                "reCount": re_count,
                "avgAttemptsBeforeAC": float(f"{avg_attempts_before_ac:.1f}"),
                "solveRate": solve_rate,
                "frictionScore": friction_score,
                "issue": issue,
                "action": action,
                "confidence": confidence,
                "color": _tag_color(tag),
            }
        )

        if solve_rate >= 0.8 and avg_attempts_before_ac <= 1.6 and attempted >= 10:
            strong_topics.append(
                {
                    "tag": tag,
                    "solved": solved,
                    "solveRate": solve_rate,
                    "avgAttempts": float(f"{avg_attempts_before_ac:.1f}"),
                }
            )

    friction_areas.sort(key=lambda a: -a["frictionScore"])
    strong_topics.sort(key=lambda t: -t["solved"])
    top_friction = friction_areas[:6]
    top_strong = strong_topics[:5]

    buckets: dict[int, dict[str, int]] = {}
    for ps in all_problems:
        rating = ps["rating"]
        if not rating or rating <= 0:
            continue
        bucket = _js_round(rating / 100) * 100
        stats = buckets.setdefault(bucket, {"solved": 0, "attempted": 0})
        stats["attempted"] += 1
        if ps["solved"]:
            stats["solved"] += 1

    good_buckets = sorted(
        bucket for bucket, stats in buckets.items() if stats["attempted"] >= 3 and stats["solved"] / stats["attempted"] >= 0.6
    )
    comfort_min = good_buckets[0] if good_buckets else 800
    comfort_max = good_buckets[-1] if good_buckets else comfort_min + 400
    # JS Object.entries iterates integer-like keys in ascending order; stable sort by solved desc.
    bucket_entries = sorted(sorted(buckets.items()), key=lambda kv: -kv[1]["solved"])
    comfort_sweet = (
        bucket_entries[0][0] if bucket_entries else _js_round((comfort_min + comfort_max) / 2 / 100) * 100
    )

    top_friction_tags = {a["tag"] for a in top_friction}
    candidates: list[dict[str, Any]] = []
    for ps in all_problems:
        friction_tag = next((t for t in ps["tags"] if t in top_friction_tags), None)
        if friction_tag is None:
            continue
        first_sub = ps["subs"][0] if ps["subs"] else {}
        contest_id = first_sub.get("problem", {}).get("contestId") or first_sub.get("contestId")
        if not ps["solved"]:
            candidates.append(
                {
                    "name": ps["name"],
                    "rating": ps["rating"] if ps["rating"] is not None else comfort_sweet,
                    "tags": ps["tags"],
                    "reason": f"Attempted {len(ps['subs'])}× — unresolved in {_capitalize(friction_tag)}",
                    "contestId": contest_id,
                    "index": first_sub.get("problem", {}).get("index"),
                }
            )
        elif ps["attemptsBeforeAC"] >= 4:
            candidates.append(
                {
                    "name": ps["name"],
                    "rating": ps["rating"] if ps["rating"] is not None else comfort_sweet,
                    "tags": ps["tags"],
                    "reason": f"Solved after {ps['attemptsBeforeAC']} attempts — high retry in {_capitalize(friction_tag)}",
                    "contestId": contest_id,
                    "index": first_sub.get("problem", {}).get("index"),
                }
            )

    candidates.sort(key=lambda c: abs(c["rating"] - comfort_sweet))
    recommended_problems = candidates[:8]

    seven_day_queue: list[dict[str, Any]] = []
    queue_tags = [a["tag"] for a in top_friction[:3]]
    for day in range(1, 8):
        if day == 7:
            seven_day_queue.append(
                {
                    "day": 7,
                    "focus": "Review & Reinforce",
                    "rating": comfort_sweet,
                    "reason": "Consolidate week's patterns and verify retention",
                    "tagColor": DEFAULT_COLOR,
                }
            )
            continue
        if day == 6:
            prob = candidates[5] if len(candidates) > 5 else None
            seven_day_queue.append(
                {
                    "day": 6,
                    "focus": "Mixed Practice",
                    "problemName": prob["name"] if prob else None,
                    **(
                        {
                            "contestId": prob["contestId"],
                            "index": prob["index"],
                        }
                        if prob and prob.get("contestId") and prob.get("index")
                        else {}
                    ),
                    "rating": prob["rating"] if prob else comfort_sweet,
                    "reason": "Cross-tag practice to consolidate patterns",
                    "tagColor": DEFAULT_COLOR,
                }
            )
            continue

        tag = queue_tags[(day - 1) % max(len(queue_tags), 1)] if queue_tags else "implementation"
        prob = candidates[day - 1] if len(candidates) > day - 1 else None
        area = next((a for a in top_friction if a["tag"] == tag), None)
        seven_day_queue.append(
            {
                "day": day,
                "focus": _capitalize(tag),
                "problemName": prob["name"] if prob else None,
                **(
                    {
                        "contestId": prob["contestId"],
                        "index": prob["index"],
                    }
                    if prob and prob.get("contestId") and prob.get("index")
                    else {}
                ),
                "rating": prob["rating"] if prob else comfort_sweet,
                "reason": area["issue"] if area else "Friction area",
                "tagColor": _tag_color(tag),
            }
        )

    handle = user.get("handle", "")
    top_tag = top_friction[0] if top_friction else None
    strong_tag = top_strong[0] if top_strong else None
    if top_tag:
        diagnosis = (
            f"{handle} has solved {unique_solved} unique problems across {len(submissions)} submissions. "
            + (f"Strongest in {_capitalize(strong_tag['tag'])}." if strong_tag else "")
            + f" Training friction appears in {', '.join(_capitalize(a['tag']) for a in top_friction[:3])}"
            + f" due to {top_tag['issue'].lower()}."
        )
    else:
        diagnosis = (
            f"{handle} has solved {unique_solved} unique problems across {len(submissions)} submissions. "
            "No significant friction patterns detected — solid all-round performance."
        )

    return {
        "handle": handle,
        "profile": {
            "handle": handle,
            "rating": user.get("rating", 0) or 0,
            "maxRating": user.get("maxRating", 0) or 0,
            "rank": user.get("rank") or "unrated",
            "maxRank": user.get("maxRank") or "unrated",
            "country": user.get("country") or "",
            "organization": user.get("organization") or "",
        },
        "summary": {
            "totalSubmissions": len(submissions),
            "uniqueSolved": unique_solved,
            "mainLanguage": main_language,
            "avgSolvedRating": avg_solved_rating,
        },
        "diagnosis": diagnosis,
        "frictionAreas": top_friction,
        "strongTopics": top_strong,
        "errorBreakdown": error_breakdown,
        "ratingComfortZone": {"min": comfort_min, "max": comfort_max, "sweet": comfort_sweet},
        "recommendedProblems": recommended_problems,
        "sevenDayQueue": seven_day_queue,
    }
