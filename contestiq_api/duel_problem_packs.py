"""Small, reviewed PvP problem packs with SolveX-authored summaries.

These packs do not claim official Codeforces judging. They provide enough
public task content to compete fairly and a private shared regression set for
SolveX practice-duel judging. Adding/changing tests requires a new pack/version.
"""

from __future__ import annotations

from typing import Any


BUILTIN_DUEL_PROBLEM_PACKS: tuple[dict[str, Any], ...] = (
    {
        "pack_id": "solvex-cf-4a-v1",
        "problem_id": "4A",
        "version": 1,
        "statement_summary": (
            "Given the integer weight of a watermelon, decide whether it can be split into "
            "two positive parts whose weights are both even."
        ),
        "input_format": "One integer w — the watermelon's weight.",
        "output_format": 'Print "YES" if such a split exists; otherwise print "NO".',
        "constraints_text": "1 ≤ w ≤ 100.",
        "sample_tests": [{"input": "8\n", "output": "YES\n"}, {"input": "2\n", "output": "NO\n"}],
        "judge_tests": [
            {"input": "1\n", "expected_output": "NO\n"},
            {"input": "2\n", "expected_output": "NO\n"},
            {"input": "4\n", "expected_output": "YES\n"},
            {"input": "99\n", "expected_output": "NO\n"},
            {"input": "100\n", "expected_output": "YES\n"},
        ],
    },
    {
        "pack_id": "solvex-cf-71a-v1",
        "problem_id": "71A",
        "version": 1,
        "statement_summary": (
            "Process a list of lowercase words. A word longer than 10 characters is replaced "
            "by its first character, the number of omitted middle characters, and its last character."
        ),
        "input_format": "The first line contains n. Each of the next n lines contains one lowercase word.",
        "output_format": "Print the transformed form of every word on its own line.",
        "constraints_text": "1 ≤ n ≤ 100; every word has 1 to 100 lowercase English letters.",
        "sample_tests": [
            {"input": "4\nword\nlocalization\ninternationalization\npneumonoultramicroscopicsilicovolcanoconiosis\n", "output": "word\nl10n\ni18n\np43s\n"}
        ],
        "judge_tests": [
            {"input": "5\nword\nlocalization\ninternationalization\nabcdefghijk\nabcdefghij\n", "expected_output": "word\nl10n\ni18n\na9k\nabcdefghij\n"},
            {"input": "3\na\nab\nabcdefghijklm\n", "expected_output": "a\nab\na11m\n"},
        ],
    },
    {
        "pack_id": "solvex-cf-231a-v1",
        "problem_id": "231A",
        "version": 1,
        "statement_summary": (
            "Three teammates independently say whether they know how to solve each proposed "
            "problem. Count the problems that at least two teammates support."
        ),
        "input_format": "The first line contains n. Each of the next n lines contains three values, each 0 or 1.",
        "output_format": "Print the number of rows containing at least two ones.",
        "constraints_text": "1 ≤ n ≤ 1000.",
        "sample_tests": [{"input": "3\n1 1 0\n1 1 1\n1 0 0\n", "output": "2\n"}],
        "judge_tests": [
            {"input": "5\n1 1 0\n1 1 1\n1 0 0\n0 1 1\n0 0 0\n", "expected_output": "3\n"},
            {"input": "1\n0 0 1\n", "expected_output": "0\n"},
        ],
    },
    {
        "pack_id": "solvex-cf-158a-v1",
        "problem_id": "158A",
        "version": 1,
        "statement_summary": (
            "Contest scores are listed in non-increasing order. Count participants whose score "
            "is positive and at least the score currently in position k."
        ),
        "input_format": "The first line contains n and k. The second line contains n scores in non-increasing order.",
        "output_format": "Print the number of participants who advance.",
        "constraints_text": "1 ≤ k ≤ n ≤ 50; every score is between 0 and 100.",
        "sample_tests": [{"input": "8 5\n10 9 8 7 7 7 5 5\n", "output": "6\n"}],
        "judge_tests": [
            {"input": "8 5\n10 9 8 7 7 7 5 5\n", "expected_output": "6\n"},
            {"input": "4 2\n0 0 0 0\n", "expected_output": "0\n"},
            {"input": "5 5\n5 4 3 2 1\n", "expected_output": "5\n"},
        ],
    },
    {
        "pack_id": "solvex-cf-50a-v1",
        "problem_id": "50A",
        "version": 1,
        "statement_summary": (
            "Find the maximum number of non-overlapping 2×1 dominoes that can be placed on an "
            "m×n rectangular board. Dominoes may be rotated."
        ),
        "input_format": "One line containing integers m and n.",
        "output_format": "Print the maximum number of dominoes.",
        "constraints_text": "1 ≤ m, n ≤ 16.",
        "sample_tests": [{"input": "2 4\n", "output": "4\n"}, {"input": "3 3\n", "output": "4\n"}],
        "judge_tests": [
            {"input": "1 1\n", "expected_output": "0\n"},
            {"input": "2 4\n", "expected_output": "4\n"},
            {"input": "3 3\n", "expected_output": "4\n"},
            {"input": "16 16\n", "expected_output": "128\n"},
        ],
    },
)
