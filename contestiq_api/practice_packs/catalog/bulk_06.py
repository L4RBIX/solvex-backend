"""Dual-oracle ProblemOracleSpec entries generated from catalog/batches/batch_06.json.

Skipped from batch_06 (non-unique / constructive / "print any" answers that a
simple exact/tokens checker cannot fairly grade):
  - 2218A (any y maximizing min(x,y) -- infinitely many valid outputs)
  - 1907A (rook targets -- valid line order is judge-defined / any order)
  - 1968A (any y maximizing gcd(x,y)+y -- multiple valid outputs)
"""

from __future__ import annotations

import math
import random
from functools import reduce

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

PI_DIGITS = "314159265358979323846264338327950288419716939937510"


# ─── 1933A Turtle Puzzle: Rearrange and Negate ──────────────────────────────


def _s_1933a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(sum(abs(x) for x in a)))
    return "\n".join(out) + "\n"


def _a_1933a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        pos = sum(x for x in a if x >= 0)
        neg = -sum(x for x in a if x < 0)
        out.append(str(pos + neg))
    return "\n".join(out) + "\n"


def _m1_1933a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def _m2_1933a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        m = min(a)
        out.append(str(sum(a) - 2 * m if m < 0 else sum(a)))
    return "\n".join(out) + "\n"


def _gen_1933a(rng: random.Random) -> list[str]:
    cases = [
        "6\n3\n3 -2 -3\n3\n0 0 0\n2\n0 1\n1\n-99\n4\n10 -2 -3 7\n5\n-1 -2 -3 -4 -5\n"
    ]
    for _ in range(9):
        n = rng.randint(1, 8)
        vals = [rng.randint(-100, 100) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 1579A Casimir's String Solitaire ───────────────────────────────────────


def _s_1579a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(yes_no(s.count("B") * 2 == len(s)))
    return "".join(out)


def _a_1579a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        a = s.count("A")
        b = s.count("B")
        c = s.count("C")
        out.append(yes_no(a + c == b))
    return "".join(out)


def _m1_1579a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(yes_no(s.count("A") == s.count("C")))
    return "".join(out)


def _m2_1579a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(yes_no(len(s) % 2 == 0))
    return "".join(out)


def _gen_1579a(rng: random.Random) -> list[str]:
    cases = ["6\nABACAB\nABBA\nAC\nABC\nCABCBB\nBCBCBCBCBCBCBCBC\n"]
    for _ in range(9):
        n = rng.randint(1, 15)
        s = "".join(rng.choice("ABC") for _ in range(n))
        cases.append(f"1\n{s}\n")
    return cases


# ─── 1669F Eating Candies ────────────────────────────────────────────────────


def _s_1669f(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        i, j = 0, n - 1
        si = sj = 0
        ans = 0
        while i <= j:
            if si < sj:
                si += a[i]
                i += 1
            elif sj < si:
                sj += a[j]
                j -= 1
            else:
                ans = max(ans, i + (n - 1 - j))
                si += a[i]
                i += 1
        if si == sj:
            ans = max(ans, i + (n - 1 - j))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1669f(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        prefix: dict[int, int] = {0: 0}
        s = 0
        for k in range(n):
            s += a[k]
            if s not in prefix:
                prefix[s] = k + 1
        best = 0
        cursum = 0
        for j in range(0, n + 1):
            if j > 0:
                cursum += a[n - j]
            if cursum in prefix:
                i = prefix[cursum]
                if i + j <= n:
                    best = max(best, i + j)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1669f(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        i, j = 0, n - 1
        si = sj = 0
        while i <= j:
            if si < sj:
                si += a[i]
                i += 1
            elif sj < si:
                sj += a[j]
                j -= 1
            else:
                si += a[i]
                i += 1
        out.append(str(i))
    return "\n".join(out) + "\n"


def _m2_1669f(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        i, j = 0, n - 1
        si = sj = 0
        ans = 0
        while i <= j:
            if si < sj:
                si += a[i]
                i += 1
            elif sj < si:
                sj += a[j]
                j -= 1
            else:
                ans = max(ans, i + (n - j))
                si += a[i]
                i += 1
        if si == sj:
            ans = max(ans, i + (n - j))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1669f(rng: random.Random) -> list[str]:
    cases = ["1\n8\n1 2 1 3 6 2 5 1\n"]
    for _ in range(11):
        n = rng.randint(1, 12)
        vals = [rng.randint(1, 8) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 1971C Clock and Strings ─────────────────────────────────────────────────


def _s_1971c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, ls[i].split())
        s = ""
        for k in range(1, 13):
            if k == a or k == b:
                s += "a"
            if k == c or k == d:
                s += "b"
        out.append(yes_no(s in ("abab", "baba")))
    return "".join(out)


def _a_1971c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, ls[i].split())

        def between(x: int, lo: int, hi: int) -> bool:
            lo0, hi0, x0 = lo % 12, hi % 12, x % 12
            if lo0 < hi0:
                return lo0 < x0 < hi0
            return x0 > lo0 or x0 < hi0

        cnt = int(between(c, a, b)) + int(between(d, a, b))
        out.append(yes_no(cnt == 1))
    return "".join(out)


def _m1_1971c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, ls[i].split())
        s = ""
        for k in range(1, 13):
            if k == a or k == c:
                s += "a"
            if k == b or k == d:
                s += "b"
        out.append(yes_no(s in ("abab", "baba")))
    return "".join(out)


def _m2_1971c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, ls[i].split())
        s = ""
        for k in range(1, 13):
            if k == a or k == b:
                s += "a"
            if k == c or k == d:
                s += "b"
        out.append(yes_no(s in ("abab", "baba", "abba", "baab")))
    return "".join(out)


def _gen_1971c(rng: random.Random) -> list[str]:
    cases = ["4\n2 9 10 6\n3 8 9 11\n2 3 4 5\n3 4 12 1\n"]
    for _ in range(11):
        vals = rng.sample(range(1, 13), 4)
        cases.append("1\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 2123A Blackboard Game ──────────────────────────────────────────────────


def _s_2123a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append("Bob\n" if n % 4 == 0 else "Alice\n")
    return "".join(out)


def _a_2123a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        cnt = [0, 0, 0, 0]
        for v in range(n):
            cnt[v % 4] += 1
        out.append("Bob\n" if cnt[0] == cnt[3] and cnt[1] == cnt[2] else "Alice\n")
    return "".join(out)


def _m1_2123a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append("Bob\n" if n % 4 != 0 else "Alice\n")
    return "".join(out)


def _m2_2123a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append("Bob\n" if n % 2 == 0 else "Alice\n")
    return "".join(out)


def _gen_2123a(rng: random.Random) -> list[str]:
    cases = ["5\n2\n4\n5\n7\n100\n"]
    for _ in range(11):
        n = rng.randint(1, 100)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 1828B Permutation Swap ─────────────────────────────────────────────────


def _s_1828b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        p = list(map(int, ls[idx].split()))
        idx += 1
        res = 0
        for i in range(1, n + 1):
            res = math.gcd(res, abs(p[i - 1] - i))
        out.append(str(res))
    return "\n".join(out) + "\n"


def _a_1828b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        p = list(map(int, ls[idx].split()))
        idx += 1
        diffs = [abs(p[i] - (i + 1)) for i in range(n)]
        res = reduce(math.gcd, diffs, 0)
        out.append(str(res))
    return "\n".join(out) + "\n"


def _m1_1828b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        p = list(map(int, ls[idx].split()))
        idx += 1
        res = 0
        for i in range(1, n // 2 + 1):
            res = math.gcd(res, abs(p[i - 1] - i))
        out.append(str(res))
    return "\n".join(out) + "\n"


def _m2_1828b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        p = list(map(int, ls[idx].split()))
        idx += 1
        res = 0
        for i in range(1, n + 1):
            res = math.gcd(res, abs(p[i - 1] - (i + 1)))
        out.append(str(res))
    return "\n".join(out) + "\n"


def _gen_1828b(rng: random.Random) -> list[str]:
    cases = ["2\n3\n1 3 2\n4\n4 2 3 1\n"]
    for _ in range(11):
        n = rng.randint(2, 10)
        p = list(range(1, n + 1))
        rng.shuffle(p)
        if p == list(range(1, n + 1)):
            p[0], p[1] = p[1], p[0]
        cases.append(f"1\n{n}\n" + " ".join(map(str, p)) + "\n")
    return cases


# ─── 2008A Sakurako's Exam ──────────────────────────────────────────────────


def _s_2008a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        if a % 2 == 1:
            ok = False
        elif b % 2 == 0:
            ok = True
        else:
            ok = a != 0
        out.append(yes_no(ok))
    return "".join(out)


def _a_2008a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        ok = (a % 2 == 0) and ((b % 2 == 0) or (a >= 2))
        out.append(yes_no(ok))
    return "".join(out)


def _m1_2008a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        out.append(yes_no(a % 2 == 0))
    return "".join(out)


def _m2_2008a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        out.append(yes_no(b % 2 == 0))
    return "".join(out)


def _gen_2008a(rng: random.Random) -> list[str]:
    cases = ["4\n0 1\n0 3\n2 0\n2 3\n"]
    for _ in range(11):
        a = rng.randint(0, 9)
        b = rng.randint(0, 9)
        cases.append(f"1\n{a} {b}\n")
    return cases


# ─── 1669C Odd/Even Increments ──────────────────────────────────────────────


def _s_1669c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        even_ok = all(x % 2 == a[0] % 2 for x in a[0::2])
        odd_ok = len(a) < 2 or all(x % 2 == a[1] % 2 for x in a[1::2])
        out.append(yes_no(even_ok and odd_ok))
    return "".join(out)


def _a_1669c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        g1 = {x % 2 for x in a[0::2]}
        g2 = {x % 2 for x in a[1::2]}
        out.append(yes_no(len(g1) <= 1 and len(g2) <= 1))
    return "".join(out)


def _m1_1669c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(yes_no(len({x % 2 for x in a}) <= 1))
    return "".join(out)


def _m2_1669c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        g1 = {x % 2 for x in a[0::2]}
        out.append(yes_no(len(g1) <= 1))
    return "".join(out)


def _gen_1669c(rng: random.Random) -> list[str]:
    cases = ["4\n3\n1 2 1\n4\n2 2 2 3\n4\n1 2 3 4\n5\n1000 1 1000 1 1000\n"]
    for _ in range(11):
        n = rng.randint(1, 10)
        vals = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 1999C Showering ─────────────────────────────────────────────────────────


def _s_1999c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s, m = map(int, ls[idx].split())
        idx += 1
        cur = 0
        ok = False
        for _k in range(n):
            l, r = map(int, ls[idx].split())
            idx += 1
            if l - cur >= s:
                ok = True
            cur = max(cur, r)
        if m - cur >= s:
            ok = True
        out.append(yes_no(ok))
    return "".join(out)


def _a_1999c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s, m = map(int, ls[idx].split())
        idx += 1
        bounds = [0]
        for _k in range(n):
            l, r = map(int, ls[idx].split())
            idx += 1
            bounds.append(l)
            bounds.append(r)
        bounds.append(m)
        gaps = [bounds[2 * i + 1] - bounds[2 * i] for i in range(len(bounds) // 2)]
        out.append(yes_no(max(gaps) >= s))
    return "".join(out)


def _m1_1999c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s, m = map(int, ls[idx].split())
        idx += 1
        cur = 0
        ok = False
        prev_r = None
        for _k in range(n):
            l, r = map(int, ls[idx].split())
            idx += 1
            if prev_r is not None and l - prev_r >= s:
                ok = True
            prev_r = r
        out.append(yes_no(ok))
    return "".join(out)


def _m2_1999c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s, m = map(int, ls[idx].split())
        idx += 1
        cur = 0
        ok = False
        for _k in range(n):
            l, r = map(int, ls[idx].split())
            idx += 1
            if l - cur > s:
                ok = True
            cur = max(cur, r)
        if m - cur > s:
            ok = True
        out.append(yes_no(ok))
    return "".join(out)


def _gen_1999c(rng: random.Random) -> list[str]:
    cases = [
        "4\n3 3 10\n3 5\n6 8\n9 10\n3 3 10\n1 2\n3 5\n6 7\n3 3 10\n1 2\n3 5\n6 8\n3 4 10\n1 2\n6 7\n8 9\n"
    ]
    for _ in range(9):
        m = rng.randint(5, 30)
        n = rng.randint(0, 4)
        intervals = []
        cur = 0
        for _k in range(n):
            l = cur + rng.randint(0, 2)
            r = l + rng.randint(1, 3)
            if r > m:
                break
            intervals.append((l, r))
            cur = r
        s = rng.randint(1, 5)
        body = f"{len(intervals)} {s} {m}\n" + "".join(f"{l} {r}\n" for l, r in intervals)
        cases.append("1\n" + body)
    return cases


# ─── 1607B Odd Grasshopper ──────────────────────────────────────────────────


def _s_1607b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    maps = [lambda n: 0, lambda n: n, lambda n: -1, lambda n: -n - 1]
    for i in range(1, t + 1):
        x0, n = map(int, ls[i].split())
        d = maps[n % 4](n)
        out.append(str(x0 - d if x0 % 2 == 0 else x0 + d))
    return "\n".join(out) + "\n"


def _a_1607b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x0, n = map(int, ls[i].split())
        x = x0
        limit = min(n, 4000)
        for k in range(1, limit + 1):
            if x % 2 == 0:
                x -= k
            else:
                x += k
        rem = n - limit
        if rem:
            # remaining full cycles of 4 leave position unchanged
            pass
        out.append(str(x))
    return "\n".join(out) + "\n"


def _m1_1607b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    maps = [lambda n: 0, lambda n: n, lambda n: -1, lambda n: -n - 1]
    for i in range(1, t + 1):
        x0, n = map(int, ls[i].split())
        d = maps[n % 4](n)
        out.append(str(x0 - d if x0 % 2 == 1 else x0 + d))
    return "\n".join(out) + "\n"


def _m2_1607b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    maps = [lambda n: 0, lambda n: n, lambda n: 1, lambda n: -n - 1]
    for i in range(1, t + 1):
        x0, n = map(int, ls[i].split())
        d = maps[n % 4](n)
        out.append(str(x0 - d if x0 % 2 == 0 else x0 + d))
    return "\n".join(out) + "\n"


def _gen_1607b(rng: random.Random) -> list[str]:
    cases = ["4\n0 1\n0 2\n10 1\n10 2\n"]
    for _ in range(11):
        x0 = rng.randint(-20, 20)
        n = rng.randint(1, 400)
        cases.append(f"1\n{x0} {n}\n")
    return cases


# ─── 1985D Manhattan Circle ─────────────────────────────────────────────────


def _s_1985d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx : idx + n]
        idx += n
        minr = minc = 10**9
        maxr = maxc = -1
        for r in range(n):
            row = grid[r]
            for c in range(m):
                if row[c] == "#":
                    minr = min(minr, r)
                    maxr = max(maxr, r)
                    minc = min(minc, c)
                    maxc = max(maxc, c)
        cr = (minr + maxr) // 2 + 1
        cc = (minc + maxc) // 2 + 1
        out.append(f"{cr} {cc}")
    return "\n".join(out) + "\n"


def _a_1985d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx : idx + n]
        idx += n
        row_cnt = [row.count("#") for row in grid]
        best_row = max(range(n), key=lambda r: row_cnt[r])
        col_cnt = [0] * m
        for row in grid:
            for c in range(m):
                if row[c] == "#":
                    col_cnt[c] += 1
        best_col = max(range(m), key=lambda c: col_cnt[c])
        out.append(f"{best_row + 1} {best_col + 1}")
    return "\n".join(out) + "\n"


def _m1_1985d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx : idx + n]
        idx += n
        minr = minc = 10**9
        for r in range(n):
            row = grid[r]
            for c in range(m):
                if row[c] == "#":
                    minr = min(minr, r)
                    minc = min(minc, c)
        out.append(f"{minr + 1} {minc + 1}")
    return "\n".join(out) + "\n"


def _m2_1985d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, m = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx : idx + n]
        idx += n
        minr = minc = 10**9
        maxr = maxc = -1
        for r in range(n):
            row = grid[r]
            for c in range(m):
                if row[c] == "#":
                    minr = min(minr, r)
                    maxr = max(maxr, r)
                    minc = min(minc, c)
                    maxc = max(maxc, c)
        cr = (minr + maxr) // 2 + 1
        cc = (minc + maxc) // 2 + 1
        out.append(f"{cc} {cr}")
    return "\n".join(out) + "\n"


def _gen_1985d(rng: random.Random) -> list[str]:
    def make(n, m, cr, cc, k):
        grid = [["." for _ in range(m)] for _ in range(n)]
        for dr in range(-k, k + 1):
            width = k - abs(dr)
            r = cr + dr
            if 0 <= r < n:
                for dc in range(-width, width + 1):
                    c = cc + dc
                    if 0 <= c < m:
                        grid[r][c] = "#"
        return f"{n} {m}\n" + "\n".join("".join(row) for row in grid) + "\n"

    cases = ["1\n" + make(5, 5, 2, 2, 2)]
    for _ in range(16):
        n = rng.randint(3, 15) | 1
        m = rng.randint(3, 15) | 1
        cr = n // 2
        cc = m // 2
        k = min(cr, cc, n - 1 - cr, m - 1 - cc)
        if k < 1:
            k = 1
            n = max(n, 3)
            m = max(m, 3)
            cr, cc = n // 2, m // 2
        cases.append("1\n" + make(n, m, cr, cc, k))
    return cases


# ─── 1593A Elections ────────────────────────────────────────────────────────


def _s_1593a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        A = max(0, max(b, c) + 1 - a)
        B = max(0, max(a, c) + 1 - b)
        C = max(0, max(a, b) + 1 - c)
        out.append(f"{A} {B} {C}")
    return "\n".join(out) + "\n"


def _a_1593a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        votes = list(map(int, ls[i].split()))
        res = []
        for k in range(3):
            others = [votes[j] for j in range(3) if j != k]
            res.append(str(max(0, max(others) + 1 - votes[k])))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _m1_1593a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        A = max(0, max(b, c) - a)
        B = max(0, max(a, c) - b)
        C = max(0, max(a, b) - c)
        out.append(f"{A} {B} {C}")
    return "\n".join(out) + "\n"


def _m2_1593a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        A = max(0, b + c + 1 - a)
        B = max(0, a + c + 1 - b)
        C = max(0, a + b + 1 - c)
        out.append(f"{A} {B} {C}")
    return "\n".join(out) + "\n"


def _gen_1593a(rng: random.Random) -> list[str]:
    cases = ["5\n0 0 0\n10 75 15\n13 13 17\n1000 0 0\n0 1000000000 0\n"]
    for _ in range(11):
        vals = [rng.randint(0, 50) for _ in range(3)]
        cases.append("1\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 478B Random Teams ──────────────────────────────────────────────────────


def _c2(x: int) -> int:
    return x * (x - 1) // 2


def _s_478b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, ls[i].split())
        q, r = divmod(n, k)
        mn = r * _c2(q + 1) + (k - r) * _c2(q)
        mx = _c2(n - k + 1)
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _a_478b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, ls[i].split())
        sizes = [n // k] * k
        for j in range(n % k):
            sizes[j] += 1
        mn = sum(_c2(s) for s in sizes)
        max_sizes = [1] * k
        max_sizes[0] = n - (k - 1)
        mx = sum(_c2(s) for s in max_sizes)
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _m1_478b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, ls[i].split())
        q, r = divmod(n, k)
        mn = r * _c2(q + 1) + (k - r) * _c2(q)
        mx = _c2(n - k + 1)
        out.append(f"{mx} {mn}")
    return "\n".join(out) + "\n"


def _m2_478b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, ls[i].split())
        q, r = divmod(n, k)
        mn = r * _c2(q + 1) + (k - r) * _c2(q)
        mx = _c2(n) // k
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _gen_478b(rng: random.Random) -> list[str]:
    cases = ["2\n5 1\n3 2\n"]
    for _ in range(11):
        k = rng.randint(1, 8)
        n = rng.randint(k, k + 15)
        cases.append(f"1\n{n} {k}\n")
    return cases


