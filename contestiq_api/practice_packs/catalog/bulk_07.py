"""Dual-oracle ProblemOracleSpec entries generated from catalog/batches/batch_07.json."""

from __future__ import annotations

import math
import random

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no


# ─── 1941C Rudolf and the Ugly String ────────────────────────────────────────


def _s_1941c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = list(ls[idx])
        idx += 1
        ans = 0
        i = 0
        n = len(s)
        while i <= n - 3:
            if s[i:i + 5] == list("mapie"):
                ans += 1
                i += 5
            elif s[i:i + 3] == list("map") or s[i:i + 3] == list("pie"):
                ans += 1
                i += 3
            else:
                i += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1941c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        ans = 0
        for pat in ("mapie", "pie", "map"):
            chars = list(s)
            pos = 0
            plen = len(pat)
            mid = plen // 2
            joined = "".join(chars)
            while True:
                found = joined.find(pat, pos)
                if found == -1:
                    break
                chars[found + mid] = "?"
                joined = "".join(chars)
                ans += 1
                pos = found + plen
            s = joined
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1941c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        out.append(str(s.count("map") + s.count("pie")))
    return "\n".join(out) + "\n"


def _m2_1941c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = list(ls[idx])
        idx += 1
        ans = 0
        i = 0
        n = len(s)
        while i <= n - 3:
            if s[i:i + 5] == list("mapie"):
                i += 5
            elif s[i:i + 3] == list("map") or s[i:i + 3] == list("pie"):
                ans += 1
                i += 3
            else:
                i += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1941c(rng: random.Random) -> list[str]:
    cases = [
        "6\n9\nmmapnapie\n9\nazabazapi\n8\nmappppie\n18\nmapmapmapmapmapmap\n1\np\n11\npppiepieeee\n",
        "3\n5\nmapie\n10\nmapiemapie\n7\nxmapiex\n",
    ]
    alphabet = "mapie" + "xyz"
    for _ in range(12):
        n = rng.randint(1, 15)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        if rng.random() < 0.5:
            pos = rng.randint(0, max(0, n - 5))
            s = s[:pos] + "mapie" + s[pos + 5:]
        cases.append(f"1\n{len(s)}\n{s}\n")
    return cases


# ─── 1335C Two Teams Composing ───────────────────────────────────────────────


def _s_1335c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        m = int(ls[idx])
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        cnt: dict[int, int] = {}
        for v in a + b:
            cnt[v] = cnt.get(v, 0) + 1
        d = len(cnt)
        mx = max(cnt.values())
        out.append(str(d + mx - 1))
    return "\n".join(out) + "\n"


def _a_1335c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        m = int(ls[idx])
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        combined = sorted(a + b)
        distinct = 1
        best_run = 1
        cur_run = 1
        for i in range(1, len(combined)):
            if combined[i] == combined[i - 1]:
                cur_run += 1
            else:
                distinct += 1
                cur_run = 1
            best_run = max(best_run, cur_run)
        out.append(str(distinct + best_run - 1))
    return "\n".join(out) + "\n"


def _m1_1335c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        m = int(ls[idx])
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        cnt: dict[int, int] = {}
        for v in a + b:
            cnt[v] = cnt.get(v, 0) + 1
        d = len(cnt)
        out.append(str(d))
    return "\n".join(out) + "\n"


def _m2_1335c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        m = int(ls[idx])
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        cnt: dict[int, int] = {}
        for v in a + b:
            cnt[v] = cnt.get(v, 0) + 1
        mx = max(cnt.values())
        out.append(str(n + m - mx + 1))
    return "\n".join(out) + "\n"


