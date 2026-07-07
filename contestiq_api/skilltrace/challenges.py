"""Challenge bank. Hidden tests live in challenge_test_sets and are returned
ONLY to the backend grading path — never through any API payload."""

from __future__ import annotations

import json
import uuid
from typing import Any

from contestiq_api.cfdata import store

# Seed bank: small, real challenges so the flow works end-to-end. Statements
# and examples are public; hidden tests exist only server-side.
SEED_CHALLENGES: list[dict[str, Any]] = [
    {
        "challenge_id": "st_implementation_l1_v1",
        "skill_id": "implementation",
        "level": 1,
        "title": "Sum With Care",
        "statement": (
            "Read two integers a and b (|a|,|b| <= 10^9), one line, separated by a space. "
            "Print a + b."
        ),
        "examples": [{"input": "2 3", "output": "5"}, {"input": "-4 4", "output": "0"}],
        "hidden_tests": [
            {"input": "10 20", "expected_output": "30"},
            {"input": "-1000000000 -1000000000", "expected_output": "-2000000000"},
            {"input": "999999999 1", "expected_output": "1000000000"},
            {"input": "0 0", "expected_output": "0"},
        ],
    },
    {
        "challenge_id": "st_binary_search_l2_v1",
        "skill_id": "binary_search",
        "level": 2,
        "title": "Count Not Above",
        "statement": (
            "First line: n and q (1 <= n,q <= 2*10^5). Second line: n integers, sorted "
            "non-decreasing. Then q lines each with an integer x. For each query print "
            "how many array values are <= x."
        ),
        "examples": [{"input": "5 2\n1 3 3 7 9\n3\n8", "output": "3\n4"}],
        "hidden_tests": [
            {"input": "3 3\n2 4 6\n1\n4\n10", "expected_output": "0\n2\n3"},
            {"input": "1 1\n5\n5", "expected_output": "1"},
            {"input": "4 2\n1 1 1 1\n0\n1", "expected_output": "0\n4"},
        ],
    },
    {
        "challenge_id": "st_greedy_l1_v1",
        "skill_id": "greedy",
        "level": 1,
        "title": "Minimum Coins",
        "statement": (
            "Read n (1 <= n <= 10^9). Using coins of value 1, 5, and 10, print the "
            "minimum number of coins that sum to n."
        ),
        "examples": [{"input": "27", "output": "5"}],
        "hidden_tests": [
            {"input": "1", "expected_output": "1"},
            {"input": "16", "expected_output": "3"},
            {"input": "99", "expected_output": "13"},
        ],
    },
]


def seed_challenges() -> dict[str, int]:
    """Idempotent seed of the challenge bank + hidden test sets."""
    now = store._now()
    inserted = 0
    with store.connect() as conn:
        for ch in SEED_CHALLENGES:
            test_set_id = f"ts_{ch['challenge_id']}"
            cursor = conn.execute(
                "INSERT OR IGNORE INTO challenges (challenge_id, skill_id, level, title, statement, examples,"
                " hidden_tests_ref, version, challenge_status, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'active', ?)",
                (
                    ch["challenge_id"], ch["skill_id"], ch["level"], ch["title"], ch["statement"],
                    json.dumps(ch["examples"], ensure_ascii=False), test_set_id, now,
                ),
            )
            inserted += cursor.rowcount
            conn.execute(
                "INSERT OR IGNORE INTO challenge_test_sets (test_set_id, challenge_id, is_hidden, tests, version, created_at)"
                " VALUES (?, ?, 1, ?, 1, ?)",
                (test_set_id, ch["challenge_id"], json.dumps(ch["hidden_tests"], ensure_ascii=False), now),
            )
    return {"challenges": inserted}


def assign_challenge(skill_id: str, level: int | None = None) -> dict[str, Any] | None:
    """Pick an active challenge for the skill (closest level, newest version)."""
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM challenges WHERE skill_id = ? AND challenge_status = 'active'"
            " ORDER BY version DESC, level ASC",
            (skill_id,),
        ).fetchall()
    if not rows:
        return None
    challenges_list = [dict(row) for row in rows]
    if level is not None:
        challenges_list.sort(key=lambda ch: (abs(ch["level"] - level), -ch["version"]))
    return challenges_list[0]


def public_challenge(challenge: dict[str, Any]) -> dict[str, Any]:
    """The ONLY challenge projection that may leave the backend."""
    return {
        "challenge_id": challenge["challenge_id"],
        "skill_id": challenge["skill_id"],
        "level": challenge["level"],
        "title": challenge["title"],
        "statement": challenge["statement"],
        "examples": json.loads(challenge["examples"]) if isinstance(challenge["examples"], str) else challenge["examples"],
        "version": challenge["version"],
    }


def hidden_tests_for(challenge_id: str) -> list[dict[str, str]]:
    """Backend grading path only. Never serialize this into a response."""
    with store.connect() as conn:
        row = conn.execute(
            "SELECT tests FROM challenge_test_sets WHERE challenge_id = ? AND is_hidden = 1"
            " ORDER BY version DESC LIMIT 1",
            (challenge_id,),
        ).fetchone()
    return json.loads(row["tests"]) if row else []


def get_challenge(challenge_id: str) -> dict[str, Any] | None:
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM challenges WHERE challenge_id = ?", (challenge_id,)).fetchone()
    return dict(row) if row else None
