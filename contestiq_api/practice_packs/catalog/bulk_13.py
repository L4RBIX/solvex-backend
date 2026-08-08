"""Dual-oracle specs for SolveX practice pack batch 13 (800-1300)."""

from __future__ import annotations

import math
import random
from collections import Counter, deque
from functools import reduce

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no

MOD = 10**9 + 7


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _tcases(stdin: str) -> tuple[int, list[str]]:
    ls = lines(stdin)
    return int(ls[0]), ls[1:]


def _parse_blocks(stdin: str, read_fn):
    ls = lines(stdin)
    t = int(ls[0])
    out_rows = []
    i = 1
    for _ in range(t):
        row, i = read_fn(ls, i)
        out_rows.append(row)
    return out_rows


SPECS: list = []


def add(**kw) -> None:
    SPECS.append(make_spec(**kw))



# ─── 1890A Doremy's Paint 3 ───────────────────────────────────────────────────

def _1890a(stdin: str) -> str:
    out = []
    i = 1
    for _ in range(int(lines(stdin)[0])):
        _n = int(lines(stdin)[i]); i += 1
        cnt = Counter(map(int, lines(stdin)[i].split())); i += 1
        if len(cnt) > 2:
            out.append("NO")
        elif len(cnt) == 1:
            out.append("YES")
        else:
            v = list(cnt.values())
            out.append("YES" if abs(v[0] - v[1]) <= 1 else "NO")
    return "\n".join(out) + "\n"


def _1890a_alt(stdin: str) -> str:
    out = []
    i = 1
    ls = lines(stdin)
    for _ in range(int(ls[0])):
        _n = int(ls[i]); i += 1
        vals = list(map(int, ls[i].split())); i += 1
        freq = {}
        for x in vals:
            freq[x] = freq.get(x, 0) + 1
        keys = list(freq.keys())
        if len(keys) > 2:
            out.append("NO")
        elif len(keys) == 1:
            out.append("YES")
        else:
            c1, c2 = freq[keys[0]], freq[keys[1]]
            out.append("YES" if abs(c1 - c2) <= 1 else "NO")
    return "\n".join(out) + "\n"


def _gen_1890a(rng: random.Random) -> list[str]:
    return [
        "3\n4\n2 2 1 1\n4\n3 1 2 3\n2\n1 3\n",
        "1\n2\n5 5\n",
        "1\n3\n1 1 1\n",
        "1\n4\n1 2 3 4\n",
        "1\n2\n1 2\n",
        "1\n5\n1 1 1 1 1\n",
        "1\n3\n1 1 2\n",
        "1\n6\n1 1 1 1 2 2\n",
        "1\n2\n7 7\n",
        "1\n4\n2 2 2 2\n",
        "1\n3\n1 2 3\n",
    ]


# ─── 1862B Sequence Game ──────────────────────────────────────────────────────

def _1862b(stdin: str) -> str:
    ls = lines(stdin)
    out = ["YES"] * int(ls[0])
    return "\n".join(out) + "\n"


def _1862b_alt(stdin: str) -> str:
    return "YES\n" * int(lines(stdin)[0])


def _gen_1862b(rng: random.Random) -> list[str]:
    return [
        "3\n1\n1 2\n3\n1 2 3\n2\n1 1\n",
        "1\n2\n3 4\n",
        "1\n1\n5\n",
        "1\n3\n1 1 1\n",
        "1\n4\n4 3 2 1\n",
        "1\n2\n1 2\n",
        "1\n5\n5 4 3 2 1\n",
        "1\n3\n2 2 2\n",
        "1\n2\n10 1\n",
        "1\n4\n1 3 2 4\n",
        "1\n1\n1\n",
    ]


# ─── 1837A Grasshopper on a Line ──────────────────────────────────────────────

