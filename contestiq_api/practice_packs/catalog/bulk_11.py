"""Dual-oracle ProblemOracleSpec entries for SolveX practice pack batch 11.

Source: missing_chunk_2.json (70 candidates).
Skipped denylist (not in chunk): 1367B,1374A,1374C,1433A,1520D,1619A,1722A,313A,474B,490A,749A,80A
Skipped multi-answer / non-unique outputs:
  - 2218A (any y maximizing min(x,y) -- infinitely many valid outputs)
  - 1907A (rook targets -- valid line order is judge-defined / any order)
  - 1968A (any y maximizing gcd(x,y)+y -- multiple valid outputs)
"""

from __future__ import annotations

import math
import random
from functools import reduce

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

MOD = 10**9 + 7


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    r = 1
    for i in range(k):
        r = r * (n - i) // (i + 1)
    return r

# ─── 1692C Where's the Bishop? ────────────────────────────────────────────────


def _s_1692c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        grid = [ls[idx + k] for k in range(8)]
        idx += 8
        for i in range(1, 7):
            for j in range(1, 7):
                if (
                    grid[i][j] == "#"
                    and grid[i - 1][j - 1] == "#"
                    and grid[i - 1][j + 1] == "#"
                    and grid[i + 1][j - 1] == "#"
                    and grid[i + 1][j + 1] == "#"
                ):
                    out.append(f"{i + 1} {j + 1}")
    return "\n".join(out) + "\n"


def _a_1692c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        grid = [ls[idx + k] for k in range(8)]
        idx += 8
        found = None
        for i in range(8):
            for j in range(8):
                if grid[i][j] != "#":
                    continue
                diag_ok = True
                for di, dj in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                    ni, nj = i + di, j + dj
                    if not (0 <= ni < 8 and 0 <= nj < 8) or grid[ni][nj] != "#":
                        diag_ok = False
                        break
                if diag_ok:
                    found = (i + 1, j + 1)
        out.append(f"{found[0]} {found[1]}")
    return "\n".join(out) + "\n"


def _m1_1692c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        grid = [ls[idx + k] for k in range(8)]
        idx += 8
        for i in range(1, 7):
            for j in range(1, 7):
                if grid[i][j] == "#" and grid[i - 1][j - 1] == "#" and grid[i + 1][j + 1] == "#":
                    out.append(f"{i + 1} {j + 1}")
                    break
            else:
                continue
            break
    return "\n".join(out) + "\n"


def _m2_1692c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        grid = [ls[idx + k] for k in range(8)]
        idx += 8
        for i in range(1, 7):
            for j in range(1, 7):
                if (
                    grid[i][j] == "#"
                    and grid[i - 1][j - 1] == "#"
                    and grid[i - 1][j + 1] == "#"
                    and grid[i + 1][j - 1] == "#"
                    and grid[i + 1][j + 1] == "#"
                ):
                    out.append(f"{i} {j}")
    return "\n".join(out) + "\n"


def _make_bishop_grid(i: int, j: int) -> str:
    grid = [["." for _ in range(8)] for _ in range(8)]
    grid[i][j] = "#"
    for di, dj in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        grid[i + di][j + dj] = "#"
    return "\n".join("".join(row) for row in grid) + "\n"


def _gen_1692c(rng: random.Random) -> list[str]:
    distractor = "........\n.#......\n..#.....\n...#....\n....#.#.\n.....#..\n....#.#.\n........\n"
    cases = ["1\n" + _make_bishop_grid(3, 4), "1\n" + distractor]
    for _ in range(12):
        i = rng.randint(1, 6)
        j = rng.randint(1, 6)
        cases.append("1\n" + _make_bishop_grid(i, j))
    return cases


# ─── 1927B Following the String ──────────────────────────────────────────────


def _s_1927b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 26
        s = []
        for v in a:
            for j in range(26):
                if cnt[j] == v:
                    cnt[j] += 1
                    s.append(chr(97 + j))
                    break
        out.append("".join(s))
    return "\n".join(out) + "\n"


def _a_1927b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = {}
        s = []
        for v in a:
            chosen = None
            for j in range(26):
                ch = chr(97 + j)
                if cnt.get(ch, 0) == v:
                    chosen = ch
                    break
            cnt[chosen] = cnt.get(chosen, 0) + 1
            s.append(chosen)
        out.append("".join(s))
    return "\n".join(out) + "\n"


def _m1_1927b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 26
        s = []
        for v in a:
            for j in range(25, -1, -1):
                if cnt[j] == v:
                    cnt[j] += 1
                    s.append(chr(97 + j))
                    break
        out.append("".join(s))
    return "\n".join(out) + "\n"


def _m2_1927b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 26
        s = []
        for v in a:
            for j in range(26):
                if cnt[j] == v:
                    s.append(chr(97 + j))
                    break
            cnt[0] += 1
        out.append("".join(s))
    return "\n".join(out) + "\n"


def _gen_1927b(rng: random.Random) -> list[str]:
    def trace_of(s: str) -> list[int]:
        seen: dict[str, int] = {}
        res = []
        for ch in s:
            res.append(seen.get(ch, 0))
            seen[ch] = seen.get(ch, 0) + 1
        return res

    cases = [
        "5\n11\n0 0 0 1 0 2 0 3 1 1 4\n10\n0 0 0 0 0 0 0 0 0 0\n1\n0\n8\n0 0 0 0 0 0 0 0\n8\n0 1 0 0 1 0 1 1\n"
    ]
    for _ in range(13):
        n = rng.randint(1, 12)
        s = "".join(rng.choice("abcxyz") for _ in range(n))
        trace = trace_of(s)
        cases.append(f"1\n{n}\n" + " ".join(map(str, trace)) + "\n")
    return cases


# ─── 476B Dreamoon and WiFi ───────────────────────────────────────────────────


def _binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


def _s_476b(stdin: str) -> str:
    ls = lines(stdin)
    s1 = ls[0].strip()
    s2 = ls[1].strip()
    target = sum(1 if c == "+" else -1 for c in s1)
    known = sum(1 if c == "+" else (-1 if c == "-" else 0) for c in s2)
    q = s2.count("?")
    need = target - known
    if abs(need) > q or (need + q) % 2 != 0:
        return "0.000000000\n"
    k = (need + q) // 2
    prob = _binom(q, k) / (2 ** q)
    return f"{prob:.9f}\n"


def _a_476b(stdin: str) -> str:
    return _s_476b(stdin)


def _m1_476b(stdin: str) -> str:
    ls = lines(stdin)
    s1 = ls[0].strip()
    s2 = ls[1].strip()
    target = sum(1 if c == "+" else -1 for c in s1)
    known = sum(1 if c == "+" else (-1 if c == "-" else 0) for c in s2)
    q = s2.count("?")
    need = target - known
    if abs(need) > q or (need + q) % 2 != 0:
        return "0.000000000\n"
    k = (need + q) // 2
    prob = _binom(q, k) / (2 ** max(q - 1, 0))
    return f"{prob:.9f}\n"


def _m2_476b(stdin: str) -> str:
    ls = lines(stdin)
    s1 = ls[0].strip()
    s2 = ls[1].strip()
    target = sum(1 if c == "+" else -1 for c in s1)
    known = sum(1 if c == "+" else (-1 if c == "-" else 0) for c in s2)
    q = s2.count("?")
    need = target - known
    if abs(need) > q or (need + q) % 2 != 0:
        return "0.000000000\n"
    k = (q - need) // 2
    prob = _binom(q, k) / (2 ** q)
    return f"{prob:.9f}\n"


def _gen_476b(rng: random.Random) -> list[str]:
    cases = ["++-+-\n+-+-+\n", "+-+-\n+-??\n", "+++\n??-\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        s1 = "".join(rng.choice("+-") for _ in range(n))
        s2 = "".join(rng.choice("+-?") for _ in range(n))
        cases.append(f"{s1}\n{s2}\n")
    return cases


# ─── 1097B Petr and a Combination Lock ───────────────────────────────────────


def _s_1097b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = [int(ls[i]) for i in range(1, n + 1)]
    for mask in range(1 << n):
        total = 0
        for j in range(n):
            if mask & (1 << j):
                total += a[j]
            else:
                total -= a[j]
        if total % 360 == 0:
            return "YES\n"
    return "NO\n"


def _a_1097b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = [int(ls[i]) for i in range(1, n + 1)]

    def dfs(i: int, total: int) -> bool:
        if i == n:
            return total % 360 == 0
        return dfs(i + 1, total + a[i]) or dfs(i + 1, total - a[i])

    return "YES\n" if dfs(0, 0) else "NO\n"


def _m1_1097b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = [int(ls[i]) for i in range(1, n + 1)]
    total = sum(a)
    return "YES\n" if total % 360 == 0 else "NO\n"


def _m2_1097b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = [int(ls[i]) for i in range(1, n + 1)]
    for mask in range(1 << n):
        total = 0
        for j in range(n):
            if mask & (1 << j):
                total += a[j]
            else:
                total -= a[j]
        if total % 180 == 0:
            return "YES\n"
    return "NO\n"


def _gen_1097b(rng: random.Random) -> list[str]:
    cases = ["3\n10\n10\n10\n", "3\n120\n120\n120\n", "3\n30\n60\n90\n"]
    for _ in range(13):
        n = rng.randint(1, 6)
        a = [rng.randint(1, 180) for _ in range(n)]
        cases.append(f"{n}\n" + "\n".join(map(str, a)) + "\n")
    return cases



# ─── 1186A Vus the Cossack and a Contest ─────────────────────────────────────


def _s_1186a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for line in ls[1:]:
        n, m, k = map(int, line.split())
        out.append("Yes" if m >= n and k >= n else "No")
    return "\n".join(out) + "\n"


def _a_1186a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for line in ls[1:]:
        n, m, k = map(int, line.split())
        out.append("Yes" if min(m, k) >= n else "No")
    return "\n".join(out) + "\n"


def _m1_1186a(stdin: str) -> str:
    ls = lines(stdin)
    out = ["Yes" if int(line.split()[1]) + int(line.split()[2]) >= int(line.split()[0]) else "No" for line in ls[1:]]
    return "\n".join(out) + "\n"


def _m2_1186a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for line in ls[1:]:
        n, m, k = map(int, line.split())
        out.append("Yes" if m >= n or k >= n else "No")
    return "\n".join(out) + "\n"


def _gen_1186a(rng: random.Random) -> list[str]:
    cases = ["2\n5 8 6\n8 5 20\n"]
    for _ in range(12):
        n, m, k = rng.randint(1, 20), rng.randint(0, 30), rng.randint(0, 30)
        cases.append(f"1\n{n} {m} {k}\n")
    return cases


# ─── 2162A Beautiful Average ─────────────────────────────────────────────────


def _solve_2162a(a: list[int]) -> int:
    evens = [x for x in a if x % 2 == 0]
    if len(evens) < 2:
        return -1
    evens.sort()
    return evens[-1] + evens[-2]


def _s_2162a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_2162a(a)))
    return "\n".join(out) + "\n"


def _a_2162a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        evens = sorted([x for x in a if x % 2 == 0])
        out.append(str(evens[-1] + evens[-2] if len(evens) >= 2 else -1))
    return "\n".join(out) + "\n"


def _m1_2162a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        odds = sorted([x for x in a if x % 2 == 1])
        out.append(str(odds[-1] + odds[-2] if len(odds) >= 2 else -1))
    return "\n".join(out) + "\n"


def _m2_2162a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        evens = [x for x in a if x % 2 == 0]
        out.append(str(max(evens) if evens else -1))
    return "\n".join(out) + "\n"


def _gen_2162a(rng: random.Random) -> list[str]:
    cases = ["3\n3\n1 2 3\n4\n1 2 2 1\n2\n2 4\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1380A Three Indices ─────────────────────────────────────────────────────


def _has_three_indices(a: list[int]) -> bool:
    for j in range(1, len(a) - 1):
        left = min(a[:j])
        if left < a[j]:
            for k in range(j + 1, len(a)):
                if a[j] < a[k]:
                    return True
    return False


def _s_1380a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_has_three_indices(a)).strip())
    return "\n".join(out) + "\n"


def _a_1380a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        ok = any(a[i] < a[j] < a[k] for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n))
        out.append(yes_no(ok).strip())
    return "\n".join(out) + "\n"


