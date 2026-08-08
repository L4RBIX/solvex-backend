"""Dual-oracle specs for SolveX practice pack batch 15 (top-up to 500+ registry)."""

from __future__ import annotations

import random

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec


def _tcases(stdin: str) -> tuple[int, list[str]]:
    ls = lines(stdin)
    t = int(ls[0])
    return t, ls[1 : 1 + t]


# ─── 1294A Collecting Coins ──────────────────────────────────────────────────

def _s_1294a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        arr = sorted([a, b, c])
        total = arr[0] + arr[1] + arr[2] + n
        if total % 3 == 0 and total // 3 >= arr[2]:
            out.append("YES")
        else:
            out.append("NO")
    return "\n".join(out) + "\n"


def _a_1294a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        hi = max(a, b, c)
        lo1 = min(a, b, c)
        mid = a + b + c - hi - lo1
        remaining = n - (2 * hi - mid - lo1)
        ok = remaining >= 0 and remaining % 3 == 0
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _m_1294a_no_ge(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        total = a + b + c + n
        out.append("YES" if total % 3 == 0 else "NO")
    return "\n".join(out) + "\n"


def _m_1294a_wrong_mod(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        arr = sorted([a, b, c])
        total = arr[0] + arr[1] + arr[2] + n
        if total % 3 == 0 and total // 3 >= arr[1]:
            out.append("YES")
        else:
            out.append("NO")
    return "\n".join(out) + "\n"


def _gen_1294a(rng: random.Random) -> list[str]:
    sample = "5\n0 2 0 0\n0 0 4 4\n1 2 3 2\n1 0 1 1\n0 0 0 100\n"
    extras = [
        "1\n1 1 1 0\n",
        "1\n0 0 0 3\n",
        "1\n2 2 2 3\n",
        "1\n5 1 1 6\n",
        "1\n0 1 2 3\n",
        "1\n10 10 10 0\n",
        "1\n1 2 3 9\n",
        "1\n0 0 1 2\n",
        "2\n0 0 0 0\n1 1 1 0\n",
        "1\n3 3 3 6\n",
    ]
    return [sample, *extras]


# ─── 1907A Rook Position ───────────────────────────────────────────────────

def _rook_board(r: int, c: int) -> str:
    rows = ["." * 8 for _ in range(8)]
    row = list(rows[r])
    row[c] = "R"
    rows[r] = "".join(row)
    return "1\n" + "\n".join(rows) + "\n"


def _s_1907a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        grid = [ls[i + r] for r in range(8)]
        i += 8
        for r in range(8):
            for c in range(8):
                if grid[r][c] == "R":
                    out.append(f"{r + 1} {c + 1}")
                    break
            else:
                continue
            break
    return "\n".join(out) + "\n"


def _a_1907a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        for r in range(8):
            row = ls[i + r]
            if "R" in row:
                out.append(f"{r + 1} {row.index('R') + 1}")
                break
        i += 8
    return "\n".join(out) + "\n"


def _gen_1907a(rng: random.Random) -> list[str]:
    sample = _rook_board(7, 3)
    extras = [_rook_board(r, c) for r, c in [(0, 0), (0, 7), (7, 0), (7, 7), (3, 4), (1, 5), (5, 1), (2, 2), (6, 6), (4, 0)]]
    return [sample, *extras]


def _build():
    specs = []

    def reg(problem_id, summary, sample_in, solve, alt, mutants, generate, **kw):
        out = solve(sample_in)
        specs.append(
            make_spec(
                problem_id,
                summary=summary,
                samples=({"input": sample_in, "output": out},),
                solve=solve,
                alt=alt,
                mutants=mutants,
                generate=generate,
                **kw,
            )
        )

    reg(
        "1294A",
        "Equal coins after n arrivals.",
        "5\n0 2 0 0\n0 0 4 4\n1 2 3 2\n1 0 1 1\n0 0 0 100\n",
        _s_1294a,
        _a_1294a,
        {"m1": _m_1294a_no_ge, "m2": _m_1294a_wrong_mod},
        _gen_1294a,
        family="math",
        checker="tokens_ci",
    )
    reg(
        "1907A",
        "Rook position on chessboard.",
        _rook_board(7, 3),
        _s_1907a,
        _a_1907a,
        {"m1": lambda s: "1 1\n", "m2": lambda s: "8 8\n"},
        _gen_1907a,
        family="implementation",
        checker="exact",
    )
    return specs


SPECS = _build()