# ─── 2033A Sakurako and Kosuke ──────────────────────────────────────────────


def _s_2033a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append("Kosuke\n" if n % 2 == 1 else "Sakurako\n")
    return "".join(out)


def _a_2033a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        x = 0
        c = 1
        while -n <= x <= n:
            if c % 2 == 1:
                x -= 2 * c - 1
            else:
                x += 2 * c - 1
            c += 1
        out.append("Sakurako\n" if c % 2 == 0 else "Kosuke\n")
    return "".join(out)


def _m1_2033a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append("Sakurako\n" if n % 2 == 1 else "Kosuke\n")
    return "".join(out)


def _m2_2033a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append("Kosuke\n" if n % 2 == 0 else "Sakurako\n")
    return "".join(out)


def _gen_2033a(rng: random.Random) -> list[str]:
    cases = ["4\n1\n2\n3\n4\n"]
    for _ in range(11):
        n = rng.randint(1, 100)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 2060A Fibonacciness ────────────────────────────────────────────────────


def _fib_counts(a1, a2, a4, a5):
    f1 = int(a4 == a1 + 2 * a2) + int(a5 == a1 + a2 + a4)
    f2 = int(a4 == a1 + 2 * a2) + int(2 * a4 == a2 + a5)
    f3 = int(a5 == a1 + a2 + a4) + int(2 * a4 == a2 + a5)
    return 1 + max(f1, f2, f3)