def _m1_1380a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(max(a) > min(a)).strip())
    return "\n".join(out) + "\n"


def _m2_1380a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(len(set(a)) >= 3).strip())
    return "\n".join(out) + "\n"


def _gen_1380a(rng: random.Random) -> list[str]:
    cases = ["3\n3\n1 2 3\n4\n2 1 4 3\n2\n1 1\n"]
    for _ in range(12):
        n = rng.randint(3, 8)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1527A And Then There Were K ─────────────────────────────────────────────


def _solve_1527a(n: int) -> int:
    return (1 << (n.bit_length() - 1)) - 1 if n else 0


def _s_1527a(stdin: str) -> str:
    return "\n".join([str(_solve_1527a(int(x))) for x in lines(stdin)[1:]]) + "\n"


def _a_1527a(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        out.append(str((1 << (n.bit_length() - 1)) - 1 if n else 0))
    return "\n".join(out) + "\n"


def _m1_1527a(stdin: str) -> str:
    return "\n".join([x for x in lines(stdin)[1:]]) + "\n"


def _m2_1527a(stdin: str) -> str:
    return "\n".join([str((1 << int(x).bit_length()) - 1) for x in lines(stdin)[1:]]) + "\n"


def _gen_1527a(rng: random.Random) -> list[str]:
    cases = ["4\n2\n5\n17\n3\n"]
    for _ in range(12):
        cases.append(f"1\n{rng.randint(1, 10**6)}\n")
    return cases


# ─── 1474B Different Divisors ────────────────────────────────────────────────


def _count_divisors(x: int) -> int:
    c, i = 0, 1
    while i * i <= x:
        if x % i == 0:
            c += 1
            if i * i != x:
                c += 1
        i += 1
    return c


def _solve_1474b(d: int) -> int:
    x = d
    while _count_divisors(x) != 4:
        x += 1
    return x


def _s_1474b(stdin: str) -> str:
    return "\n".join([str(_solve_1474b(int(x))) for x in lines(stdin)[1:]]) + "\n"


def _a_1474b(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        ans = int(x)
        while _count_divisors(ans) != 4:
            ans += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1474b(stdin: str) -> str:
    return "\n".join([str(int(x) + 1) for x in lines(stdin)[1:]]) + "\n"


def _m2_1474b(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        d = int(x)
        out.append(str(d if _count_divisors(d) == 4 else d + 1))
    return "\n".join(out) + "\n"


def _gen_1474b(rng: random.Random) -> list[str]:
    cases = ["4\n1\n2\n3\n4\n"]
    for _ in range(12):
        cases.append(f"1\n{rng.randint(1, 200)}\n")
    return cases


# ─── 2149A Be Positive ───────────────────────────────────────────────────────


def _solve_2149a(a: list[int]) -> int:
    z = sum(1 for x in a if x == 0)
    neg = sum(1 for x in a if x == -1)
    return z + (2 if neg % 2 else 0)


def _s_2149a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_2149a(a)))
    return "\n".join(out) + "\n"


def _a_2149a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        z = sum(1 for x in a if x == 0)
        neg = sum(1 for x in a if x == -1)
        out.append(str(z + 2 * (neg & 1)))
    return "\n".join(out) + "\n"


def _m1_2149a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(sum(1 for x in a if x == 0)))
    return "\n".join(out) + "\n"


def _m2_2149a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(len(a)))
    return "\n".join(out) + "\n"


def _gen_2149a(rng: random.Random) -> list[str]:
    cases = ["1\n3\n-1 0 1\n", "2\n2\n-1 -1\n3\n0 0 0\n"]
    for _ in range(12):
        n = rng.randint(1, 8)
        a = [rng.choice([-1, 0, 1]) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1999B Card Game ─────────────────────────────────────────────────────────


def _solve_1999b(a: list[int], b: list[int]) -> bool:
    a.sort(); b.sort()
    return a[-1] > b[-1]


def _s_1999b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        b = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_solve_1999b(a, b)).strip())
    return "\n".join(out) + "\n"


def _a_1999b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = sorted(map(int, ls[idx].split())); idx += 1
        b = sorted(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(a[-1] > b[-1]).strip())
    return "\n".join(out) + "\n"


def _m1_1999b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        b = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(max(a) >= max(b)).strip())
    return "\n".join(out) + "\n"


def _m2_1999b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        b = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(min(a) > min(b)).strip())
    return "\n".join(out) + "\n"


def _gen_1999b(rng: random.Random) -> list[str]:
    cases = ["3\n1\n1\n1\n1\n2\n2\n2\n2\n2\n1 2\n2 1\n"]
    for _ in range(12):
        n = rng.randint(1, 5)
        a = [rng.randint(1, 10) for _ in range(n)]
        b = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 1521A Nastia and Nearly Good Numbers ────────────────────────────────────


def _solve_1521a(n: int, m: int) -> int:
    x = n
    while _gcd(x, n) <= 1 or _gcd(x + 1, m) <= 1:
        x += 1
    return x


def _s_1521a(stdin: str) -> str:
    return "\n".join([str(_solve_1521a(*map(int, line.split()))) for line in lines(stdin)[1:]]) + "\n"


def _a_1521a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, m = map(int, line.split())
        x = n
        while _gcd(x, n) <= 1 or _gcd(x + 1, m) <= 1:
            x += 1
        out.append(str(x))
    return "\n".join(out) + "\n"


def _m1_1521a(stdin: str) -> str:
    return "\n".join([line.split()[0] for line in lines(stdin)[1:]]) + "\n"


def _m2_1521a(stdin: str) -> str:
    return "\n".join([str(int(line.split()[0]) + 1) for line in lines(stdin)[1:]]) + "\n"


def _gen_1521a(rng: random.Random) -> list[str]:
    cases = ["3\n3 11\n5 10\n8 17\n"]
    for _ in range(12):
        n, m = rng.randint(2, 50), rng.randint(2, 50)
        cases.append(f"1\n{n} {m}\n")
    return cases


# ─── 1914C Quests ────────────────────────────────────────────────────────────


def _solve_1914c(n: int, m: int, k: int, d: int) -> int:
    coins, level = m, 0
    while level < n and coins > 0:
        take = min(coins, k, n - level)
        level += take
        coins -= take
    return level


def _s_1914c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m, k, d = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_1914c(n, m, k, d)))
    return "\n".join(out) + "\n"


def _a_1914c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m, k, d = map(int, ls[idx].split()); idx += 1
        out.append(str(min(n, m)))
    return "\n".join(out) + "\n"


def _m1_1914c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m, k, d = map(int, ls[idx].split()); idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1914c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m, k, d = map(int, ls[idx].split()); idx += 1
        out.append(str(min(n, k)))
    return "\n".join(out) + "\n"


def _gen_1914c(rng: random.Random) -> list[str]:
    cases = ["3\n100 50 2 1\n100 50 2 2\n100 50 2 3\n"]
    for _ in range(12):
        n, m, k, d = rng.randint(5, 50), rng.randint(1, 50), rng.randint(1, 10), rng.randint(1, 5)
        cases.append(f"1\n{n} {m} {k} {d}\n")
    return cases


# ─── 1933B Turtle Math ───────────────────────────────────────────────────────


def _solve_1933b(d: str) -> bool:
    digits = [int(c) for c in d]
    total = sum(digits)
    if total % 3 == 0:
        return True
    for i in range(len(digits)):
        if (total - digits[i]) % 3 == 0:
            return True
    return False


def _s_1933b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        d = ls[idx]; idx += 1
        out.append(yes_no(_solve_1933b(d)).strip())
    return "\n".join(out) + "\n"


def _a_1933b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        d = ls[idx]; idx += 1
        s = sum(map(int, d))
        ok = s % 3 == 0 or any((s - int(c)) % 3 == 0 for c in d)
        out.append(yes_no(ok).strip())
    return "\n".join(out) + "\n"


def _m1_1933b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        d = ls[idx]; idx += 1
        out.append(yes_no(sum(map(int, d)) % 3 == 0).strip())
    return "\n".join(out) + "\n"


def _m2_1933b(stdin: str) -> str:
    return "YES\n"


def _gen_1933b(rng: random.Random) -> list[str]:
    cases = ["3\n3\n123\n3\n111\n2\n11\n"]
    for _ in range(12):
        n = rng.randint(1, 8)
        d = "".join(str(rng.randint(0, 9)) for _ in range(n))
        cases.append(f"1\n{n}\n{d}\n")
    return cases


# ─── 1915E Romantic Glasses ──────────────────────────────────────────────────


def _solve_1915e(a: list[int]) -> bool:
    seen = {0}
    cur = 0
    for i, v in enumerate(a, 1):
        cur += v if i % 2 else -v
        if cur in seen:
            return True
        seen.add(cur)
    return False


def _s_1915e(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_solve_1915e(a)).strip())
    return "\n".join(out) + "\n"


def _a_1915e(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        pref = [0]
        for i, v in enumerate(a, 1):
            pref.append(pref[-1] + (v if i % 2 else -v))
        ok = len(pref) != len(set(pref))
        out.append(yes_no(ok).strip())
    return "\n".join(out) + "\n"


def _m1_1915e(stdin: str) -> str:
    return "NO\n"


def _m2_1915e(stdin: str) -> str:
    return "YES\n"


def _gen_1915e(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 3\n4\n1 1 1 1\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        a = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1722C Word Game ─────────────────────────────────────────────────────────


def _solve_1722c(words: list[str]) -> int:
    start = [0] * 26
    end = [0] * 26
    for w in words:
        start[ord(w[0]) - 97] += 1
        end[ord(w[-1]) - 97] += 1
    bad = 0
    for i in range(26):
        bad = max(bad, end[i] - start[i])
    return len(words) - bad


def _s_1722c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        words = [ls[idx + i] for i in range(n)]; idx += n
        out.append(str(_solve_1722c(words)))
    return "\n".join(out) + "\n"


def _a_1722c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        words = [ls[idx + i] for i in range(n)]; idx += n
        st, en = [0] * 26, [0] * 26
        for w in words:
            st[ord(w[0]) - 97] += 1
            en[ord(w[-1]) - 97] += 1
        deficit = max(en[i] - st[i] for i in range(26))
        out.append(str(n - deficit))
    return "\n".join(out) + "\n"


def _m1_1722c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += n
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1722c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += n
        out.append("1")
    return "\n".join(out) + "\n"


def _gen_1722c(rng: random.Random) -> list[str]:
    cases = ["1\n3\nabc\nbcd\ncde\n"]
    for _ in range(12):
        n = rng.randint(2, 6)
        words = ["".join(rng.choice("abcde") for _ in range(rng.randint(2, 4))) for _ in range(n)]
        cases.append(f"1\n{n}\n" + "\n".join(words) + "\n")
    return cases


# ─── 1462C Unique Number ─────────────────────────────────────────────────────


def _solve_1462c(cnt: list[int]) -> str:
    if cnt[0] > 0 and sum(cnt[1:]) == 0:
        return "-1"
    digits = []
    for d in range(9, -1, -1):
        digits.extend([str(d)] * cnt[d])
    return "".join(digits)


def _s_1462c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        idx += 1
        cnt = list(map(int, ls[idx].split())); idx += 1
        out.append(_solve_1462c(cnt))
    return "\n".join(out) + "\n"


def _a_1462c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        idx += 1
        cnt = list(map(int, ls[idx].split())); idx += 1
        if cnt[0] and sum(cnt[1:]) == 0:
            out.append("-1")
        else:
            parts = []
            for d in range(9, -1, -1):
                parts.append(str(d) * cnt[d])
            out.append("".join(parts))
    return "\n".join(out) + "\n"


def _m1_1462c(stdin: str) -> str:
    return "-1\n"


def _m2_1462c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        idx += 1
        cnt = list(map(int, ls[idx].split())); idx += 1
        out.append("0" * cnt[0])
    return "\n".join(out) + "\n"


def _gen_1462c(rng: random.Random) -> list[str]:
    cases = ["3\n0 0 0 0 0 0 0 0 0 1\n0 0 0 0 0 0 0 0 1 1\n0 0 0 0 0 0 0 1 1 1\n"]
    for _ in range(12):
        cnt = [rng.randint(0, 3) for _ in range(10)]
        if sum(cnt) == 0:
            cnt[1] = 1
        cases.append(f"1\n0\n" + " ".join(map(str, cnt)) + "\n")
    return cases


# ─── 1832C Contrast Value ────────────────────────────────────────────────────


def _solve_1832c(a: list[int]) -> int:
    mx = max(a)
    b = [x for x in a if x != mx]
    if not b:
        return 0
    uniq = sorted(set(b))
    if len(uniq) <= 1:
        return 0
    return uniq[-1] - uniq[0]


def _s_1832c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1832c(a)))
    return "\n".join(out) + "\n"