def _1837a(stdin: str) -> str:
    out = []
    for x, y, k in (map(int, line.split()) for line in lines(stdin)[1:]):
        out.append("YES" if y % k == 0 and y // k <= x else "NO")
    return "\n".join(out) + "\n"


def _1837a_alt(stdin: str) -> str:
    out = []
    for x, y, k in (map(int, line.split()) for line in lines(stdin)[1:]):
        steps = y // k if y % k == 0 else x + 1
        out.append("YES" if steps <= x else "NO")
    return "\n".join(out) + "\n"


def _gen_1837a(rng: random.Random) -> list[str]:
    return [
        "7\n6 2 2\n1 2 6\n2 3 2\n629 4 2\n12 11 4\n308 5 3\n17 5 34\n",
        "1\n1 2 2\n",
        "1\n5 10 5\n",
        "1\n3 6 3\n",
        "1\n2 4 2\n",
        "1\n10 20 2\n",
        "1\n1 1 1\n",
        "1\n4 8 4\n",
        "1\n3 9 3\n",
        "1\n2 5 2\n",
        "1\n7 14 2\n",
    ]


# ─── 1343A Candies ────────────────────────────────────────────────────────────

def _1343a_val(n: int) -> int:
    k = 0
    while k * (k + 1) // 2 <= n:
        k += 1
    return k - 1


def _1343a(stdin: str) -> str:
    return "\n".join(str(_1343a_val(int(x))) for x in lines(stdin)[1:]) + "\n"


def _1343a_alt(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        lo, hi = 1, n
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if mid * (mid + 1) // 2 <= n:
                lo = mid
            else:
                hi = mid - 1
        out.append(str(lo))
    return "\n".join(out) + "\n"


def _gen_1343a(rng: random.Random) -> list[str]:
    return [
        "7\n1\n3\n4\n1\n12\n123456789\n1000000000\n",
        "1\n1\n",
        "1\n6\n",
        "1\n10\n",
        "1\n15\n",
        "1\n21\n",
        "1\n28\n",
        "1\n36\n",
        "1\n45\n",
        "1\n55\n",
        "1\n66\n",
    ]


# ─── 460A Vasya and Socks ─────────────────────────────────────────────────────

def _460a_days(n: int, m: int) -> int:
    days = 0
    while n > 0:
        n -= 2
        days += 1
        if days % m == 0:
            if n < 0:
                days -= 1
                break
            n += 2
    return days


def _460a(stdin: str) -> str:
    n, m = map(int, lines(stdin)[0].split())
    return f"{_460a_days(n, m)}\n"


def _460a_alt(stdin: str) -> str:
    n, m = map(int, lines(stdin)[0].split())
    return f"{_460a_days(n, m)}\n"


def _gen_460a(rng: random.Random) -> list[str]:
    return [
        "9 2\n",
        "6 1\n",
        "4 2\n",
        "10 3\n",
        "2 1\n",
        "8 4\n",
        "12 2\n",
        "5 5\n",
        "3 1\n",
        "7 7\n",
        "20 5\n",
    ]


# ─── 1992A Only Pluses ────────────────────────────────────────────────────────

def _1992a_case(a: list[int]) -> int:
    best = a[0] * a[1] * a[2]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    for m in range(3):
                        b = [a[0] + i, a[1] + j, a[2] + k + l + m]
                        best = max(best, b[0] * b[1] * b[2])
    return best


def _1992a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        _n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        out.append(str(_1992a_case(a)))
    return "\n".join(out) + "\n"


def _1992a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        _n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        best = -1
        for x in range(a[0], a[0] + 6):
            for y in range(a[1], a[1] + 6):
                for z in range(a[2], a[2] + 6):
                    if (x - a[0]) + (y - a[1]) + (z - a[2]) <= 5:
                        best = max(best, x * y * z)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _gen_1992a(rng: random.Random) -> list[str]:
    return [
        "2\n3\n1 2 3\n3\n1 1 1\n",
        "1\n3\n2 2 2\n",
        "1\n3\n1 1 5\n",
        "1\n3\n3 3 3\n",
        "1\n3\n1 2 1\n",
        "1\n3\n4 1 1\n",
        "1\n3\n2 3 4\n",
        "1\n3\n5 5 1\n",
        "1\n3\n1 3 2\n",
        "1\n3\n2 1 3\n",
        "1\n3\n6 1 1\n",
    ]


# ─── 1462A Favorite Sequence ──────────────────────────────────────────────────

def _1462a_case(pairs: list[tuple[int, int]]) -> str:
    from collections import defaultdict
    g = defaultdict(list)
    deg = Counter()
    for a, b in pairs:
        g[a].append(b)
        g[b].append(a)
        deg[a] += 1
        deg[b] += 1
    start = next(k for k, v in deg.items() if v == 1)
    path = [start]
    prev = -1
    cur = start
    while len(path) < len(deg):
        nxt = next(x for x in g[cur] if x != prev)
        path.append(nxt)
        prev, cur = cur, nxt
    return " ".join(map(str, path))


def _1462a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        pairs = [tuple(map(int, ls[i + j].split())) for j in range(n - 1)]
        i += n - 1
        out.append(_1462a_case(pairs))
    return "\n".join(out) + "\n"


def _1462a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        edges = [tuple(map(int, ls[i + j].split())) for j in range(n - 1)]
        i += n - 1
        adj = {}
        for a, b in edges:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        ends = [k for k, v in adj.items() if len(v) == 1]
        s = ends[0]
        res = [s]
        used = {s}
        while len(res) < n:
            for nb in adj[res[-1]]:
                if nb not in used:
                    res.append(nb)
                    used.add(nb)
                    break
        out.append(" ".join(map(str, res)))
    return "\n".join(out) + "\n"


def _gen_1462a(rng: random.Random) -> list[str]:
    return [
        "1\n4\n3 1\n1 2\n2 4\n",
        "1\n3\n1 2\n2 3\n",
        "1\n5\n1 2\n2 3\n3 4\n4 5\n",
        "1\n4\n2 1\n1 3\n3 4\n",
        "1\n3\n5 7\n7 3\n",
        "1\n4\n10 2\n2 3\n3 4\n",
        "1\n3\n4 5\n5 6\n",
        "1\n5\n1 5\n5 2\n2 3\n3 4\n",
        "1\n4\n7 8\n8 9\n9 10\n",
        "1\n3\n2 4\n4 6\n",
        "1\n4\n1 3\n3 2\n2 4\n",
    ]


# ─── 1831A Twin Permutations ──────────────────────────────────────────────────

def _1831a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        p = list(map(int, ls[i].split())); i += 1
        out.append(" ".join(str(n + 1 - x) for x in p))
    return "\n".join(out) + "\n"


def _1831a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        p = list(map(int, ls[i].split())); i += 1
        q = [0] * n
        for i0, v in enumerate(p):
            q[v - 1] = n - i0
        out.append(" ".join(map(str, q)))
    return "\n".join(out) + "\n"


def _gen_1831a(rng: random.Random) -> list[str]:
    return [
        "1\n4\n1 2 3 4\n",
        "1\n3\n2 3 1\n",
        "1\n5\n5 4 3 2 1\n",
        "1\n2\n1 2\n",
        "1\n6\n3 1 4 2 6 5\n",
        "1\n3\n3 2 1\n",
        "1\n4\n4 1 3 2\n",
        "1\n5\n1 3 5 2 4\n",
        "1\n2\n2 1\n",
        "1\n7\n1 2 3 4 5 6 7\n",
        "1\n3\n1 3 2\n",
    ]


# ─── 1325A EhAb AnD gCd ───────────────────────────────────────────────────────

def _1325a_pair(x: int) -> str:
  if x % 2 == 0:
    return f"2 {x - 2}"
  for d in range(3, x, 2):
    if x % d == 0:
      return f"{d} {x - d}"
  return f"3 {x - 3}"


def _1325a(stdin: str) -> str:
    return "\n".join(_1325a_pair(int(x)) for x in lines(stdin)[1:]) + "\n"


def _1325a_alt(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        found = None
        for a in range(2, n):
            b = n - a
            if _gcd(a, b) > 1:
                found = f"{a} {b}"
                break
        out.append(found or f"2 {n-2}")
    return "\n".join(out) + "\n"


def _gen_1325a(rng: random.Random) -> list[str]:
    return [
        "2\n4\n6\n",
        "1\n8\n",
        "1\n10\n",
        "1\n12\n",
        "1\n14\n",
        "1\n16\n",
        "1\n18\n",
        "1\n20\n",
        "1\n22\n",
        "1\n24\n",
        "1\n26\n",
    ]


# ─── 2185A Perfect Root ───────────────────────────────────────────────────────

def _2185a_val(n: int) -> int:
    for b in range(1, 65):
        p = b**b
        if p == n:
            return b
        if p > n:
            break
    return -1


def _2185a(stdin: str) -> str:
    return "\n".join(str(_2185a_val(int(x))) for x in lines(stdin)[1:]) + "\n"


def _2185a_alt(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        ans = -1
        b = 1
        while b**b <= n and b < 65:
            if b**b == n:
                ans = b
                break
            b += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _gen_2185a(rng: random.Random) -> list[str]:
    return [
        "5\n2\n4\n6\n8\n16\n",
        "1\n1\n",
        "1\n27\n",
        "1\n256\n",
        "1\n3\n",
        "1\n5\n",
        "1\n9\n",
        "1\n3125\n",
        "1\n7\n",
        "1\n10\n",
        "1\n3124\n",
    ]


# ─── 1805A We Need the Zero ───────────────────────────────────────────────────

def _1805a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        x = 0
        for v in a:
            x ^= v
        if x == 0:
            out.append("0")
        else:
            pos = {}
            ans = None
            for idx, v in enumerate(a):
                need = x ^ v
                if need in pos:
                    ans = f"{pos[need] + 1} {idx + 1}"
                    break
                pos[v] = idx
            out.append(ans or "0")
    return "\n".join(out) + "\n"


def _1805a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        total = reduce(lambda p, q: p ^ q, a, 0)
        if total == 0:
            out.append("0")
            continue
        pair = "0"
        for i1 in range(n):
            for i2 in range(i1 + 1, n):
                if (a[i1] ^ a[i2]) == 0:
                    pair = f"{i1 + 1} {i2 + 1}"
                    break
            if pair != "0":
                break
        out.append(pair)
    return "\n".join(out) + "\n"


def _gen_1805a(rng: random.Random) -> list[str]:
    return [
        "3\n3\n1 2 3\n3\n1 1 1\n3\n2 2 3\n",
        "1\n2\n5 5\n",
        "1\n4\n1 2 3 3\n",
        "1\n3\n4 4 4\n",
        "1\n2\n1 1\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n3\n7 7 7\n",
        "1\n4\n2 2 5 5\n",
        "1\n3\n1 1 2\n",
        "1\n6\n1 1 2 2 3 3\n",
        "1\n2\n3 4\n",
    ]


# ─── 2132A Homework ───────────────────────────────────────────────────────────

def _2132a(stdin: str) -> str:
    out = []
    for a, b, c, x, y, z in (map(int, line.split()) for line in lines(stdin)[1:]):
        out.append(str(max(0, a - x) + max(0, b - y) + max(0, c - z)))
    return "\n".join(out) + "\n"


def _2132a_alt(stdin: str) -> str:
    out = []
    for parts in (line.split() for line in lines(stdin)[1:]):
        a, b, c, x, y, z = map(int, parts)
        s = sum(max(0, v - t) for v, t in ((a, x), (b, y), (c, z)))
        out.append(str(s))
    return "\n".join(out) + "\n"


def _gen_2132a(rng: random.Random) -> list[str]:
    return [
        "3\n1 2 3 1 1 1\n5 5 5 3 3 3\n10 1 1 5 0 0\n",
        "1\n0 0 0 0 0 0\n",
        "1\n5 5 5 5 5 5\n",
        "1\n1 1 1 2 2 2\n",
        "1\n3 3 3 1 1 1\n",
        "1\n10 10 10 1 1 1\n",
        "1\n2 4 6 1 2 3\n",
        "1\n7 8 9 7 8 9\n",
        "1\n1 2 3 0 0 0\n",
        "1\n4 4 4 10 10 10\n",
        "1\n6 6 6 2 2 2\n",
    ]


# ─── 115A Party ───────────────────────────────────────────────────────────────

def _115a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    bosses = list(map(int, ls[1].split()))
    parent = [0] * (n + 1)
    for i in range(2, n + 1):
        parent[i] = bosses[i - 2]
    depth = [0] * (n + 1)
    for i in range(2, n + 1):
        depth[i] = depth[parent[i]] + 1
    return str(max(depth[1:]) + 1) + "\n"


def _115a_alt(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    bosses = list(map(int, ls[1].split()))
    parent = [0] * (n + 1)
    for i in range(2, n + 1):
        parent[i] = bosses[i - 2]
    best = 1
    for v in range(1, n + 1):
        d = 1
        cur = v
        while parent[cur] != 0:
            d += 1
            cur = parent[cur]
        best = max(best, d)
    return str(best) + "\n"


def _gen_115a(rng: random.Random) -> list[str]:
    return [
        "5\n1 2 3 4\n",
        "3\n1 1\n",
        "4\n1 2 2\n",
        "6\n1 1 2 2 3\n",
        "2\n1\n",
        "7\n1 1 1 2 2 2\n",
        "8\n1 2 2 3 3 3 4\n",
        "5\n1 1 1 1\n",
        "10\n1 1 2 2 3 3 4 4 5\n",
        "3\n1 2\n",
        "6\n1 2 3 3 3\n",
    ]


# ─── 1760C Advantage ──────────────────────────────────────────────────────────

def _1760c(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        row = []
        for j in range(n):
            mx = max(a[k] for k in range(n) if k != j)
            row.append(str(a[j] - mx))
        out.append(" ".join(row))
    return "\n".join(out) + "\n"


def _1760c_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        row = []
        for j, val in enumerate(a):
            others = [a[k] for k in range(n) if k != j]
            row.append(str(val - max(others)))
        out.append(" ".join(row))
    return "\n".join(out) + "\n"


def _gen_1760c(rng: random.Random) -> list[str]:
    return [
        "1\n4\n5 3 3 1\n",
        "1\n3\n1 2 3\n",
        "1\n5\n10 10 5 3 2\n",
        "1\n2\n5 5\n",
        "1\n6\n1 1 1 1 1 1\n",
        "1\n4\n4 3 2 1\n",
        "1\n3\n5 5 5\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n4\n2 2 2 2\n",
        "1\n3\n100 50 50\n",
        "1\n4\n7 7 3 3\n",
    ]


# ─── 686A Free Ice Cream ─────────────────────────────────────────────────────

def _686a(stdin: str) -> str:
    ls = lines(stdin)
    n, k = map(int, ls[0].split())
    ice = k
    angry = 0
    for line in ls[1:]:
        sign, x = line.split()
        x = int(x)
        if sign == "+":
            ice += x
        elif ice >= x:
            ice -= x
        else:
            angry += 1
    return str(angry) + "\n"


def _686a_alt(stdin: str) -> str:
    ls = lines(stdin)
    n, k = map(int, ls[0].split())
    cur = k
    res = 0
    for ev in ls[1:]:
        op, val = ev[0], int(ev.split()[1])
        if op == "+":
            cur += val
        elif cur < val:
            res += 1
        else:
            cur -= val
    return str(res) + "\n"


def _gen_686a(rng: random.Random) -> list[str]:
    return [
        "5 10\n+ 5\n- 7\n+ 13\n- 2\n- 6\n",
        "3 5\n+ 1\n- 10\n+ 3\n",
        "2 0\n- 1\n- 1\n",
        "4 100\n- 50\n- 50\n- 50\n+ 10\n",
        "1 5\n+ 5\n",
        "2 3\n- 2\n- 2\n",
        "3 1\n+ 10\n- 5\n- 10\n",
        "4 20\n- 5\n+ 5\n- 30\n- 1\n",
        "2 0\n+ 1\n- 1\n",
        "3 2\n- 3\n+ 10\n- 5\n",
        "1 1000\n- 1\n",
    ]


# ─── 2114A Square Year ────────────────────────────────────────────────────────

def _2114a(n: int) -> str:
    for a in range(int(n**0.5) + 1):
        b2 = n - a * a
        b = int(b2**0.5)
        if b * b == b2:
            return f"{a} {b}"
    return "-1"


def _2114a_s(stdin: str) -> str:
    return "\n".join(_2114a(int(x)) for x in lines(stdin)[1:]) + "\n"


def _2114a_alt(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        found = "-1"
        for a in range(int(n**0.5) + 2):
            rem = n - a * a
            b = int(rem**0.5)
            if b >= 0 and a * a + b * b == n:
                found = f"{a} {b}"
                break
        out.append(found)
    return "\n".join(out) + "\n"


def _gen_2114a(rng: random.Random) -> list[str]:
    return [
        "3\n5\n4\n6\n",
        "1\n1\n",
        "1\n2\n",
        "1\n25\n",
        "1\n10\n",
        "1\n13\n",
        "1\n100\n",
        "1\n50\n",
        "1\n3\n",
        "1\n8\n",
        "1\n17\n",
    ]


# ─── 1904A Forked! ────────────────────────────────────────────────────────────

def _1904a_case(a, b, c, d, kx, ky):
    moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    seen = set()
    for dx1, dy1 in moves:
        x1, y1 = a + dx1, b + dy1
        if (x1, y1) == (c, d):
            continue
        for dx2, dy2 in moves:
            x2, y2 = x1 + dx2, y1 + dy2
            if (x2, y2) == (c, d):
                continue
            seen.add((x2, y2))
    return len(seen)


def _1904a(stdin: str) -> str:
  ls = lines(stdin)
  out = []
  i = 1
  for _ in range(int(ls[0])):
    a,b,c,d = map(int, ls[i].split()); i += 1
    kx, ky = map(int, ls[i].split()); i += 1
    out.append(str(_1904a_case(a,b,c,d,kx,ky)))
  return "\n".join(out) + "\n"


def _1904a_alt(stdin: str) -> str:
  ls = lines(stdin)
  out = []
  i = 1
  moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
  for _ in range(int(ls[0])):
    a,b,c,d = map(int, ls[i].split()); i += 1
    kx, ky = map(int, ls[i].split()); i += 1
    good = set()
    for dx1, dy1 in moves:
      x1, y1 = a+dx1, b+dy1
      if (x1,y1)==(c,d): continue
      for dx2, dy2 in moves:
        x2,y2 = x1+dx2, y1+dy2
        if (x2,y2)!=(c,d):
          good.add((x2,y2))
    out.append(str(len(good)))
  return "\n".join(out) + "\n"


def _gen_1904a(rng: random.Random) -> list[str]:
    return [
        "1\n0 0 1 2\n3 3\n",
        "1\n0 0 0 0\n1 1\n",
        "1\n1 1 2 2\n0 0\n",
        "1\n0 0 2 1\n5 5\n",
        "1\n3 3 4 4\n0 0\n",
        "1\n0 0 1 0\n2 2\n",
        "1\n5 5 6 6\n0 0\n",
        "1\n0 0 3 3\n1 1\n",
        "1\n2 2 3 3\n0 0\n",
        "1\n0 0 1 1\n4 4\n",
        "1\n1 2 3 4\n0 0\n",
    ]


# ─── 1869A Make It Zero ───────────────────────────────────────────────────────

def _1869a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        if n == 2:
            out.append("YES" if a[0] == a[1] else "NO")
        else:
            out.append("YES")
    return "\n".join(out) + "\n"


def _1869a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        if n < 3:
            out.append("YES" if a[0] == a[1] else "NO")
        else:
            out.append("YES")
    return "\n".join(out) + "\n"


def _gen_1869a(rng: random.Random) -> list[str]:
    return [
        "3\n2\n1 1\n2\n2 3\n4\n1 2 3 4\n",
        "1\n2\n5 5\n",
        "1\n2\n1 2\n",
        "1\n3\n1 2 3\n",
        "1\n5\n1 1 1 1 1\n",
        "1\n4\n0 0 0 0\n",
        "1\n3\n5 5 5\n",
        "1\n2\n0 0\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n3\n2 4 6\n",
        "1\n2\n7 8\n",
    ]


# ─── 2185B Prefix Max ─────────────────────────────────────────────────────────

def _2185b_case(a: list[int]) -> int:
    n = len(a)
    pref = []
    cur = -10**18
    for v in a:
        cur = max(cur, v)
        pref.append(cur)
    total = sum(pref)

    def score(skip: int) -> int:
        cur2 = -10**18
        s = 0
        for i, v in enumerate(a):
            if i == skip:
                continue
            cur2 = max(cur2, v)
            s += cur2
        return s

    return max(score(i) for i in range(n))


def _2185b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        out.append(str(_2185b_case(a)))
    return "\n".join(out) + "\n"


def _2185b_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        best = 0
        for skip in range(n):
            cur = -10**18
            s = 0
            for j, v in enumerate(a):
                if j == skip:
                    continue
                cur = max(cur, v)
                s += cur
            best = max(best, s)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _gen_2185b(rng: random.Random) -> list[str]:
    return [
        "1\n4\n1 2 3 4\n",
        "1\n3\n5 1 2\n",
        "1\n5\n1 5 2 4 3\n",
        "1\n2\n10 1\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n3\n3 3 3\n",
        "1\n4\n4 3 2 1\n",
        "1\n5\n2 2 2 2 2\n",
        "1\n3\n1 3 2\n",
        "1\n4\n2 1 4 3\n",
        "1\n5\n10 1 1 1 1\n",
    ]


# ─── 1794B Not Dividing ───────────────────────────────────────────────────────

def _1794b_case(a: list[int]) -> int:
    a = list(a)
    ops = 0
    for i in range(len(a) - 1):
        while a[i] % a[i + 1] == 0 or a[i + 1] % a[i] == 0:
            a[i + 1] += 1
            ops += 1
    return ops


def _1794b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        a = list(map(int, ls[i].split())); i += 1
        out.append(str(_1794b_case(a)))
    return "\n".join(out) + "\n"


def _1794b_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i]); i += 1
        arr = list(map(int, ls[i].split())); i += 1
        cnt = 0
        for j in range(n - 1):
            while arr[j] % arr[j + 1] == 0 or arr[j + 1] % arr[j] == 0:
                arr[j + 1] += 1
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _gen_1794b(rng: random.Random) -> list[str]:
    return [
        "1\n3\n2 4 8\n",
        "1\n2\n1 1\n",
        "1\n4\n1 2 3 4\n",
        "1\n3\n6 3 2\n",
        "1\n5\n1 1 1 1 1\n",
        "1\n3\n4 2 2\n",
        "1\n4\n3 6 2 4\n",
        "1\n2\n5 10\n",
        "1\n3\n2 2 2\n",
        "1\n4\n7 7 7 7\n",
        "1\n3\n1 3 9\n",
    ]


def _build() -> list:
    specs = []

    def reg(problem_id, summary, sample_in, solve, alt, mutants, generate, **kw):
        sample_out = solve(sample_in)
        specs.append(
            make_spec(
                problem_id,
                summary=summary,
                samples=({"input": sample_in, "output": sample_out},),
                solve=solve,
                alt=alt,
                mutants=mutants,
                generate=generate,
                **kw,
            )
        )

    reg("1890A", "At most two colors with counts differing by at most 1.", "3\n4\n2 2 1 1\n4\n3 1 2 3\n2\n1 3\n", _1890a, _1890a_alt, {"always_no": lambda s: "NO\n" * int(lines(s)[0]), "always_yes": lambda s: "YES\n" * int(lines(s)[0])}, _gen_1890a, family="constructive", checker="tokens_ci")
    reg("1862B", "Always YES: can make strictly increasing sequence.", "3\n1\n1 2\n3\n1 2 3\n2\n1 1\n", _1862b, _1862b_alt, {"always_no": lambda s: "NO\n" * int(lines(s)[0]), "flip": lambda s: "NO\n" if lines(s)[0] == "1" else _1862b(s)}, _gen_1862b, family="constructive", checker="tokens_ci")
    reg("1837A", "Grasshopper reaches y in at most x jumps of size k.", "7\n6 2 2\n1 2 6\n2 3 2\n629 4 2\n12 11 4\n308 5 3\n17 5 34\n", _1837a, _1837a_alt, {"always_yes": lambda s: "YES\n" * len(lines(s)[1:]), "always_no": lambda s: "NO\n" * len(lines(s)[1:])}, _gen_1837a, family="math", checker="tokens_ci")
    reg("1343A", "Max k with k(k+1)/2 <= n.", "7\n1\n3\n4\n1\n12\n123456789\n1000000000\n", _1343a, _1343a_alt, {"n": lambda s: s, "one": lambda s: "1\n" * len(lines(s)[1:])}, _gen_1343a, family="math")
    reg("460A", "Vasya socks simulation until cannot wear pair.", "9 2\n", _460a, _460a_alt, {"n": lambda s: lines(s)[0].split()[0] + "\n", "zero": lambda s: "0\n"}, _gen_460a, family="simulation")
    reg("1992A", "Max product after five +1 operations on three numbers.", "2\n3\n1 2 3\n3\n1 1 1\n", _1992a, _1992a_alt, {"sum": lambda s: "6\n" * int(lines(s)[0]), "zero": lambda s: "0\n" * int(lines(s)[0])}, _gen_1992a, family="brute_force")
    reg("1462A", "Reconstruct sequence from adjacent pairs.", "1\n4\n3 1\n1 2\n2 4\n", _1462a, _1462a_alt, {"reverse": lambda s: _1462a(s).strip()[::-1] + "\n", "first": lambda s: lines(s)[2].split()[0] + "\n"}, _gen_1462a, family="graphs", checker="tokens")
    reg("1831A", "Twin permutation q[i]=n+1-p[i].", "1\n4\n1 2 3 4\n", _1831a, _1831a_alt, {"same": lambda s: "\n".join(lines(s)[2:] if len(lines(s)) > 2 else []) + "\n", "ones": lambda s: "1\n"}, _gen_1831a, family="constructive", checker="tokens")
    reg("1325A", "Split x into a+b with gcd(a,b)>1.", "2\n4\n6\n", _1325a, _1325a_alt, {"half": lambda s: "\n".join(str(int(x)//2) + " " + str((int(x)+1)//2) for x in lines(s)[1:]) + "\n", "one": lambda s: "\n".join("1 " + str(int(x)-1) for x in lines(s)[1:]) + "\n"}, _gen_1325a, family="math", checker="tokens")
    reg("2185A", "Smallest b with b^b == n or -1.", "5\n2\n4\n6\n8\n16\n", _2185a, _2185a_alt, {"zero": lambda s: "0\n" * len(lines(s)[1:]), "one": lambda s: "1\n" * len(lines(s)[1:])}, _gen_2185a, family="math")
    reg("1805A", "XOR zero: output 0 or two equal elements.", "3\n3\n1 2 3\n3\n1 1 1\n3\n2 2 3\n", _1805a, _1805a_alt, {"zero": lambda s: "0\n" * int(lines(s)[0]), "one_two": lambda s: "1 2\n" * int(lines(s)[0])}, _gen_1805a, family="bitmasks")
    reg("2132A", "Sum of homework deficits across three subjects.", "3\n1 2 3 1 1 1\n5 5 5 3 3 3\n10 1 1 5 0 0\n", _2132a, _2132a_alt, {"zero": lambda s: "0\n" * len(lines(s)[1:]), "sum_abc": lambda s: "\n".join(str(sum(map(int, l.split()[:3]))) for l in lines(s)[1:]) + "\n"}, _gen_2132a, family="math")
    reg("115A", "Max depth in rooted tree from employee 1.", "5\n1 2 3 4\n", _115a, _115a_alt, {"n": lambda s: lines(s)[0], "one": lambda s: "1\n"}, _gen_115a, family="trees")
    reg("1760C", "Advantage score minus max of others for each player.", "1\n4\n5 3 3 1\n", _1760c, _1760c_alt, {"zero": lambda s: "0\n" * int(lines(s)[0]), "max": lambda s: "\n".join(" ".join(lines(s)[2].split()) for _ in range(int(lines(s)[0]))) + "\n"}, _gen_1760c, family="implementation", checker="tokens")
    reg("686A", "Angry people when ice cream runs out.", "5 10\n+ 5\n- 7\n+ 13\n- 2\n- 6\n", _686a, _686a_alt, {"zero": lambda s: "0\n", "n": lambda s: lines(s)[0].split()[0] + "\n"}, _gen_686a, family="simulation")
    reg("2114A", "Find a,b with a^2+b^2=n or -1.", "3\n5\n4\n6\n", _2114a_s, _2114a_alt, {"zero": lambda s: "0 0\n" * len(lines(s)[1:]), "neg": lambda s: "-1\n" * len(lines(s)[1:])}, _gen_2114a, family="math", checker="tokens")
    reg("1904A", "Count knight double-move destinations avoiding block.", "1\n0 0 1 2\n3 3\n", _1904a, _1904a_alt, {"zero": lambda s: "0\n" * int(lines(s)[0]), "big": lambda s: "100\n" * int(lines(s)[0])}, _gen_1904a, family="brute_force")
    reg("1869A", "Make array zero with given operations.", "3\n2\n1 1\n2\n2 3\n4\n1 2 3 4\n", _1869a, _1869a_alt, {"always_no": lambda s: "NO\n" * int(lines(s)[0]), "always_yes": lambda s: "YES\n" * int(lines(s)[0])}, _gen_1869a, family="constructive", checker="tokens_ci")
    reg("2185B", "Max prefix-max sum after removing one element.", "1\n4\n1 2 3 4\n", _2185b, _2185b_alt, {"zero": lambda s: "0\n" * int(lines(s)[0]), "sum": lambda s: "10\n" * int(lines(s)[0])}, _gen_2185b, family="greedy")
    reg("1794B", "Min increments so no adjacent divides.", "1\n3\n2 4 8\n", _1794b, _1794b_alt, {"zero": lambda s: "0\n" * int(lines(s)[0]), "one": lambda s: "1\n" * int(lines(s)[0])}, _gen_1794b, family="greedy")

    return specs


SPECS = _build()

_KEEP = ['1890A', '1862B', '1837A', '1343A', '1462A', '1325A', '2185A', '2132A', '115A', '1760C', '686A', '1904A', '1869A', '2185B']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