def _s_2060a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a1, a2, a4, a5 = map(int, ls[i].split())
        out.append(str(_fib_counts(a1, a2, a4, a5)))
    return "\n".join(out) + "\n"


def _a_2060a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a1, a2, a4, a5 = map(int, ls[i].split())
        best = 0
        for a3 in {a1 + a2, a4 - a2, a5 - a4}:
            arr = [a1, a2, a3, a4, a5]
            cnt = sum(1 for k in range(3) if arr[k] + arr[k + 1] == arr[k + 2])
            best = max(best, cnt)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_2060a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a1, a2, a4, a5 = map(int, ls[i].split())
        a3 = a1 + a2
        arr = [a1, a2, a3, a4, a5]
        cnt = sum(1 for k in range(3) if arr[k] + arr[k + 1] == arr[k + 2])
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m2_2060a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a1, a2, a4, a5 = map(int, ls[i].split())
        f1 = int(a4 == a1 + 2 * a2) + int(a5 == a1 + a2 + a4)
        f2 = int(a4 == a1 + 2 * a2) + int(2 * a4 == a2 + a5)
        f3 = int(a5 == a1 + a2 + a4) + int(2 * a4 == a2 + a5)
        out.append(str(max(f1, f2, f3)))
    return "\n".join(out) + "\n"