def _a_1832c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        mx = max(a)
        rest = sorted(set(x for x in a if x != mx))
        out.append(str(0 if len(rest) <= 1 else rest[-1] - rest[0]))
    return "\n".join(out) + "\n"


def _m1_1832c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        u = sorted(set(a))
        out.append(str(u[-1] - u[0] if len(u) > 1 else 0))
    return "\n".join(out) + "\n"


def _m2_1832c(stdin: str) -> str:
    return "0\n"


def _gen_1832c(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 3\n4\n1 1 2 2\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        a = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 459A Pashmak and Garden ─────────────────────────────────────────────────


def _rect_area(x1, y1, x2, y2) -> int:
    return max(0, x2 - x1) * max(0, y2 - y1)


def _s_459a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    x1, y1, x2, y2 = map(int, ls[1].split())
    x3, y3, x4, y4 = map(int, ls[2].split())
    a1 = _rect_area(x1, y1, x2, y2)
    a2 = _rect_area(x3, y3, x4, y4)
    ix1, iy1 = max(x1, x3), max(y1, y3)
    ix2, iy2 = min(x2, x4), min(y2, y4)
    inter = _rect_area(ix1, iy1, ix2, iy2)
    return str(a1 + a2 - inter) + "\n"


def _a_459a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    x1, y1, x2, y2 = map(int, ls[1].split())
    x3, y3, x4, y4 = map(int, ls[2].split())
    cells = set()
    for x in range(x1, x2):
        for y in range(y1, y2):
            cells.add((x, y))
    for x in range(x3, x4):
        for y in range(y3, y4):
            cells.add((x, y))
    return str(len(cells)) + "\n"


def _m1_459a(stdin: str) -> str:
    ls = lines(stdin)
    x1, y1, x2, y2 = map(int, ls[1].split())
    x3, y3, x4, y4 = map(int, ls[2].split())
    return str(_rect_area(x1, y1, x2, y2) + _rect_area(x3, y3, x4, y4)) + "\n"


def _m2_459a(stdin: str) -> str:
    ls = lines(stdin)
    x1, y1, x2, y2 = map(int, ls[1].split())
    return str(_rect_area(x1, y1, x2, y2)) + "\n"


def _gen_459a(rng: random.Random) -> list[str]:
    cases = ["100\n1 1 5 5\n3 3 8 8\n"]
    for _ in range(12):
        n = rng.randint(20, 100)
        r1 = [rng.randint(0, n - 2) for _ in range(4)]
        r2 = [rng.randint(0, n - 2) for _ in range(4)]
        cases.append(f"{n}\n" + " ".join(map(str, r1)) + "\n" + " ".join(map(str, r2)) + "\n")
    return cases


# ─── 2050A Line Breaks ─────────────────────────────────────────────────────────


def _solve_2050a(k: int, x: int, words: list[str]) -> bool:
    lines_used = 1
    cur = 0
    for w in words:
        need = len(w) if cur == 0 else cur + 1 + len(w)
        if need > x:
            lines_used += 1
            cur = len(w)
        else:
            cur = need
    return lines_used <= k


def _s_2050a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        k, x = map(int, ls[idx].split()); idx += 1
        words = ls[idx].split(); idx += 1
        out.append(yes_no(_solve_2050a(k, x, words)).strip())
    return "\n".join(out) + "\n"


def _a_2050a(stdin: str) -> str:
    return _s_2050a(stdin)


def _m1_2050a(stdin: str) -> str:
    return "YES\n"


def _m2_2050a(stdin: str) -> str:
    return "NO\n"


def _gen_2050a(rng: random.Random) -> list[str]:
    cases = ["2\n3 10\ncodeforces\n3 10\ncodeforces\n", "1\n1 5\na b c\n"]
    for _ in range(12):
        k, x = rng.randint(1, 5), rng.randint(5, 20)
        n = rng.randint(1, 6)
        words = [rng.choice("abcde") * rng.randint(1, 4) for _ in range(n)]
        cases.append(f"1\n{k} {x}\n" + " ".join(words) + "\n")
    return cases


# ─── 1514B AND 0 Sum Big ───────────────────────────────────────────────────────


def _solve_1514b(n: int, k: int) -> int:
    return pow(n, k, MOD)


def _s_1514b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_1514b(n, k)))
    return "\n".join(out) + "\n"


def _a_1514b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        r = 1
        for _ in range(k):
            r = (r * n) % MOD
        out.append(str(r))
    return "\n".join(out) + "\n"


def _m1_1514b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        out.append(str(n * k))
    return "\n".join(out) + "\n"


def _m2_1514b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _gen_1514b(rng: random.Random) -> list[str]:
    cases = ["2\n2 2\n5 3\n"]
    for _ in range(12):
        n, k = rng.randint(2, 10), rng.randint(1, 5)
        cases.append(f"1\n{n} {k}\n")
    return cases


# ─── 1921B Arranging Cats ────────────────────────────────────────────────────


def _solve_1921b(s: str, t: str) -> int:
    zt = sum(1 for a, b in zip(s, t) if a == "0" and b == "1")
    oz = sum(1 for a, b in zip(s, t) if a == "1" and b == "0")
    return max(zt, oz)


def _s_1921b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s, tt = ls[idx], ls[idx + 1]; idx += 2
        out.append(str(_solve_1921b(s, tt)))
    return "\n".join(out) + "\n"


def _a_1921b(stdin: str) -> str:
    return _s_1921b(stdin)


def _m1_1921b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s, tt = ls[idx], ls[idx + 1]; idx += 2
        out.append(str(sum(a != b for a, b in zip(s, tt))))
    return "\n".join(out) + "\n"


def _m2_1921b(stdin: str) -> str:
    return "0\n" * int(lines(stdin)[0])


def _gen_1921b(rng: random.Random) -> list[str]:
    cases = ["2\n3\n000\n111\n4\n0011\n1100\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        s = "".join(rng.choice("01") for _ in range(n))
        t = "".join(rng.choice("01") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n{t}\n")
    return cases


# ─── 1862A Gift Carpet ───────────────────────────────────────────────────────


def _solve_1862a(grid: list[str], p: str) -> bool:
    n, m = len(grid), len(grid[0])
    pi = 0
    for i in range(n):
        row = grid[i]
        dirs = range(m) if i % 2 == 0 else range(m - 1, -1, -1)
        for j in dirs:
            if pi < len(p) and row[j] == p[pi]:
                pi += 1
    return pi == len(p)


def _s_1862a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split()); idx += 1
        grid = [ls[idx + i] for i in range(n)]; idx += n
        p = ls[idx]; idx += 1
        out.append(yes_no(_solve_1862a(grid, p)).strip())
    return "\n".join(out) + "\n"


def _a_1862a(stdin: str) -> str:
    return _s_1862a(stdin)


def _m1_1862a(stdin: str) -> str:
    return "YES\n"


def _m2_1862a(stdin: str) -> str:
    return "NO\n"


def _gen_1862a(rng: random.Random) -> list[str]:
    cases = ["1\n3 3\naeb\nbcd\ncea\nabcde\n"]
    for _ in range(12):
        n, m = 3, 3
        grid = ["".join(rng.choice("abcde") for _ in range(m)) for _ in range(n)]
        p = "".join(rng.choice("abcde") for _ in range(rng.randint(2, 5)))
        cases.append(f"1\n{n} {m}\n" + "\n".join(grid) + "\n" + p + "\n")
    return cases


# ─── 1421A XORwice ───────────────────────────────────────────────────────────


def _s_1421a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a, b = map(int, ls[idx].split()); idx += 1
        out.append(str(0 if a == b else 1))
    return "\n".join(out) + "\n"


def _a_1421a(stdin: str) -> str:
    return _s_1421a(stdin)


def _m1_1421a(stdin: str) -> str:
    return "1\n"


def _m2_1421a(stdin: str) -> str:
    return "0\n"


def _gen_1421a(rng: random.Random) -> list[str]:
    cases = ["3\n1 1\n2 2\n3 4\n"]
    for _ in range(12):
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        cases.append(f"1\n{a} {b}\n")
    return cases


# ─── 1789A Serval and Mocha's Array ──────────────────────────────────────────


def _solve_1789a(a: list[int]) -> bool:
    n = len(a)
    vals = set(a)
    for i in range(n):
        for j in range(i + 1, n):
            g = _gcd(a[i], a[j])
            if g in vals:
                return True
    return False


def _s_1789a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_solve_1789a(a)).strip())
    return "\n".join(out) + "\n"


def _a_1789a(stdin: str) -> str:
    return _s_1789a(stdin)


def _m1_1789a(stdin: str) -> str:
    return "NO\n"


def _m2_1789a(stdin: str) -> str:
    return "YES\n"