def _gen_1335c(rng: random.Random) -> list[str]:
    cases = ["2\n1\n3\n1\n4\n2\n1 2\n2\n2 2\n"]
    for _ in range(13):
        n = rng.randint(1, 6)
        m = rng.randint(1, 6)
        a = [rng.randint(1, 5) for _ in range(n)]
        b = [rng.randint(1, 5) for _ in range(m)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + f"\n{m}\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 1977A Little Nikita ─────────────────────────────────────────────────────


def _s_1977a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, m = map(int, ls[i].split())
        out.append(yes_no(n >= m and (n - m) % 2 == 0).strip().capitalize())
    return "\n".join(out) + "\n"


def _a_1977a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, m = map(int, ls[i].split())
        ok = n >= m and (n % 2) == (m % 2)
        out.append("Yes" if ok else "No")
    return "\n".join(out) + "\n"


def _m1_1977a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, m = map(int, ls[i].split())
        out.append("Yes" if n >= m else "No")
    return "\n".join(out) + "\n"


def _m2_1977a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n, m = map(int, ls[i].split())
        out.append("Yes" if (n - m) % 2 == 0 else "No")
    return "\n".join(out) + "\n"


def _gen_1977a(rng: random.Random) -> list[str]:
    cases = ["3\n3 3\n2 4\n5 3\n"]
    for _ in range(13):
        n = rng.randint(1, 100)
        m = rng.randint(1, 100)
        cases.append(f"1\n{n} {m}\n")
    return cases


# ─── 2131A Lever ──────────────────────────────────────────────────────────────


def _s_2131a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        total = sum(max(a[i] - b[i], 0) for i in range(n))
        out.append(str(total + 1))
    return "\n".join(out) + "\n"


def _a_2131a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        total = 1
        for i in range(n):
            diff = a[i] - b[i]
            if diff > 0:
                total += diff
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m1_2131a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        total = sum(max(a[i] - b[i], 0) for i in range(n))
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m2_2131a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        total = sum(abs(a[i] - b[i]) for i in range(n))
        out.append(str(total + 1))
    return "\n".join(out) + "\n"


def _gen_2131a(rng: random.Random) -> list[str]:
    cases = ["2\n2\n6 4\n5 5\n1\n1\n1\n"]
    for _ in range(13):
        n = rng.randint(1, 6)
        a = [rng.randint(1, 10) for _ in range(n)]
        b = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 1490C Sum of Cubes ───────────────────────────────────────────────────────


def _s_1490c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x = int(ls[i])
        found = False
        a = 1
        while a * a * a < x:
            rem = x - a * a * a
            b = round(rem ** (1.0 / 3.0))
            for cand in (b - 1, b, b + 1):
                if cand >= 1 and cand ** 3 == rem:
                    found = True
                    break
            if found:
                break
            a += 1
        out.append(yes_no(found).strip())
    return "\n".join(out) + "\n"


def _a_1490c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    cubes = set()
    a = 1
    while a ** 3 <= 10 ** 12:
        cubes.add(a ** 3)
        a += 1
    out = []
    for i in range(1, t + 1):
        x = int(ls[i])
        found = False
        a = 1
        while a ** 3 < x:
            if (x - a ** 3) in cubes:
                found = True
                break
            a += 1
        out.append("YES" if found else "NO")
    return "\n".join(out) + "\n"


def _m1_1490c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x = int(ls[i])
        found = False
        a = 1
        while a * a * a <= x:
            rem = x - a * a * a
            b = round(rem ** (1.0 / 3.0))
            for cand in (b - 1, b, b + 1):
                if cand >= 0 and cand ** 3 == rem:
                    found = True
                    break
            if found:
                break
            a += 1
        out.append("YES" if found else "NO")
    return "\n".join(out) + "\n"


def _m2_1490c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x = int(ls[i])
        found = False
        a = 1
        while a * a * a < x:
            rem = x - a * a * a
            b = round(rem ** (1.0 / 2.0))
            for cand in (b - 1, b, b + 1):
                if cand >= 1 and cand ** 3 == rem:
                    found = True
                    break
            if found:
                break
            a += 1
        out.append("YES" if found else "NO")
    return "\n".join(out) + "\n"


def _gen_1490c(rng: random.Random) -> list[str]:
    cases = ["7\n1\n2\n4\n34\n35\n16\n703657519796\n"]
    for _ in range(13):
        x = rng.randint(1, 2000)
        cases.append(f"1\n{x}\n")
    return cases


# ─── 2091A Olympiad Date ─────────────────────────────────────────────────────


def _s_2091a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 10
        need = {0: 3, 1: 1, 2: 2, 3: 1, 5: 1}
        ans = 0
        for i, d in enumerate(a):
            cnt[d] += 1
            if ans == 0 and all(cnt[k] >= v for k, v in need.items()):
                ans = i + 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_2091a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        c0 = c1 = c2 = c3 = c5 = 0
        ans = 0
        for i, d in enumerate(a):
            if d == 0:
                c0 += 1
            elif d == 1:
                c1 += 1
            elif d == 2:
                c2 += 1
            elif d == 3:
                c3 += 1
            elif d == 5:
                c5 += 1
            if ans == 0 and c0 >= 3 and c1 >= 1 and c2 >= 2 and c3 >= 1 and c5 >= 1:
                ans = i + 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_2091a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 10
        need = {0: 2, 1: 1, 2: 2, 3: 1, 5: 1}
        ans = 0
        for i, d in enumerate(a):
            cnt[d] += 1
            if ans == 0 and all(cnt[k] >= v for k, v in need.items()):
                ans = i + 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m2_2091a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 10
        need = {0: 3, 1: 1, 2: 2, 3: 1, 5: 1}
        for d in a:
            cnt[d] += 1
        out.append(str(n if all(cnt[k] >= v for k, v in need.items()) else 0))
    return "\n".join(out) + "\n"


def _gen_2091a(rng: random.Random) -> list[str]:
    cases = [
        "4\n10\n2 0 1 2 3 2 5 0 0 1\n8\n2 0 1 2 3 2 5 0\n8\n2 0 1 0 3 2 5 0\n16\n2 3 1 2 3 0 1 9 2 1 0 3 5 4 0 3\n"
    ]
    for _ in range(13):
        n = rng.randint(1, 12)
        a = [rng.randint(0, 9) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1660A Vasya and Coins ────────────────────────────────────────────────────


def _s_1660a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        out.append(str(1 if a == 0 else a + 2 * b + 1))
    return "\n".join(out) + "\n"


def _a_1660a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        if a == 0:
            out.append("1")
        else:
            out.append(str(a + 2 * b + 1))
    return "\n".join(out) + "\n"


def _m1_1660a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        out.append(str(a + 2 * b + 1))
    return "\n".join(out) + "\n"


def _m2_1660a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        out.append(str(1 if a == 0 else a + b + 1))
    return "\n".join(out) + "\n"


def _gen_1660a(rng: random.Random) -> list[str]:
    cases = ["4\n1 1\n4 0\n0 2\n0 0\n"]
    for _ in range(13):
        a = rng.randint(0, 20)
        b = rng.randint(0, 20)
        cases.append(f"1\n{a} {b}\n")
    return cases


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


# ─── 1726A Mainak and Array ──────────────────────────────────────────────────


def _s_1726a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ans = a[-1] - min(a)
        ans = max(ans, max(a) - a[0])
        for i in range(n):
            ans = max(ans, a[i - 1] - a[i])
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1726a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        best = -10 ** 9
        for i in range(n):
            best = max(best, a[(i - 1) % n] - a[i])
        for i in range(1, n):
            best = max(best, a[i] - a[0])
        for i in range(n - 1):
            best = max(best, a[n - 1] - a[i])
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1726a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(a[-1] - a[0]))
    return "\n".join(out) + "\n"


def _m2_1726a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ans = max(a) - a[0]
        for i in range(n):
            ans = max(ans, a[i - 1] - a[i])
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1726a(rng: random.Random) -> list[str]:
    cases = ["1\n6\n1 3 9 11 5 7\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1696B NIT Destroys the Universe ─────────────────────────────────────────


def _s_1696b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        if all(v == 0 for v in a):
            out.append("0")
            continue
        first = next(i for i, v in enumerate(a) if v != 0)
        last = max(i for i, v in enumerate(a) if v != 0)
        seg = a[first:last + 1]
        if all(v != 0 for v in seg):
            out.append("1")
        else:
            out.append("2")
    return "\n".join(out) + "\n"


def _a_1696b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        nz = [i for i, v in enumerate(a) if v != 0]
        if not nz:
            out.append("0")
        elif all(a[i] != 0 for i in range(nz[0], nz[-1] + 1)):
            out.append("1")
        else:
            out.append("2")
    return "\n".join(out) + "\n"


def _m1_1696b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        if all(v == 0 for v in a):
            out.append("0")
        elif 0 not in a:
            out.append("1")
        else:
            out.append("2")
    return "\n".join(out) + "\n"


def _m2_1696b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append("2")
    return "\n".join(out) + "\n"


def _gen_1696b(rng: random.Random) -> list[str]:
    cases = ["3\n5\n0 0 0 0 0\n4\n0 1 2 0\n4\n1 0 2 3\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        a = [rng.choice([0, 0, 1, 2, 3]) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1353C Board Moves ───────────────────────────────────────────────────────


def _s_1353c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        total = 0
        for k in range(1, n // 2 + 1):
            total += k * k
        out.append(str(total * 8))
    return "\n".join(out) + "\n"


def _a_1353c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        moves = 0
        layer = 8
        for k in range(1, n // 2 + 1):
            moves += layer * k
            layer += 8
        out.append(str(moves))
    return "\n".join(out) + "\n"


def _m1_1353c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        total = 0
        for k in range(1, n // 2 + 1):
            total += k * k
        out.append(str(total * 4))
    return "\n".join(out) + "\n"


def _m2_1353c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        total = 0
        for k in range(1, n // 2 + 1):
            total += k
        out.append(str(total * 8))
    return "\n".join(out) + "\n"


def _gen_1353c(rng: random.Random) -> list[str]:
    cases = ["3\n1\n3\n5\n"]
    for _ in range(13):
        n = rng.randrange(1, 30, 2)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 1560B Who's Opposite? ───────────────────────────────────────────────────


def _s_1560b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        n = 2 * abs(a - b)
        if a > n or b > n or c > n or n == 0:
            out.append("-1")
        else:
            d = c + n // 2
            while d > n:
                d -= n
            out.append(str(d))
    return "\n".join(out) + "\n"


def _a_1560b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        n = 2 * abs(a - b)
        if n == 0 or a > n or b > n or c > n:
            out.append("-1")
        else:
            half = n // 2
            d = c + half if c <= half else c - half
            out.append(str(d))
    return "\n".join(out) + "\n"


def _m1_1560b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        n = 2 * abs(a - b)
        if a > n or b > n or c > n or n == 0:
            out.append("-1")
        else:
            d = c + n // 2 + 1
            while d > n:
                d -= n
            while d < 1:
                d += n
            out.append(str(d))
    return "\n".join(out) + "\n"


def _m2_1560b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, ls[i].split())
        n = abs(a - b)
        if a > n or b > n or c > n or n == 0:
            out.append("-1")
        else:
            d = c + n // 2
            while d > n:
                d -= n
            out.append(str(d))
    return "\n".join(out) + "\n"


def _gen_1560b(rng: random.Random) -> list[str]:
    cases = ["3\n6 2 4\n2 3 1\n2 4 10\n"]
    for _ in range(13):
        a = rng.randint(1, 10)
        b = rng.randint(1, 10)
        c = rng.randint(1, 20)
        cases.append(f"1\n{a} {b} {c}\n")
    return cases


# ─── 1325B CopyCopyCopyCopyCopy ──────────────────────────────────────────────


def _s_1325b(stdin: str) -> str:
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


def _a_1325b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        cnt = 1
        for i in range(1, n):
            if a[i] != a[i - 1]:
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1325b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1325b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(max(a)))
    return "\n".join(out) + "\n"


def _gen_1325b(rng: random.Random) -> list[str]:
    cases = ["2\n5\n3 2 1 3 2\n1\n5\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        a = [rng.randint(1, 5) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1917B Erase First or Second Letter ──────────────────────────────────────


def _s_1917b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        seen: set[str] = set()
        ans = 0
        for ch in s:
            seen.add(ch)
            ans += len(seen)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1917b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        cnt = [0] * 26
        distinct = 0
        ans = 0
        for ch in s:
            k = ord(ch) - 97
            if cnt[k] == 0:
                distinct += 1
            cnt[k] += 1
            ans += distinct
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1917b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        out.append(str(len(set(s))))
    return "\n".join(out) + "\n"


def _m2_1917b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        seen: set[str] = set()
        ans = 0
        for ch in s:
            ans += len(seen)
            seen.add(ch)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1917b(rng: random.Random) -> list[str]:
    cases = ["2\n11\nabracadabra\n1\na\n"]
    for _ in range(13):
        n = rng.randint(1, 10)
        s = "".join(rng.choice("abc") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 1702A Round Down the Price ──────────────────────────────────────────────


def _s_1702a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        m = int(ls[i])
        k = 10 ** (len(str(m)) - 1)
        out.append(str(m - k))
    return "\n".join(out) + "\n"


def _a_1702a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        m = int(ls[i])
        k = 1
        while k * 10 <= m:
            k *= 10
        out.append(str(m - k))
    return "\n".join(out) + "\n"


def _m1_1702a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        m = int(ls[i])
        k = 10 ** len(str(m))
        out.append(str(m - k))
    return "\n".join(out) + "\n"


def _m2_1702a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        m = int(ls[i])
        out.append(str(m // 2))
    return "\n".join(out) + "\n"


def _gen_1702a(rng: random.Random) -> list[str]:
    cases = ["7\n1\n2\n178\n20\n999999999\n9000\n987654321\n"]
    for _ in range(13):
        m = rng.randint(1, 10 ** 6)
        cases.append(f"1\n{m}\n")
    return cases


# ─── 1980B Choosing Cubes ────────────────────────────────────────────────────


def _s_1980b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, f, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        f -= 1
        k -= 1
        x = a[f]
        sa = sorted(a, reverse=True)
        if sa[k] > x:
            out.append("NO")
        elif sa[k] < x:
            out.append("YES")
        else:
            out.append("YES" if k == n - 1 or sa[k + 1] < x else "MAYBE")
    return "\n".join(out) + "\n"


def _a_1980b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, f, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        x = a[f - 1]
        more = sum(1 for v in a if v > x)
        equal = sum(1 for v in a if v == x)
        if more >= k:
            out.append("NO")
        elif more + equal <= k:
            out.append("YES")
        else:
            out.append("MAYBE")
    return "\n".join(out) + "\n"


def _m1_1980b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, f, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        x = a[f - 1]
        more = sum(1 for v in a if v > x)
        equal = sum(1 for v in a if v == x)
        if more >= k:
            out.append("NO")
        elif more + equal < k:
            out.append("YES")
        else:
            out.append("MAYBE")
    return "\n".join(out) + "\n"


def _m2_1980b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, f, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        x = a[f - 1]
        more = sum(1 for v in a if v > x)
        out.append("YES" if more < k else "NO")
    return "\n".join(out) + "\n"


def _gen_1980b(rng: random.Random) -> list[str]:
    cases = ["1\n5 2 2\n4 3 3 2 3\n"]
    for _ in range(13):
        n = rng.randint(2, 8)
        f = rng.randint(1, n)
        k = rng.randint(1, n)
        a = [rng.randint(1, 5) for _ in range(n)]
        cases.append(f"1\n{n} {f} {k}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 2117A False Alarm ───────────────────────────────────────────────────────


def _s_2117a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        closed = [i for i, v in enumerate(a) if v == 1]
        l, r = min(closed), max(closed)
        out.append(yes_no(x >= r - l + 1).strip())
    return "\n".join(out) + "\n"


def _a_2117a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        l = next(i for i in range(n) if a[i] == 1)
        r = n - 1 - next(i for i in range(n) if a[n - 1 - i] == 1)
        out.append("YES" if r - l + 1 <= x else "NO")
    return "\n".join(out) + "\n"


def _m1_2117a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        closed = [i for i, v in enumerate(a) if v == 1]
        l, r = min(closed), max(closed)
        out.append("YES" if x >= r - l else "NO")
    return "\n".join(out) + "\n"


def _m2_2117a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append("YES" if x >= sum(a) else "NO")
    return "\n".join(out) + "\n"


def _gen_2117a(rng: random.Random) -> list[str]:
    cases = [
        "3\n5 1\n0 0 1 0 0\n5 3\n1 0 1 0 1\n3 10\n1 1 1\n",
        "2\n5 3\n1 0 0 1 0\n5 4\n1 0 0 1 0\n",
    ]
    for _ in range(12):
        n = rng.randint(1, 8)
        a = [rng.choice([0, 1]) for _ in range(n)]
        if 1 not in a:
            a[rng.randint(0, n - 1)] = 1
        x = rng.randint(1, 8)
        cases.append(f"1\n{n} {x}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1840A Cipher Shifer ─────────────────────────────────────────────────────


def _s_1840a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        i = 0
        n = len(s)
        res = []
        while i < n:
            ch = s[i]
            j = i + 1
            while s[j] != ch:
                j += 1
            res.append(ch)
            i = j + 1
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _a_1840a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        res = []
        pos = 0
        n = len(s)
        while pos < n:
            end = s.index(s[pos], pos + 1)
            res.append(s[pos])
            pos = end + 1
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _m1_1840a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        out.append("".join(sorted(set(s))))
    return "\n".join(out) + "\n"


def _m2_1840a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        i = 0
        n = len(s)
        res = []
        while i < n:
            ch = s[i]
            j = i + 1
            while j < n and s[j] != ch:
                j += 1
            res.append(ch)
            i += 2
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _gen_1840a(rng: random.Random) -> list[str]:
    cases = ["3\n8\nabacabac\n5\nqzxcq\n20\nccooddeeffoorrcceess\n"]
    for _ in range(13):
        letters = "codeforces"
        base = "".join(rng.choice(letters) for _ in range(rng.randint(1, 4)))
        s = []
        for ch in base:
            filler_len = rng.randint(0, 3)
            filler_alpha = [c for c in "abcdefghij" if c != ch]
            s.append(ch)
            s.extend(rng.choice(filler_alpha) for _ in range(filler_len))
            s.append(ch)
        joined = "".join(s)
        cases.append(f"1\n{len(joined)}\n{joined}\n")
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


# ─── 709A Juicer ──────────────────────────────────────────────────────────────


def _s_709a(stdin: str) -> str:
    ls = lines(stdin)
    n, b, d = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    juice = 0
    empties = 0
    for orange in a:
        if orange <= b:
            juice += orange
            if juice > d:
                empties += 1
                juice = 0
    return str(empties) + "\n"


def _a_709a(stdin: str) -> str:
    ls = lines(stdin)
    n, b, d = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    total = 0
    empties = 0
    for orange in a:
        if orange > b:
            continue
        total += orange
        if total > d:
            empties += 1
            total = 0
    return str(empties) + "\n"


def _m1_709a(stdin: str) -> str:
    ls = lines(stdin)
    n, b, d = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    juice = 0
    empties = 0
    for orange in a:
        if orange <= b:
            juice += orange
            if juice > d:
                empties += 1
    return str(empties) + "\n"


def _m2_709a(stdin: str) -> str:
    ls = lines(stdin)
    n, b, d = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    juice = 0
    empties = 0
    for orange in a:
        juice += orange
        if juice > d:
            empties += 1
            juice = 0
    return str(empties) + "\n"


def _gen_709a(rng: random.Random) -> list[str]:
    cases = ["2 7 10\n5 6\n", "1 3 10\n5\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        b = rng.randint(3, 10)
        d = rng.randint(b, 20)
        a = [rng.randint(1, 12) for _ in range(n)]
        cases.append(f"{n} {b} {d}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 2126B No Casino in the Mountains ────────────────────────────────────────


def _s_2126b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ans = 0
        cnt = 0
        for v in a:
            if v == 1:
                ans += (cnt + 1) // (k + 1)
                cnt = 0
            else:
                cnt += 1
        ans += (cnt + 1) // (k + 1)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_2126b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        segments = []
        cnt = 0
        for v in a:
            if v == 1:
                segments.append(cnt)
                cnt = 0
            else:
                cnt += 1
        segments.append(cnt)
        ans = sum((seg + 1) // (k + 1) for seg in segments)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_2126b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ans = 0
        cnt = 0
        for v in a:
            if v == 1:
                ans += cnt // k
                cnt = 0
            else:
                cnt += 1
        ans += cnt // k
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m2_2126b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        good = sum(1 for v in a if v == 0)
        out.append(str(good // k))
    return "\n".join(out) + "\n"


def _gen_2126b(rng: random.Random) -> list[str]:
    cases = ["3\n7 3\n0 0 0 1 0 0 0\n7 3\n0 0 0 0 0 0 0\n4 1\n1 1 1 1\n"]
    for _ in range(13):
        n = rng.randint(1, 10)
        k = rng.randint(1, n)
        a = [rng.choice([0, 0, 1]) for _ in range(n)]
        cases.append(f"1\n{n} {k}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1992B Angry Monk ────────────────────────────────────────────────────────


def _s_1992b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mx = max(a)
        out.append(str(2 * (n - mx) - k + 1))
    return "\n".join(out) + "\n"


def _a_1992b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        mx = a[-1]
        rest_sum = n - mx
        out.append(str(rest_sum * 2 - (k - 1)))
    return "\n".join(out) + "\n"


def _m1_1992b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mx = max(a)
        out.append(str(2 * (n - mx) - k))
    return "\n".join(out) + "\n"


def _m2_1992b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mn = min(a)
        out.append(str(2 * (n - mn) - k + 1))
    return "\n".join(out) + "\n"


def _gen_1992b(rng: random.Random) -> list[str]:
    cases = ["1\n5 2\n3 2\n"]
    for _ in range(13):
        k = rng.randint(2, 5)
        parts = [rng.randint(1, 8) for _ in range(k)]
        n = sum(parts)
        cases.append(f"1\n{n} {k}\n" + " ".join(map(str, parts)) + "\n")
    return cases


# ─── 1832B Maximum Sum ───────────────────────────────────────────────────────


def _s_1832b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        pref = [0] * (n + 1)
        for i in range(n):
            pref[i + 1] = pref[i] + a[i]
        ans = 0
        for i in range(k + 1):
            l = 2 * i
            r = n - (k - i)
            ans = max(ans, pref[r] - pref[l])
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1832b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        best = 0
        for m in range(k + 1):
            removed_min = 2 * m
            removed_max = k - m
            seg = a[removed_min:n - removed_max]
            best = max(best, sum(seg))
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1832b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        pref = [0] * (n + 1)
        for i in range(n):
            pref[i + 1] = pref[i] + a[i]
        out.append(str(pref[n - k] - pref[0]))
    return "\n".join(out) + "\n"


def _m2_1832b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        pref = [0] * (n + 1)
        for i in range(n):
            pref[i + 1] = pref[i] + a[i]
        ans = 0
        for i in range(k + 1):
            l = i
            r = n - (k - i)
            if 0 <= l <= r <= n:
                ans = max(ans, pref[r] - pref[l])
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1832b(rng: random.Random) -> list[str]:
    cases = ["1\n7 1\n1 2 5 6 10 6 8\n"]
    for _ in range(13):
        n = rng.randint(3, 12)
        k = rng.randint(1, max(1, (n - 1) // 2))
        a = rng.sample(range(1, 100), n)
        cases.append(f"1\n{n} {k}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 2171A Shizuku Hoshikawa and Farm Legs ───────────────────────────────────


def _s_2171a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append(str(n // 4 + 1) if n % 2 == 0 else "0")
    return "\n".join(out) + "\n"


def _a_2171a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        if n % 2 != 0:
            out.append("0")
            continue
        cnt = 0
        y = 0
        while 4 * y <= n:
            x = n - 4 * y
            if x % 2 == 0 and x >= 0:
                cnt += 1
            y += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_2171a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append(str(n // 4) if n % 2 == 0 else "0")
    return "\n".join(out) + "\n"


def _m2_2171a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append(str(n // 4 + 1))
    return "\n".join(out) + "\n"


def _gen_2171a(rng: random.Random) -> list[str]:
    cases = ["5\n2\n3\n4\n6\n100\n"]
    for _ in range(13):
        n = rng.randint(1, 100)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 139A Petr and Book ──────────────────────────────────────────────────────


_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _s_139a(stdin: str) -> str:
    ls = lines(stdin)
    start = ls[0].strip()
    a = [int(ls[i]) for i in range(1, 8)]
    total = sum(a)
    idx0 = _DAYS.index(start)
    result_idx = (idx0 + total) % 7
    return _DAYS[result_idx] + "\n"


def _a_139a(stdin: str) -> str:
    ls = lines(stdin)
    start = ls[0].strip()
    a = [int(ls[i]) for i in range(1, 8)]
    total = sum(a)
    idx0 = _DAYS.index(start)
    shift = total % 7
    result_idx = idx0
    for _ in range(shift):
        result_idx = (result_idx + 1) % 7
    return _DAYS[result_idx] + "\n"


def _m1_139a(stdin: str) -> str:
    ls = lines(stdin)
    start = ls[0].strip()
    a = [int(ls[i]) for i in range(1, 8)]
    total = sum(a)
    idx0 = _DAYS.index(start)
    result_idx = (idx0 + total - 1) % 7
    return _DAYS[result_idx] + "\n"


def _m2_139a(stdin: str) -> str:
    ls = lines(stdin)
    start = ls[0].strip()
    a = [int(ls[i]) for i in range(1, 8)]
    total = sum(a) - a[0]
    idx0 = _DAYS.index(start)
    result_idx = (idx0 + total) % 7
    return _DAYS[result_idx] + "\n"


def _gen_139a(rng: random.Random) -> list[str]:
    cases = ["monday\n1\n2\n3\n4\n5\n6\n7\n", "sunday\n1\n1\n1\n1\n1\n1\n1\n"]
    for _ in range(13):
        start = rng.choice(_DAYS)
        a = [rng.randint(0, 1000) for _ in range(7)]
        cases.append(start + "\n" + "\n".join(map(str, a)) + "\n")
    return cases


# ─── 1876A Helmets in Night Light ────────────────────────────────────────────


def _s_1876a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, p = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        order = sorted(range(n), key=lambda i: b[i])
        total = p
        remaining = n - 1
        for i in order:
            if remaining <= 0 or b[i] >= p:
                break
            cnt = min(remaining, a[i])
            total += cnt * b[i]
            remaining -= cnt
        total += p * remaining
        out.append(str(total))
    return "\n".join(out) + "\n"


def _a_1876a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, p = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        pairs = sorted(zip(b, a))
        total = 0
        remaining = n - 1
        for cost, cap in pairs:
            if cost >= p:
                break
            take = cap if cap < remaining else remaining
            total += take * cost
            remaining -= take
            if remaining == 0:
                break
        total += p * remaining + p
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m1_1876a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, p = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        order = sorted(range(n), key=lambda i: b[i])
        total = p
        remaining = n - 1
        for i in order:
            if remaining <= 0:
                break
            cnt = min(remaining, a[i])
            total += cnt * b[i]
            remaining -= cnt
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m2_1876a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, p = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(p * n))
    return "\n".join(out) + "\n"


def _gen_1876a(rng: random.Random) -> list[str]:
    cases = ["1\n6 3\n1 2 3 4 2 2\n2 3 1 5 4 6\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        p = rng.randint(1, 10)
        a = [rng.randint(1, 6) for _ in range(n)]
        b = [rng.randint(1, 10) for _ in range(n)]
        cases.append(f"1\n{n} {p}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 1974A Phone Desktop ─────────────────────────────────────────────────────


def _s_1974a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        icons = a + b
        out.append(str((icons + 23) // 24))
    return "\n".join(out) + "\n"


def _a_1974a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        total = a + b
        screens = total // 24
        if total % 24 != 0:
            screens += 1
        out.append(str(screens))
    return "\n".join(out) + "\n"


def _m1_1974a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        icons = a + b
        out.append(str(icons // 24))
    return "\n".join(out) + "\n"


def _m2_1974a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, ls[i].split())
        icons = a + b
        out.append(str((icons + 23) // 25))
    return "\n".join(out) + "\n"


def _gen_1974a(rng: random.Random) -> list[str]:
    cases = ["4\n1 1\n7 2\n0 0\n24 0\n"]
    for _ in range(13):
        a = rng.randint(0, 99)
        b = rng.randint(0, 99)
        cases.append(f"1\n{a} {b}\n")
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
    ls = lines(stdin)
    s1 = ls[0].strip()
    s2 = ls[1].strip()
    ax = sum(1 if c == "+" else -1 for c in s1)
    bx = 0
    qcnt = 0
    for c in s2:
        if c == "+":
            bx += 1
        elif c == "-":
            bx -= 1
        else:
            qcnt += 1
    diff = abs(ax - bx)
    head = (diff + qcnt) // 2
    if (diff + qcnt) % 2 != 0 or head > qcnt or head < 0:
        return "0.000000000\n"

    def fact(x: int) -> int:
        r = 1
        for i in range(2, x + 1):
            r *= i
        return r

    prob = fact(qcnt) / fact(qcnt - head) / fact(head) * (0.5 ** qcnt)
    return f"{prob:.9f}\n"


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


# ─── 1372B Omkar and Last Class of Math ──────────────────────────────────────


def _smallest_prime_factor(n: int) -> int:
    if n % 2 == 0:
        return 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return i
        i += 2
    return n


def _s_1372b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        if n % 2 == 0:
            k = n // 2
        else:
            p = _smallest_prime_factor(n)
            k = n // p
        k, other = min(k, n - k), max(k, n - k)
        out.append(f"{k} {other}")
    return "\n".join(out) + "\n"


def _a_1372b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        best_k = n - 1
        d = 2
        while d * d <= n:
            if n % d == 0:
                best_k = n // d
                break
            d += 1
        k, other = min(best_k, n - best_k), max(best_k, n - best_k)
        out.append(f"{k} {other}")
    return "\n".join(out) + "\n"


def _m1_1372b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append(f"1 {n - 1}")
    return "\n".join(out) + "\n"


def _m2_1372b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        if n % 2 == 0:
            k = n // 2 - 1
        else:
            p = _smallest_prime_factor(n)
            k = n // p
        out.append(f"{k} {n - k}")
    return "\n".join(out) + "\n"


def _gen_1372b(rng: random.Random) -> list[str]:
    cases = ["3\n4\n6\n9\n"]
    for _ in range(13):
        n = rng.randint(2, 200)
        cases.append(f"1\n{n}\n")
    return cases


# ─── 1831B Array merging ─────────────────────────────────────────────────────


def _s_1831b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1

        def runs(arr: list[int]) -> dict[int, int]:
            best: dict[int, int] = {}
            cur = 1
            for i in range(len(arr)):
                if i > 0 and arr[i] == arr[i - 1]:
                    cur += 1
                else:
                    cur = 1
                best[arr[i]] = max(best.get(arr[i], 0), cur)
            return best

        ra = runs(a)
        rb = runs(b)
        ans = 0
        for v in set(ra) | set(rb):
            ans = max(ans, ra.get(v, 0) + rb.get(v, 0))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1831b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1
        max_a: dict[int, int] = {}
        run = 0
        prev = None
        for v in a:
            run = run + 1 if v == prev else 1
            prev = v
            max_a[v] = max(max_a.get(v, 0), run)
        max_b: dict[int, int] = {}
        run = 0
        prev = None
        for v in b:
            run = run + 1 if v == prev else 1
            prev = v
            max_b[v] = max(max_b.get(v, 0), run)
        best = 0
        for v, ca in max_a.items():
            best = max(best, ca + max_b.get(v, 0))
        for v, cb in max_b.items():
            best = max(best, cb + max_a.get(v, 0))
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1831b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1

        def max_run(arr: list[int]) -> int:
            best = 1
            cur = 1
            for i in range(1, len(arr)):
                cur = cur + 1 if arr[i] == arr[i - 1] else 1
                best = max(best, cur)
            return best

        out.append(str(max_run(a) + max_run(b)))
    return "\n".join(out) + "\n"


def _m2_1831b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        b = list(map(int, ls[idx].split()))
        idx += 1

        def runs(arr: list[int]) -> dict[int, int]:
            best: dict[int, int] = {}
            cur = 1
            for i in range(len(arr)):
                if i > 0 and arr[i] == arr[i - 1]:
                    cur += 1
                else:
                    cur = 1
                best[arr[i]] = max(best.get(arr[i], 0), cur)
            return best

        ra = runs(a)
        rb = runs(b)
        ans = 0
        for v in set(ra):
            ans = max(ans, ra.get(v, 0) + rb.get(v, 0))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1831b(rng: random.Random) -> list[str]:
    cases = [
        "3\n2\n1 2\n2 1\n1\n1\n1\n4\n1 2 1 2\n2 1 2 1\n",
        "1\n4\n1 3 3 3\n2 2 2 2\n",
    ]
    for _ in range(12):
        n = rng.randint(1, 6)
        a = [rng.randint(1, 3) for _ in range(n)]
        b = [rng.randint(1, 3) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n")
    return cases


# ─── 2195A Sieve of Erato67henes ─────────────────────────────────────────────


def _s_2195a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(yes_no(67 in a).strip())
    return "\n".join(out) + "\n"


def _a_2195a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append("YES" if any(v == 67 for v in a) else "NO")
    return "\n".join(out) + "\n"


def _m1_2195a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        prod = 1
        for v in a:
            prod *= v
        out.append("YES" if prod == 67 else "NO")
    return "\n".join(out) + "\n"


def _m2_2195a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append("YES" if any(v == 67 for v in a) or sum(a) == 67 else "NO")
    return "\n".join(out) + "\n"


def _gen_2195a(rng: random.Random) -> list[str]:
    cases = ["2\n5\n1 7 6 7 67\n5\n1 3 5 7 8\n", "1\n2\n60 7\n"]
    for _ in range(12):
        n = rng.randint(1, 5)
        a = [rng.randint(1, 67) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1420B Rock and Lever ────────────────────────────────────────────────────


def _s_1420b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        cnt = [0] * 32
        for v in a:
            cnt[v.bit_length() - 1] += 1
        ans = sum(c * (c - 1) // 2 for c in cnt)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1420b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        groups: dict[int, int] = {}
        for v in a:
            b = v.bit_length()
            groups[b] = groups.get(b, 0) + 1
        ans = 0
        for c in groups.values():
            ans += c * (c - 1) // 2
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1420b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        groups: dict[int, int] = {}
        for v in a:
            b = v.bit_length()
            groups[b] = groups.get(b, 0) + 1
        ans = sum(c * c for c in groups.values())
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m2_1420b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        n = len(a)
        ans = 0
        for i in range(n):
            for j in range(i + 1, n):
                if (a[i] ^ a[j]) >= (a[i] & a[j]):
                    ans += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_1420b(rng: random.Random) -> list[str]:
    cases = ["1\n4\n15 4 4 2\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        a = [rng.randint(1, 30) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1691B Shoe Shuffling ────────────────────────────────────────────────────


def _s_1691b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        s = list(map(int, ls[idx].split()))
        idx += 1
        p = list(range(1, n + 1))
        ok = True
        l = 0
        while l < n:
            r = l
            while r + 1 < n and s[r + 1] == s[l]:
                r += 1
            if l == r:
                ok = False
                break
            block = p[l:r + 1]
            p[l:r + 1] = [block[-1]] + block[:-1]
            l = r + 1
        out.append(" ".join(map(str, p)) if ok else "-1")
    return "\n".join(out) + "\n"


def _a_1691b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        s = list(map(int, ls[idx].split()))
        idx += 1
        groups: dict[int, list[int]] = {}
        for i, v in enumerate(s):
            groups.setdefault(v, []).append(i)
        if any(len(idxs) < 2 for idxs in groups.values()):
            out.append("-1")
            continue
        p = [0] * n
        for idxs in groups.values():
            m = len(idxs)
            for k in range(m):
                p[idxs[k]] = idxs[(k - 1) % m] + 1
        out.append(" ".join(map(str, p)))
    return "\n".join(out) + "\n"


def _m1_1691b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        s = list(map(int, ls[idx].split()))
        idx += 1
        groups: dict[int, list[int]] = {}
        for i, v in enumerate(s):
            groups.setdefault(v, []).append(i)
        p = [0] * n
        ok = True
        for idxs in groups.values():
            if len(idxs) < 2:
                ok = False
                break
            m = len(idxs)
            for k in range(m):
                p[idxs[k]] = idxs[k] + 1
        out.append(" ".join(map(str, p)) if ok else "-1")
    return "\n".join(out) + "\n"


def _m2_1691b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        s = list(map(int, ls[idx].split()))
        idx += 1
        groups: dict[int, list[int]] = {}
        for i, v in enumerate(s):
            groups.setdefault(v, []).append(i)
        if any(len(idxs) < 2 for idxs in groups.values()):
            out.append("-1")
            continue
        p = list(range(1, n + 1))
        out.append(" ".join(map(str, p)))
    return "\n".join(out) + "\n"


def _gen_1691b(rng: random.Random) -> list[str]:
    cases = ["2\n2\n1 1\n3\n1 2 3\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        sizes = sorted(rng.randint(1, 5) for _ in range(n))
        cases.append(f"1\n{n}\n" + " ".join(map(str, sizes)) + "\n")
    return cases


# ─── 1473A Replacing Elements ────────────────────────────────────────────────


def _s_1473a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        out.append(yes_no(a[-1] <= d or a[0] + a[1] <= d).strip())
    return "\n".join(out) + "\n"


def _a_1473a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        mx = max(a)
        two_min = sum(sorted(a)[:2])
        out.append("YES" if mx <= d or two_min <= d else "NO")
    return "\n".join(out) + "\n"


def _m1_1473a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        out.append("YES" if a[-1] <= d else "NO")
    return "\n".join(out) + "\n"


def _m2_1473a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split())
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        out.append("YES" if a[0] + a[1] <= d else "NO")
    return "\n".join(out) + "\n"


def _gen_1473a(rng: random.Random) -> list[str]:
    cases = ["2\n5 3\n2 3 4 6 6\n3 4\n1 2 3\n", "1\n3 5\n1 5 5\n"]
    for _ in range(12):
        n = rng.randint(3, 8)
        d = rng.randint(1, 20)
        a = [rng.randint(1, 20) for _ in range(n)]
        cases.append(f"1\n{n} {d}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1506C Double-ended Strings ──────────────────────────────────────────────


def _s_1506c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        a = ls[idx]
        idx += 1
        b = ls[idx]
        idx += 1
        n, m = len(a), len(b)
        ans = 0
        for length in range(1, min(n, m) + 1):
            for i in range(n - length + 1):
                for j in range(m - length + 1):
                    if a[i:i + length] == b[j:j + length]:
                        ans = max(ans, length)
        out.append(str(n + m - 2 * ans))
    return "\n".join(out) + "\n"


def _a_1506c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        a = ls[idx]
        idx += 1
        b = ls[idx]
        idx += 1
        n, m = len(a), len(b)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        best = 0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    best = max(best, dp[i][j])
        out.append(str(n + m - 2 * best))
    return "\n".join(out) + "\n"


def _m1_1506c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        a = ls[idx]
        idx += 1
        b = ls[idx]
        idx += 1
        n, m = len(a), len(b)
        common = len(set(a) & set(b))
        out.append(str(n + m - 2 * common))
    return "\n".join(out) + "\n"


def _m2_1506c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        a = ls[idx]
        idx += 1
        b = ls[idx]
        idx += 1
        n, m = len(a), len(b)
        ans = 0
        for length in range(1, min(n, m) + 1):
            for i in range(n - length + 1):
                for j in range(m - length + 1):
                    if a[i:i + length] == b[j:j + length]:
                        ans = max(ans, length)
        out.append(str(n + m - ans))
    return "\n".join(out) + "\n"


def _gen_1506c(rng: random.Random) -> list[str]:
    cases = ["5\nhello\nicpc\nabcde\ndefgh\na\nz\nabc\ncba\ncodeforces\ntechnocup\n"]
    for _ in range(13):
        n = rng.randint(1, 6)
        m = rng.randint(1, 6)
        a = "".join(rng.choice("abc") for _ in range(n))
        b = "".join(rng.choice("abc") for _ in range(m))
        cases.append(f"1\n{a}\n{b}\n")
    return cases


# ─── 1843A Sasha and Array Coloring ──────────────────────────────────────────


def _s_1843a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        ans = sum(a[-i - 1] - a[i] for i in range(n // 2))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1843a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        half = n // 2
        low = a[:half]
        high = a[n - half:]
        ans = sum(h - l for h, l in zip(high, low))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1843a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        a.sort(reverse=True)
        ans = sum(a[-i - 1] - a[i] for i in range(n // 2))
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m2_1843a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = sorted(map(int, ls[idx].split()))
        idx += 1
        out.append(str(a[-1] - a[0]))
    return "\n".join(out) + "\n"


def _gen_1843a(rng: random.Random) -> list[str]:
    cases = ["3\n5\n1 5 6 3 4\n1\n5\n4\n1 6 3 9\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        a = [rng.randint(1, 50) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1650A Deletions of Two Adjacent Letters ─────────────────────────────────


def _s_1650a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        stack: list[str] = []
        for ch in s:
            if stack and stack[-1] == ch:
                stack.pop()
            else:
                stack.append(ch)
        out.append(yes_no(len(stack) == 0).strip())
    return "\n".join(out) + "\n"


def _a_1650a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = list(ls[idx])
        idx += 1
        changed = True
        while changed:
            changed = False
            i = 0
            new_s = []
            while i < len(s):
                if i + 1 < len(s) and s[i] == s[i + 1]:
                    i += 2
                    changed = True
                else:
                    new_s.append(s[i])
                    i += 1
            s = new_s
        out.append("YES" if not s else "NO")
    return "\n".join(out) + "\n"


def _m1_1650a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        out.append("YES" if len(s) % 2 == 0 else "NO")
    return "\n".join(out) + "\n"


def _m2_1650a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        stack: list[str] = []
        for ch in s:
            if stack and stack[-1] != ch:
                stack.pop()
            else:
                stack.append(ch)
        out.append("YES" if len(stack) == 0 else "NO")
    return "\n".join(out) + "\n"


def _gen_1650a(rng: random.Random) -> list[str]:
    def make_reducible(n: int) -> str:
        if n == 0:
            return ""
        if rng.random() < 0.5 and n >= 2:
            ch = rng.choice("ab")
            return ch + make_reducible(n - 2) + ch
        parts = []
        remaining = n
        while remaining > 0:
            take = min(remaining, rng.choice([2, 2, 4]))
            if take % 2 != 0:
                take -= 1
            if take == 0:
                take = remaining if remaining % 2 == 0 else remaining - 1
            if take <= 0:
                break
            parts.append(make_reducible(take))
            remaining -= take
        return "".join(parts)

    cases = ["4\n6\nabccba\n4\nabab\n3\nabc\n2\naa\n"]
    for _ in range(13):
        if rng.random() < 0.6:
            n = rng.randint(1, 5) * 2
            s = make_reducible(n)
        else:
            n = rng.randint(1, 9)
            s = "".join(rng.choice("ab") for _ in range(n))
        cases.append(f"1\n{len(s)}\n{s}\n")
    return cases


# ─── 1899C Yarik and Array ───────────────────────────────────────────────────


def _s_1899c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        ans = a[0]
        mn = min(0, a[0])
        total = a[0]
        for i in range(1, n):
            if (a[i] % 2 == 0) == (a[i - 1] % 2 == 0):
                mn = 0
                total = 0
            total += a[i]
            ans = max(ans, total - mn)
            mn = min(mn, total)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1899c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        best = a[0]
        cur = a[0]
        for i in range(1, n):
            if (a[i] - a[i - 1]) % 2 != 0:
                cur = max(cur + a[i], a[i])
            else:
                cur = a[i]
            best = max(best, cur)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1899c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        best = a[0]
        cur = a[0]
        for i in range(1, n):
            if (a[i] - a[i - 1]) % 2 != 0:
                cur = cur + a[i]
            else:
                cur = a[i]
            best = max(best, cur)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m2_1899c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        out.append(str(max(a)))
    return "\n".join(out) + "\n"


def _gen_1899c(rng: random.Random) -> list[str]:
    cases = [
        "7\n5\n1 2 3 4 5\n4\n9 9 8 8\n6\n-1 4 -1 0 5 -4\n4\n-1 2 4 -3\n1\n-1000\n3\n101 -99 101\n20\n-10 5 -8 10 6 -10 7 9 -2 -6 7 2 -4 6 -1 7 -6 -7 4 1\n"
    ]
    for _ in range(13):
        n = rng.randint(1, 8)
        a = [rng.randint(-10, 10) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 822A I'm bored with life ────────────────────────────────────────────────


def _s_822a(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    n = min(a, b)
    result = 1
    for i in range(2, n + 1):
        result *= i
    return str(result) + "\n"


def _a_822a(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    n = a if a < b else b
    return str(math.factorial(n)) + "\n"


def _m1_822a(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    n = max(a, b)
    result = 1
    for i in range(2, n + 1):
        result *= i
    return str(result) + "\n"


def _m2_822a(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    n = min(a, b)
    result = 1
    for i in range(2, n):
        result *= i
    return str(result) + "\n"


def _gen_822a(rng: random.Random) -> list[str]:
    cases = ["4 3\n", "1 1\n", "12 5\n"]
    for _ in range(13):
        small = rng.randint(1, 12)
        big = rng.randint(small, 10 ** 6)
        if rng.random() < 0.5:
            cases.append(f"{small} {big}\n")
        else:
            cases.append(f"{big} {small}\n")
    return cases


# ─── 1800A Is It a Cat? ───────────────────────────────────────────────────────


def _s_1800a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx].lower()
        idx += 1
        squashed = []
        for ch in s:
            if not squashed or squashed[-1] != ch:
                squashed.append(ch)
        out.append(yes_no("".join(squashed) == "meow").strip())
    return "\n".join(out) + "\n"


def _a_1800a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    order = "meow"
    for _ in range(t):
        idx += 1
        s = ls[idx].lower()
        idx += 1
        pos = 0
        ok = True
        for ch in s:
            if ch not in order:
                ok = False
                break
            if ch == order[pos]:
                continue
            elif pos + 1 < len(order) and ch == order[pos + 1]:
                pos += 1
            else:
                ok = False
                break
        if pos != len(order) - 1:
            ok = False
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _m1_1800a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx].lower()
        idx += 1
        out.append("YES" if sorted(set(s)) == sorted("meow") else "NO")
    return "\n".join(out) + "\n"


def _m2_1800a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx].lower()
        idx += 1
        squashed = []
        for ch in s:
            if not squashed or squashed[-1] != ch:
                squashed.append(ch)
        out.append("YES" if "".join(squashed).startswith("meow") else "NO")
    return "\n".join(out) + "\n"


def _gen_1800a(rng: random.Random) -> list[str]:
    cases = ["4\n4\nmeow\n9\nmmmEeOWww\n7\nMweo12z\n7\nmeowmeo\n"]
    for _ in range(13):
        if rng.random() < 0.5:
            s = "".join(
                rng.choice(letter * rng.randint(1, 3)) for letter in "meow"
            )
            s = "".join(c.upper() if rng.random() < 0.3 else c for c in s)
        else:
            s = "".join(rng.choice("meowxy") for _ in range(rng.randint(1, 8)))
        cases.append(f"1\n{len(s)}\n{s}\n")
    return cases


# ─── 1303A Erasing Zeroes ────────────────────────────────────────────────────


def _s_1303a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(str(s.strip("0").count("0")))
    return "\n".join(out) + "\n"


def _a_1303a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        if "1" not in s:
            out.append("0")
            continue
        first = s.index("1")
        last = len(s) - 1 - s[::-1].index("1")
        out.append(str(s[first:last + 1].count("0")))
    return "\n".join(out) + "\n"


def _m1_1303a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(str(s.count("0")))
    return "\n".join(out) + "\n"


def _m2_1303a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        out.append(str(s.lstrip("0").count("0")))
    return "\n".join(out) + "\n"


def _gen_1303a(rng: random.Random) -> list[str]:
    cases = ["3\n010011\n0\n1111000\n"]
    for _ in range(13):
        n = rng.randint(1, 10)
        s = "".join(rng.choice("01") for _ in range(n))
        cases.append(f"1\n{s}\n")
    return cases


# ─── 2167C Isamatdin and His Magic Wand! ─────────────────────────────────────


def _s_2167c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        has_odd = any(v % 2 == 1 for v in a)
        has_even = any(v % 2 == 0 for v in a)
        if has_odd and has_even:
            out.append(" ".join(map(str, sorted(a))))
        else:
            out.append(" ".join(map(str, a)))
    return "\n".join(out) + "\n"


def _a_2167c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        odd = sum(1 for v in a if v % 2)
        even = len(a) - odd
        if odd > 0 and even > 0:
            result = sorted(a)
        else:
            result = a
        out.append(" ".join(map(str, result)))
    return "\n".join(out) + "\n"


def _m1_2167c(stdin: str) -> str:
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


def _m2_2167c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        has_odd = any(v % 2 == 1 for v in a)
        has_even = any(v % 2 == 0 for v in a)
        if has_odd and has_even:
            out.append(" ".join(map(str, sorted(a, reverse=True))))
        else:
            out.append(" ".join(map(str, a)))
    return "\n".join(out) + "\n"


def _gen_2167c(rng: random.Random) -> list[str]:
    cases = ["4\n4\n2 3 1 4\n5\n3 2 1 3 4\n4\n3 7 5 1\n2\n1000000000 2\n"]
    for _ in range(13):
        n = rng.randint(1, 8)
        if rng.random() < 0.3:
            parity = rng.choice([0, 1])
            a = [rng.randint(1, 20) * 2 + parity for _ in range(n)]
        else:
            a = [rng.randint(1, 40) for _ in range(n)]
        cases.append(f"1\n{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


# ─── 1996B Scale ─────────────────────────────────────────────────────────────


def _s_1996b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx:idx + n]
        idx += n
        rows = []
        for i in range(0, n, k):
            row = "".join(grid[i][j] for j in range(0, n, k))
            rows.append(row)
        out.append("\n".join(rows))
    return "\n".join(out) + "\n"


def _a_1996b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx:idx + n]
        idx += n
        rows = []
        for i in range(n // k):
            chars = []
            for j in range(n // k):
                chars.append(grid[i * k][j * k])
            rows.append("".join(chars))
        out.append("\n".join(rows))
    return "\n".join(out) + "\n"


def _m1_1996b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx:idx + n]
        idx += n
        rows = []
        for i in range(0, n, k):
            row = "".join(grid[i][j] for j in range(0, n, k))
            rows.append(row)
        rows.reverse()
        out.append("\n".join(rows))
    return "\n".join(out) + "\n"


def _m2_1996b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, k = map(int, ls[idx].split())
        idx += 1
        grid = ls[idx:idx + n]
        idx += n
        rows = []
        for i in range(0, n, k):
            row = "".join(grid[i][min(j + k, n - 1)] for j in range(0, n, k))
            rows.append(row)
        out.append("\n".join(rows))
    return "\n".join(out) + "\n"


def _gen_1996b(rng: random.Random) -> list[str]:
    def make_grid(n: int, k: int) -> list[str]:
        blocks = n // k
        vals = [[rng.choice("01") for _ in range(blocks)] for _ in range(blocks)]
        grid = []
        for bi in range(blocks):
            for _ in range(k):
                row = "".join(vals[bi][bj] * k for bj in range(blocks))
                grid.append(row)
        return grid

    cases = ["1\n4 2\n0011\n0011\n1111\n1111\n"]
    for _ in range(13):
        k = rng.randint(1, 3)
        blocks = rng.randint(1, 4)
        n = k * blocks
        grid = make_grid(n, k)
        cases.append(f"1\n{n} {k}\n" + "\n".join(grid) + "\n")
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


# ─── 1095A Repeating Cipher ──────────────────────────────────────────────────


def _s_1095a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        res = []
        for i, ch in enumerate(s):
            res.append(ch * (i + 1))
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _a_1095a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        res = []
        count = 1
        for ch in s:
            res.append(ch * count)
            count += 1
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _m1_1095a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        res = []
        for i, ch in enumerate(s):
            res.append(ch * i if i > 0 else ch)
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _m2_1095a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        n = len(s)
        res = []
        for i, ch in enumerate(s):
            res.append(ch * (n - i))
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _gen_1095a(rng: random.Random) -> list[str]:
    cases = ["3\n3\ncba\n1\nu\n9\ncodeforces\n"]
    for _ in range(13):
        n = rng.randint(1, 6)
        s = "".join(rng.choice("abc") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 1337B Kana and Dragon Quest game ────────────────────────────────────────


def _s_1337b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x, n, m = map(int, ls[i].split())
        while x > 0 and n and x // 2 + 10 < x:
            n -= 1
            x = x // 2 + 10
        out.append(yes_no(x <= m * 10).strip())
    return "\n".join(out) + "\n"


def _a_1337b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x, n, m = map(int, ls[i].split())
        uses = n
        while uses > 0:
            new_x = x // 2 + 10
            if new_x >= x:
                break
            x = new_x
            uses -= 1
        out.append("YES" if x <= 10 * m else "NO")
    return "\n".join(out) + "\n"


def _m1_1337b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x, n, m = map(int, ls[i].split())
        while x > 0 and n and x // 2 + 10 < x:
            n -= 1
            x = x // 2 + 10
        out.append("YES" if x < m * 10 else "NO")
    return "\n".join(out) + "\n"


def _m2_1337b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        x, n, m = map(int, ls[i].split())
        out.append("YES" if x <= m * 10 else "NO")
    return "\n".join(out) + "\n"


def _gen_1337b(rng: random.Random) -> list[str]:
    cases = ["3\n100 3 4\n189 3 4\n64 2 3\n", "1\n100 1 6\n"]
    for _ in range(12):
        x = rng.randint(1, 200)
        n = rng.randint(0, 10)
        m = rng.randint(0, 10)
        cases.append(f"1\n{x} {n} {m}\n")
    return cases


# ─── 1675A Food for Animals ──────────────────────────────────────────────────


def _s_1675a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, x, y = map(int, ls[i].split())
        x2 = max(x - a, 0)
        y2 = max(y - b, 0)
        out.append(yes_no(x2 + y2 <= c).strip())
    return "\n".join(out) + "\n"


def _a_1675a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, x, y = map(int, ls[i].split())
        ax = min(a, x)
        by = min(b, y)
        rem_x = x - ax
        rem_y = y - by
        out.append("YES" if c >= rem_x + rem_y else "NO")
    return "\n".join(out) + "\n"


def _m1_1675a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, x, y = map(int, ls[i].split())
        x2 = max(x - a, 0)
        y2 = max(y - b, 0)
        out.append("YES" if x2 + y2 < c else "NO")
    return "\n".join(out) + "\n"


def _m2_1675a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, x, y = map(int, ls[i].split())
        out.append("YES" if x <= a + c and y <= b + c else "NO")
    return "\n".join(out) + "\n"


def _gen_1675a(rng: random.Random) -> list[str]:
    cases = ["7\n1 1 4 2 3\n0 0 0 0 0\n5 5 0 4 6\n1 1 1 1 1\n50000000 50000000 100000000 100000000 100000000\n0 0 0 100000000 100000000\n1 3 2 2 5\n"]
    for _ in range(13):
        a = rng.randint(0, 10)
        b = rng.randint(0, 10)
        c = rng.randint(0, 10)
        x = rng.randint(0, 10)
        y = rng.randint(0, 10)
        cases.append(f"1\n{a} {b} {c} {x} {y}\n")
    return cases


# ─── 275A Lights Out ─────────────────────────────────────────────────────────


def _s_275a(stdin: str) -> str:
    ls = lines(stdin)
    presses = [list(map(int, ls[i].split())) for i in range(3)]
    state = [[1] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if presses[i][j] % 2 == 1:
                for di, dj in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 3 and 0 <= nj < 3:
                        state[ni][nj] ^= 1
    return "\n".join("".join(map(str, row)) for row in state) + "\n"


def _a_275a(stdin: str) -> str:
    ls = lines(stdin)
    presses = [list(map(int, ls[i].split())) for i in range(3)]
    toggles = [[0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for di, dj in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < 3 and 0 <= nj < 3:
                    toggles[ni][nj] += presses[i][j]
    rows = []
    for i in range(3):
        row = "".join("0" if toggles[i][j] % 2 == 1 else "1" for j in range(3))
        rows.append(row)
    return "\n".join(rows) + "\n"


def _m1_275a(stdin: str) -> str:
    ls = lines(stdin)
    presses = [list(map(int, ls[i].split())) for i in range(3)]
    state = [[1] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if presses[i][j] % 2 == 1:
                state[i][j] ^= 1
    return "\n".join("".join(map(str, row)) for row in state) + "\n"


def _m2_275a(stdin: str) -> str:
    ls = lines(stdin)
    presses = [list(map(int, ls[i].split())) for i in range(3)]
    state = [[1] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if presses[i][j] % 2 == 0:
                for di, dj in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 3 and 0 <= nj < 3:
                        state[ni][nj] ^= 1
    return "\n".join("".join(map(str, row)) for row in state) + "\n"


def _gen_275a(rng: random.Random) -> list[str]:
    cases = ["1 0 0\n0 0 0\n0 0 1\n", "1 0 1\n8 8 8\n2 0 3\n"]
    for _ in range(13):
        rows = []
        for _r in range(3):
            rows.append(" ".join(str(rng.randint(0, 5)) for _ in range(3)))
        cases.append("\n".join(rows) + "\n")
    return cases


# ─── 2106A Dr. TC ─────────────────────────────────────────────────────────────


def _s_2106a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        base = s.count("1")
        total = 0
        for ch in s:
            total += base + 1 if ch == "0" else base - 1
        out.append(str(total))
    return "\n".join(out) + "\n"


def _a_2106a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        idx += 1
        s = ls[idx]
        idx += 1
        total = 0
        for i in range(n):
            flipped = list(s)
            flipped[i] = "0" if s[i] == "1" else "1"
            total += flipped.count("1")
        out.append(str(total))
    return "\n".join(out) + "\n"


def _m1_2106a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        base = s.count("1")
        out.append(str(base * len(s)))
    return "\n".join(out) + "\n"


def _m2_2106a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        idx += 1
        s = ls[idx]
        idx += 1
        base = s.count("1")
        total = 0
        for ch in s:
            total += base - 1 if ch == "0" else base + 1
        out.append(str(total))
    return "\n".join(out) + "\n"


def _gen_2106a(rng: random.Random) -> list[str]:
    cases = ["3\n1\n0\n1\n0\n5\n10000\n"]
    for _ in range(13):
        n = rng.randint(1, 10)
        s = "".join(rng.choice("01") for _ in range(n))
        cases.append(f"1\n{n}\n{s}\n")
    return cases


# ─── 2008C Longest Good Array ────────────────────────────────────────────────


def _s_2008c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        l, r = map(int, ls[i].split())
        diff = r - l
        n = 1
        while n * (n + 1) // 2 <= diff:
            n += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _a_2008c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        l, r = map(int, ls[i].split())
        diff = r - l
        lo, hi = 1, 200000
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if mid * (mid - 1) // 2 <= diff:
                lo = mid
            else:
                hi = mid - 1
        out.append(str(lo))
    return "\n".join(out) + "\n"


def _m1_2008c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        l, r = map(int, ls[i].split())
        diff = r - l
        n = 1
        while n * (n + 1) // 2 < diff:
            n += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_2008c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        l, r = map(int, ls[i].split())
        diff = r - l
        n = 1
        while n * (n - 1) // 2 <= diff:
            n += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _gen_2008c(rng: random.Random) -> list[str]:
    cases = ["5\n1 2\n1 5\n2 2\n10 20\n1 1000000000\n"]
    for _ in range(13):
        l = rng.randint(1, 1000)
        r = l + rng.randint(0, 2000)
        cases.append(f"1\n{l} {r}\n")
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
        "1941C",
        "Count minimum characters to insert so a string has no 'map' or 'pie' substring.",
        ({"input": "6\n9\nmmapnapie\n9\nazabazapi\n8\nmappppie\n18\nmapmapmapmapmapmap\n1\np\n11\npppiepieeee\n", "output": "2\n0\n2\n6\n0\n2\n"},),
        _s_1941c,
        _a_1941c,
        {"double_count_overlap": _m1_1941c, "skip_mapie": _m2_1941c},
        _gen_1941c,
        family="strings",
    )
    add(
        "1335C",
        "Maximize the combined size of an all-distinct team and an all-equal team.",
        ({"input": "1\n1\n3\n1\n4\n", "output": "2\n"},),
        _s_1335c,
        _a_1335c,
        {"distinct_only": _m1_1335c, "wrong_formula": _m2_1335c},
        _gen_1335c,
        family="counting",
    )
    add(
        "1977A",
        "Determine if a tower can end up with exactly m cubes after n add/remove moves.",
        ({"input": "3\n3 3\n2 4\n5 3\n", "output": "Yes\nNo\nYes\n"},),
        _s_1977a,
        _a_1977a,
        {"ignore_parity": _m1_1977a, "ignore_bound": _m2_1977a},
        _gen_1977a,
        family="parity",
    )
    add(
        "2131A",
        "Count iterations of the Lever process comparing arrays a and b.",
        ({"input": "1\n2\n7 3\n5 6\n", "output": "3\n"},),
        _s_2131a,
        _a_2131a,
        {"no_plus_one": _m1_2131a, "abs_diff": _m2_2131a},
        _gen_2131a,
        family="simulation",
    )
    add(
        "1490C",
        "Check if x can be written as the sum of cubes of two positive integers.",
        ({"input": "7\n1\n2\n4\n34\n35\n16\n703657519796\n", "output": "NO\nYES\nNO\nNO\nYES\nYES\nYES\n"},),
        _s_1490c,
        _a_1490c,
        {"allow_zero": _m1_1490c, "wrong_root": _m2_1490c},
        _gen_1490c,
        family="math",
    )
    add(
        "2091A",
        "Find the earliest draw index at which digits 0103 2025 can all be assembled.",
        ({"input": "1\n10\n2 0 1 2 3 2 5 0 0 1\n", "output": "9\n"},),
        _s_2091a,
        _a_2091a,
        {"wrong_need": _m1_2091a, "no_early_stop": _m2_2091a},
        _gen_2091a,
        family="counting",
    )
    add(
        "1660A",
        "Find the minimum amount Vasya cannot pay using a 1-burle and b 2-burle coins.",
        ({"input": "4\n1 1\n4 0\n0 2\n0 0\n", "output": "4\n5\n1\n1\n"},),
        _s_1660a,
        _a_1660a,
        {"ignore_zero_case": _m1_1660a, "wrong_coeff": _m2_1660a},
        _gen_1660a,
        family="math",
    )
    add(
        "1692C",
        "Find the position of the bishop on an 8x8 board from its diagonal footprint.",
        ({"input": "1\n........\n........\n...#.#..\n....#...\n...#.#..\n........\n........\n........\n", "output": "4 5\n"},),
        _s_1692c,
        _a_1692c,
        {"missing_two_diagonals": _m1_1692c, "off_by_one": _m2_1692c},
        _gen_1692c,
        family="grid",
    )
    add(
        "1726A",
        "Maximize a[n-1]-a[0] after cyclically rotating one contiguous subsegment.",
        ({"input": "1\n6\n1 3 9 11 5 7\n", "output": "10\n"},),
        _s_1726a,
        _a_1726a,
        {"no_rotation": _m1_1726a, "missing_case": _m2_1726a},
        _gen_1726a,
        family="greedy",
    )
    add(
        "1696B",
        "Minimum mex-replace operations on a subarray to zero out the whole array.",
        ({"input": "1\n4\n0 1 2 0\n", "output": "1\n"},),
        _s_1696b,
        _a_1696b,
        {"wrong_zero_check": _m1_1696b, "always_two": _m2_1696b},
        _gen_1696b,
        family="implementation",
    )
    add(
        "1353C",
        "Minimum moves to gather all figures on an odd n x n board into one cell.",
        ({"input": "1\n3\n", "output": "8\n"},),
        _s_1353c,
        _a_1353c,
        {"half_factor": _m1_1353c, "linear_layer": _m2_1353c},
        _gen_1353c,
        family="math",
    )
    add(
        "1560B",
        "Given who two people in a circle look at, find who person c looks at.",
        ({"input": "1\n6 2 4\n", "output": "8\n"},),
        _s_1560b,
        _a_1560b,
        {"off_by_one_shift": _m1_1560b, "half_circle": _m2_1560b},
        _gen_1560b,
        family="math",
    )
    add(
        "1325B",
        "Length of the longest increasing subsequence of n copies of array a concatenated.",
        ({"input": "1\n5\n3 2 1 3 2\n", "output": "3\n"},),
        _s_1325b,
        _a_1325b,
        {"always_n": _m1_1325b, "return_max_value": _m2_1325b},
        _gen_1325b,
        family="counting",
    )
    add(
        "1917B",
        "Count distinct non-empty strings reachable by erasing the first or second letter.",
        ({"input": "5\n5\naaaaa\n1\nz\n5\nababa\n14\nbcdaaaabcdaaaa\n20\nabcdefghijklmnopqrst\n", "output": "5\n1\n9\n50\n210\n"},),
        _s_1917b,
        _a_1917b,
        {"only_distinct_letters": _m1_1917b, "add_before_insert": _m2_1917b},
        _gen_1917b,
        family="counting",
    )
    add(
        "1702A",
        "Find how much to subtract from m to reach the largest power of 10 not exceeding it.",
        ({"input": "1\n178\n", "output": "78\n"},),
        _s_1702a,
        _a_1702a,
        {"next_power_up": _m1_1702a, "half_value": _m2_1702a},
        _gen_1702a,
        family="math",
    )
    add(
        "1980B",
        "Determine if Dmitry's favorite cube is always/never/sometimes among the top k removed.",
        ({"input": "1\n5 2 2\n4 3 3 2 3\n", "output": "MAYBE\n"},),
        _s_1980b,
        _a_1980b,
        {"off_by_one_boundary": _m1_1980b, "ignore_ties": _m2_1980b},
        _gen_1980b,
        family="sortings",
    )
    add(
        "2117A",
        "Determine if a single x-second button use lets you pass all closed doors.",
        ({"input": "1\n5 1\n0 0 1 0 0\n", "output": "YES\n"},),
        _s_2117a,
        _a_2117a,
        {"off_by_one_span": _m1_2117a, "sum_instead_of_span": _m2_2117a},
        _gen_2117a,
        family="greedy",
    )
    add(
        "1840A",
        "Decrypt a cipher string where each letter of the message is bracketed by copies of itself.",
        ({"input": "1\n8\nabacabac\n", "output": "ac\n"},),
        _s_1840a,
        _a_1840a,
        {"unique_sorted": _m1_1840a, "wrong_step": _m2_1840a},
        _gen_1840a,
        family="two_pointer",
    )
    add(
        "1927B",
        "Reconstruct a string from its trace (count of equal earlier characters).",
        ({"input": "1\n11\n0 0 0 1 0 2 0 3 1 1 4\n", "output": "abcadaeabca\n"},),
        _s_1927b,
        _a_1927b,
        {"reverse_alphabet": _m1_1927b, "wrong_counter_index": _m2_1927b},
        _gen_1927b,
        family="greedy",
    )
    add(
        "709A",
        "Count how many times the juicer's waste section overflows and empties.",
        ({"input": "2 7 10\n5 6\n", "output": "1\n"},),
        _s_709a,
        _a_709a,
        {"wrong_threshold": _m1_709a, "no_size_filter": _m2_709a},
        _gen_709a,
        family="simulation",
    )
    add(
        "2126B",
        "Maximum number of k-day hikes with mandatory 1-day rest, given good/rainy days.",
        ({"input": "1\n7 3\n0 0 0 1 0 0 0\n", "output": "2\n"},),
        _s_2126b,
        _a_2126b,
        {"wrong_denominator": _m1_2126b, "ignore_segments": _m2_2126b},
        _gen_2126b,
        family="greedy",
    )
    add(
        "1992B",
        "Minimum split/merge operations to reunite k casserole pieces into one of length n.",
        ({"input": "1\n5 2\n3 2\n", "output": "3\n"},),
        _s_1992b,
        _a_1992b,
        {"off_by_one": _m1_1992b, "wrong_pivot": _m2_1992b},
        _gen_1992b,
        family="greedy",
    )
    add(
        "1832B",
        "Maximize remaining sum after k operations removing two minimums or one maximum.",
        (
            {
                "input": "6\n5 1\n2 5 1 10 6\n5 2\n2 5 1 10 6\n3 1\n1 2 3\n6 1\n15 22 12 10 13 11\n6 2\n15 22 12 10 13 11\n5 1\n999999996 999999999 999999997 999999998 999999995\n",
                "output": "21\n11\n3\n62\n46\n3999999986\n",
            },
        ),
        _s_1832b,
        _a_1832b,
        {"always_remove_min": _m1_1832b, "wrong_offsets": _m2_1832b},
        _gen_1832b,
        family="prefix_sum",
    )
    add(
        "2171A",
        "Count configurations of chickens (2 legs) and cows (4 legs) giving n total legs.",
        ({"input": "1\n4\n", "output": "2\n"},),
        _s_2171a,
        _a_2171a,
        {"missing_plus_one": _m1_2171a, "ignore_parity": _m2_2171a},
        _gen_2171a,
        family="math",
    )
    add(
        "139A",
        "Find the day of week after reading a books-per-day schedule for a week.",
        ({"input": "monday\n1\n2\n3\n4\n5\n6\n7\n", "output": "monday\n"},),
        _s_139a,
        _a_139a,
        {"off_by_one": _m1_139a, "skip_first_day": _m2_139a},
        _gen_139a,
        family="simulation",
    )
    add(
        "1876A",
        "Minimum cost for Pak Chanek to notify all residents directly or via chained shares.",
        (
            {
                "input": "3\n6 3\n2 3 2 1 1 3\n4 3 2 6 3 6\n1 100000\n1\n100000\n4 94\n1 4 2 3\n103 96 86 57\n",
                "output": "16\n100000\n265\n",
            },
        ),
        _s_1876a,
        _a_1876a,
        {"drop_max_only": _m1_1876a, "off_by_one_index": _m2_1876a},
        _gen_1876a,
        family="greedy",
    )
    add(
        "1974A",
        "Minimum number of 24-icon screens needed for a phone desktop.",
        ({"input": "1\n1 1\n", "output": "1\n"},),
        _s_1974a,
        _a_1974a,
        {"floor_div": _m1_1974a, "wrong_capacity": _m2_1974a},
        _gen_1974a,
        family="math",
    )
    add(
        "476B",
        "Probability that Dreamoon's noisy movement ends at the intended position.",
        ({"input": "++-+-\n+-+-+\n", "output": "1.000000000\n"},),
        _s_476b,
        _a_476b,
        {"wrong_power": _m1_476b, "no_parity_check": _m2_476b},
        _gen_476b,
        checker="float",
        family="combinatorics",
    )
    add(
        "1372B",
        "Split n into a+b minimizing LCM(a,b).",
        ({"input": "3\n4\n6\n9\n", "output": "2 2\n3 3\n3 6\n"},),
        _s_1372b,
        _a_1372b,
        {"trivial_split": _m1_1372b, "half_minus_one": _m2_1372b},
        _gen_1372b,
        family="number_theory",
    )
    add(
        "1831B",
        "Maximum length of an equal-value run achievable by merging arrays a and b.",
        ({"input": "1\n2\n1 2\n2 1\n", "output": "2\n"},),
        _s_1831b,
        _a_1831b,
        {"ignore_value_match": _m1_1831b, "one_sided_union": _m2_1831b},
        _gen_1831b,
        family="greedy",
    )
    add(
        "2195A",
        "Determine if some subset of the array multiplies to exactly 67.",
        ({"input": "1\n5\n1 7 6 7 67\n", "output": "YES\n"},),
        _s_2195a,
        _a_2195a,
        {"product_equals_67": _m1_2195a, "sum_also_counts": _m2_2195a},
        _gen_2195a,
        family="math",
    )
    add(
        "1420B",
        "Count pairs (i,j) where a_i AND a_j >= a_i XOR a_j.",
        (
            {
                "input": "5\n5\n1 4 3 7 10\n3\n1 1 1\n4\n6 2 5 3\n2\n2 4\n1\n1\n",
                "output": "1\n3\n2\n0\n0\n",
            },
        ),
        _s_1420b,
        _a_1420b,
        {"squared_group": _m1_1420b, "brute_force_noop": _m2_1420b},
        _gen_1420b,
        family="bitmask",
    )
    add(
        "1691B",
        "Construct a valid shoe-shuffling permutation or report impossibility.",
        ({"input": "1\n2\n1 1\n", "output": "2 1\n"},),
        _s_1691b,
        _a_1691b,
        {"identity_within_group": _m1_1691b, "ignore_group_check": _m2_1691b},
        _gen_1691b,
        checker="tokens",
        family="constructive",
    )
    add(
        "1473A",
        "Determine if replacing elements with sums of other two can bound all values by d.",
        ({"input": "1\n5 3\n2 3 4 6 6\n", "output": "NO\n"},),
        _s_1473a,
        _a_1473a,
        {"ignore_two_min": _m1_1473a, "ignore_max": _m2_1473a},
        _gen_1473a,
        family="greedy",
    )
    add(
        "1506C",
        "Minimum end-deletions from strings a and b to make them equal (longest common substring).",
        ({"input": "1\nhello\nicpc\n", "output": "9\n"},),
        _s_1506c,
        _a_1506c,
        {"distinct_char_overlap": _m1_1506c, "single_subtract": _m2_1506c},
        _gen_1506c,
        family="strings",
    )
    add(
        "1843A",
        "Maximize total (max-min) cost when partitioning array into color groups.",
        ({"input": "1\n5\n1 5 6 3 4\n", "output": "7\n"},),
        _s_1843a,
        _a_1843a,
        {"wrong_half": _m1_1843a, "single_group": _m2_1843a},
        _gen_1843a,
        family="greedy",
    )
    add(
        "1650A",
        "Determine if a string can be fully erased by deleting adjacent equal-letter pairs.",
        ({"input": "1\n6\nabccba\n", "output": "YES\n"},),
        _s_1650a,
        _a_1650a,
        {"parity_only": _m1_1650a, "wrong_stack_rule": _m2_1650a},
        _gen_1650a,
        family="stack",
    )
    add(
        "1899C",
        "Maximum sum subarray where adjacent elements alternate parity.",
        ({"input": "1\n5\n1 2 3 4 5\n", "output": "15\n"},),
        _s_1899c,
        _a_1899c,
        {"no_reset": _m1_1899c, "ignore_subarray": _m2_1899c},
        _gen_1899c,
        family="dp",
    )
    add(
        "822A",
        "Compute GCD(A!, B!) which equals factorial of min(A, B).",
        ({"input": "4 3\n", "output": "6\n"},),
        _s_822a,
        _a_822a,
        {"use_max": _m1_822a, "off_by_one_factorial": _m2_822a},
        _gen_822a,
        family="math",
    )
    add(
        "1800A",
        "Determine if a string (after squashing consecutive duplicates) equals 'meow'.",
        ({"input": "1\n4\nmeow\n", "output": "YES\n"},),
        _s_1800a,
        _a_1800a,
        {"anagram_check": _m1_1800a, "prefix_only": _m2_1800a},
        _gen_1800a,
        family="strings",
    )
    add(
        "1303A",
        "Minimum zeros to erase so all 1s in the string form one contiguous block.",
        ({"input": "1\n010011\n", "output": "2\n"},),
        _s_1303a,
        _a_1303a,
        {"count_all_zeros": _m1_1303a, "wrong_strip_side": _m2_1303a},
        _gen_1303a,
        family="strings",
    )
    add(
        "2167C",
        "Lexicographically smallest array reachable by swapping elements of different parity.",
        ({"input": "1\n4\n2 3 1 4\n", "output": "1 2 3 4\n"},),
        _s_2167c,
        _a_2167c,
        {"always_sort": _m1_2167c, "sort_descending": _m2_2167c},
        _gen_2167c,
        checker="tokens",
        family="constructive",
    )
    add(
        "1996B",
        "Reduce an n x n binary grid by factor k by sampling one cell per block.",
        ({"input": "1\n4 2\n0011\n0011\n1111\n1111\n", "output": "01\n11\n"},),
        _s_1996b,
        _a_1996b,
        {"reversed_rows": _m1_1996b, "wrong_block_corner": _m2_1996b},
        _gen_1996b,
        family="grid",
    )
    add(
        "1097B",
        "Determine if some +/- assignment of n rotation angles sums to a multiple of 360.",
        ({"input": "3\n120\n120\n120\n", "output": "YES\n"},),
        _s_1097b,
        _a_1097b,
        {"all_positive": _m1_1097b, "mod_180": _m2_1097b},
        _gen_1097b,
        family="bitmask",
    )
    add(
        "1095A",
        "Decode a repeating cipher where the i-th character of s repeats i times.",
        ({"input": "1\n3\ncba\n", "output": "cbbaaa\n"},),
        _s_1095a,
        _a_1095a,
        {"off_by_one_repeat": _m1_1095a, "reversed_repeat_count": _m2_1095a},
        _gen_1095a,
        family="strings",
    )
    add(
        "1337B",
        "Determine if a dragon can be defeated using limited halving and flat-damage spells.",
        ({"input": "1\n100 3 4\n", "output": "YES\n"},),
        _s_1337b,
        _a_1337b,
        {"strict_inequality": _m1_1337b, "ignore_void_absorption": _m2_1337b},
        _gen_1337b,
        family="greedy",
    )
    add(
        "1675A",
        "Determine if there is enough dedicated and universal food for all dogs and cats.",
        ({"input": "1\n1 1 4 2 3\n", "output": "YES\n"},),
        _s_1675a,
        _a_1675a,
        {"strict_inequality": _m1_1675a, "wrong_bound": _m2_1675a},
        _gen_1675a,
        family="greedy",
    )
    add(
        "275A",
        "Compute final 3x3 light grid state after a given number of presses per light.",
        ({"input": "1 0 0\n0 0 0\n0 0 1\n", "output": "001\n010\n100\n"},),
        _s_275a,
        _a_275a,
        {"no_neighbor_toggle": _m1_275a, "inverted_parity": _m2_275a},
        _gen_275a,
        family="grid",
    )
    add(
        "2106A",
        "Count total 1s across n rows, each s with one bit flipped.",
        (
            {
                "input": "5\n3\n101\n1\n1\n5\n00000\n2\n11\n3\n010\n",
                "output": "5\n0\n5\n2\n4\n",
            },
        ),
        _s_2106a,
        _a_2106a,
        {"ignore_flip": _m1_2106a, "swapped_sign": _m2_2106a},
        _gen_2106a,
        family="math",
    )
    add(
        "2008C",
        "Maximum length of a strictly-increasing array with strictly increasing gaps in [l, r].",
        ({"input": "1\n1 5\n", "output": "3\n"},),
        _s_2008c,
        _a_2008c,
        {"strict_le": _m1_2008c, "wrong_formula": _m2_2008c},
        _gen_2008c,
        family="binary_search",
    )

    return specs


SPECS = _build()

_KEEP = ['1941C', '1335C', '1977A', '2131A', '1490C', '2091A', '1660A', '1726A', '1696B', '1353C', '1560B', '1325B', '1917B', '1702A', '1980B', '2117A', '1840A', '709A', '2126B', '1992B', '1832B', '2171A', '139A', '1876A', '1974A', '1372B', '1831B', '2195A', '1420B', '1691B', '1473A', '1506C', '1843A', '1650A', '1899C', '822A', '1800A', '1303A', '2167C', '1996B', '1095A', '1337B', '1675A', '275A', '2106A', '2008C']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
