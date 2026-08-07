"""Trusted oracles and generators for automatic practice packs.

Oracles are implemented from problem definitions (not scraped CF hidden tests).
A pack is auto-activated only after multi-oracle agreement + mutation gates.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from contestiq_api.practice_packs.checkers import outputs_match
from contestiq_api.practice_packs.mutation import score_mutations
from contestiq_api.practice_packs.quality import DEFAULT_THRESHOLDS, evaluate_quality

OracleFn = Callable[[str], str]
MutantMap = dict[str, OracleFn]


@dataclass(frozen=True)
class ProblemOracleSpec:
    problem_id: str
    checker_type: str
    oracle_strategy: str
    statement_summary: str
    input_format: str
    output_format: str
    constraints_text: str
    sample_tests: tuple[dict[str, str], ...]
    oracles: tuple[OracleFn, ...]
    mutants: MutantMap
    generate_cases: Callable[[random.Random], list[str]]
    pack_version: int = 1


def _ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


# ─── 11A Increasing Sequence ─────────────────────────────────────────────────


def _oracle_11a_greedy(stdin: str) -> str:
    lines = stdin.strip().splitlines()
    n, d = map(int, lines[0].split())
    b = list(map(int, lines[1].split()))
    assert len(b) == n
    ans = 0
    for i in range(1, n):
        if b[i] <= b[i - 1]:
            need = b[i - 1] + 1 - b[i]
            moves = _ceil_div(need, d)
            b[i] += moves * d
            ans += moves
    return f"{ans}\n"


def _oracle_11a_math(stdin: str) -> str:
    """Independent formulation: track required strict lower bound."""
    lines = stdin.strip().splitlines()
    n, d = map(int, lines[0].split())
    b = list(map(int, lines[1].split()))
    ans = 0
    prev = b[0]
    for i in range(1, n):
        cur = b[i]
        if cur > prev:
            prev = cur
            continue
        need = prev + 1 - cur
        moves = (need + d - 1) // d
        cur += moves * d
        ans += moves
        prev = cur
    return f"{ans}\n"


def _mut_11a_strict_less(stdin: str) -> str:
    lines = stdin.strip().splitlines()
    n, d = map(int, lines[0].split())
    b = list(map(int, lines[1].split()))
    ans = 0
    for i in range(1, n):
        if b[i] < b[i - 1]:  # wrong: allows equals
            need = b[i - 1] + 1 - b[i]
            moves = _ceil_div(need, d)
            b[i] += moves * d
            ans += moves
    return f"{ans}\n"


def _mut_11a_no_update(stdin: str) -> str:
    lines = stdin.strip().splitlines()
    n, d = map(int, lines[0].split())
    b = list(map(int, lines[1].split()))
    ans = 0
    for i in range(1, n):
        if b[i] <= b[i - 1]:
            need = b[i - 1] + 1 - b[i]
            moves = _ceil_div(need, d)
            ans += moves  # forgot b[i] += moves * d
    return f"{ans}\n"


def _mut_11a_floor_div(stdin: str) -> str:
    lines = stdin.strip().splitlines()
    n, d = map(int, lines[0].split())
    b = list(map(int, lines[1].split()))
    ans = 0
    for i in range(1, n):
        if b[i] <= b[i - 1]:
            need = b[i - 1] + 1 - b[i]
            moves = need // d  # wrong floor
            if moves == 0:
                moves = 1
            b[i] += moves * d
            ans += moves
    return f"{ans}\n"


def _mut_11a_plus_one(stdin: str) -> str:
    lines = stdin.strip().splitlines()
    n, d = map(int, lines[0].split())
    b = list(map(int, lines[1].split()))
    ans = 0
    for i in range(1, n):
        if b[i] <= b[i - 1]:
            need = b[i - 1] - b[i]  # off-by-one
            moves = _ceil_div(max(need, 1), d)
            b[i] += moves * d
            ans += moves
    return f"{ans}\n"


def _gen_11a(rng: random.Random) -> list[str]:
    cases: list[str] = []
    # Official sample
    cases.append("4 2\n1 3 3 2\n")
    # Equal adjacent
    cases.append("3 5\n10 10 10\n")
    # Already increasing
    cases.append("5 1\n1 2 3 4 5\n")
    # Strictly decreasing
    cases.append("5 3\n20 15 10 5 1\n")
    # d = 1
    cases.append("4 1\n5 5 4 10\n")
    # large d
    cases.append("4 1000000\n1 1 1 1\n")
    # near constraints values
    cases.append("6 7\n1000000 999999 1 2 2 1000000\n")
    # long chain propagation
    n = 40
    b = [100 - i for i in range(n)]
    cases.append(f"{n} 2\n" + " ".join(map(str, b)) + "\n")
    # multiple increments needed
    cases.append("3 2\n1 1 1\n")
    # random medium
    for _ in range(6):
        n = rng.randint(2, 30)
        d = rng.randint(1, 50)
        vals = [rng.randint(1, 1000) for _ in range(n)]
        cases.append(f"{n} {d}\n" + " ".join(map(str, vals)) + "\n")
    return cases


SPEC_11A = ProblemOracleSpec(
    problem_id="11A",
    checker_type="exact",
    oracle_strategy="dual_independent_greedy_math",
    statement_summary=(
        "You are given a sequence and a positive integer d. In one move you may add d "
        "to any element. Find the minimum number of moves to make the sequence strictly increasing."
    ),
    input_format="First line: n and d. Second line: n integers b0..bn-1.",
    output_format="Print one integer — the minimum number of moves.",
    constraints_text="2 ≤ n ≤ 2000; 1 ≤ d ≤ 10^6; 1 ≤ bi ≤ 10^6.",
    sample_tests=({"input": "4 2\n1 3 3 2\n", "output": "3\n"},),
    oracles=(_oracle_11a_greedy, _oracle_11a_math),
    mutants={
        "strict_less": _mut_11a_strict_less,
        "no_update": _mut_11a_no_update,
        "floor_div": _mut_11a_floor_div,
        "off_by_one": _mut_11a_plus_one,
    },
    generate_cases=_gen_11a,
    pack_version=1,
)


# ─── Classic Div2-A mathematical oracles ─────────────────────────────────────


def _yes_no(flag: bool) -> str:
    return "YES\n" if flag else "NO\n"


def _spec_simple(
    problem_id: str,
    *,
    summary: str,
    input_format: str,
    output_format: str,
    constraints: str,
    samples: tuple[dict[str, str], ...],
    solve: OracleFn,
    alt: OracleFn,
    mutants: MutantMap,
    generate: Callable[[random.Random], list[str]],
    checker: str = "tokens_ci",
    strategy: str = "dual_math_oracle",
) -> ProblemOracleSpec:
    return ProblemOracleSpec(
        problem_id=problem_id,
        checker_type=checker,
        oracle_strategy=strategy,
        statement_summary=summary,
        input_format=input_format,
        output_format=output_format,
        constraints_text=constraints,
        sample_tests=samples,
        oracles=(solve, alt),
        mutants=mutants,
        generate_cases=generate,
        pack_version=1,
    )


def _classic_specs() -> list[ProblemOracleSpec]:
    specs: list[ProblemOracleSpec] = [SPEC_11A]

    # 1A Theatre Square
    def s1a(stdin: str) -> str:
        n, m, a = map(int, stdin.split())
        return f"{math.ceil(n / a) * math.ceil(m / a)}\n"

    def s1a_alt(stdin: str) -> str:
        n, m, a = map(int, stdin.split())
        return f"{((n + a - 1) // a) * ((m + a - 1) // a)}\n"

    def m1a(stdin: str) -> str:
        n, m, a = map(int, stdin.split())
        return f"{(n // a) * (m // a)}\n"

    specs.append(
        _spec_simple(
            "1A",
            summary="Cover an n×m rectangle with a×a flagstones; count how many are needed.",
            input_format="Three integers n, m, a.",
            output_format="Print one integer.",
            constraints="1 ≤ n,m,a ≤ 10^9.",
            samples=({"input": "6 6 4\n", "output": "4\n"},),
            solve=s1a,
            alt=s1a_alt,
            mutants={"floor": m1a},
            generate=lambda rng: [
                "6 6 4\n",
                "1 1 1\n",
                "1000000000 1000000000 1\n",
            ]
            + [
                f"{rng.randint(1,10**6)} {rng.randint(1,10**6)} {rng.randint(1,10**5)}\n"
                for _ in range(8)
            ],
            checker="exact",
        )
    )

    # 4A Watermelon
    def s4a(stdin: str) -> str:
        w = int(stdin.strip())
        return _yes_no(w >= 4 and w % 2 == 0)

    def s4a_alt(stdin: str) -> str:
        w = int(stdin.strip())
        return _yes_no(w > 2 and w % 2 == 0)

    def m4a(stdin: str) -> str:
        w = int(stdin.strip())
        return _yes_no(w % 2 == 0)

    specs.append(
        _spec_simple(
            "4A",
            summary="Can weight w be split into two positive even parts?",
            input_format="One integer w.",
            output_format='Print "YES" or "NO".',
            constraints="1 ≤ w ≤ 100.",
            samples=({"input": "8\n", "output": "YES\n"}, {"input": "2\n", "output": "NO\n"}),
            solve=s4a,
            alt=s4a_alt,
            mutants={"allow_two": m4a},
            generate=lambda rng: [f"{w}\n" for w in list(range(1, 21)) + [99, 100]],
            checker="tokens_ci",
        )
    )

    # 71A Way Too Long Words
    def s71a(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        out = []
        for w in lines[1 : 1 + n]:
            out.append(w if len(w) <= 10 else f"{w[0]}{len(w) - 2}{w[-1]}")
        return "\n".join(out) + "\n"

    def s71a_alt(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        out = []
        for w in lines[1 : 1 + n]:
            if len(w) > 10:
                out.append(w[0] + str(len(w) - 2) + w[-1])
            else:
                out.append(w)
        return "\n".join(out) + "\n"

    def m71a(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        out = []
        for w in lines[1 : 1 + n]:
            out.append(w if len(w) < 10 else f"{w[0]}{len(w) - 2}{w[-1]}")
        return "\n".join(out) + "\n"

    specs.append(
        _spec_simple(
            "71A",
            summary="Abbreviate words longer than 10 characters.",
            input_format="n then n lowercase words.",
            output_format="Print each transformed word.",
            constraints="1 ≤ n ≤ 100; word length 1..100.",
            samples=(
                {
                    "input": "4\nword\nlocalization\ninternationalization\npneumonoultramicroscopicsilicovolcanoconiosis\n",
                    "output": "word\nl10n\ni18n\np43s\n",
                },
            ),
            solve=s71a,
            alt=s71a_alt,
            mutants={"lt10": m71a},
            generate=lambda rng: [
                "4\nword\nlocalization\ninternationalization\npneumonoultramicroscopicsilicovolcanoconiosis\n",
                "3\na\nab\nabcdefghijklm\n",
                "2\nabcdefghij\nabcdefghijk\n",
            ]
            + [
                f"3\n{''.join(rng.choice('abc') for _ in range(rng.randint(1,20)))}\n"
                f"{''.join(rng.choice('xyz') for _ in range(rng.randint(8,15)))}\n"
                f"{''.join(rng.choice('q') for _ in range(rng.randint(1,12)))}\n"
                for _ in range(5)
            ],
            checker="exact",
        )
    )

    # Helper to add many formula problems
    def add_int_formula(
        pid: str,
        summary: str,
        sample_in: str,
        sample_out: str,
        solve: OracleFn,
        alt: OracleFn,
        mutant: OracleFn,
        gen: Callable[[random.Random], list[str]],
        inp: str = "See constraints.",
        out: str = "Print the answer.",
        cons: str = "Within Codeforces statement constraints.",
        checker: str = "exact",
    ) -> None:
        specs.append(
            _spec_simple(
                pid,
                summary=summary,
                input_format=inp,
                output_format=out,
                constraints=cons,
                samples=({"input": sample_in, "output": sample_out},),
                solve=solve,
                alt=alt,
                mutants={"mut": mutant},
                generate=gen,
                checker=checker,
            )
        )

    # 50A Domino piling
    add_int_formula(
        "50A",
        "Max 2×1 dominoes on m×n board.",
        "2 4\n",
        "4\n",
        lambda s: f"{(lambda m, n: (m * n) // 2)(*map(int, s.split()))}\n",
        lambda s: f"{(lambda m, n: (m * n) >> 1)(*map(int, s.split()))}\n",
        lambda s: f"{(lambda m, n: (m * n + 1) // 2)(*map(int, s.split()))}\n",
        lambda rng: ["1 1\n", "2 4\n", "3 3\n", "16 16\n"]
        + [f"{rng.randint(1,16)} {rng.randint(1,16)}\n" for _ in range(6)],
        inp="m n",
        out="Print max dominoes.",
        cons="1 ≤ m,n ≤ 16.",
    )

    # 231A Team
    def s231(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        return f"{sum(1 for i in range(1, n + 1) if sum(map(int, lines[i].split())) >= 2)}\n"

    def s231b(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        c = 0
        for i in range(1, n + 1):
            a, b, d = map(int, lines[i].split())
            c += a + b + d >= 2
        return f"{c}\n"

    def m231(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        return f"{sum(1 for i in range(1, n + 1) if sum(map(int, lines[i].split())) >= 1)}\n"

    specs.append(
        _spec_simple(
            "231A",
            summary="Count problems with at least two confident teammates.",
            input_format="n then n lines of three 0/1 values.",
            output_format="Print the count.",
            constraints="1 ≤ n ≤ 1000.",
            samples=({"input": "3\n1 1 0\n1 1 1\n1 0 0\n", "output": "2\n"},),
            solve=s231,
            alt=s231b,
            mutants={"ge1": m231},
            generate=lambda rng: [
                "3\n1 1 0\n1 1 1\n1 0 0\n",
                "1\n0 0 1\n",
                "5\n1 1 0\n1 1 1\n1 0 0\n0 1 1\n0 0 0\n",
            ]
            + [
                str(n)
                + "\n"
                + "\n".join(
                    " ".join(str(rng.randint(0, 1)) for _ in range(3)) for _ in range(n)
                )
                + "\n"
                for n in [rng.randint(1, 8) for _ in range(5)]
            ],
            checker="exact",
        )
    )

    # 158A Next Round
    def s158(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n, k = map(int, lines[0].split())
        a = list(map(int, lines[1].split()))
        threshold = a[k - 1]
        return f"{sum(1 for x in a if x >= threshold and x > 0)}\n"

    def s158b(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n, k = map(int, lines[0].split())
        a = list(map(int, lines[1].split()))
        t = a[k - 1]
        c = 0
        for x in a:
            if x > 0 and x >= t:
                c += 1
        return f"{c}\n"

    def m158(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n, k = map(int, lines[0].split())
        a = list(map(int, lines[1].split()))
        return f"{sum(1 for x in a if x >= a[k - 1])}\n"

    specs.append(
        _spec_simple(
            "158A",
            summary="Count participants advancing past place k with positive score.",
            input_format="n k then n non-increasing scores.",
            output_format="Print the count.",
            constraints="1 ≤ k ≤ n ≤ 50; scores 0..100.",
            samples=({"input": "8 5\n10 9 8 7 7 7 5 5\n", "output": "6\n"},),
            solve=s158,
            alt=s158b,
            mutants={"allow_zero": m158},
            generate=lambda rng: [
                "8 5\n10 9 8 7 7 7 5 5\n",
                "4 2\n0 0 0 0\n",
                "5 5\n5 4 3 2 1\n",
                "1 1\n0\n",
            ]
            + [
                (
                    lambda n, k: f"{n} {k}\n"
                    + " ".join(
                        str(x)
                        for x in sorted(
                            (rng.randint(0, 100) for _ in range(n)), reverse=True
                        )
                    )
                    + "\n"
                )(rng.randint(1, 20), 1)
                for _ in range(6)
            ],
            checker="exact",
        )
    )

    # 282A Bit++
    def s282(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        x = 0
        for stmt in lines[1 : 1 + n]:
            x += 1 if "+" in stmt else -1
        return f"{x}\n"

    def s282b(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        return f"{sum(1 if '+' in s else -1 for s in lines[1:1+n])}\n"

    def m282(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        return f"{sum(1 for s in lines[1:1+n] if '+' in s)}\n"

    specs.append(
        _spec_simple(
            "282A",
            summary="Simulate Bit++ statements starting from x=0.",
            input_format="n then n statements.",
            output_format="Print final x.",
            constraints="1 ≤ n ≤ 150.",
            samples=({"input": "1\n++X\n", "output": "1\n"},),
            solve=s282,
            alt=s282b,
            mutants={"only_plus": m282},
            generate=lambda rng: [
                "1\n++X\n",
                "2\nX++\n--X\n",
            ]
            + [
                str(n)
                + "\n"
                + "\n".join(rng.choice(["++X", "X++", "--X", "X--"]) for _ in range(n))
                + "\n"
                for n in [rng.randint(1, 20) for _ in range(8)]
            ],
            checker="exact",
        )
    )

    # 112A Petya and Strings
    def s112(stdin: str) -> str:
        a, b = stdin.strip().splitlines()[:2]
        a, b = a.casefold(), b.casefold()
        return f"{(a > b) - (a < b)}\n"

    def s112b(stdin: str) -> str:
        a, b = stdin.strip().splitlines()[:2]
        x = a.lower()
        y = b.lower()
        if x < y:
            return "-1\n"
        if x > y:
            return "1\n"
        return "0\n"

    def m112(stdin: str) -> str:
        a, b = stdin.strip().splitlines()[:2]
        return f"{(a > b) - (a < b)}\n"

    specs.append(
        _spec_simple(
            "112A",
            summary="Case-insensitive lexicographic compare of two equal-length strings.",
            input_format="Two lines with equal-length strings.",
            output_format="Print -1, 0, or 1.",
            constraints="Length 1..100.",
            samples=({"input": "aaaa\naaaA\n", "output": "0\n"},),
            solve=s112,
            alt=s112b,
            mutants={"case_sensitive": m112},
            generate=lambda rng: [
                "aaaa\naaaA\n",
                "abs\nAbz\n",
                "abcdefg\nAbCdEfF\n",
            ]
            + [
                (
                    lambda L: (
                        "".join(rng.choice("abcXYZ") for _ in range(L))
                        + "\n"
                        + "".join(rng.choice("abcXYZ") for _ in range(L))
                        + "\n"
                    )
                )(rng.randint(1, 12))
                for _ in range(7)
            ],
            checker="exact",
        )
    )

    # 263A Beautiful Matrix
    def s263(stdin: str) -> str:
        grid = [list(map(int, line.split())) for line in stdin.strip().splitlines()]
        for i in range(5):
            for j in range(5):
                if grid[i][j] == 1:
                    return f"{abs(i - 2) + abs(j - 2)}\n"
        return "0\n"

    def s263b(stdin: str) -> str:
        rows = stdin.strip().splitlines()
        for i, row in enumerate(rows):
            if "1" in row.split():
                j = row.split().index("1")
                return f"{abs(i - 2) + abs(j - 2)}\n"
        return "0\n"

    def m263(stdin: str) -> str:
        grid = [list(map(int, line.split())) for line in stdin.strip().splitlines()]
        for i in range(5):
            for j in range(5):
                if grid[i][j] == 1:
                    return f"{abs(i - 2) * abs(j - 2)}\n"
        return "0\n"

    def gen263(rng: random.Random) -> list[str]:
        cases = []
        for r, c in [(2, 2), (0, 0), (4, 4), (1, 3), (3, 1)]:
            g = [["0"] * 5 for _ in range(5)]
            g[r][c] = "1"
            cases.append("\n".join(" ".join(row) for row in g) + "\n")
        for _ in range(5):
            g = [["0"] * 5 for _ in range(5)]
            g[rng.randint(0, 4)][rng.randint(0, 4)] = "1"
            cases.append("\n".join(" ".join(row) for row in g) + "\n")
        return cases

    specs.append(
        _spec_simple(
            "263A",
            summary="Moves to bring the single 1 to the center of a 5×5 matrix.",
            input_format="5 lines of 5 integers.",
            output_format="Print Manhattan moves.",
            constraints="Exactly one 1.",
            samples=(
                {
                    "input": "0 0 0 0 0\n0 0 0 0 1\n0 0 0 0 0\n0 0 0 0 0\n0 0 0 0 0\n",
                    "output": "3\n",
                },
            ),
            solve=s263,
            alt=s263b,
            mutants={"product": m263},
            generate=gen263,
            checker="exact",
        )
    )

    # 339A Helpful Maths
    def s339(stdin: str) -> str:
        parts = stdin.strip().split("+")
        return "+".join(sorted(parts)) + "\n"

    def s339b(stdin: str) -> str:
        nums = [int(x) for x in stdin.strip().split("+")]
        nums.sort()
        return "+".join(map(str, nums)) + "\n"

    def m339(stdin: str) -> str:
        return stdin.strip() + "\n"

    specs.append(
        _spec_simple(
            "339A",
            summary="Sort summands in a sum of 1,2,3.",
            input_format="One string like 3+2+1.",
            output_format="Print sorted sum.",
            constraints="Length ≥1.",
            samples=({"input": "3+2+1\n", "output": "1+2+3\n"},),
            solve=s339,
            alt=s339b,
            mutants={"identity": m339},
            generate=lambda rng: [
                "3+2+1\n",
                "1+1+3+1+3\n",
                "2\n",
            ]
            + [
                "+".join(str(rng.randint(1, 3)) for _ in range(rng.randint(1, 10))) + "\n"
                for _ in range(7)
            ],
            checker="exact",
        )
    )

    # 281A Word Capitalization
    def s281(stdin: str) -> str:
        w = stdin.strip()
        return (w[:1].upper() + w[1:]) + "\n"

    def s281b(stdin: str) -> str:
        w = stdin.strip()
        if not w:
            return "\n"
        return w[0].upper() + w[1:] + "\n"

    def m281(stdin: str) -> str:
        return stdin.strip().upper() + "\n"

    specs.append(
        _spec_simple(
            "281A",
            summary="Capitalize the first character of a word.",
            input_format="One word.",
            output_format="Print the capitalized word.",
            constraints="Non-empty.",
            samples=({"input": "cAPS\n", "output": "CAPS\n"},),
            solve=s281,
            alt=s281b,
            mutants={"all_upper": m281},
            generate=lambda rng: [
                "cAPS\n",
                "a\n",
                "Codeforces\n",
            ]
            + [
                "".join(rng.choice("aAbBcC") for _ in range(rng.randint(1, 12))) + "\n"
                for _ in range(7)
            ],
            checker="exact",
        )
    )

    # 266A Stones on the Table
    def s266(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        s = lines[1]
        return f"{sum(1 for i in range(1, len(s)) if s[i] == s[i - 1])}\n"

    def s266b(stdin: str) -> str:
        s = stdin.strip().splitlines()[1]
        c = 0
        for i in range(len(s) - 1):
            if s[i] == s[i + 1]:
                c += 1
        return f"{c}\n"

    def m266(stdin: str) -> str:
        s = stdin.strip().splitlines()[1]
        return f"{len(s) - len(set(s))}\n"

    specs.append(
        _spec_simple(
            "266A",
            summary="Count adjacent same-color stones to remove.",
            input_format="n then a string of R/G/B.",
            output_format="Print removals.",
            constraints="1 ≤ n ≤ 50.",
            samples=({"input": "3\nRRG\n", "output": "1\n"},),
            solve=s266,
            alt=s266b,
            mutants={"setdiff": m266},
            generate=lambda rng: [
                "3\nRRG\n",
                "5\nRRRRR\n",
                "1\nB\n",
            ]
            + [
                f"{n}\n" + "".join(rng.choice("RGB") for _ in range(n)) + "\n"
                for n in [rng.randint(1, 20) for _ in range(7)]
            ],
            checker="exact",
        )
    )

    # 236A Boy or Girl
    def s236(stdin: str) -> str:
        s = stdin.strip()
        return "CHAT WITH HER!\n" if len(set(s)) % 2 == 0 else "IGNORE HIM!\n"

    def s236b(stdin: str) -> str:
        n = len(set(stdin.strip()))
        return ("CHAT WITH HER!\n" if n % 2 == 0 else "IGNORE HIM!\n")

    def m236(stdin: str) -> str:
        s = stdin.strip()
        return "CHAT WITH HER!\n" if len(set(s)) % 2 else "IGNORE HIM!\n"

    specs.append(
        _spec_simple(
            "236A",
            summary="Boy/girl by parity of distinct letters.",
            input_format="One username string.",
            output_format="Print the decision line.",
            constraints="Lowercase letters.",
            samples=({"input": "wjmzbmr\n", "output": "CHAT WITH HER!\n"},),
            solve=s236,
            alt=s236b,
            mutants={"inverted": m236},
            generate=lambda rng: [
                "wjmzbmr\n",
                "xiaodao\n",
                "sevenkplus\n",
            ]
            + [
                "".join(rng.choice("abcde") for _ in range(rng.randint(1, 15))) + "\n"
                for _ in range(7)
            ],
            checker="exact",
        )
    )

    # 617A Elephant
    def s617(stdin: str) -> str:
        x = int(stdin.strip())
        return f"{(x + 4) // 5}\n"

    def s617b(stdin: str) -> str:
        x = int(stdin.strip())
        return f"{math.ceil(x / 5)}\n"

    def m617(stdin: str) -> str:
        x = int(stdin.strip())
        return f"{x // 5}\n"

    specs.append(
        _spec_simple(
            "617A",
            summary="Min steps of size 1..5 to reach x.",
            input_format="One integer x.",
            output_format="Print steps.",
            constraints="1 ≤ x ≤ 10^6.",
            samples=({"input": "5\n", "output": "1\n"},),
            solve=s617,
            alt=s617b,
            mutants={"floor": m617},
            generate=lambda rng: [f"{x}\n" for x in [1, 5, 12, 999999] + [rng.randint(1, 10**6) for _ in range(6)]],
            checker="exact",
        )
    )

    # 546A Soldier and Bananas
    def s546(stdin: str) -> str:
        k, n, w = map(int, stdin.split())
        cost = k * w * (w + 1) // 2
        return f"{max(0, cost - n)}\n"

    def s546b(stdin: str) -> str:
        k, n, w = map(int, stdin.split())
        need = sum(k * i for i in range(1, w + 1))
        return f"{0 if need <= n else need - n}\n"

    def m546(stdin: str) -> str:
        k, n, w = map(int, stdin.split())
        return f"{k * w * (w + 1) // 2 - n}\n"

    specs.append(
        _spec_simple(
            "546A",
            summary="Borrow amount for banana costs k,2k,...,w k.",
            input_format="k n w",
            output_format="Print borrow amount.",
            constraints="Positive integers.",
            samples=({"input": "3 17 4\n", "output": "13\n"},),
            solve=s546,
            alt=s546b,
            mutants={"neg_ok": m546},
            generate=lambda rng: [
                "3 17 4\n",
                "1 100 1\n",
            ]
            + [
                f"{rng.randint(1,100)} {rng.randint(0,1000)} {rng.randint(1,50)}\n"
                for _ in range(8)
            ],
            checker="exact",
        )
    )

    # 791A Bear and Big Brother
    def s791(stdin: str) -> str:
        a, b = map(int, stdin.split())
        years = 0
        while a <= b:
            a *= 3
            b *= 2
            years += 1
        return f"{years}\n"

    def s791b(stdin: str) -> str:
        a, b = map(int, stdin.split())
        y = 0
        while True:
            if a > b:
                return f"{y}\n"
            a *= 3
            b *= 2
            y += 1

    def m791(stdin: str) -> str:
        a, b = map(int, stdin.split())
        years = 0
        while a < b:
            a *= 3
            b *= 2
            years += 1
        return f"{years}\n"

    specs.append(
        _spec_simple(
            "791A",
            summary="Years until Limak outweighs Bob (×3 vs ×2).",
            input_format="a b",
            output_format="Print years.",
            constraints="1 ≤ a ≤ b ≤ 10.",
            samples=({"input": "4 7\n", "output": "2\n"},),
            solve=s791,
            alt=s791b,
            mutants={"strict": m791},
            generate=lambda rng: [
                "4 7\n",
                "4 9\n",
                "1 1\n",
            ]
            + [f"{rng.randint(1,10)} {rng.randint(1,10)}\n" for _ in range(7)],
            checker="exact",
        )
    )

    # 977A Wrong Subtraction
    def s977(stdin: str) -> str:
        n, k = map(int, stdin.split())
        for _ in range(k):
            n = n // 10 if n % 10 == 0 else n - 1
        return f"{n}\n"

    def s977b(stdin: str) -> str:
        n, k = map(int, stdin.split())
        for _ in range(k):
            if n % 10:
                n -= 1
            else:
                n //= 10
        return f"{n}\n"

    def m977(stdin: str) -> str:
        n, k = map(int, stdin.split())
        return f"{n - k}\n"

    specs.append(
        _spec_simple(
            "977A",
            summary="Subtract 1 or divide by 10 when last digit is 0, k times.",
            input_format="n k",
            output_format="Print result.",
            constraints="2 ≤ n ≤ 10^9; 1 ≤ k ≤ 50.",
            samples=({"input": "512 4\n", "output": "50\n"},),
            solve=s977,
            alt=s977b,
            mutants={"minus_k": m977},
            generate=lambda rng: [
                "512 4\n",
                "1000000000 9\n",
            ]
            + [
                f"{rng.randint(2, 10**6)} {rng.randint(1, 20)}\n" for _ in range(8)
            ],
            checker="exact",
        )
    )

    # 116A Tram
    def s116(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        cur = best = 0
        for i in range(1, n + 1):
            a, b = map(int, lines[i].split())
            cur = cur - a + b
            best = max(best, cur)
        return f"{best}\n"

    def s116b(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        cur = 0
        caps = []
        for i in range(1, n + 1):
            a, b = map(int, lines[i].split())
            cur += b - a
            caps.append(cur)
        return f"{max(caps)}\n"

    def m116(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        n = int(lines[0])
        return f"{sum(int(lines[i].split()[1]) for i in range(1, n + 1))}\n"

    def gen116(rng: random.Random) -> list[str]:
        cases = ["4\n0 3\n2 5\n4 2\n4 0\n"]
        for _ in range(8):
            n = rng.randint(1, 10)
            cur = 0
            lines = [str(n)]
            for i in range(n):
                a = rng.randint(0, cur)
                b = rng.randint(0, 10)
                cur = cur - a + b
                lines.append(f"{a} {b}")
            cases.append("\n".join(lines) + "\n")
        return cases

    specs.append(
        _spec_simple(
            "116A",
            summary="Minimum tram capacity over the route.",
            input_format="n then n lines a_i b_i.",
            output_format="Print capacity.",
            constraints="1 ≤ n ≤ 1000.",
            samples=({"input": "4\n0 3\n2 5\n4 2\n4 0\n", "output": "6\n"},),
            solve=s116,
            alt=s116b,
            mutants={"sum_enter": m116},
            generate=gen116,
            checker="exact",
        )
    )

    # 1328A Divisibility Problem
    def s1328(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            a, b = map(int, lines[i].split())
            out.append(str((b - a % b) % b))
        return "\n".join(out) + "\n"

    def s1328b(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            a, b = map(int, lines[i].split())
            r = a % b
            out.append("0" if r == 0 else str(b - r))
        return "\n".join(out) + "\n"

    def m1328(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            a, b = map(int, lines[i].split())
            out.append(str(b - a % b))
        return "\n".join(out) + "\n"

    specs.append(
        _spec_simple(
            "1328A",
            summary="Min moves to make a divisible by b (+1 each).",
            input_format="t then t lines a b.",
            output_format="Print t answers.",
            constraints="1 ≤ t ≤ 10^4.",
            samples=({"input": "5\n10 4\n13 9\n100 13\n123 456\n92 46\n", "output": "2\n5\n4\n333\n0\n"},),
            solve=s1328,
            alt=s1328b,
            mutants={"no_mod0": m1328},
            generate=lambda rng: [
                "5\n10 4\n13 9\n100 13\n123 456\n92 46\n",
            ]
            + [
                "3\n"
                + "\n".join(
                    f"{rng.randint(1,1000)} {rng.randint(1,1000)}" for _ in range(3)
                )
                + "\n"
                for _ in range(8)
            ],
            checker="exact",
        )
    )

    # 1335A Candies and Two Sisters
    def s1335(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            n = int(lines[i])
            out.append(str((n - 1) // 2))
        return "\n".join(out) + "\n"

    def s1335b(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            n = int(lines[i])
            out.append(str(n // 2 - (0 if n % 2 else 1) if n > 1 else 0))
        return "\n".join(out) + "\n"

    # Fix alt to be clearly correct:
    def s1335b_fixed(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            n = int(lines[i])
            out.append(str(max(0, (n - 1) // 2)))
        return "\n".join(out) + "\n"

    def m1335(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out = []
        for i in range(1, t + 1):
            n = int(lines[i])
            out.append(str(n // 2))
        return "\n".join(out) + "\n"

    specs.append(
        _spec_simple(
            "1335A",
            summary="Ways to split n candies with a>b and a+b=n.",
            input_format="t then t integers n.",
            output_format="Print t answers.",
            constraints="1 ≤ t ≤ 10^4; 1 ≤ n ≤ 10^9.",
            samples=({"input": "6\n7\n1\n2\n3\n2000000000\n76324123\n", "output": "3\n0\n0\n1\n999999999\n38162061\n"},),
            solve=s1335,
            alt=s1335b_fixed,
            mutants={"n_div2": m1335},
            generate=lambda rng: [
                "6\n7\n1\n2\n3\n2000000000\n76324123\n",
            ]
            + [
                "4\n"
                + "\n".join(str(rng.randint(1, 10**6)) for _ in range(4))
                + "\n"
                for _ in range(8)
            ],
            checker="exact",
        )
    )

    # 1352A Sum of Round Numbers
    def s1352(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        chunks = []
        for i in range(1, t + 1):
            n = lines[i].strip()
            parts = []
            for idx, ch in enumerate(reversed(n)):
                if ch != "0":
                    parts.append(ch + ("0" * idx))
            chunks.append(str(len(parts)))
            chunks.append(" ".join(reversed(parts)))
        return "\n".join(chunks) + "\n"

    def s1352b(stdin: str) -> str:
        # Same logic, different loop direction
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        out_lines = []
        for i in range(1, t + 1):
            n = int(lines[i])
            parts = []
            place = 1
            while n:
                dig = n % 10
                if dig:
                    parts.append(str(dig * place))
                n //= 10
                place *= 10
            parts.reverse()
            out_lines.append(str(len(parts)))
            out_lines.append(" ".join(parts))
        return "\n".join(out_lines) + "\n"

    def m1352(stdin: str) -> str:
        lines = stdin.strip().splitlines()
        t = int(lines[0])
        chunks = []
        for i in range(1, t + 1):
            chunks.append("1")
            chunks.append(lines[i].strip())
        return "\n".join(chunks) + "\n"

    specs.append(
        _spec_simple(
            "1352A",
            summary="Decompose n into round numbers.",
            input_format="t then t integers.",
            output_format="For each: count then the parts.",
            constraints="1 ≤ t ≤ 1000.",
            samples=({"input": "5\n5009\n7\n10000\n25\n100000\n", "output": "2\n5000 9\n1\n7\n1\n10000\n2\n20 5\n1\n100000\n"},),
            solve=s1352,
            alt=s1352b,
            mutants={"raw": m1352},
            generate=lambda rng: [
                "5\n5009\n7\n10000\n25\n100000\n",
            ]
            + [
                "3\n"
                + "\n".join(str(rng.randint(1, 100000)) for _ in range(3))
                + "\n"
                for _ in range(8)
            ],
            checker="tokens",
        )
    )

    # 486A Calculating Function
    def s486(stdin: str) -> str:
        n = int(stdin.strip())
        return f"{n // 2 if n % 2 == 0 else -(n + 1) // 2}\n"

    def s486b(stdin: str) -> str:
        n = int(stdin.strip())
        if n % 2 == 0:
            return f"{n // 2}\n"
        return f"{-(n // 2 + 1)}\n"

    def m486(stdin: str) -> str:
        n = int(stdin.strip())
        return f"{n // 2}\n"

    specs.append(
        _spec_simple(
            "486A",
            summary="f(n)= -1+2-3+...+(-1)^n n.",
            input_format="n",
            output_format="Print f(n).",
            constraints="1 ≤ n ≤ 10^15.",
            samples=({"input": "4\n", "output": "2\n"},),
            solve=s486,
            alt=s486b,
            mutants={"half": m486},
            generate=lambda rng: [f"{x}\n" for x in [1, 2, 3, 4, 5, 10**15, 10**15 - 1] + [rng.randint(1, 10**9) for _ in range(5)]],
            checker="exact",
        )
    )

    # 750A New Year and Hurry
    def s750(stdin: str) -> str:
        n, k = map(int, stdin.split())
        remain = 240 - k
        solved = 0
        for i in range(1, n + 1):
            if remain < 5 * i:
                break
            remain -= 5 * i
            solved += 1
        return f"{solved}\n"

    def s750b(stdin: str) -> str:
        n, k = map(int, stdin.split())
        t = 240 - k
        c = 0
        need = 0
        for i in range(1, n + 1):
            need += 5 * i
            if need > t:
                break
            c += 1
        return f"{c}\n"

    def m750(stdin: str) -> str:
        n, k = map(int, stdin.split())
        return f"{min(n, (240 - k) // 5)}\n"

    specs.append(
        _spec_simple(
            "750A",
            summary="Max problems solvable before party with 5i minutes each.",
            input_format="n k",
            output_format="Print count.",
            constraints="1 ≤ n ≤ 10; 1 ≤ k ≤ 240.",
            samples=({"input": "3 222\n", "output": "2\n"},),
            solve=s750,
            alt=s750b,
            mutants={"flat5": m750},
            generate=lambda rng: [
                "3 222\n",
                "4 190\n",
                "7 1\n",
            ]
            + [f"{rng.randint(1,10)} {rng.randint(1,240)}\n" for _ in range(7)],
            checker="exact",
        )
    )

    return specs


ORACLE_REGISTRY: dict[str, ProblemOracleSpec] = {
    spec.problem_id: spec for spec in _classic_specs()
}


def build_candidate_pack(
    problem_id: str,
    *,
    rng_seed: int = 11,
) -> dict[str, Any]:
    spec = ORACLE_REGISTRY[problem_id]
    rng = random.Random(rng_seed)
    raw_inputs = spec.generate_cases(rng)
    # Deduplicate while preserving order
    seen: set[str] = set()
    inputs: list[str] = []
    for item in raw_inputs:
        if item not in seen:
            seen.add(item)
            inputs.append(item)

    primary, secondary = spec.oracles[0], spec.oracles[1]
    tests: list[dict[str, str]] = []
    disagreements = 0
    for stdin in inputs:
        out_a = primary(stdin)
        out_b = secondary(stdin)
        if not outputs_match(out_a, out_b, checker_type=spec.checker_type):
            disagreements += 1
            continue
        tests.append({"input": stdin, "expected_output": out_a})

    if disagreements:
        raise ValueError(
            f"{problem_id}: oracles disagree on {disagreements} generated case(s)"
        )
    if len(tests) < 2:
        raise ValueError(f"{problem_id}: insufficient agreed tests")

    checker = lambda a, e: outputs_match(a, e, checker_type=spec.checker_type)
    mutation = score_mutations(
        tests,
        correct=primary,
        mutants=spec.mutants,
        checker=checker,
    )
    has_sample = any(
        outputs_match(t["input"], s["input"], checker_type="exact")
        or t["input"].strip() == s["input"].strip()
        for t in tests
        for s in spec.sample_tests
    )
    # Prefer embedding official samples explicitly
    for sample in spec.sample_tests:
        sample_in = sample["input"]
        expected = primary(sample_in)
        if not any(t["input"] == sample_in for t in tests):
            tests.insert(0, {"input": sample_in, "expected_output": expected})
        has_sample = True

    quality = evaluate_quality(
        test_count=len(tests),
        mutation_score=mutation.mutation_score,
        oracle_count=len(spec.oracles),
        oracles_agree=disagreements == 0,
        has_sample=has_sample,
        thresholds=DEFAULT_THRESHOLDS,
    )
    quality["mutation"] = mutation.as_dict()

    return {
        "pack_id": f"solvex-auto-{problem_id.lower()}-v{spec.pack_version}",
        "problem_id": problem_id,
        "version": spec.pack_version,
        "statement_summary": spec.statement_summary,
        "input_format": spec.input_format,
        "output_format": spec.output_format,
        "constraints_text": spec.constraints_text,
        "sample_tests": [dict(s) for s in spec.sample_tests],
        "judge_tests": tests,
        "review_state": "reviewed" if quality["passed"] else "validation_failed",
        "checker_type": spec.checker_type,
        "oracle_strategy": spec.oracle_strategy,
        "provenance": {
            "source": "solvex_auto_oracle_registry",
            "oracle_strategy": spec.oracle_strategy,
            "rng_seed": rng_seed,
            "not_official_cf_tests": True,
        },
        "quality_report": quality,
        "mutation_score": mutation.mutation_score,
        "test_count": len(tests),
    }


def list_oracle_problem_ids() -> list[str]:
    return sorted(ORACLE_REGISTRY)