def _gen_1789a(rng: random.Random) -> list[str]:
    cases = ["2\n3\n2 4 6\n3\n1 2 3\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1919A Wallet Exchange ───────────────────────────────────────────────────


def _s_1919a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a, b = map(int, ls[idx].split()); idx += 1
        out.append(yes_no((a + b) % 2 == 0).strip())
    return "\n".join(out) + "\n"


def _a_1919a(stdin: str) -> str:
    return _s_1919a(stdin)


def _m1_1919a(stdin: str) -> str:
    return "YES\n"


def _m2_1919a(stdin: str) -> str:
    return "NO\n"


def _gen_1919a(rng: random.Random) -> list[str]:
    cases = ["3\n1 1\n2 2\n3 4\n"]
    for _ in range(12):
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        cases.append(f"1\n{a} {b}\n")
    return cases


# ─── 2137A Collatz Conjecture ────────────────────────────────────────────────


def _collatz_reachable(x: int, y: int) -> bool:
    if x == y:
        return True
    seen = set()
    cur = x
    for _ in range(200):
        if cur == y:
            return True
        if cur in seen:
            return False
        seen.add(cur)
        if cur % 2 == 0:
            cur //= 2
        else:
            cur = 3 * cur + 1
    return False


def _s_2137a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        x, y = map(int, ls[idx].split()); idx += 1
        out.append(yes_no(_collatz_reachable(x, y)).strip())
    return "\n".join(out) + "\n"


def _a_2137a(stdin: str) -> str:
    return _s_2137a(stdin)


def _m1_2137a(stdin: str) -> str:
    return "NO\n"


def _m2_2137a(stdin: str) -> str:
    return "YES\n"


def _gen_2137a(rng: random.Random) -> list[str]:
    cases = ["3\n3 3\n7 2\n6 3\n"]
    for _ in range(12):
        x, y = rng.randint(1, 20), rng.randint(1, 20)
        cases.append(f"1\n{x} {y}\n")
    return cases


# ─── 688B Lovely Palindromes ─────────────────────────────────────────────────


def _next_palindrome(n: str) -> str:
    if len(n) == 1:
        return n
    half = (len(n) + 1) // 2
    left = n[:half]
    if len(n) % 2 == 0:
        cand = left + left[::-1]
        if cand >= n:
            return cand
        left = str(int(left) + 1)
        return left + left[::-1]
    cand = left + left[:-1][::-1]
    if cand >= n:
        return cand
    left = str(int(left) + 1)
    return left + left[:-1][::-1]


def _s_688b(stdin: str) -> str:
    return _next_palindrome(lines(stdin)[0].strip()) + "\n"


def _a_688b(stdin: str) -> str:
    n = lines(stdin)[0].strip()
    p = _next_palindrome(n)
    return p + "\n"


def _m1_688b(stdin: str) -> str:
    return lines(stdin)[0].strip() + "\n"


def _m2_688b(stdin: str) -> str:
    n = lines(stdin)[0].strip()
    return n + n[::-1] + "\n"


def _gen_688b(rng: random.Random) -> list[str]:
    cases = ["808\n", "9\n", "1000\n", "123\n", "5\n", "99\n", "100\n", "1234\n", "7\n", "11\n", "19\n", "88\n"]
    for _ in range(5):
        cases.append(str(rng.randint(1, 9999)) + "\n")
    return cases


# ─── 567A Lineland Mail ────────────────────────────────────────────────────────


def _solve_567a(a: list[int]) -> tuple[int, int]:
    n = len(a)
    mins, maxs = [], []
    for i in range(n):
        left = abs(a[i] - a[i - 1]) if i else abs(a[i] - a[1])
        right = abs(a[i] - a[i + 1]) if i < n - 1 else abs(a[i] - a[n - 2])
        mins.append(min(left, right))
        maxs.append(max(left, right))
    return min(mins), max(maxs)


def _s_567a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    lo, hi = _solve_567a(a)
    out = [f"{lo} {hi}" for _ in range(n)]
    return "\n".join(out) + "\n"


def _a_567a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    out = []
    for i in range(n):
        if i == 0:
            mn = abs(a[0] - a[1])
            mx = abs(a[-1] - a[0])
        elif i == n - 1:
            mn = abs(a[-1] - a[-2])
            mx = abs(a[-1] - a[0])
        else:
            mn = min(abs(a[i] - a[i - 1]), abs(a[i] - a[i + 1]))
            mx = max(abs(a[-1] - a[i]), abs(a[0] - a[i]))
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _m1_567a(stdin: str) -> str:
    n = int(lines(stdin)[0])
    return "\n".join(["0 0"] * n) + "\n"


def _m2_567a(stdin: str) -> str:
    n = int(lines(stdin)[0])
    return "\n".join(["1 1"] * n) + "\n"


def _gen_567a(rng: random.Random) -> list[str]:
    cases = ["4\n-3 5 1 2\n", "2\n10 20\n", "3\n1 5 9\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        a = sorted([rng.randint(-50, 50) for _ in range(n)])
        cases.append(f"{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1633A Div. 7 ──────────────────────────────────────────────────────────────


def _solve_1633a(n: int) -> int:
    s = f"{n:03d}"
    for i in range(3):
        for d in range(10):
            if d == int(s[i]):
                continue
            t = int(s[:i] + str(d) + s[i + 1:])
            if t >= 100 and t % 7 == 0:
                return t
    return -1


def _s_1633a(stdin: str) -> str:
    return "\n".join(str(_solve_1633a(int(x))) for x in lines(stdin)[1:]) + "\n"


def _a_1633a(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        ans = -1
        for v in range(100, 1000):
            if v % 7 == 0 and sum(abs(((v // (10 ** i)) % 10) - ((n // (10 ** i)) % 10)) for i in range(3)) == 1:
                ans = v
                break
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1633a(stdin: str) -> str:
    return "-1\n"


def _m2_1633a(stdin: str) -> str:
    return "\n".join(lines(stdin)[1:]) + "\n"


def _gen_1633a(rng: random.Random) -> list[str]:
    cases = ["3\n105\n100\n1\n"]
    for _ in range(12):
        cases.append(f"1\n{rng.randint(100, 999)}\n")
    return cases


# ─── 2037A Twice ─────────────────────────────────────────────────────────────


def _solve_2037a(a: list[int]) -> int:
    from collections import Counter
    return sum(v // 2 for v in Counter(a).values())


def _s_2037a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_2037a(a)))
    return "\n".join(out) + "\n"


def _a_2037a(stdin: str) -> str:
    return _s_2037a(stdin)


def _m1_2037a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(len(a) // 2))
    return "\n".join(out) + "\n"


def _m2_2037a(stdin: str) -> str:
    return "0\n"


def _gen_2037a(rng: random.Random) -> list[str]:
    cases = ["3\n5\n1 2 3 2 1\n4\n1 1 1 1\n3\n1 2 3\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        a = [rng.randint(1, 5) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1362A Johnny and Ancient Computer ───────────────────────────────────────


def _solve_1362a(a: int, b: int) -> int:
    ops = 0
    while a != b:
        if a > b:
            if a % b == 0:
                ops += a // b - 1
                a = b
            else:
                a *= 2
                ops += 1
        else:
            if b % a == 0:
                ops += b // a - 1
                b = a
            else:
                b *= 2
                ops += 1
    return ops


def _s_1362a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a, b = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_1362a(a, b)))
    return "\n".join(out) + "\n"


def _a_1362a(stdin: str) -> str:
    return _s_1362a(stdin)


def _m1_1362a(stdin: str) -> str:
    return "0\n"


def _m2_1362a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a, b = map(int, ls[idx].split()); idx += 1
        out.append(str(abs(a - b)))
    return "\n".join(out) + "\n"


def _gen_1362a(rng: random.Random) -> list[str]:
    cases = ["3\n1 2\n3 6\n3 9\n"]
    for _ in range(12):
        a = rng.randint(1, 20)
        b = a * rng.randint(1, 5)
        cases.append(f"1\n{a} {b}\n")
    return cases


# ─── 1716A 2-3 Moves ─────────────────────────────────────────────────────────


def _solve_1716a(n: int) -> int:
    if n == 1:
        return 2
    if n == 2:
        return 1
    return (n + 2) // 3


def _s_1716a(stdin: str) -> str:
    return "\n".join(str(_solve_1716a(int(x))) for x in lines(stdin)[1:]) + "\n"


def _a_1716a(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        if n == 1:
            out.append("2")
        elif n % 2 == 0:
            out.append(str(n // 2 if n == 2 else (n + 2) // 3))
        else:
            out.append(str((n + 2) // 3))
    return "\n".join(out) + "\n"


def _m1_1716a(stdin: str) -> str:
    return "\n".join(lines(stdin)[1:]) + "\n"


def _m2_1716a(stdin: str) -> str:
    return "\n".join(str(int(x) // 2) for x in lines(stdin)[1:]) + "\n"


def _gen_1716a(rng: random.Random) -> list[str]:
    cases = ["4\n1\n2\n4\n6\n"]
    for _ in range(12):
        cases.append(f"1\n{rng.randint(1, 30)}\n")
    return cases


# ─── 268B Buttons ──────────────────────────────────────────────────────────────


def _solve_268b(n: int) -> int:
    if n == 1:
        return 1
    return n + 2 * _solve_268b(n - 1)


def _s_268b(stdin: str) -> str:
    return str(_solve_268b(int(lines(stdin)[0].strip()))) + "\n"


def _a_268b(stdin: str) -> str:
    return _s_268b(stdin)


def _m1_268b(stdin: str) -> str:
    n = int(lines(stdin)[0].strip())
    return str(n) + "\n"


def _m2_268b(stdin: str) -> str:
    n = int(lines(stdin)[0].strip())
    return str(2 ** n) + "\n"


def _gen_268b(rng: random.Random) -> list[str]:
    return [f"{n}\n" for n in range(1, 13)]


# ─── 1742D Coprime ───────────────────────────────────────────────────────────


def _solve_1742d(a: list[int]) -> int:
    n = len(a)
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            if _gcd(a[i], a[j]) == 1:
                cnt += 1
    return cnt


def _s_1742d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1742d(a)))
    return "\n".join(out) + "\n"


def _a_1742d(stdin: str) -> str:
    return _s_1742d(stdin)


def _m1_1742d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        out.append(str(n * (n - 1) // 2))
    return "\n".join(out) + "\n"


def _m2_1742d(stdin: str) -> str:
    return "0\n"


def _gen_1742d(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 3\n4\n1 1 2 3\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1527B1 Palindrome Game (easy) ───────────────────────────────────────────


def _solve_1527b1(n: int, s: str) -> bool:
    if n % 2 == 1:
        return True
    return s != s[::-1]


def _s_1527b1(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(yes_no(_solve_1527b1(n, s)).strip())
    return "\n".join(out) + "\n"


def _a_1527b1(stdin: str) -> str:
    return _s_1527b1(stdin)


def _m1_1527b1(stdin: str) -> str:
    return "YES\n"


def _m2_1527b1(stdin: str) -> str:
    return "NO\n"


def _gen_1527b1(rng: random.Random) -> list[str]:
    cases = ["3\n1\na\n2\nab\n3\nabc\n"]
    for _ in range(12):
        n = rng.randint(1, 8)
        s = "".join(rng.choice("abc") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 1418A Buying Torches ──────────────────────────────────────────────────────


def _solve_1418a(r: int, k: int, x: int, y: int, c: int) -> int:
    sticks = 0
    torches = k
    nights = r
    while nights > 0:
        burn = min(nights, torches * y)
        nights -= burn
        if nights == 0:
            break
        need = (burn + y - 1) // y
        sticks += need * c
        torches = need
    return sticks


def _s_1418a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        r, k, x, y, c = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_1418a(r, k, x, y, c)))
    return "\n".join(out) + "\n"


def _a_1418a(stdin: str) -> str:
    return _s_1418a(stdin)


def _m1_1418a(stdin: str) -> str:
    return "0\n"


def _m2_1418a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        r, k, x, y, c = map(int, ls[idx].split()); idx += 1
        out.append(str(r * c))
    return "\n".join(out) + "\n"


def _gen_1418a(rng: random.Random) -> list[str]:
    cases = ["2\n8 1 1 1 1\n8 4 2 1 4\n"]
    for _ in range(12):
        r, k, x, y, c = rng.randint(1, 20), rng.randint(1, 5), rng.randint(1, 3), rng.randint(1, 3), rng.randint(1, 5)
        cases.append(f"1\n{r} {k} {x} {y} {c}\n")
    return cases


# ─── 1182A Filling Shapes ────────────────────────────────────────────────────


def _solve_1182a(n: int) -> int:
    if n % 2:
        return 0
    k = n // 2
    if k == 1:
        return 1
    a, b = 1, 1
    for _ in range(2, k + 1):
        a, b = b, a + b
    return b


def _s_1182a(stdin: str) -> str:
    return str(_solve_1182a(int(lines(stdin)[0].strip()))) + "\n"


def _a_1182a(stdin: str) -> str:
    return _s_1182a(stdin)


def _m1_1182a(stdin: str) -> str:
    return "1\n"


def _m2_1182a(stdin: str) -> str:
    n = int(lines(stdin)[0].strip())
    return str(n // 2) + "\n"


def _gen_1182a(rng: random.Random) -> list[str]:
    return [f"{n}\n" for n in [2, 4, 6, 8, 10, 12, 1, 3, 5, 14, 16, 20]]


# ─── 1791G1 Teleporters (Easy) ───────────────────────────────────────────────


def _solve_1791g1(n: int, c: list[int], a: list[int]) -> int:
    idx = sorted(range(n), key=lambda i: c[i])
    cost = 0
    pos = 1
    taken = set()
    for i in idx:
        if i + 1 in taken:
            continue
        cost += c[i]
        taken.add(i + 1)
        pos = n + 1
    return cost


def _s_1791g1(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        c = list(map(int, ls[idx].split())); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        order = sorted(range(n), key=lambda i: c[i])
        total = 0
        used = [False] * n
        for i in order:
            if used[i]:
                continue
            total += c[i]
            used[i] = True
            if i + 1 < n:
                used[i + 1] = True
        out.append(str(total))
    return "\n".join(out) + "\n"


def _a_1791g1(stdin: str) -> str:
    return _s_1791g1(stdin)


def _m1_1791g1(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        c = list(map(int, ls[idx].split())); idx += 1
        idx += 1
        out.append(str(sum(c)))
    return "\n".join(out) + "\n"


def _m2_1791g1(stdin: str) -> str:
    return "0\n"


def _gen_1791g1(rng: random.Random) -> list[str]:
    cases = ["1\n3\n1 2 3\n1 2 3\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        c = [rng.randint(1, 10) for _ in range(n)]
        a = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, c)) + "\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1472C Long Jumps ────────────────────────────────────────────────────────


def _solve_1472c(a: list[int]) -> int:
    n = len(a)
    pos = 0
    while pos < n - 1:
        best = pos
        for j in range(pos + 1, min(n, pos + a[pos] + 1)):
            best = max(best, j)
        if best == pos:
            break
        pos = best
    return pos


def _s_1472c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1472c(a)))
    return "\n".join(out) + "\n"


def _a_1472c(stdin: str) -> str:
    return _s_1472c(stdin)


def _m1_1472c(stdin: str) -> str:
    return "0\n"


def _m2_1472c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(n - 1))
    return "\n".join(out) + "\n"


def _gen_1472c(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 1\n4\n2 1 1 1\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        a = [rng.randint(1, 5) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1582B Luntik and Subsequences ───────────────────────────────────────────


def _solve_1582b(a: list[int]) -> int:
    z = sum(1 for x in a if x == 0)
    o = sum(1 for x in a if x == 1)
    return (2 ** o - 1) * (2 ** z)


def _s_1582b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1582b(a)))
    return "\n".join(out) + "\n"


def _a_1582b(stdin: str) -> str:
    return _s_1582b(stdin)


def _m1_1582b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(2 ** sum(a)))
    return "\n".join(out) + "\n"


def _m2_1582b(stdin: str) -> str:
    return "1\n"


def _gen_1582b(rng: random.Random) -> list[str]:
    cases = ["3\n3\n1 0 1\n2\n0 0\n4\n1 1 1 1\n"]
    for _ in range(12):
        n = rng.randint(1, 10)
        a = [rng.randint(0, 1) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1715B Beautiful Array ───────────────────────────────────────────────────


def _solve_1715b(n: int, k: int, b: list[int]) -> int:
    need = max(0, n * k - sum(b))
    rem = sum(b) % n
    if rem and need > 0 and rem + need < n:
        need += n - (rem + need) % n
    return need


def _s_1715b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        m = int(ls[idx]); idx += 1
        b = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1715b(n, k, b)))
    return "\n".join(out) + "\n"


def _a_1715b(stdin: str) -> str:
    return _s_1715b(stdin)


def _m1_1715b(stdin: str) -> str:
    return "0\n"


def _m2_1715b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        m = int(ls[idx]); idx += 1
        b = list(map(int, ls[idx].split())); idx += 1
        out.append(str(n * k))
    return "\n".join(out) + "\n"


def _gen_1715b(rng: random.Random) -> list[str]:
    cases = ["1\n3 2\n3\n1 1 1\n"]
    for _ in range(12):
        n, k = rng.randint(2, 5), rng.randint(1, 5)
        m = rng.randint(1, 5)
        b = [rng.randint(1, 5) for _ in range(m)]
        cases.append(f"1\n{n} {k}\n{m}\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 1549A Gregor and Cryptography ───────────────────────────────────────────


def _solve_1549a(p: int, q: int, m: int, e: int) -> int:
    inv = pow(p, -1, m)
    return (e * inv) % m


def _s_1549a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        p, q, m, e = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_1549a(p, q, m, e)))
    return "\n".join(out) + "\n"


def _a_1549a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        p, q, m, e = map(int, ls[idx].split()); idx += 1
        x = 1
        while (p * x) % m != e:
            x += 1
        out.append(str(x))
    return "\n".join(out) + "\n"


def _m1_1549a(stdin: str) -> str:
    return "1\n"


def _m2_1549a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        p, q, m, e = map(int, ls[idx].split()); idx += 1
        out.append(str(e))
    return "\n".join(out) + "\n"


def _gen_1549a(rng: random.Random) -> list[str]:
    cases = ["1\n2 3 5 4\n"]
    for _ in range(12):
        m = rng.choice([5, 7, 11, 13])
        p = rng.randint(2, m - 1)
        q = rng.randint(2, m - 1)
        e = (p * rng.randint(1, m - 1)) % m
        cases.append(f"1\n{p} {q} {m} {e}\n")
    return cases


# ─── 1354B Ternary String ────────────────────────────────────────────────────


def _solve_1354b(s: str) -> int:
    best = len(s) + 1
    for left in range(3):
        for mid in range(3):
            for right in range(3):
                if left == mid or mid == right or left == right:
                    continue
                i = 0
                while i < len(s) and s[i] != str(left):
                    i += 1
                j = i
                while j < len(s) and s[j] != str(mid):
                    j += 1
                k = j
                while k < len(s) and s[k] != str(right):
                    k += 1
                if k < len(s):
                    best = min(best, k - i + 1)
    return best if best <= len(s) else 0


def _s_1354b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        s = ls[idx]; idx += 1
        out.append(str(_solve_1354b(s)))
    return "\n".join(out) + "\n"


def _a_1354b(stdin: str) -> str:
    return _s_1354b(stdin)


def _m1_1354b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = [str(len(ls[i])) for i in range(1, t + 1)]
    return "\n".join(out) + "\n"


def _m2_1354b(stdin: str) -> str:
    return "1\n"


def _gen_1354b(rng: random.Random) -> list[str]:
    cases = ["3\n001122\n012\n012012012012\n"]
    for _ in range(12):
        n = rng.randint(3, 15)
        s = "".join(str(rng.randint(0, 2)) for _ in range(n))
        cases.append(f"1\n{s}\n")
    return cases


# ─── 1690A Print a Pedestal ──────────────────────────────────────────────────


def _solve_1690a(n: int) -> tuple[int, int, int]:
    if n % 3 == 0:
        h1 = n // 3
        return h1, h1 + 1, h1 - 1
    if n % 3 == 1:
        h1 = n // 3
        return h1, h1 + 2, h1 - 1
    h1 = n // 3 + 1
    return h1, n // 3 + 2, n // 3


def _s_1690a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        h1, h2, h3 = _solve_1690a(n)
        out.append(f"{h1} {h2} {h3}")
    return "\n".join(out) + "\n"


def _a_1690a(stdin: str) -> str:
    return _s_1690a(stdin)


def _m1_1690a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        h = n // 3
        out.append(f"{h} {h} {h}")
    return "\n".join(out) + "\n"


def _m2_1690a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        out.append(f"{n} 1 1")
    return "\n".join(out) + "\n"


def _gen_1690a(rng: random.Random) -> list[str]:
    cases = ["3\n6\n7\n8\n"]
    for _ in range(12):
        cases.append(f"1\n{rng.randint(6, 30)}\n")
    return cases


# ─── 1692E Binary Deque ──────────────────────────────────────────────────────


def _solve_1692e(k: int, a: list[int]) -> int:
    n = len(a)
    if n < k:
        return 0
    cur = sum(a[:k])
    best = cur
    for j in range(k, n):
        cur += a[j] - a[j - k]
        best = max(best, cur)
    return best


def _s_1692e(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1692e(k, a)))
    return "\n".join(out) + "\n"


def _a_1692e(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        best = 0
        for i in range(n - k + 1):
            best = max(best, sum(a[i:i + k]))
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1692e(stdin: str) -> str:
    return "0\n"


def _m2_1692e(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split()); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def _gen_1692e(rng: random.Random) -> list[str]:
    cases = ["2\n5 2\n1 0 1 0 1\n6 3\n1 0 1 0 1 0\n"]
    for _ in range(12):
        n, k = rng.randint(3, 12), rng.randint(1, n if 'n' in dir() else 3)
        n = rng.randint(3, 12)
        k = rng.randint(1, n)
        a = [rng.randint(0, 1) for _ in range(n)]
        cases.append(f"1\n{n} {k}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1538C Number of Pairs ───────────────────────────────────────────────────


def _solve_1538c(a: list[int], l: int, r: int) -> int:
    a.sort()
    n = len(a)
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            if l <= a[i] + a[j] <= r:
                cnt += 1
    return cnt


def _s_1538c(stdin: str) -> str:
    ls = lines(stdin)
    n, q = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    out = []
    for i in range(2, 2 + q):
        l, r = map(int, ls[i].split())
        out.append(str(_solve_1538c(a, l, r)))
    return "\n".join(out) + "\n"


def _a_1538c(stdin: str) -> str:
    return _s_1538c(stdin)


def _m1_1538c(stdin: str) -> str:
    ls = lines(stdin)
    q = int(ls[0].split()[1])
    return "\n".join(["0"] * q) + "\n"


def _m2_1538c(stdin: str) -> str:
    ls = lines(stdin)
    q = int(ls[0].split()[1])
    return "\n".join(["1"] * q) + "\n"


def _gen_1538c(rng: random.Random) -> list[str]:
    cases = ["5 3\n1 2 3 4 5\n1 5\n2 4\n3 3\n"]
    for _ in range(12):
        n, q = rng.randint(3, 8), rng.randint(1, 5)
        a = [rng.randint(1, 10) for _ in range(n)]
        qs = [f"{rng.randint(1, 10)} {rng.randint(10, 20)}" for _ in range(q)]
        cases.append(f"{n} {q}\n" + " ".join(map(str, a)) + "\n" + "\n".join(qs) + "\n")
    return cases


# ─── 1899B 250 Thousand Tons of TNT ──────────────────────────────────────────


def _solve_1899b(a: list[int]) -> int:
    n = len(a)
    best = 0
    for i in range(1, n):
        left = sum(a[:i])
        right = sum(a[i:])
        best = max(best, left * right)
    return best


def _s_1899b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1899b(a)))
    return "\n".join(out) + "\n"


def _a_1899b(stdin: str) -> str:
    return _s_1899b(stdin)


def _m1_1899b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(sum(a) ** 2))
    return "\n".join(out) + "\n"


def _m2_1899b(stdin: str) -> str:
    return "0\n"


def _gen_1899b(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 3\n4\n1 1 1 1\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        a = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1931B Make Equal ────────────────────────────────────────────────────────


def _solve_1931b(a: list[int]) -> bool:
    mx = max(a)
    for x in a:
        if mx % x != 0:
            return False
        v = mx // x
        while v > 1:
            if v % 2:
                return False
            v //= 2
    return True


def _s_1931b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_solve_1931b(a)).strip())
    return "\n".join(out) + "\n"


def _a_1931b(stdin: str) -> str:
    return _s_1931b(stdin)


def _m1_1931b(stdin: str) -> str:
    return "YES\n"


def _m2_1931b(stdin: str) -> str:
    return "NO\n"


def _gen_1931b(rng: random.Random) -> list[str]:
    cases = ["3\n2\n1 2\n3\n1 2 4\n2\n1 3\n"]
    for _ in range(12):
        n = rng.randint(2, 6)
        mx = rng.randint(2, 32)
        a = [mx // (2 ** rng.randint(0, 3)) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1915D Unnatural Language Processing ─────────────────────────────────────


def _solve_1915d(s: str) -> int:
    n = len(s)
    i = 0
    parts = 0
    while i < n:
        parts += 1
        j = i + 1
        while j <= n and s[i:j] == s[i:j][::-1]:
            j += 1
        i = j
    return parts


def _s_1915d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(str(_solve_1915d(s)))
    return "\n".join(out) + "\n"


def _a_1915d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        cnt = 0
        i = 0
        while i < n:
            cnt += 1
            j = i + 1
            while j <= n and s[i:j] == s[i:j][::-1]:
                j += 1
            i = j
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1915d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1915d(stdin: str) -> str:
    return "1\n"


def _gen_1915d(rng: random.Random) -> list[str]:
    cases = ["2\n5\naaaaa\n4\nabba\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        s = "".join(rng.choice("abc") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 540A Combination Lock ───────────────────────────────────────────────────


def _solve_540a(s: str, t: str) -> int:
    n = int(s)
    total = 0
    for a, b in zip(s, t):
        d = abs(int(a) - int(b))
        total += min(d, 10 - d)
    return total


def _s_540a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    s, t = ls[1], ls[2]
    return str(_solve_540a(s, t)) + "\n"


def _a_540a(stdin: str) -> str:
    return _s_540a(stdin)


def _m1_540a(stdin: str) -> str:
    ls = lines(stdin)
    s, t = ls[1], ls[2]
    return str(sum(abs(int(a) - int(b)) for a, b in zip(s, t))) + "\n"


def _m2_540a(stdin: str) -> str:
    return "0\n"


def _gen_540a(rng: random.Random) -> list[str]:
    cases = ["3\n010\n909\n", "2\n00\n00\n"]
    for _ in range(12):
        n = rng.randint(1, 5)
        s = "".join(str(rng.randint(0, 9)) for _ in range(n))
        t = "".join(str(rng.randint(0, 9)) for _ in range(n))
        cases.append(f"{n}\n{s}\n{t}\n")
    return cases


# ─── 1914A Problemsolving Log ────────────────────────────────────────────────


def _solve_1914a(s: str) -> int:
    done = set()
    for i in range(len(s) - 1):
        if s[i + 1] < s[i]:
            done.add(s[i])
    done.add(s[-1])
    return len(done)


def _s_1914a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(str(_solve_1914a(s)))
    return "\n".join(out) + "\n"


def _a_1914a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        mx = 0
        for ch in s:
            mx = max(mx, ord(ch) - 64)
        out.append(str(mx))
    return "\n".join(out) + "\n"


def _m1_1914a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1914a(stdin: str) -> str:
    return "1\n"


def _gen_1914a(rng: random.Random) -> list[str]:
    cases = ["2\n3\nABC\n4\nABBC\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        s = "".join(chr(65 + rng.randint(0, 3)) for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 2051A Preparing for the Olympiad ─────────────────────────────────────────


def _solve_2051a(n: int, x: int, y: int) -> int:
    if x > y:
        x, y = y, x
    days = 0
    rem = n
    while rem > 0:
        if rem >= x + y:
            rem -= x + y
            days += 2
        elif rem >= y:
            days += 1
            rem = 0
        else:
            days += 1
            rem = 0
    return days


def _s_2051a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, x, y = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_2051a(n, x, y)))
    return "\n".join(out) + "\n"


def _a_2051a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, x, y = map(int, ls[idx].split()); idx += 1
        out.append(str((n + x + y - 1) // (x + y) * 2))
    return "\n".join(out) + "\n"


def _m1_2051a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, x, y = map(int, ls[idx].split()); idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_2051a(stdin: str) -> str:
    return "1\n"


def _gen_2051a(rng: random.Random) -> list[str]:
    cases = ["3\n10 2 3\n5 1 2\n8 4 4\n"]
    for _ in range(12):
        n, x, y = rng.randint(1, 20), rng.randint(1, 5), rng.randint(1, 5)
        cases.append(f"1\n{n} {x} {y}\n")
    return cases


# ─── 1473B String LCM ────────────────────────────────────────────────────────


def _solve_1473b(a: str, b: str) -> int:
    if len(a) * len(b) > 10 ** 6:
        return -1
    la, lb = len(a), len(b)
    if a + b != b + a:
        return -1
    return la * lb // len(a + b) * len(a + b)


def _lcm_len(a: str, b: str) -> int:
    if a + b != b + a:
        return -1
    g = a + b
    return len(a) * len(b) // len(g)


def _s_1473b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a = ls[idx]; b = ls[idx + 1]; idx += 2
        out.append(str(_lcm_len(a, b)))
    return "\n".join(out) + "\n"


def _a_1473b(stdin: str) -> str:
    return _s_1473b(stdin)


def _m1_1473b(stdin: str) -> str:
    return "-1\n"


def _m2_1473b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a = ls[idx]; b = ls[idx + 1]; idx += 2
        out.append(str(len(a) + len(b)))
    return "\n".join(out) + "\n"


def _gen_1473b(rng: random.Random) -> list[str]:
    cases = ["2\nab\nabab\nb\naba\n", "1\na\na\n"]
    for _ in range(12):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
        cases.append(f"1\n{s}\n{s}\n")
    return cases


# ─── 2179A Blackslex and Password ────────────────────────────────────────────


def _solve_2179a(s: str) -> int:
    n = len(s)
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            if s[i] == "b" and s[j] == "s":
                cnt += 1
    return cnt


def _s_2179a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        s = ls[idx]; idx += 1
        out.append(str(_solve_2179a(s)))
    return "\n".join(out) + "\n"


def _a_2179a(stdin: str) -> str:
    return _s_2179a(stdin)


def _m1_2179a(stdin: str) -> str:
    return "0\n"


def _m2_2179a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        s = ls[idx]; idx += 1
        out.append(str(s.count("b") * s.count("s")))
    return "\n".join(out) + "\n"


def _gen_2179a(rng: random.Random) -> list[str]:
    cases = ["2\nbs\nbbss\n3\nbbb\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        s = "".join(rng.choice("bs") for _ in range(n))
        cases.append(f"1\n{s}\n")
    return cases


# ─── 1927D Find the Different Ones! ──────────────────────────────────────────


def _solve_1927d(a: list[int], queries: list[tuple[int, int]]) -> list[int]:
    n = len(a)
    res = []
    for l, r in queries:
        ans = -1
        for i in range(l - 1, r - 1):
            if a[i] != a[i + 1]:
                ans = i + 1
                break
        res.append(ans)
    return res


def _s_1927d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out_all = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        q = int(ls[idx]); idx += 1
        qs = []
        for _ in range(q):
            l, r = map(int, ls[idx].split()); idx += 1
            qs.append((l, r))
        out_all.extend(map(str, _solve_1927d(a, qs)))
    return "\n".join(out_all) + "\n"


def _a_1927d(stdin: str) -> str:
    return _s_1927d(stdin)


def _m1_1927d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    cnt = 0
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        q = int(ls[idx]); idx += 1
        idx += q
        cnt += q
    return "\n".join(["-1"] * cnt) + "\n"


def _m2_1927d(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    cnt = 0
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        q = int(ls[idx]); idx += 1
        idx += q
        cnt += q
    return "\n".join(["1"] * cnt) + "\n"


def _gen_1927d(rng: random.Random) -> list[str]:
    cases = ["1\n5\n1 2 2 1 3\n2\n1 4\n2 5\n"]
    for _ in range(12):
        n = rng.randint(3, 8)
        a = [rng.randint(1, 5) for _ in range(n)]
        q = rng.randint(1, 3)
        qs = [f"{rng.randint(1, n)} {rng.randint(1, n)}" for _ in range(q)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + f"\n{q}\n" + "\n".join(qs) + "\n")
    return cases


# ─── 1793C Dora and Search ───────────────────────────────────────────────────


def _solve_1793c(a: list[int]) -> tuple[int, int]:
    n = len(a)
    mn_i = a.index(min(a))
    mx_i = a.index(max(a))
    if mn_i < mx_i:
        return mn_i + 1, mx_i + 1
    return mx_i + 1, mn_i + 1


def _s_1793c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        i, j = _solve_1793c(a)
        out.append(f"{i} {j}")
    return "\n".join(out) + "\n"


def _a_1793c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append("1 2")
    return "\n".join(out) + "\n"


def _m1_1793c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        out.append(f"{n} {n}")
    return "\n".join(out) + "\n"


def _m2_1793c(stdin: str) -> str:
    return "1 1\n"


def _gen_1793c(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 3\n4\n2 1 4 3\n"]
    for _ in range(12):
        n = rng.randint(3, 8)
        a = list(range(1, n + 1))
        rng.shuffle(a)
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 2123B Tournament ────────────────────────────────────────────────────────


def _solve_2123b(n: int, j: int, k: int, skills: list[int]) -> bool:
    target = skills[j - 1]
    stronger = sum(1 for x in skills if x > target)
    return stronger < k


def _s_2123b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, j, k = map(int, ls[idx].split()); idx += 1
        skills = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_solve_2123b(n, j, k, skills)).strip())
    return "\n".join(out) + "\n"


def _a_2123b(stdin: str) -> str:
    return _s_2123b(stdin)


def _m1_2123b(stdin: str) -> str:
    return "YES\n"


def _m2_2123b(stdin: str) -> str:
    return "NO\n"


def _gen_2123b(rng: random.Random) -> list[str]:
    cases = ["2\n4 3 2\n1 2 3 4\n4 2 2\n1 2 3 4\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        skills = [rng.randint(1, 20) for _ in range(n)]
        j = rng.randint(1, n)
        k = rng.randint(1, n)
        cases.append(f"1\n{n} {j} {k}\n" + " ".join(map(str, skills)) + "\n")
    return cases


# ─── 1676C Most Similar Words ────────────────────────────────────────────────


def _hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def _solve_1676c(words: list[str]) -> int:
    best = 10 ** 9
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            best = min(best, _hamming(words[i], words[j]))
    return best


def _s_1676c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split()); idx += 1
        words = [ls[idx + i] for i in range(n)]; idx += n
        out.append(str(_solve_1676c(words)))
    return "\n".join(out) + "\n"


def _a_1676c(stdin: str) -> str:
    return _s_1676c(stdin)


def _m1_1676c(stdin: str) -> str:
    return "0\n"


def _m2_1676c(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split()); idx += 1
        idx += n
        out.append(str(m))
    return "\n".join(out) + "\n"


def _gen_1676c(rng: random.Random) -> list[str]:
    cases = ["1\n3 4\nbest\nsame\ncase\n"]
    for _ in range(12):
        n, m = rng.randint(2, 5), rng.randint(3, 6)
        words = ["".join(rng.choice("abc") for _ in range(m)) for _ in range(n)]
        cases.append(f"1\n{n} {m}\n" + "\n".join(words) + "\n")
    return cases


# ─── 1665B Array Cloning Technique ───────────────────────────────────────────


def _solve_1665b(a: list[int]) -> int:
    from collections import Counter
    c = Counter(a)
    mx = max(c.values())
    n = len(a)
    return n - mx + max(0, mx - 1)


def _s_1665b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1665b(a)))
    return "\n".join(out) + "\n"


def _a_1665b(stdin: str) -> str:
    return _s_1665b(stdin)


def _m1_1665b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1665b(stdin: str) -> str:
    return "0\n"


def _gen_1665b(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 2 3\n4\n1 1 1 1\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        a = [rng.randint(1, 5) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 34A Reconnaissance 2 ────────────────────────────────────────────────────


def _solve_34a(a: list[int]) -> int:
    n = len(a)
    best = 10 ** 9
    for i in range(n):
        d = min(abs(a[i] - a[(i + 1) % n]), abs(a[i] - a[(i - 1) % n]))
        best = min(best, d)
    return best


def _s_34a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    return str(_solve_34a(a)) + "\n"


def _a_34a(stdin: str) -> str:
    return _s_34a(stdin)


def _m1_34a(stdin: str) -> str:
    a = list(map(int, lines(stdin)[1].split()))
    return str(max(a) - min(a)) + "\n"


def _m2_34a(stdin: str) -> str:
    return "0\n"


def _gen_34a(rng: random.Random) -> list[str]:
    cases = ["4\n1 10 8 3\n", "3\n1 2 3\n"]
    for _ in range(12):
        n = rng.randint(3, 10)
        a = [rng.randint(1, 100) for _ in range(n)]
        cases.append(f"{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1941B Rudolf and 121 ────────────────────────────────────────────────────


def _solve_1941b(n: int, a: list[int]) -> int:
    ops = 0
    b = a[:]
    for i in range(n - 2):
        if b[i] == 0 and b[i + 1] == 0 and b[i + 2] == 0:
            b[i] = b[i + 1] = b[i + 2] = 1
            ops += 1
    if any(x == 0 for x in b):
        return -1
    return ops


def _s_1941b(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1941b(n, a)))
    return "\n".join(out) + "\n"


def _a_1941b(stdin: str) -> str:
    return _s_1941b(stdin)


def _m1_1941b(stdin: str) -> str:
    return "-1\n"


def _m2_1941b(stdin: str) -> str:
    return "0\n"


def _gen_1941b(rng: random.Random) -> list[str]:
    cases = ["2\n3\n0 0 0\n4\n1 0 1 0\n"]
    for _ in range(12):
        n = rng.randint(3, 10)
        a = [rng.randint(0, 1) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1929A Sasha and the Beautiful Array ─────────────────────────────────────


def _solve_1929a(a: list[int]) -> int:
    cost = 0
    for i in range(1, len(a)):
        if a[i] <= a[i - 1]:
            need = a[i - 1] + 1 - a[i]
            cost += need
            a[i] += need
    return cost


def _s_1929a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1929a(a)))
    return "\n".join(out) + "\n"


def _a_1929a(stdin: str) -> str:
    return _s_1929a(stdin)


def _m1_1929a(stdin: str) -> str:
    return "0\n"


def _m2_1929a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def _gen_1929a(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 1 1\n4\n1 3 2 4\n"]
    for _ in range(12):
        n = rng.randint(2, 8)
        a = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1833A Musical Puzzle ────────────────────────────────────────────────────


def _solve_1833a(a: list[int]) -> int:
    seen = set()
    for i in range(len(a) - 1):
        seen.add((a[i], a[i + 1]))
    return len(seen)


def _s_1833a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_solve_1833a(a)))
    return "\n".join(out) + "\n"


def _a_1833a(stdin: str) -> str:
    return _s_1833a(stdin)


def _m1_1833a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += 1
        out.append(str(n - 1))
    return "\n".join(out) + "\n"


def _m2_1833a(stdin: str) -> str:
    return "1\n"


def _gen_1833a(rng: random.Random) -> list[str]:
    cases = ["2\n4\n1 2 2 1\n3\n1 2 3\n"]
    for _ in range(12):
        n = rng.randint(2, 10)
        a = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1485A Add and Divide ────────────────────────────────────────────────────


def _solve_1485a(a: int, b: int, d: int) -> int:
    if a % d == 0:
        return 0
    x = a
    for ops in range(1, 10001):
        if x % d == 0:
            return ops
        x += b
    return ops


def _s_1485a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a, b, d = map(int, ls[idx].split()); idx += 1
        out.append(str(_solve_1485a(a, b, d)))
    return "\n".join(out) + "\n"


def _a_1485a(stdin: str) -> str:
    ls = lines(stdin)
    t, idx = int(ls[0]), 1
    out = []
    for _ in range(t):
        a, b, d = map(int, ls[idx].split()); idx += 1
        if a % d == 0:
            out.append("0")
        else:
            x = a
            ops = 0
            for _ in range(10001):
                if x % d == 0:
                    break
                x += b
                ops += 1
            out.append(str(ops))
    return "\n".join(out) + "\n"


def _m1_1485a(stdin: str) -> str:
    return "1\n"


def _m2_1485a(stdin: str) -> str:
    return "0\n"


def _gen_1485a(rng: random.Random) -> list[str]:
    cases = ["3\n6 4 2\n7 3 2\n10 5 3\n"]
    for _ in range(12):
        d = rng.randint(2, 5)
        b = rng.randint(1, 5)
        a = d * rng.randint(1, 5) + rng.randint(0, min(b, d) - 1)
        cases.append(f"1\n{a} {b} {d}\n")
    return cases


# ─── 118B Present from Lena ──────────────────────────────────────────────────


def _solve_118b(n: int) -> str:
    rows = []
    for i in range(n + 1):
        row = []
        c = 1
        for j in range(i + 1):
            row.append(str(c))
            c = c * (i - j) // (j + 1)
        rows.append(" ".join(row))
    return "\n".join(rows) + "\n"


def _s_118b(stdin: str) -> str:
    return _solve_118b(int(lines(stdin)[0].strip()))


def _a_118b(stdin: str) -> str:
    return _s_118b(stdin)


def _m1_118b(stdin: str) -> str:
    n = int(lines(stdin)[0].strip())
    return "\n".join(["1"] * (n + 1)) + "\n"


def _m2_118b(stdin: str) -> str:
    n = int(lines(stdin)[0].strip())
    return str(n) + "\n"


def _gen_118b(rng: random.Random) -> list[str]:
    return [f"{n}\n" for n in range(1, 13)]


# ─── 766A Mahmoud and Longest Uncommon Subsequence ────────────────────────────


def _solve_766a(s: str, t: str) -> int:
    if s == t:
        return 0
    if s in t or t in s:
        return max(len(s), len(t))
    return max(len(s), len(t))


def _s_766a(stdin: str) -> str:
    ls = lines(stdin)
    return str(_solve_766a(ls[0], ls[1])) + "\n"


def _a_766a(stdin: str) -> str:
    return _s_766a(stdin)


def _m1_766a(stdin: str) -> str:
    ls = lines(stdin)
    return str(len(ls[0])) + "\n"


def _m2_766a(stdin: str) -> str:
    return "0\n"


def _gen_766a(rng: random.Random) -> list[str]:
    cases = ["aba\naba\n", "abc\ndef\n", "abcd\nbcd\n", "a\naa\n"]
    for _ in range(12):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(1, 5)))
        t = "".join(rng.choice("abc") for _ in range(rng.randint(1, 5)))
        cases.append(f"{s}\n{t}\n")
    return cases


def _build() -> list:
    specs = []

    def add(problem_id, summary, samples, solve, alt, mutants, generate, **kw):
        specs.append(
            make_spec(
                problem_id,
                summary=summary,
                samples=samples,
                solve=solve,
                alt=alt,
                mutants=mutants,
                generate=generate,
                **kw,
            )
        )

    add("1186A", "YES if both m and k are at least n.", ({"input": '2\n5 8 6\n8 5 20\n', "output": 'Yes\nNo\n'},), _s_1186a, _a_1186a, {"wrong1": _m1_1186a, "wrong2": _m2_1186a}, _gen_1186a, family="math", checker="tokens_ci")
    add("2162A", "Max sum of two even elements or -1.", ({"input": '2\n3\n1 2 3\n2\n2 4\n', "output": '-1\n6\n'},), _s_2162a, _a_2162a, {"wrong1": _m1_2162a, "wrong2": _m2_2162a}, _gen_2162a, family="brute_force", checker="exact")
    add("1380A", "Exists i<j<k with a[i]<a[j]<a[k].", ({"input": '2\n3\n1 2 3\n2\n1 1\n', "output": 'YES\nNO\n'},), _s_1380a, _a_1380a, {"wrong1": _m1_1380a, "wrong2": _m2_1380a}, _gen_1380a, family="brute_force", checker="tokens_ci")
    add("1527A", "Max k with n AND k AND ... AND k equals zero.", ({"input": '4\n2\n5\n17\n3\n', "output": '1\n3\n15\n1\n'},), _s_1527a, _a_1527a, {"wrong1": _m1_1527a, "wrong2": _m2_1527a}, _gen_1527a, family="bitmasks", checker="exact")
    add("1474B", "Smallest x>=d with exactly four divisors.", ({"input": '2\n1\n4\n', "output": '6\n6\n'},), _s_1474b, _a_1474b, {"wrong1": _m1_1474b, "wrong2": _m2_1474b}, _gen_1474b, family="number_theory", checker="exact")
    add("2149A", "Min ops to make all positive using -1/0/1.", ({"input": '1\n3\n-1 0 1\n', "output": '3\n'},), _s_2149a, _a_2149a, {"wrong1": _m1_2149a, "wrong2": _m2_2149a}, _gen_2149a, family="math", checker="exact")
    add("1999B", "Sasha wins card game with first-player ties.", ({"input": '2\n1\n1\n1\n2\n1 2\n2 1\n', "output": 'NO\nYES\n'},), _s_1999b, _a_1999b, {"wrong1": _m1_1999b, "wrong2": _m2_1999b}, _gen_1999b, family="games", checker="tokens_ci")
    add("1521A", "Smallest x>=n with gcd(x,n)>1 and gcd(x+1,m)>1.", ({"input": '1\n3 11\n', "output": '21\n'},), _s_1521a, _a_1521a, {"wrong1": _m1_1521a, "wrong2": _m2_1521a}, _gen_1521a, family="number_theory", checker="exact")
    add("1914C", "Max quest level with coin and stamina limits.", ({"input": '1\n100 50 2 1\n', "output": '50\n'},), _s_1914c, _a_1914c, {"wrong1": _m1_1914c, "wrong2": _m2_1914c}, _gen_1914c, family="greedy", checker="exact")
    add("1692C", "Find bishop position from diagonal footprint.", ({"input": '1\n........\n........\n...#.#..\n....#...\n...#.#..\n........\n........\n........\n', "output": '4 5\n'},), _s_1692c, _a_1692c, {"wrong1": _m1_1692c, "wrong2": _m2_1692c}, _gen_1692c, family="grid", checker="exact")
    add("1927B", "Reconstruct string from trace counts.", ({"input": '1\n11\n0 0 0 1 0 2 0 3 1 1 4\n', "output": 'abcadaeabca\n'},), _s_1927b, _a_1927b, {"wrong1": _m1_1927b, "wrong2": _m2_1927b}, _gen_1927b, family="greedy", checker="exact")
    add("476B", "Probability Dreamoon reaches intended WiFi position.", ({"input": '++-+-\n+-+-+\n', "output": '1.000000000\n'},), _s_476b, _a_476b, {"wrong1": _m1_476b, "wrong2": _m2_476b}, _gen_476b, family="combinatorics", checker="exact")
    add("1097B", "YES if +/- angle assignment sums to multiple of 360.", ({"input": '3\n120\n120\n120\n', "output": 'YES\n'},), _s_1097b, _a_1097b, {"wrong1": _m1_1097b, "wrong2": _m2_1097b}, _gen_1097b, family="bitmask", checker="tokens_ci")
    add("1933B", "Remove one digit so remaining sum divisible by 3.", ({"input": '2\n3\n123\n3\n111\n', "output": 'YES\nYES\n'},), _s_1933b, _a_1933b, {"wrong1": _m1_1933b, "wrong2": _m2_1933b}, _gen_1933b, family="math", checker="tokens_ci")
    add("1915E", "Exists segment with equal odd/even position sums.", ({"input": '1\n4\n1 1 1 1\n', "output": 'YES\n'},), _s_1915e, _a_1915e, {"wrong1": _m1_1915e, "wrong2": _m2_1915e}, _gen_1915e, family="prefix_sum", checker="tokens_ci")
    add("1722C", "Max word chain where last char equals next first.", ({"input": '1\n3\nabc\nbcd\ncde\n', "output": '3\n'},), _s_1722c, _a_1722c, {"wrong1": _m1_1722c, "wrong2": _m2_1722c}, _gen_1722c, family="greedy", checker="exact")
    add("1462C", "Build largest number from digit counts or -1.", ({"input": '1\n0\n0 0 0 0 0 0 0 0 0 1\n', "output": '0\n'},), _s_1462c, _a_1462c, {"wrong1": _m1_1462c, "wrong2": _m2_1462c}, _gen_1462c, family="constructive", checker="exact")
    add("1832C", "Max contrast after removing one maximum element.", ({"input": '1\n3\n1 2 3\n', "output": '1\n'},), _s_1832c, _a_1832c, {"wrong1": _m1_1832c, "wrong2": _m2_1832c}, _gen_1832c, family="greedy", checker="exact")
    add("459A", "Count cells in union of two rectangles on n x n grid.", ({"input": '100\n1 1 5 5\n3 3 8 8\n', "output": '46\n'},), _s_459a, _a_459a, {"wrong1": _m1_459a, "wrong2": _m2_459a}, _gen_459a, family="geometry", checker="exact")
    add("2050A", "Fit words on k lines of width x.", ({"input": '1\n3 10\ncodeforces\n', "output": 'YES\n'},), _s_2050a, _a_2050a, {"wrong1": _m1_2050a, "wrong2": _m2_2050a}, _gen_2050a, family="greedy", checker="tokens_ci")
    add("1514B", "Count arrays length k with AND zero: n^k mod 1e9+7.", ({"input": '1\n2 2\n', "output": '4\n'},), _s_1514b, _a_1514b, {"wrong1": _m1_1514b, "wrong2": _m2_1514b}, _gen_1514b, family="math", checker="exact")
    add("1921B", "Min swaps to equalize two binary strings.", ({"input": '1\n4\n0011\n1100\n', "output": '2\n'},), _s_1921b, _a_1921b, {"wrong1": _m1_1921b, "wrong2": _m2_1921b}, _gen_1921b, family="greedy", checker="exact")
    add("1862A", "Spell Vanya on snake carpet grid.", ({"input": '1\n3 3\naeb\nbcd\ncea\nabcde\n', "output": 'YES\n'},), _s_1862a, _a_1862a, {"wrong1": _m1_1862a, "wrong2": _m2_1862a}, _gen_1862a, family="strings", checker="tokens_ci")
    add("1421A", "Min XOR operations to make a equal b.", ({"input": '2\n1 1\n3 4\n', "output": '0\n1\n'},), _s_1421a, _a_1421a, {"wrong1": _m1_1421a, "wrong2": _m2_1421a}, _gen_1421a, family="bitmasks", checker="exact")
    add("1789A", "Exists pair whose gcd is in the array.", ({"input": '1\n3\n2 4 6\n', "output": 'YES\n'},), _s_1789a, _a_1789a, {"wrong1": _m1_1789a, "wrong2": _m2_1789a}, _gen_1789a, family="number_theory", checker="tokens_ci")
    add("1919A", "Wallet exchange game: (a+b) even.", ({"input": '2\n1 1\n2 3\n', "output": 'YES\nNO\n'},), _s_1919a, _a_1919a, {"wrong1": _m1_1919a, "wrong2": _m2_1919a}, _gen_1919a, family="games", checker="tokens_ci")
    add("2137A", "Reach y from x via Collatz steps.", ({"input": '2\n3 3\n7 2\n', "output": 'YES\nNO\n'},), _s_2137a, _a_2137a, {"wrong1": _m1_2137a, "wrong2": _m2_2137a}, _gen_2137a, family="math", checker="tokens_ci")
    add("688B", "Smallest palindrome >= n as string.", ({"input": '808\n', "output": '818\n'},), _s_688b, _a_688b, {"wrong1": _m1_688b, "wrong2": _m2_688b}, _gen_688b, family="constructive", checker="exact")
    add("567A", "Min and max mail delivery distances on line.", ({"input": '4\n-3 5 1 2\n', "output": '2 5\n2 5\n1 4\n1 4\n'},), _s_567a, _a_567a, {"wrong1": _m1_567a, "wrong2": _m2_567a}, _gen_567a, family="greedy", checker="exact")
    add("1633A", "Change one digit to divisible by 7 or -1.", ({"input": '1\n105\n', "output": '105\n'},), _s_1633a, _a_1633a, {"wrong1": _m1_1633a, "wrong2": _m2_1633a}, _gen_1633a, family="brute_force", checker="exact")
    add("2037A", "Max pairs from equal elements.", ({"input": '1\n5\n1 2 3 2 1\n', "output": '2\n'},), _s_2037a, _a_2037a, {"wrong1": _m1_2037a, "wrong2": _m2_2037a}, _gen_2037a, family="counting", checker="exact")
    add("1362A", "Double smaller until equal; count ops.", ({"input": '1\n3 6\n', "output": '1\n'},), _s_1362a, _a_1362a, {"wrong1": _m1_1362a, "wrong2": _m2_1362a}, _gen_1362a, family="simulation", checker="exact")
    add("1716A", "Min moves using 2 and 3 steps.", ({"input": '4\n1\n2\n4\n6\n', "output": '2\n1\n2\n2\n'},), _s_1716a, _a_1716a, {"wrong1": _m1_1716a, "wrong2": _m2_1716a}, _gen_1716a, family="math", checker="exact")
    add("268B", "Buttons on n layers simulation.", ({"input": '3\n', "output": '11\n'},), _s_268b, _a_268b, {"wrong1": _m1_268b, "wrong2": _m2_268b}, _gen_268b, family="math", checker="exact")
    add("1742D", "Count coprime pairs in array.", ({"input": '1\n3\n1 2 3\n', "output": '2\n'},), _s_1742d, _a_1742d, {"wrong1": _m1_1742d, "wrong2": _m2_1742d}, _gen_1742d, family="number_theory", checker="exact")
    add("1527B1", "Alice wins easy palindrome game.", ({"input": '2\n1\na\n2\nab\n', "output": 'YES\nNO\n'},), _s_1527b1, _a_1527b1, {"wrong1": _m1_1527b1, "wrong2": _m2_1527b1}, _gen_1527b1, family="games", checker="tokens_ci")
    add("1418A", "Min sticks to buy torches for r nights.", ({"input": '1\n8 1 1 1 1\n', "output": '7\n'},), _s_1418a, _a_1418a, {"wrong1": _m1_1418a, "wrong2": _m2_1418a}, _gen_1418a, family="simulation", checker="exact")
    add("1182A", "Ways to tile 2xn board with 2x1 and 2x2.", ({"input": '4\n', "output": '2\n'},), _s_1182a, _a_1182a, {"wrong1": _m1_1182a, "wrong2": _m2_1182a}, _gen_1182a, family="dp", checker="exact")
    add("1791G1", "Min teleporter cost easy version.", ({"input": '1\n3\n1 2 3\n1 2 3\n', "output": '3\n'},), _s_1791g1, _a_1791g1, {"wrong1": _m1_1791g1, "wrong2": _m2_1791g1}, _gen_1791g1, family="greedy", checker="exact")
    add("1472C", "Max jumps in long jump game.", ({"input": '1\n4\n2 1 1 1\n', "output": '3\n'},), _s_1472c, _a_1472c, {"wrong1": _m1_1472c, "wrong2": _m2_1472c}, _gen_1472c, family="dp", checker="exact")
    add("1582B", "Count non-empty subsequences with at least one 1.", ({"input": '1\n3\n1 0 1\n', "output": '6\n'},), _s_1582b, _a_1582b, {"wrong1": _m1_1582b, "wrong2": _m2_1582b}, _gen_1582b, family="combinatorics", checker="exact")
    add("1715B", "Min insertions for beautiful array.", ({"input": '1\n3 2\n3\n1 1 1\n', "output": '3\n'},), _s_1715b, _a_1715b, {"wrong1": _m1_1715b, "wrong2": _m2_1715b}, _gen_1715b, family="math", checker="exact")
    add("1549A", "Find x with p*x ≡ e mod m.", ({"input": '1\n2 3 5 4\n', "output": '2\n'},), _s_1549a, _a_1549a, {"wrong1": _m1_1549a, "wrong2": _m2_1549a}, _gen_1549a, family="math", checker="exact")
    add("1354B", "Min subarray containing 0,1,2.", ({"input": '1\n6\n012012\n', "output": '3\n'},), _s_1354b, _a_1354b, {"wrong1": _m1_1354b, "wrong2": _m2_1354b}, _gen_1354b, family="sliding_window", checker="exact")
    add("1690A", "Print pedestal heights h1 h2 h3.", ({"input": '1\n6\n', "output": '2 3 1\n'},), _s_1690a, _a_1690a, {"wrong1": _m1_1690a, "wrong2": _m2_1690a}, _gen_1690a, family="constructive", checker="tokens")
    add("1692E", "Max sum subarray of length k.", ({"input": '1\n5 2\n1 0 1 0 1\n', "output": '2\n'},), _s_1692e, _a_1692e, {"wrong1": _m1_1692e, "wrong2": _m2_1692e}, _gen_1692e, family="sliding_window", checker="exact")
    add("1538C", "Count pairs with sum in [l,r].", ({"input": '5 1\n1 2 3 4 5\n1 10\n', "output": '10\n'},), _s_1538c, _a_1538c, {"wrong1": _m1_1538c, "wrong2": _m2_1538c}, _gen_1538c, family="two_pointer", checker="exact")
    add("1899B", "Max product of left and right segment sums.", ({"input": '1\n3\n1 2 3\n', "output": '9\n'},), _s_1899b, _a_1899b, {"wrong1": _m1_1899b, "wrong2": _m2_1899b}, _gen_1899b, family="brute_force", checker="exact")
    add("1931B", "Make all equal by doubling only.", ({"input": '1\n3\n1 2 4\n', "output": 'YES\n'},), _s_1931b, _a_1931b, {"wrong1": _m1_1931b, "wrong2": _m2_1931b}, _gen_1931b, family="math", checker="tokens_ci")
    add("1915D", "Min palindrome partition count.", ({"input": '1\n4\nabba\n', "output": '1\n'},), _s_1915d, _a_1915d, {"wrong1": _m1_1915d, "wrong2": _m2_1915d}, _gen_1915d, family="greedy", checker="exact")
    add("540A", "Combination lock rotation distance sum.", ({"input": '3\n010\n909\n', "output": '6\n'},), _s_540a, _a_540a, {"wrong1": _m1_540a, "wrong2": _m2_540a}, _gen_540a, family="implementation", checker="exact")
    add("1914A", "Max problem number solved from log.", ({"input": '1\n4\nABBC\n', "output": '2\n'},), _s_1914a, _a_1914a, {"wrong1": _m1_1914a, "wrong2": _m2_1914a}, _gen_1914a, family="strings", checker="exact")
    add("2051A", "Min days to solve n problems.", ({"input": '1\n10 2 3\n', "output": '4\n'},), _s_2051a, _a_2051a, {"wrong1": _m1_2051a, "wrong2": _m2_2051a}, _gen_2051a, family="greedy", checker="exact")
    add("1473B", "Length of string lcm or -1.", ({"input": '1\nab\nabab\n', "output": '4\n'},), _s_1473b, _a_1473b, {"wrong1": _m1_1473b, "wrong2": _m2_1473b}, _gen_1473b, family="strings", checker="exact")
    add("2179A", "Count bs before s pairs in string.", ({"input": '1\nbbss\n', "output": '4\n'},), _s_2179a, _a_2179a, {"wrong1": _m1_2179a, "wrong2": _m2_2179a}, _gen_2179a, family="counting", checker="exact")
    add("1927D", "First index with different neighbor in range.", ({"input": '1\n5\n1 2 2 1 3\n1\n1 4\n', "output": '1\n'},), _s_1927d, _a_1927d, {"wrong1": _m1_1927d, "wrong2": _m2_1927d}, _gen_1927d, family="brute_force", checker="exact")
    add("1793C", "Remove one element for unique min and max.", ({"input": '1\n3\n1 2 3\n', "output": '1 3\n'},), _s_1793c, _a_1793c, {"wrong1": _m1_1793c, "wrong2": _m2_1793c}, _gen_1793c, family="constructive", checker="tokens")
    add("2123B", "Can player j win tournament with k losses.", ({"input": '1\n4 3 2\n1 2 3 4\n', "output": 'YES\n'},), _s_2123b, _a_2123b, {"wrong1": _m1_2123b, "wrong2": _m2_2123b}, _gen_2123b, family="greedy", checker="tokens_ci")
    add("1676C", "Min hamming distance between words.", ({"input": '1\n3 4\nbest\nsame\ncase\n', "output": '3\n'},), _s_1676c, _a_1676c, {"wrong1": _m1_1676c, "wrong2": _m2_1676c}, _gen_1676c, family="strings", checker="exact")
    add("1665B", "Min ops to clone array to all equal.", ({"input": '1\n4\n1 1 1 1\n', "output": '3\n'},), _s_1665b, _a_1665b, {"wrong1": _m1_1665b, "wrong2": _m2_1665b}, _gen_1665b, family="greedy", checker="exact")
    add("34A", "Min circular distance between two soldiers.", ({"input": '4\n1 10 8 3\n', "output": '2\n'},), _s_34a, _a_34a, {"wrong1": _m1_34a, "wrong2": _m2_34a}, _gen_34a, family="implementation", checker="exact")
    add("1941B", "Min ops to build 1,2,1 pattern.", ({"input": '1\n3\n0 0 0\n', "output": '1\n'},), _s_1941b, _a_1941b, {"wrong1": _m1_1941b, "wrong2": _m2_1941b}, _gen_1941b, family="greedy", checker="exact")
    add("1929A", "Min cost to make array strictly increasing.", ({"input": '1\n3\n1 1 1\n', "output": '2\n'},), _s_1929a, _a_1929a, {"wrong1": _m1_1929a, "wrong2": _m2_1929a}, _gen_1929a, family="greedy", checker="exact")
    add("1833A", "Count distinct adjacent pairs.", ({"input": '1\n4\n1 2 2 1\n', "output": '2\n'},), _s_1833a, _a_1833a, {"wrong1": _m1_1833a, "wrong2": _m2_1833a}, _gen_1833a, family="counting", checker="exact")
    add("1485A", "Min ops add b until divisible by d.", ({"input": '1\n6 4 2\n', "output": '1\n'},), _s_1485a, _a_1485a, {"wrong1": _m1_1485a, "wrong2": _m2_1485a}, _gen_1485a, family="math", checker="exact")
    add("118B", "Pascal triangle pyramid output.", ({"input": '2\n', "output": '1\n1 1\n'},), _s_118b, _a_118b, {"wrong1": _m1_118b, "wrong2": _m2_118b}, _gen_118b, family="constructive", checker="exact")
    add("766A", "Longest uncommon subsequence length.", ({"input": 'aba\naba\n', "output": '0\n'},), _s_766a, _a_766a, {"wrong1": _m1_766a, "wrong2": _m2_766a}, _gen_766a, family="strings", checker="exact")

    return specs


SPECS = _build()

_KEEP = ['1186A', '2162A', '1380A', '1527A', '1474B', '2149A', '1521A', '1914C', '1692C', '1927B', '1933B', '1915E', '1832C', '2050A', '1514B', '1921B', '1421A', '1789A', '1919A', '2037A', '1362A', '1716A', '268B', '1418A', '1182A', '1582B', '1715B', '1549A', '1690A', '1538C', '1899B', '2179A', '1927D', '2123B', '1665B', '34A', '1941B', '766A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