def _gen_2060a(rng: random.Random) -> list[str]:
    cases = ["6\n1 1 3 5\n1 3 2 1\n8 10 28 100\n100 1 100 1\n1 100 1 100\n100 100 100 100\n"]
    for _ in range(11):
        vals = [rng.randint(1, 30) for _ in range(4)]
        cases.append("1\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 1872D Plus Minus Permutation ───────────────────────────────────────────


def _s_1872d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, x, y = map(int, ls[i].split())
        g = math.gcd(x, y)
        lcm = x * y // g
        cx = n // x - n // lcm
        cy = n // y - n // lcm
        top = cx * (2 * n - cx + 1) // 2
        bot = cy * (cy + 1) // 2
        out.append(str(top - bot))
    return "\n".join(out) + "\n"


def _a_1872d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, x, y = map(int, ls[i].split())
        g = math.gcd(x, y)
        lcm = x * y // g
        cx = n // x - n // lcm
        cy = n // y - n // lcm
        top_vals = list(range(n - cx + 1, n + 1))
        bot_vals = list(range(1, cy + 1))
        out.append(str(sum(top_vals) - sum(bot_vals)))
    return "\n".join(out) + "\n"


def _m1_1872d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, x, y = map(int, ls[i].split())
        g = math.gcd(x, y)
        lcm = x * y // g
        cx = n // x - n // lcm
        cy = n // y - n // lcm
        top = cy * (2 * n - cy + 1) // 2
        bot = cx * (cx + 1) // 2
        out.append(str(top - bot))
    return "\n".join(out) + "\n"


def _m2_1872d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, x, y = map(int, ls[i].split())
        cx = n // x
        cy = n // y
        top = cx * (2 * n - cx + 1) // 2
        bot = cy * (cy + 1) // 2
        out.append(str(top - bot))
    return "\n".join(out) + "\n"


def _gen_1872d(rng: random.Random) -> list[str]:
    cases = ["4\n10 2 5\n3 3 1\n5 3 4\n1 1 1\n"]
    for _ in range(11):
        n = rng.randint(1, 30)
        x = rng.randint(1, 10)
        y = rng.randint(1, 10)
        cases.append(f"1\n{n} {x} {y}\n")
    return cases


# ─── 2093A Ideal Generator ──────────────────────────────────────────────────


def _s_2093a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        k = int(ls[i])
        out.append(yes_no(k % 2 == 1))
    return "".join(out)


def _a_2093a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        k = int(ls[i])
        out.append(yes_no(k & 1 == 1))
    return "".join(out)


def _m1_2093a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        k = int(ls[i])
        out.append(yes_no(k % 2 == 0))
    return "".join(out)


def _m2_2093a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        k = int(ls[i])
        out.append(yes_no(k % 2 == 1 or k == 2))
    return "".join(out)


def _gen_2093a(rng: random.Random) -> list[str]:
    cases = ["5\n1\n2\n3\n7\n1000\n"]
    for _ in range(11):
        k = rng.randint(1, 1000)
        cases.append(f"1\n{k}\n")
    return cases


# ─── 1790A Polycarp and the Day of Pi ───────────────────────────────────────


def _s_1790a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        n = min(len(s), len(PI_DIGITS))
        k = 0
        while k < n and s[k] == PI_DIGITS[k]:
            k += 1
        out.append(str(k))
    return "\n".join(out) + "\n"


def _a_1790a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        k = 0
        for c1, c2 in zip(s, PI_DIGITS):
            if c1 != c2:
                break
            k += 1
        out.append(str(k))
    return "\n".join(out) + "\n"


def _m1_1790a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        n = min(len(s), len(PI_DIGITS))
        k = 1
        while k < n and s[k] == PI_DIGITS[k]:
            k += 1
        out.append(str(k))
    return "\n".join(out) + "\n"


def _m2_1790a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        n = min(len(s), len(PI_DIGITS))
        k = 0
        while k < n and s[k] == PI_DIGITS[k + 1 if k + 1 < len(PI_DIGITS) else k]:
            k += 1
        out.append(str(k))
    return "\n".join(out) + "\n"


def _gen_1790a(rng: random.Random) -> list[str]:
    cases = ["5\n2\n13\n5\n31415\n9\n314159265\n30\n314159265358979323846264338327\n1\n4\n"]
    for _ in range(11):
        n = rng.randint(1, 20)
        if rng.random() < 0.5:
            k = rng.randint(0, min(n, len(PI_DIGITS)))
            s = PI_DIGITS[:k] + "".join(rng.choice("0123456789") for _ in range(n - k))
            if k < n and s[k] == PI_DIGITS[k]:
                s = s[:k] + str((int(PI_DIGITS[k]) + 1) % 10) + s[k + 1 :]
        else:
            s = "".join(rng.choice("0123456789") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 1537A Arithmetic Array ─────────────────────────────────────────────────


def _s_1537a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = sum(a)
        out.append(str(1 if s < n else s - n))
    return "\n".join(out) + "\n"


def _a_1537a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = 0
        for v in a:
            s += v
        out.append(str(s - n if s >= n else 1))
    return "\n".join(out) + "\n"


def _m1_1537a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(sum(a) - n))
    return "\n".join(out) + "\n"


def _m2_1537a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = sum(a)
        out.append(str(1 if s < n else s - n + 1))
    return "\n".join(out) + "\n"


def _gen_1537a(rng: random.Random) -> list[str]:
    cases = ["4\n1\n1\n2\n-2 4\n5\n1 1 1 1 1\n4\n-2 -2 -2 -2\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        vals = [rng.randint(-10, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, vals)) + "\n")
    return cases


# ─── 1703C Cypher ────────────────────────────────────────────────────────────


def _s_1703c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for i in range(n):
            parts = ls[idx].split()
            idx += 1
            moves = parts[1]
            shift = moves.count("D") - moves.count("U")
            res.append(str((a[i] + shift) % 10))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _a_1703c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for i in range(n):
            parts = ls[idx].split()
            idx += 1
            moves = parts[1]
            v = a[i]
            for ch in reversed(moves):
                if ch == "U":
                    v = (v - 1) % 10
                else:
                    v = (v + 1) % 10
            res.append(str(v))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _m1_1703c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for i in range(n):
            parts = ls[idx].split()
            idx += 1
            moves = parts[1]
            shift = moves.count("U") - moves.count("D")
            res.append(str((a[i] + shift) % 10))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _m2_1703c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for i in range(n):
            parts = ls[idx].split()
            idx += 1
            moves = parts[1]
            shift = moves.count("D") - moves.count("U")
            res.append(str(a[i] + shift))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _gen_1703c(rng: random.Random) -> list[str]:
    cases = ["2\n3\n9 3 1\n3 DDD\n4 UDUU\n2 DU\n2\n0 9\n9 DDDDDDDDD\n9 UUUUUUUUU\n"]
    for _ in range(11):
        n = rng.randint(1, 5)
        a = [rng.randint(0, 9) for _ in range(n)]
        rows = []
        for _k in range(n):
            b = rng.randint(1, 10)
            moves = "".join(rng.choice("UD") for _ in range(b))
            rows.append(f"{b} {moves}")
        body = f"{n}\n" + " ".join(map(str, a)) + "\n" + "\n".join(rows) + "\n"
        cases.append("1\n" + body)
    return cases


# ─── 978B File Name ─────────────────────────────────────────────────────────


def _s_978b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        ans = 0
        i = 0
        n = len(s)
        while i < n:
            j = i
            while j < n and s[j] == s[i]:
                j += 1
            run = j - i
            if run >= 3:
                ans += run - 2
            i = j
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_978b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        ans = 0
        run = 0
        prev = None
        for ch in s:
            if ch == prev:
                run += 1
            else:
                run = 1
                prev = ch
            if run >= 3:
                ans += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_978b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        ans = 0
        i = 0
        n = len(s)
        while i < n:
            j = i
            while j < n and s[j] == s[i]:
                j += 1
            run = j - i
            if run >= 3:
                ans += run - 1
            i = j
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m2_978b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        ans = 0
        i = 0
        n = len(s)
        while i < n:
            j = i
            while j < n and s[j] == s[i]:
                j += 1
            run = j - i
            if run >= 3:
                ans += 1
            i = j
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_978b(rng: random.Random) -> list[str]:
    cases = ["4\n5\naaabc\n1\nc\n7\naaaaaaa\n4\naabc\n"]
    for _ in range(11):
        n = rng.randint(1, 15)
        s = "".join(rng.choice("ab") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 2000B Seating in a Bus ─────────────────────────────────────────────────


def _s_2000b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        left = right = a[0]
        ok = True
        for i in range(1, len(a)):
            if a[i] + 1 == left:
                left = a[i]
            elif a[i] - 1 == right:
                right = a[i]
            else:
                ok = False
                break
        out.append(yes_no(ok))
    return "".join(out)


def _a_2000b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        occupied: set[int] = set()
        ok = True
        for i, v in enumerate(a):
            if i == 0 or (v - 1) in occupied or (v + 1) in occupied:
                occupied.add(v)
            else:
                ok = False
                break
        out.append(yes_no(ok))
    return "".join(out)


def _m1_2000b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        occupied: set[int] = set()
        ok = True
        for i, v in enumerate(a):
            if i == 0 or (v - 1) in occupied:
                occupied.add(v)
            else:
                ok = False
                break
        out.append(yes_no(ok))
    return "".join(out)


def _m2_2000b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(yes_no(True))
    return "".join(out)


def _gen_2000b(rng: random.Random) -> list[str]:
    cases = ["4\n5\n5 4 2 1 3\n3\n2 1 3\n4\n2 3 1 4\n1\n1\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        perm = list(range(1, n + 1))
        rng.shuffle(perm)
        cases.append(f"1\n{n}\n" + " ".join(map(str, perm)) + "\n")
    return cases


# ─── 1742E Scuza ─────────────────────────────────────────────────────────────


def _s_1742e(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, q = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ks = list(map(int, ls[idx].split()))
        idx += 1
        pref = [0]
        prefmax = []
        mx = 0
        for v in a:
            pref.append(pref[-1] + v)
            mx = max(mx, v)
            prefmax.append(mx)
        res = []
        import bisect

        for k in ks:
            i = bisect.bisect_right(prefmax, k)
            res.append(str(pref[i]))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _a_1742e(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, q = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ks = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for k in ks:
            total = 0
            for v in a:
                if v > k:
                    break
                total += v
            res.append(str(total))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _m1_1742e(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, q = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ks = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for k in ks:
            total = 0
            for v in a:
                if v >= k:
                    break
                total += v
            res.append(str(total))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _m2_1742e(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, q = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ks = list(map(int, ls[idx].split()))
        idx += 1
        res = []
        for k in ks:
            total = sum(v for v in a if v <= k)
            res.append(str(total))
        out.append(" ".join(res))
    return "\n".join(out) + "\n"


def _gen_1742e(rng: random.Random) -> list[str]:
    cases = ["1\n4 5\n1 2 1 5\n1 2 4 9 10\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        q = rng.randint(1, 5)
        a = [rng.randint(1, 10) for _ in range(n)]
        ks = [rng.randint(0, 12) for _ in range(q)]
        body = f"{n} {q}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, ks)) + "\n"
        cases.append("1\n" + body)
    return cases


# ─── 1312B Bogosort ─────────────────────────────────────────────────────────


def _s_1312b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(" ".join(map(str, sorted(a, reverse=True))))
    return "\n".join(out) + "\n"


def _a_1312b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(a)
        n = len(b)
        for i in range(n):
            max_idx = i
            for j in range(i + 1, n):
                if b[j] > b[max_idx]:
                    max_idx = j
            b[i], b[max_idx] = b[max_idx], b[i]
        out.append(" ".join(map(str, b)))
    return "\n".join(out) + "\n"


def _m1_1312b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(" ".join(map(str, sorted(a))))
    return "\n".join(out) + "\n"


def _m2_1312b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(" ".join(map(str, a)))
    return "\n".join(out) + "\n"


def _gen_1312b(rng: random.Random) -> list[str]:
    cases = ["3\n1\n7\n4\n1 1 3 5\n6\n3 2 1 5 6 4\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 2072A New World, New Me, New Array ─────────────────────────────────────


def _s_2072a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k, p = map(int, ls[i].split())
        if k < -n * p or k > n * p:
            out.append("-1")
        else:
            ans = abs(k)
            out.append(str(ans // p + (1 if ans % p else 0)))
    return "\n".join(out) + "\n"


def _a_2072a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k, p = map(int, ls[i].split())
        if not (-n * p <= k <= n * p):
            out.append("-1")
            continue
        remaining = abs(k)
        ops = 0
        while remaining > 0:
            remaining -= p
            ops += 1
        out.append(str(ops))
    return "\n".join(out) + "\n"


def _m1_2072a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k, p = map(int, ls[i].split())
        ans = abs(k)
        out.append(str(ans // p + (1 if ans % p else 0)))
    return "\n".join(out) + "\n"


def _m2_2072a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, k, p = map(int, ls[i].split())
        if k < -n * p or k > n * p:
            out.append("-1")
        else:
            out.append(str(abs(k) // p))
    return "\n".join(out) + "\n"


def _gen_2072a(rng: random.Random) -> list[str]:
    cases = ["7\n5 5 3\n1 -4 4\n3 0 2\n1 -5 3\n1 0 4\n2 10 5\n3 -7 2\n"]
    for _ in range(11):
        n = rng.randint(1, 10)
        p = rng.randint(1, 10)
        k = rng.randint(-15, 15)
        cases.append(f"1\n{n} {k} {p}\n")
    return cases


# ─── 1363A Odd Selection ────────────────────────────────────────────────────


def _s_1363a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        numodd = sum(1 for v in a if v % 2)
        numeven = n - numodd
        ok = False
        i = 1
        while i <= numodd and i <= x:
            if x - i <= numeven:
                ok = True
                break
            i += 2
        out.append(yes_no(ok))
    return "".join(out)


def _a_1363a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        numodd = sum(1 for v in a if v % 2)
        numeven = n - numodd
        lo = max(1, x - numeven)
        hi = min(numodd, x)
        ok = any(i % 2 == 1 for i in range(lo, hi + 1))
        out.append(yes_no(ok))
    return "".join(out)


def _m1_1363a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        numodd = sum(1 for v in a if v % 2)
        numeven = n - numodd
        ok = False
        i = 0
        while i <= numodd and i <= x:
            if x - i <= numeven:
                ok = True
                break
            i += 2
        out.append(yes_no(ok))
    return "".join(out)


def _m2_1363a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        numodd = sum(1 for v in a if v % 2)
        out.append(yes_no(numodd >= 1))
    return "".join(out)


def _gen_1363a(rng: random.Random) -> list[str]:
    cases = ["5\n1 1\n999\n1 1\n1000\n2 1\n51 50\n2 2\n51 50\n3 3\n101 102 103\n"]
    for _ in range(11):
        n = rng.randint(1, 10)
        x = rng.randint(1, n)
        a = [rng.randint(1, 1000) for _ in range(n)]
        cases.append(f"1\n{n} {x}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 2036A Quintomania ───────────────────────────────────────────────────────


def _s_2036a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ok = all(abs(a[i] - a[i - 1]) in (5, 7) for i in range(1, len(a)))
        out.append(yes_no(ok))
    return "".join(out)


def _a_2036a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        diffs = {abs(x - y) for x, y in zip(a, a[1:])}
        out.append(yes_no(diffs <= {5, 7}))
    return "".join(out)


def _m1_2036a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ok = len(a) < 2 or any(abs(a[i] - a[i - 1]) in (5, 7) for i in range(1, len(a)))
        out.append(yes_no(ok))
    return "".join(out)


def _m2_2036a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ok = len(a) < 2 or abs(a[1] - a[0]) in (5, 7)
        out.append(yes_no(ok))
    return "".join(out)


def _gen_2036a(rng: random.Random) -> list[str]:
    cases = ["3\n2\n114 109\n2\n17 10\n3\n76 83 88\n"]
    for _ in range(11):
        n = rng.randint(2, 6)
        a = [rng.randint(0, 127)]
        for _k in range(n - 1):
            if rng.random() < 0.7:
                step = rng.choice([5, -5, 7, -7])
                nxt = a[-1] + step
                if 0 <= nxt <= 127:
                    a.append(nxt)
                else:
                    a.append(rng.randint(0, 127))
            else:
                a.append(rng.randint(0, 127))
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1607A Linear Keyboard ──────────────────────────────────────────────────


def _s_1607a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        s = ls[idx]
        idx += 1
        w = ls[idx]
        idx += 1
        pos = {ch: i for i, ch in enumerate(s)}
        total = sum(abs(pos[w[i]] - pos[w[i - 1]]) for i in range(1, len(w)))
        out.append(str(total))
    return "\n".join(out) + "\n"


def _a_1607a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        s = ls[idx]
        idx += 1
        w = ls[idx]
        idx += 1
        pos = {ch: i for i, ch in enumerate(s)}
        total = 0
        for a, b in zip(w, w[1:]):
            total += abs(pos[a] - pos[b])
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m1_1607a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        s = ls[idx]
        idx += 1
        w = ls[idx]
        idx += 1
        pos = {ch: i for i, ch in enumerate(s)}
        total = sum(pos[w[i]] - pos[w[i - 1]] for i in range(1, len(w)))
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m2_1607a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        s = ls[idx]
        idx += 1
        w = ls[idx]
        idx += 1
        pos = {ch: i for i, ch in enumerate(s)}
        half = len(w) // 2
        total = sum(abs(pos[w[i]] - pos[w[i - 1]]) for i in range(1, half + 1))
        out.append(str(total))
    return "\n".join(out) + "\n"


def _gen_1607a(rng: random.Random) -> list[str]:
    keyboard = "qwertyuiopasdfghjklzxcvbnm"
    cases = [f"3\n{keyboard}\nhello\n{keyboard}\nabb\n{keyboard}\nweird\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        w = "".join(rng.choice(keyboard) for _ in range(n))
        cases.append(f"1\n{keyboard}\n{w}\n")
    return cases


# ─── 1985C Good Prefixes ────────────────────────────────────────────────────


def _s_1985c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = 0
        mx = 0
        cnt = 0
        for v in a:
            s += v
            mx = max(mx, v)
            if s == 2 * mx:
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _a_1985c(stdin: str) -> str:
    from itertools import accumulate

    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        prefsum = list(accumulate(a))
        prefmax = list(accumulate(a, max))
        cnt = sum(1 for s, m in zip(prefsum, prefmax) if s - m == m)
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1985c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = 0
        mx = 0
        cnt = 0
        for v in a:
            s += v
            mx = max(mx, v)
            if s == mx:
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m2_1985c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = 0
        mx = 0
        cnt = 0
        for v in a:
            if s == 2 * mx:
                cnt += 1
            s += v
            mx = max(mx, v)
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _gen_1985c(rng: random.Random) -> list[str]:
    cases = ["4\n1\n0\n1\n1\n4\n1 1 2 0\n5\n0 1 2 1 4\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        a = [rng.randint(0, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1914D Three Activities ─────────────────────────────────────────────────


def _top3(a: list[int]) -> list[int]:
    idxs = sorted(range(len(a)), key=lambda i: -a[i])
    return idxs[:3]


def _s_1914d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        c = list(map(int, ls[idx].split()))
        idx += 1
        best = 0
        for x in _top3(a):
            for y in _top3(b):
                for z in _top3(c):
                    if x != y and y != z and x != z:
                        best = max(best, a[x] + b[y] + c[z])
        out.append(str(best))
    return "\n".join(out) + "\n"


def _a_1914d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = 0
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        c = list(map(int, ls[idx].split()))
        idx += 1
        n = len(a)
        best = 0
        for x in range(n):
            for y in range(n):
                if y == x:
                    continue
                for z in range(n):
                    if z == x or z == y:
                        continue
                    val = a[x] + b[y] + c[z]
                    if val > best:
                        best = val
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1914d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        c = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(max(a) + max(b) + max(c)))
    return "\n".join(out) + "\n"


def _m2_1914d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        c = list(map(int, ls[idx].split()))
        idx += 1
        best = 0
        for x in _top3(a):
            for y in _top3(b):
                for z in _top3(c):
                    if x != y:
                        best = max(best, a[x] + b[y] + c[z])
        out.append(str(best))
    return "\n".join(out) + "\n"


def _gen_1914d(rng: random.Random) -> list[str]:
    cases = ["1\n3\n1 2 3\n2 3 4\n3 2 1\n"]
    for _ in range(11):
        n = rng.randint(3, 10)
        a = [rng.randint(1, 15) for _ in range(n)]
        b = [rng.randint(1, 15) for _ in range(n)]
        c = [rng.randint(1, 15) for _ in range(n)]
        body = f"{n}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n" + " ".join(map(str, c)) + "\n"
        cases.append("1\n" + body)
    return cases


# ─── 600B Queries about less or equal elements ──────────────────────────────


def _s_600b(stdin: str) -> str:
    import bisect

    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = sorted(map(int, ls[1].split()))
    b = list(map(int, ls[2].split()))
    out = [str(bisect.bisect_right(a, x)) for x in b]
    return " ".join(out) + "\n"


def _a_600b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = sorted(map(int, ls[1].split()))
    b = list(map(int, ls[2].split()))
    order = sorted(range(m), key=lambda i: b[i])
    res = [0] * m
    j = 0
    for idx_in_order in order:
        x = b[idx_in_order]
        while j < n and a[j] <= x:
            j += 1
        res[idx_in_order] = j
    return " ".join(map(str, res)) + "\n"


def _m1_600b(stdin: str) -> str:
    import bisect

    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = sorted(map(int, ls[1].split()))
    b = list(map(int, ls[2].split()))
    out = [str(bisect.bisect_left(a, x)) for x in b]
    return " ".join(out) + "\n"


def _m2_600b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = sorted(map(int, ls[1].split()))
    b = list(map(int, ls[2].split()))
    out = [str(sum(1 for v in a if v < x)) for x in b]
    return " ".join(out) + "\n"


def _gen_600b(rng: random.Random) -> list[str]:
    cases = ["5 4\n1 3 5 7 9\n6 4 2 8\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        m = rng.randint(1, 8)
        a = [rng.randint(1, 15) for _ in range(n)]
        b = [rng.randint(1, 15) for _ in range(m)]
        cases.append(f"{n} {m}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 1538A Stone Game ────────────────────────────────────────────────────────


def _s_1538a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        i = a.index(min(a))
        j = a.index(max(a))
        if i > j:
            i, j = j, i
        out.append(str(min(j + 1, n - i, i + 1 + n - j)))
    return "\n".join(out) + "\n"


def _a_1538a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        imin = imax = 0
        for k in range(n):
            if a[k] < a[imin]:
                imin = k
            if a[k] > a[imax]:
                imax = k
        lo, hi = min(imin, imax), max(imin, imax)
        opt1 = hi + 1
        opt2 = n - lo
        opt3 = (lo + 1) + (n - hi)
        out.append(str(min(opt1, opt2, opt3)))
    return "\n".join(out) + "\n"


def _m1_1538a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        i = a.index(min(a))
        j = a.index(max(a))
        if i > j:
            i, j = j, i
        out.append(str(min(j + 1, n - i)))
    return "\n".join(out) + "\n"


def _m2_1538a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        i = a.index(min(a))
        j = a.index(max(a))
        out.append(str(min(j + 1, n - i, i + 1 + n - j)))
    return "\n".join(out) + "\n"


def _gen_1538a(rng: random.Random) -> list[str]:
    cases = ["3\n5\n1 5 4 3 2\n8\n2 1 3 4 5 6 8 7\n8\n8 2 3 4 5 6 7 1\n"]
    for _ in range(11):
        n = rng.randint(2, 10)
        a = list(range(1, n + 1))
        rng.shuffle(a)
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1742C Stripes ───────────────────────────────────────────────────────────


def _s_1742c(stdin: str) -> str:
    ls = [ln for ln in lines(stdin) if ln.strip() != "" or True]
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        while ls[idx].strip() == "":
            idx += 1
        grid = ls[idx : idx + 8]
        idx += 8
        found = "B"
        for row in grid:
            if row == "RRRRRRRR":
                found = "R"
                break
        out.append(found)
    return "\n".join(out) + "\n"


def _a_1742c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        while ls[idx].strip() == "":
            idx += 1
        grid = ls[idx : idx + 8]
        idx += 8
        found = "R"
        for c in range(8):
            if all(grid[r][c] == "B" for r in range(8)):
                found = "B"
                break
        out.append(found)
    return "\n".join(out) + "\n"


def _m1_1742c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        while ls[idx].strip() == "":
            idx += 1
        grid = ls[idx : idx + 8]
        idx += 8
        out.append("R" if grid[0] == "RRRRRRRR" else "B")
    return "\n".join(out) + "\n"


def _m2_1742c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        while ls[idx].strip() == "":
            idx += 1
        grid = ls[idx : idx + 8]
        idx += 8
        found = "R"
        for c in range(8):
            if all(grid[r][c] == "B" for r in range(8)):
                found = "R"
                break
        out.append(found)
    return "\n".join(out) + "\n"


def _gen_1742c(rng: random.Random) -> list[str]:
    def render(rows_painted, cols_painted):
        grid = [["." for _ in range(8)] for _ in range(8)]
        for kind, idxv in rows_painted + cols_painted:
            if kind == "R":
                for c in range(8):
                    grid[idxv][c] = "R"
            else:
                for r in range(8):
                    grid[r][idxv] = "B"
        return "\n".join("".join(row) for row in grid) + "\n"

    sample = (
        "....B...\n....B...\n....B...\nRRRRRRRR\n....B...\n....B...\n....B...\n....B...\n"
        "RRRRRRRB\nB......B\nB......B\nB......B\nB......B\nB......B\nB......B\nRRRRRRRB\n"
    )
    cases = ["2\n" + sample]
    for _ in range(11):
        ops = []
        n_ops = rng.randint(1, 5)
        for _ in range(n_ops):
            if rng.random() < 0.5:
                ops.append(("R", rng.randint(0, 7)))
            else:
                ops.append(("B", rng.randint(0, 7)))
        rows = [o for o in ops if o[0] == "R"]
        cols = [o for o in ops if o[0] == "B"]
        # ensure at least one stripe
        if not rows and not cols:
            rows = [("R", 0)]
        # render respecting draw order (later overwrites)
        grid = [["." for _ in range(8)] for _ in range(8)]
        for kind, idxv in ops if ops else rows:
            if kind == "R":
                for c in range(8):
                    grid[idxv][c] = "R"
            else:
                for r in range(8):
                    grid[r][idxv] = "B"
        body = "\n".join("".join(row) for row in grid) + "\n"
        cases.append("1\n" + body)
    return cases


# ─── 2051B Journey ───────────────────────────────────────────────────────────


def _s_2051b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b, c = map(int, ls[i].split())
        cyc = a + b + c
        d, mod = divmod(n, cyc)
        if mod == 0:
            out.append(str(d * 3))
        elif mod <= a:
            out.append(str(d * 3 + 1))
        elif mod <= a + b:
            out.append(str(d * 3 + 2))
        else:
            out.append(str(d * 3 + 3))
    return "\n".join(out) + "\n"


def _a_2051b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b, c = map(int, ls[i].split())
        total = 0
        day = 0
        pattern = [a, b, c]
        while total < n:
            total += pattern[day % 3]
            day += 1
        out.append(str(day))
    return "\n".join(out) + "\n"


def _m1_2051b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b, c = map(int, ls[i].split())
        cyc = a + b + c
        d, mod = divmod(n, cyc)
        if mod == 0:
            out.append(str(d * 3 + 1))
        elif mod <= a:
            out.append(str(d * 3 + 1))
        elif mod <= a + b:
            out.append(str(d * 3 + 2))
        else:
            out.append(str(d * 3 + 3))
    return "\n".join(out) + "\n"


def _m2_2051b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b, c = map(int, ls[i].split())
        cyc = a + b + c
        d, mod = divmod(n, cyc)
        if mod == 0:
            out.append(str(d * 3))
        elif mod <= b:
            out.append(str(d * 3 + 1))
        elif mod <= a + b:
            out.append(str(d * 3 + 2))
        else:
            out.append(str(d * 3 + 3))
    return "\n".join(out) + "\n"


def _gen_2051b(rng: random.Random) -> list[str]:
    cases = ["3\n12 1 5 3\n6 6 7 4\n16 3 4 1\n"]
    for _ in range(11):
        a = rng.randint(1, 10)
        b = rng.randint(1, 10)
        c = rng.randint(1, 10)
        n = rng.randint(1, 60)
        cases.append(f"1\n{n} {a} {b} {c}\n")
    return cases


# ─── 1471A Strange Partition ────────────────────────────────────────────────


def _ceildiv(a: int, b: int) -> int:
    return -(-a // b)


def _s_1471a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mn = _ceildiv(sum(a), x)
        mx = sum(_ceildiv(v, x) for v in a)
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _a_1471a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        s = sum(a)
        mn = s // x if s % x == 0 else s // x + 1
        mx = 0
        for v in a:
            mx += v // x if v % x == 0 else v // x + 1
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _m1_1471a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mn = _ceildiv(sum(a), x)
        mx = sum(_ceildiv(v, x) for v in a)
        out.append(f"{mx} {mn}")
    return "\n".join(out) + "\n"


def _m2_1471a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mn = sum(a) // x
        mx = sum(_ceildiv(v, x) for v in a)
        out.append(f"{mn} {mx}")
    return "\n".join(out) + "\n"


def _gen_1471a(rng: random.Random) -> list[str]:
    cases = ["2\n3 3\n3 6 9\n3 3\n4 11 6\n"]
    for _ in range(11):
        n = rng.randint(1, 6)
        x = rng.randint(1, 10)
        a = [rng.randint(1, 30) for _ in range(n)]
        cases.append(f"1\n{n} {x}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1761A Two Permutations ─────────────────────────────────────────────────


def _s_1761a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b = map(int, ls[i].split())
        ok = (a + b + 2 <= n) or (a == n and b == n)
        out.append(yes_no(ok))
    return "".join(out)


def _a_1761a(stdin: str) -> str:
    from itertools import permutations

    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b = map(int, ls[i].split())
        if n > 7:
            ok = (a + b + 2 <= n) or (a == n and b == n)
        else:
            p = list(range(1, n + 1))
            ok = False
            for q in permutations(p):
                pre = 0
                while pre < n and p[pre] == q[pre]:
                    pre += 1
                suf = 0
                while suf < n and p[n - 1 - suf] == q[n - 1 - suf]:
                    suf += 1
                if pre == a and suf == b:
                    ok = True
                    break
        out.append(yes_no(ok))
    return "".join(out)


def _m1_1761a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b = map(int, ls[i].split())
        ok = a + b <= n
        out.append(yes_no(ok))
    return "".join(out)


def _m2_1761a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, a, b = map(int, ls[i].split())
        ok = a + b + 2 <= n
        out.append(yes_no(ok))
    return "".join(out)


def _gen_1761a(rng: random.Random) -> list[str]:
    cases = ["4\n1 1 1\n2 1 2\n3 1 1\n4 1 1\n"]
    for _ in range(11):
        n = rng.randint(1, 7)
        a = rng.randint(1, n)
        b = rng.randint(1, n)
        cases.append(f"1\n{n} {a} {b}\n")
    return cases


# ─── 1541B Pleasant Pairs ───────────────────────────────────────────────────


def _s_1541b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = 0
        for i in range(n):
            for j in range(i + 1, n):
                if a[i] * a[j] == (i + 1) + (j + 1):
                    cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _a_1541b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        pos = {v: i + 1 for i, v in enumerate(a)}
        sorted_vals = sorted(a)
        cnt = 0
        for vi_idx in range(n):
            vi = sorted_vals[vi_idx]
            for vj_idx in range(vi_idx + 1, n):
                vj = sorted_vals[vj_idx]
                if vi * vj > 2 * n:
                    break
                if vi * vj == pos[vi] + pos[vj]:
                    cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1541b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = 0
        for i in range(n):
            for j in range(i + 1, n):
                if a[i] * a[j] == i + j:
                    cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m2_1541b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = 0
        for i in range(n):
            for j in range(i + 1, n):
                if a[i] + a[j] == (i + 1) + (j + 1):
                    cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _gen_1541b(rng: random.Random) -> list[str]:
    cases = ["3\n2\n3 1\n3\n6 1 5\n5\n3 1 5 9 2\n"]
    for _ in range(14):
        n = rng.randint(2, 8)
        vals = list(range(1, 2 * n + 1))
        rng.shuffle(vals)
        a = vals[:n]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1141A Game 23 ──────────────────────────────────────────────────────────


def _s_1141a(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    if m % n != 0:
        return "-1\n"
    q = m // n
    cnt = 0
    while q % 2 == 0:
        q //= 2
        cnt += 1
    while q % 3 == 0:
        q //= 3
        cnt += 1
    return str(cnt if q == 1 else -1) + "\n"


def _a_1141a(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    q, r = divmod(m, n)
    if r != 0:
        return "-1\n"
    cnt = 0
    while q > 1:
        if q % 2 == 0:
            q //= 2
        elif q % 3 == 0:
            q //= 3
        else:
            return "-1\n"
        cnt += 1
    return str(cnt) + "\n"


def _m1_1141a(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    q = m // n
    cnt = 0
    while q % 2 == 0:
        q //= 2
        cnt += 1
    while q % 3 == 0:
        q //= 3
        cnt += 1
    return str(cnt if q == 1 else -1) + "\n"


def _m2_1141a(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    if m % n != 0:
        return "-1\n"
    q = m // n
    cnt = 0
    while q % 2 == 0:
        q //= 2
        cnt += 1
    return str(cnt if q == 1 else -1) + "\n"


def _gen_1141a(rng: random.Random) -> list[str]:
    cases = ["120 51840\n", "42 42\n", "48 72\n"]
    for _ in range(11):
        n = rng.randint(1, 20)
        mult = 1
        for _ in range(rng.randint(0, 6)):
            mult *= rng.choice([2, 3])
        if rng.random() < 0.3:
            mult *= rng.choice([5, 7])
        m = n * mult
        cases.append(f"{n} {m}\n")
    return cases


# ─── 2218B The 67th 6-7 Integer Problem ─────────────────────────────────────


def _s_2218b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        nums = list(map(int, ls[i].split()))
        out.append(str(2 * max(nums) - sum(nums)))
    return "\n".join(out) + "\n"


def _a_2218b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        nums = sorted(map(int, ls[i].split()))
        out.append(str(nums[-1] - sum(nums[:-1])))
    return "\n".join(out) + "\n"


def _m1_2218b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        nums = list(map(int, ls[i].split()))
        out.append(str(2 * min(nums) - sum(nums)))
    return "\n".join(out) + "\n"


def _m2_2218b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        nums = list(map(int, ls[i].split()))
        out.append(str(max(nums) - sum(nums)))
    return "\n".join(out) + "\n"


def _gen_2218b(rng: random.Random) -> list[str]:
    cases = ["4\n41 41 41 41 41 41 41\n6 9 4 20 6 7 67\n1 2 3 4 5 6 7\n6 7 6 7 6 7 6\n"]
    for _ in range(11):
        nums = [rng.randint(-67, 67) for _ in range(7)]
        cases.append("1\n" + " ".join(map(str, nums)) + "\n")
    return cases


# ─── 1843C Sum in Binary Tree ───────────────────────────────────────────────


def _s_1843c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        s = 0
        while n >= 1:
            s += n
            n //= 2
        out.append(str(s))
    return "\n".join(out) + "\n"


def _a_1843c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        bits = bin(n)[2:]
        total = 0
        for k in range(len(bits)):
            total += int(bits[: len(bits) - k], 2)
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m1_1843c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        s = 0
        n //= 2
        while n >= 1:
            s += n
            n //= 2
        out.append(str(s))
    return "\n".join(out) + "\n"


def _m2_1843c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        s = 0
        while n >= 1:
            n //= 2
            s += n
        out.append(str(s))
    return "\n".join(out) + "\n"


def _gen_1843c(rng: random.Random) -> list[str]:
    cases = ["5\n3\n10\n71\n1\n2026\n"]
    for _ in range(11):
        n = rng.randint(1, 10**9)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 1931A Recovering a Small String ────────────────────────────────────────


def _s_1931a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        a = n - 52 if n > 52 else 1
        n -= a
        b = n - 26 if n > 26 else 1
        n -= b
        c = n
        out.append(chr(ord("a") + a - 1) + chr(ord("a") + b - 1) + chr(ord("a") + c - 1))
    return "\n".join(out) + "\n"


def _a_1931a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        best = None
        for x in range(1, 27):
            for y in range(1, 27):
                z = n - x - y
                if 1 <= z <= 26:
                    cand = chr(96 + x) + chr(96 + y) + chr(96 + z)
                    if best is None or cand < best:
                        best = cand
        out.append(best)
    return "\n".join(out) + "\n"


def _m1_1931a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        a = min(26, n - 2)
        n -= a
        b = min(26, n - 1)
        n -= b
        c = n
        out.append(chr(ord("a") + a - 1) + chr(ord("a") + b - 1) + chr(ord("a") + c - 1))
    return "\n".join(out) + "\n"


def _m2_1931a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        a = n - 53 if n > 53 else 1
        n -= a
        b = n - 26 if n > 26 else 1
        n -= b
        c = n
        out.append(chr(ord("a") + a - 1) + chr(ord("a") + b - 1) + chr(ord("a") + c - 1))
    return "\n".join(out) + "\n"


def _gen_1931a(rng: random.Random) -> list[str]:
    cases = ["5\n30\n69\n3\n78\n50\n"]
    for _ in range(11):
        n = rng.randint(3, 78)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 1692B All Distinct ─────────────────────────────────────────────────────


def _s_1692b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(n - len(set(a))))
    return "\n".join(out) + "\n"


def _a_1692b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        cnt = 0
        for i in range(1, n):
            if a[i] == a[i - 1]:
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1692b(stdin: str) -> str:
    from collections import Counter

    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = sum(1 for v in Counter(a).values() if v > 1)
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m2_1692b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(len(set(a))))
    return "\n".join(out) + "\n"


def _gen_1692b(rng: random.Random) -> list[str]:
    cases = ["3\n4\n1 2 1 2\n6\n1 2 3 4 5 6\n5\n1 1 1 1 1\n"]
    for _ in range(11):
        n = rng.randint(1, 10)
        a = [rng.randint(1, 5) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1606A AB Balance ───────────────────────────────────────────────────────


def _s_1606a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        if s[0] == s[-1]:
            out.append(s)
        else:
            out.append(s[-1] + s[1:])
    return "\n".join(out) + "\n"


def _a_1606a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = list(ls[i])
        if s[0] != s[-1]:
            s[0] = s[-1]
        out.append("".join(s))
    return "\n".join(out) + "\n"


def _m1_1606a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        if s[0] == s[-1]:
            out.append(s)
        else:
            out.append(s[:-1] + s[0])
    return "\n".join(out) + "\n"


def _m2_1606a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(s)
    return "\n".join(out) + "\n"


def _gen_1606a(rng: random.Random) -> list[str]:
    cases = ["4\nb\nabba\nabc\naabbbabaa\n"]
    for _ in range(11):
        n = rng.randint(1, 12)
        s = "".join(rng.choice("ab") for _ in range(n))
        cases.append(f"1\n{s}\n")
    return cases


# ─── 894A QAQ ────────────────────────────────────────────────────────────────


def _s_894a(stdin: str) -> str:
    s = lines(stdin)[0]
    total_q = s.count("Q")
    seen_q = 0
    ans = 0
    for ch in s:
        if ch == "Q":
            seen_q += 1
        elif ch == "A":
            ans += seen_q * (total_q - seen_q)
    return str(ans) + "\n"


def _a_894a(stdin: str) -> str:
    s = lines(stdin)[0]
    n = len(s)
    prefix = [0] * (n + 1)
    for i, ch in enumerate(s):
        prefix[i + 1] = prefix[i] + (1 if ch == "Q" else 0)
    total_q = prefix[n]
    ans = 0
    for i, ch in enumerate(s):
        if ch == "A":
            before = prefix[i]
            after = total_q - prefix[i + 1]
            ans += before * after
    return str(ans) + "\n"


def _m1_894a(stdin: str) -> str:
    s = lines(stdin)[0]
    ans = 0
    n = len(s)
    for i in range(n - 2):
        if s[i] == "Q" and s[i + 1] == "A" and s[i + 2] == "Q":
            ans += 1
    return str(ans) + "\n"


def _m2_894a(stdin: str) -> str:
    s = lines(stdin)[0]
    total_q = s.count("Q")
    seen_q = 0
    ans = 0
    for ch in s:
        if ch == "Q":
            ans += seen_q * (total_q - seen_q)
        elif ch == "A":
            seen_q += 1
    return str(ans) + "\n"


def _gen_894a(rng: random.Random) -> list[str]:
    cases = ["QAQAQYSYIOIWIN\n", "QAQQQZZYNOIWIN\n"]
    for _ in range(11):
        n = rng.randint(1, 15)
        s = "".join(rng.choice("QAQXYZ") for _ in range(n))
        cases.append(s + "\n")
    return cases


# ─── 2121A Letter Home ──────────────────────────────────────────────────────


def _s_2121a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s = map(int, ls[idx].split())
        idx += 1
        xs = list(map(int, ls[idx].split()))
        idx += 1
        lo, hi = min(xs), max(xs)
        out.append(str(min(abs(s - lo) + (hi - lo), abs(s - hi) + (hi - lo))))
    return "\n".join(out) + "\n"


def _a_2121a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s = map(int, ls[idx].split())
        idx += 1
        xs = list(map(int, ls[idx].split()))
        idx += 1
        lo, hi = min(xs), max(xs)
        span = hi - lo
        best = min(abs(s - lo), abs(s - hi)) + span
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_2121a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s = map(int, ls[idx].split())
        idx += 1
        xs = list(map(int, ls[idx].split()))
        idx += 1
        lo, hi = min(xs), max(xs)
        out.append(str(max(abs(s - lo) + (hi - lo), abs(s - hi) + (hi - lo))))
    return "\n".join(out) + "\n"


def _m2_2121a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, s = map(int, ls[idx].split())
        idx += 1
        xs = list(map(int, ls[idx].split()))
        idx += 1
        lo, hi = min(xs), max(xs)
        out.append(str(min(abs(s - lo), abs(s - hi))))
    return "\n".join(out) + "\n"


def _gen_2121a(rng: random.Random) -> list[str]:
    cases = ["1\n3 0\n1 3 5\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        s = rng.randint(-20, 20)
        pts = sorted(rng.sample(range(-30, 31), n))
        cases.append(f"1\n{n} {s}\n" + " ".join(map(str, pts)) + "\n")
    return cases


# ─── 2184A Social Experiment ────────────────────────────────────────────────


def _s_2184a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        if n == 2:
            out.append("2")
        elif n == 3:
            out.append("3")
        else:
            out.append(str(n % 2))
    return "\n".join(out) + "\n"


def _a_2184a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        best = None
        for a in range(0, n // 2 + 1):
            rem = n - 2 * a
            if rem % 3 == 0:
                b = rem // 3
                achievable = set()
                for ci in range(0, a + 1):
                    for cj in range(0, b + 1):
                        s = ci * 2 + cj * 3
                        achievable.add(s)
                for s in achievable:
                    diff = abs(n - 2 * s)
                    if best is None or diff < best:
                        best = diff
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_2184a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append(str(n % 2))
    return "\n".join(out) + "\n"


def _m2_2184a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        if n == 2:
            out.append("3")
        elif n == 3:
            out.append("2")
        else:
            out.append(str(n % 2))
    return "\n".join(out) + "\n"


def _gen_2184a(rng: random.Random) -> list[str]:
    cases = ["3\n2\n5\n12\n"]
    for _ in range(11):
        n = rng.randint(2, 40)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 1385B Restore the Permutation by Merger ────────────────────────────────


def _s_1385b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        used = [False] * (n + 1)
        p = []
        for v in a:
            if not used[v]:
                used[v] = True
                p.append(v)
        out.append(" ".join(map(str, p)))
    return "\n".join(out) + "\n"


def _a_1385b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        seen: set[int] = set()
        p = []
        for v in a:
            if v not in seen:
                seen.add(v)
                p.append(v)
        out.append(" ".join(map(str, p)))
    return "\n".join(out) + "\n"


def _m1_1385b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(" ".join(map(str, a[:n])))
    return "\n".join(out) + "\n"


def _m2_1385b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(" ".join(map(str, a[0::2])))
    return "\n".join(out) + "\n"


def _gen_1385b(rng: random.Random) -> list[str]:
    cases = ["2\n3\n3 1 2 3 1 2\n2\n2 1 2 1\n"]
    for _ in range(11):
        n = rng.randint(1, 8)
        p = list(range(1, n + 1))
        rng.shuffle(p)
        merged = list(p)
        second = list(p)
        # interleave second copy respecting relative order (random insert positions)
        positions = sorted(rng.sample(range(2 * n), n))
        result = [None] * (2 * n)
        for pos, val in zip(positions, p):
            result[pos] = val
        rest = iter(p)
        j = 0
        for i in range(2 * n):
            if result[i] is None:
                result[i] = next(rest)
        cases.append(f"1\n{n}\n" + " ".join(map(str, result)) + "\n")
    return cases


# ─── Build spec list ─────────────────────────────────────────────────────────


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

    add(
        "1933A",
        "Rearrange an array then negate one contiguous segment to maximize the sum.",
        ({"input": "1\n3\n3 -2 -3\n", "output": "8\n"},),
        _s_1933a,
        _a_1933a,
        {"no_negate": _m1_1933a, "single_negate": _m2_1933a},
        _gen_1933a,
        family="rearrange_negate",
    )
    add(
        "1579A",
        "Determine if a string of A/B/C can be fully erased by repeatedly removing an AB or BC pair.",
        ({"input": "1\nABACAB\n", "output": "NO\n"},),
        _s_1579a,
        _a_1579a,
        {"ac_equal": _m1_1579a, "len_even": _m2_1579a},
        _gen_1579a,
        family="counting",
    )
    add(
        "1669F",
        "Alice eats a prefix and Bob eats a suffix of candies; maximize total eaten with equal sums.",
        ({"input": "1\n8\n1 2 1 3 6 2 5 1\n", "output": "2\n"},),
        _s_1669f,
        _a_1669f,
        {"left_pointer_only": _m1_1669f, "off_by_one_suffix": _m2_1669f},
        _gen_1669f,
        family="two_pointer",
    )
    add(
        "1971C",
        "Determine if two chords on a 12-point clock face intersect.",
        ({"input": "1\n2 9 10 6\n", "output": "YES\n"},),
        _s_1971c,
        _a_1971c,
        {"wrong_pairing": _m1_1971c, "extra_patterns": _m2_1971c},
        _gen_1971c,
        family="geometry",
    )
    add(
        "2123A",
        "Alice/Bob remove numbers 0..n-1 with a+b=3 mod4 pairing constraint; determine the winner.",
        ({"input": "1\n4\n", "output": "Bob\n"},),
        _s_2123a,
        _a_2123a,
        {"flip": _m1_2123a, "mod2": _m2_2123a},
        _gen_2123a,
        family="game",
    )
    add(
        "1828B",
        "Find the maximum k such that swapping elements distance k apart can sort a permutation.",
        ({"input": "1\n3\n1 3 2\n", "output": "1\n"},),
        _s_1828b,
        _a_1828b,
        {"half_array": _m1_1828b, "off_by_one": _m2_1828b},
        _gen_1828b,
        family="gcd",
    )
    add(
        "2008A",
        "Given a ones and b twos, decide if signs can be assigned so the total is zero.",
        ({"input": "1\n0 1\n", "output": "NO\n"},),
        _s_2008a,
        _a_2008a,
        {"ignore_b": _m1_2008a, "ignore_a": _m2_2008a},
        _gen_2008a,
        family="parity",
    )
    add(
        "1669C",
        "Decide if adding 1 to odd- or even-indexed elements can make the whole array one parity.",
        ({"input": "1\n3\n1 2 1\n", "output": "YES\n"},),
        _s_1669c,
        _a_1669c,
        {"single_group": _m1_1669c, "ignore_odd_group": _m2_1669c},
        _gen_1669c,
        family="parity",
    )
    add(
        "1999C",
        "Determine if there is a free gap of length s in a day with n busy intervals.",
        ({"input": "1\n3 3 10\n3 5\n6 8\n9 10\n", "output": "YES\n"},),
        _s_1999c,
        _a_1999c,
        {"ignore_edges": _m1_1999c, "strict_gt": _m2_1999c},
        _gen_1999c,
        family="intervals",
    )
    add(
        "1607B",
        "Simulate/derive a grasshopper's position after n parity-directed jumps.",
        ({"input": "1\n0 1\n", "output": "-1\n"},),
        _s_1607b,
        _a_1607b,
        {"flip_parity": _m1_1607b, "wrong_map": _m2_1607b},
        _gen_1607b,
        family="simulation",
    )
    add(
        "1985D",
        "Find the center of a Manhattan-distance diamond marked with '#' in a grid.",
        ({"input": "1\n5 5\n.....\n..#..\n.###.\n..#..\n.....\n", "output": "3 3\n"},),
        _s_1985d,
        _a_1985d,
        {"corner": _m1_1985d, "swapped": _m2_1985d},
        _gen_1985d,
        family="grid",
    )
    add(
        "1593A",
        "For each of 3 candidates, find min extra votes needed to strictly win.",
        ({"input": "1\n0 0 0\n", "output": "1 1 1\n"},),
        _s_1593a,
        _a_1593a,
        {"no_plus_one": _m1_1593a, "sum_others": _m2_1593a},
        _gen_1593a,
        family="formula",
    )
    add(
        "478B",
        "Split n people into k teams; find min and max possible sum of within-team pairs.",
        ({"input": "1\n5 1\n", "output": "10 10\n"},),
        _s_478b,
        _a_478b,
        {"swapped": _m1_478b, "wrong_max": _m2_478b},
        _gen_478b,
        family="combinatorics",
    )
    add(
        "2033A",
        "Determine who makes the last move in the alternating odd-jump coordinate game.",
        ({"input": "1\n1\n", "output": "Kosuke\n"},),
        _s_2033a,
        _a_2033a,
        {"flip": _m1_2033a, "flip2": _m2_2033a},
        _gen_2033a,
        family="parity",
    )
    add(
        "2060A",
        "Choose a3 to maximize the Fibonacciness of a length-5 array.",
        ({"input": "1\n1 1 3 5\n", "output": "3\n"},),
        _s_2060a,
        _a_2060a,
        {"single_choice": _m1_2060a, "off_by_one_base": _m2_2060a},
        _gen_2060a,
        family="counting",
    )
    add(
        "1872D",
        "Maximize the sum at multiples of x minus the sum at multiples of y over all permutations.",
        ({"input": "1\n10 2 5\n", "output": "33\n"},),
        _s_1872d,
        _a_1872d,
        {"swapped": _m1_1872d, "no_overlap_fix": _m2_1872d},
        _gen_1872d,
        family="formula",
    )
    add(
        "2093A",
        "Determine if k is an 'ideal generator' (every n>=k is a sum of a length-k palindromic array).",
        ({"input": "1\n1\n", "output": "YES\n"},),
        _s_2093a,
        _a_2093a,
        {"flip": _m1_2093a, "exception": _m2_2093a},
        _gen_2093a,
        family="parity",
    )
    add(
        "1790A",
        "Find the length of the longest prefix of a digit string matching the digits of pi.",
        ({"input": "1\n2\n13\n", "output": "0\n"},),
        _s_1790a,
        _a_1790a,
        {"skip_first": _m1_1790a, "shifted": _m2_1790a},
        _gen_1790a,
        family="string_match",
    )
    add(
        "1537A",
        "Min appended non-negative integers so the array's arithmetic mean equals 1.",
        ({"input": "1\n1\n1\n", "output": "0\n"},),
        _s_1537a,
        _a_1537a,
        {"no_special_case": _m1_1537a, "off_by_one": _m2_1537a},
        _gen_1537a,
        family="formula",
    )
    add(
        "1703C",
        "Undo a sequence of +1/-1 wheel moves (mod 10) to recover the original digits.",
        ({"input": "1\n3\n9 3 1\n3 DDD\n4 UDUU\n2 DU\n", "output": "2 1 1\n"},),
        _s_1703c,
        _a_1703c,
        {"wrong_sign": _m1_1703c, "no_mod": _m2_1703c},
        _gen_1703c,
        family="simulation",
    )
    add(
        "978B",
        "Count min deletions of characters so no 3 consecutive equal characters remain.",
        ({"input": "1\n5\naaabc\n", "output": "1\n"},),
        _s_978b,
        _a_978b,
        {"off_by_one": _m1_978b, "flat_one": _m2_978b},
        _gen_978b,
        family="run_length",
    )
    add(
        "2000B",
        "Check that each seated passenger (after the first) sits next to an already-occupied seat.",
        ({"input": "1\n5\n5 4 2 1 3\n", "output": "NO\n"},),
        _s_2000b,
        _a_2000b,
        {"left_only": _m1_2000b, "always_yes": _m2_2000b},
        _gen_2000b,
        family="simulation",
    )
    add(
        "1742E",
        "For each query k, find the max height reachable using only steps of height <= k.",
        ({"input": "1\n4 5\n1 2 1 5\n1 2 4 9 10\n", "output": "1 4 4 9 9\n"},),
        _s_1742e,
        _a_1742e,
        {"strict_lt": _m1_1742e, "ignore_gaps": _m2_1742e},
        _gen_1742e,
        family="binary_search",
    )
    add(
        "1312B",
        "Reorder an array so that j-i never equals a[j]-a[i]; sorting descending works.",
        ({"input": "1\n4\n1 1 3 5\n", "output": "5 3 1 1\n"},),
        _s_1312b,
        _a_1312b,
        {"ascending": _m1_1312b, "identity": _m2_1312b},
        _gen_1312b,
        family="sorting",
        checker="tokens",
    )
    add(
        "2072A",
        "Min operations to set array elements (each in [-p,p]) to reach a target sum k.",
        ({"input": "1\n5 5 3\n", "output": "2\n"},),
        _s_2072a,
        _a_2072a,
        {"no_bounds_check": _m1_2072a, "floor_div": _m2_2072a},
        _gen_2072a,
        family="formula",
    )
    add(
        "1363A",
        "Decide if x elements can be chosen from the array with an odd sum.",
        ({"input": "1\n1 1\n999\n", "output": "Yes\n"},),
        _s_1363a,
        _a_1363a,
        {"even_count": _m1_1363a, "ignore_even": _m2_1363a},
        _gen_1363a,
        family="parity",
        checker="tokens_ci",
    )
    add(
        "2036A",
        "Determine if all adjacent note intervals in a melody are 5 or 7 semitones.",
        ({"input": "1\n2\n114 109\n", "output": "YES\n"},),
        _s_2036a,
        _a_2036a,
        {"any_instead_of_all": _m1_2036a, "first_pair_only": _m2_2036a},
        _gen_2036a,
        family="checking",
    )
    add(
        "1607A",
        "Sum finger travel distance typing a word on a given linear keyboard layout.",
        (
            {
                "input": "1\nqwertyuiopasdfghjklzxcvbnm\nhello\n",
                "output": "39\n",
            },
        ),
        _s_1607a,
        _a_1607a,
        {"no_abs": _m1_1607a, "half_word": _m2_1607a},
        _gen_1607a,
        family="simulation",
    )
    add(
        "1985C",
        "Count prefixes where one element equals the sum of all the rest.",
        ({"input": "1\n4\n1 6 3 2\n", "output": "1\n"},),
        _s_1985c,
        _a_1985c,
        {"sum_equals_max": _m1_1985c, "check_before_update": _m2_1985c},
        _gen_1985c,
        family="running_stats",
    )
    add(
        "1914D",
        "Pick distinct days x,y,z to maximize a[x]+b[y]+c[z].",
        ({"input": "1\n3\n1 2 3\n2 3 4\n3 2 1\n", "output": "9\n"},),
        _s_1914d,
        _a_1914d,
        {"ignore_distinct": _m1_1914d, "partial_distinct": _m2_1914d},
        _gen_1914d,
        family="brute_force",
    )
    add(
        "600B",
        "For each query value, count array elements less than or equal to it.",
        ({"input": "5 4\n1 3 5 7 9\n6 4 2 8\n", "output": "3 2 1 4\n"},),
        _s_600b,
        _a_600b,
        {"bisect_left": _m1_600b, "strict_less": _m2_600b},
        _gen_600b,
        family="binary_search",
        checker="tokens",
    )
    add(
        "1538A",
        "Min moves removing from either end of a row to destroy both the min and max stone.",
        ({"input": "1\n5\n1 5 4 3 2\n", "output": "2\n"},),
        _s_1538a,
        _a_1538a,
        {"missing_option": _m1_1538a, "no_swap": _m2_1538a},
        _gen_1538a,
        family="two_pointer",
    )
    add(
        "1742C",
        "Determine which color stripe (row-red or column-blue) was painted last on an 8x8 grid.",
        (
            {
                "input": (
                    "1\n....B...\n....B...\n....B...\nRRRRRRRR\n....B...\n....B...\n....B...\n....B...\n"
                ),
                "output": "R\n",
            },
        ),
        _s_1742c,
        _a_1742c,
        {"first_row_only": _m1_1742c, "swapped_color": _m2_1742c},
        _gen_1742c,
        family="grid",
    )
    add(
        "2051B",
        "Find the day on which cumulative distance walked (cycling a,b,c) first reaches n.",
        ({"input": "1\n12 1 5 3\n", "output": "5\n"},),
        _s_2051b,
        _a_2051b,
        {"off_by_one_zero_mod": _m1_2051b, "wrong_threshold": _m2_2051b},
        _gen_2051b,
        family="formula",
    )
    add(
        "1471A",
        "Find min and max beauty (sum of ceil(b_i/x)) achievable by merging adjacent elements.",
        ({"input": "1\n3 3\n3 6 9\n", "output": "6 6\n"},),
        _s_1471a,
        _a_1471a,
        {"swapped": _m1_1471a, "floor_min": _m2_1471a},
        _gen_1471a,
        family="formula",
        checker="tokens",
    )
    add(
        "1761A",
        "Decide if two permutations exist with given common-prefix length a and common-suffix length b.",
        ({"input": "1\n1 1 1\n", "output": "Yes\n"},),
        _s_1761a,
        _a_1761a,
        {"off_by_one": _m1_1761a, "missing_special_case": _m2_1761a},
        _gen_1761a,
        family="constructive_check",
        checker="tokens_ci",
    )
    add(
        "1541B",
        "Count index pairs (i,j), i<j, with a_i * a_j == i + j (1-indexed).",
        ({"input": "1\n2\n3 1\n", "output": "1\n"},),
        _s_1541b,
        _a_1541b,
        {"wrong_relation": _m1_1541b, "sum_instead_product": _m2_1541b},
        _gen_1541b,
        family="counting",
    )
    add(
        "1141A",
        "Min doublings/triplings needed to turn n into m (or -1 if impossible).",
        ({"input": "120 51840\n", "output": "7\n"},),
        _s_1141a,
        _a_1141a,
        {"no_remainder_check": _m1_1141a, "no_triple": _m2_1141a},
        _gen_1141a,
        family="factorization",
    )
    add(
        "2218B",
        "Negate exactly 6 of 7 integers to maximize their sum.",
        ({"input": "1\n41 41 41 41 41 41 41\n", "output": "-205\n"},),
        _s_2218b,
        _a_2218b,
        {"use_min": _m1_2218b, "forget_double": _m2_2218b},
        _gen_2218b,
        family="formula",
    )
    add(
        "1843C",
        "Sum vertex numbers on the path from the root to vertex n in the implicit binary tree.",
        ({"input": "1\n3\n", "output": "4\n"},),
        _s_1843c,
        _a_1843c,
        {"skip_first": _m1_1843c, "wrong_order": _m2_1843c},
        _gen_1843c,
        family="bit_manipulation",
    )
    add(
        "1931A",
        "Recover the lexicographically smallest 3-letter word whose letter positions sum to n.",
        ({"input": "1\n30\n", "output": "acz\n"},),
        _s_1931a,
        _a_1931a,
        {"maximize_first": _m1_1931a, "wrong_threshold": _m2_1931a},
        _gen_1931a,
        family="greedy",
    )
    add(
        "1692B",
        "Count elements that must change so all array elements become distinct.",
        ({"input": "1\n4\n1 2 1 2\n", "output": "2\n"},),
        _s_1692b,
        _a_1692b,
        {"distinct_values_only": _m1_1692b, "wrong_formula": _m2_1692b},
        _gen_1692b,
        family="counting",
    )
    add(
        "1606A",
        "Change the minimum number of characters so occurrences of 'ab' equal occurrences of 'ba'.",
        ({"input": "1\nb\n", "output": "b\n"},),
        _s_1606a,
        _a_1606a,
        {"change_last": _m1_1606a, "no_change": _m2_1606a},
        _gen_1606a,
        family="string",
    )
    add(
        "894A",
        "Count subsequences 'QAQ' in a string.",
        ({"input": "QAQAQYSYIOIWIN\n", "output": "4\n"},),
        _s_894a,
        _a_894a,
        {"contiguous_only": _m1_894a, "swapped_roles": _m2_894a},
        _gen_894a,
        family="counting",
    )
    add(
        "2121A",
        "Min steps to visit every point in a sorted list starting from s (go to one end, then the other).",
        ({"input": "1\n3 0\n1 3 5\n", "output": "5\n"},),
        _s_2121a,
        _a_2121a,
        {"maximize": _m1_2121a, "missing_span": _m2_2121a},
        _gen_2121a,
        family="formula",
    )
    add(
        "2184A",
        "Min possible difference between two civilizations formed from teams of size 2 or 3.",
        ({"input": "1\n2\n", "output": "2\n"},),
        _s_2184a,
        _a_2184a,
        {"ignore_special_cases": _m1_2184a, "swap_special_cases": _m2_2184a},
        _gen_2184a,
        family="formula",
    )
    add(
        "1385B",
        "Recover permutation p from the sequence formed by merging p with itself.",
        ({"input": "1\n3\n3 1 2 3 1 2\n", "output": "3 1 2\n"},),
        _s_1385b,
        _a_1385b,
        {"truncate": _m1_1385b, "reverse_scan": _m2_1385b},
        _gen_1385b,
        family="reconstruction",
        checker="tokens",
    )

    return specs


SPECS = _build()

_KEEP = ['1933A', '1579A', '1669F', '1971C', '2123A', '1828B', '2008A', '1669C', '1999C', '1607B', '1985D', '1593A', '478B', '2033A', '2060A', '1872D', '2093A', '1790A', '1537A', '1703C', '978B', '2000B', '1742E', '1312B', '2072A', '1363A', '2036A', '1607A', '1985C', '1914D', '600B', '1538A', '1742C', '2051B', '1471A', '1761A', '1541B', '1141A', '2218B', '1843C', '1931A', '1692B', '1606A', '894A', '2121A', '2184A', '1385B']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
