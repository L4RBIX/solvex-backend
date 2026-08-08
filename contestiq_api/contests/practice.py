"""Post-contest practice + analysis for a Codeforces handle."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.contests.lifecycle import readiness_payload, refresh_problem_lifecycle
from contestiq_api.contests.similar import list_similar


def contest_practice(contest_id: int, handle: str) -> dict[str, Any]:
    handle = (handle or "").strip()
    with store.connect() as conn:
        contest = conn.execute(
            "SELECT * FROM cf_contests WHERE contest_id = ?",
            (contest_id,),
        ).fetchone()
        problems = conn.execute(
            """
            SELECT problem_key, problem_index, name, rating, tags
            FROM problems WHERE contest_id = ?
            ORDER BY problem_index
            """,
            (contest_id,),
        ).fetchall()
        subs = []
        if handle:
            subs = conn.execute(
                """
                SELECT problem_key, verdict, creation_time, passed_test_count
                FROM cf_submissions_normalized
                WHERE handle = ? AND contest_id = ?
                ORDER BY creation_time ASC
                """,
                (handle.lower(), contest_id),
            ).fetchall()

    by_problem: dict[str, list[Any]] = {}
    for row in subs:
        by_problem.setdefault(row["problem_key"], []).append(row)

    solved: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    wrong_attempts = 0
    weak_tags: Counter[str] = Counter()

    for p in problems:
        pid = p["problem_key"]
        tags = json.loads(p["tags"] or "[]")
        attempts = by_problem.get(pid) or []
        life = refresh_problem_lifecycle(pid)
        ready = readiness_payload(life)
        entry = {
            "problem_id": pid,
            "index": p["problem_index"],
            "name": p["name"],
            "rating": p["rating"],
            "tags": tags,
            "readiness": ready,
            "attempts": len(attempts),
            "similar": list_similar(pid, limit=5),
        }
        if not attempts:
            skipped.append(entry)
            continue
        ac = any((a["verdict"] or "") == "OK" for a in attempts)
        fails = sum(1 for a in attempts if (a["verdict"] or "") not in {"OK", "COMPILATION_ERROR"})
        wrong_attempts += fails
        entry["wrong_before_ac"] = fails
        if ac:
            solved.append(entry)
        else:
            missed.append(entry)
            for tag in tags:
                weak_tags[str(tag)] += 1

    # Follow-up: similar to missed first, then skipped.
    follow_up: list[dict[str, Any]] = []
    seen: set[str] = set()
    for bucket in (missed, skipped):
        for item in bucket:
            for sim in item.get("similar") or []:
                sid = sim["problem_id"]
                if sid in seen:
                    continue
                seen.add(sid)
                follow_up.append(sim)
                if len(follow_up) >= 12:
                    break
            if len(follow_up) >= 12:
                break
        if len(follow_up) >= 12:
            break

    return {
        "contest_id": contest_id,
        "contest_name": contest["name"] if contest else f"Contest {contest_id}",
        "handle": handle or None,
        "solved": solved,
        "missed": missed,
        "skipped": skipped,
        "stats": {
            "solved_count": len(solved),
            "missed_count": len(missed),
            "skipped_count": len(skipped),
            "wrong_attempts": wrong_attempts,
            "problem_count": len(problems),
        },
        "weak_topics": [
            {"tag": tag, "misses": count} for tag, count in weak_tags.most_common(8)
        ],
        "recommended_follow_up": follow_up,
    }
