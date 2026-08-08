"""Dual-oracle ProblemOracleSpec entries for SolveX practice pack batch 12.

Source: missing_chunk_3.json (70 candidates).
Skipped denylist: 1367B,1374A,1374C,1433A,1520D,1619A,1722A,313A,474B,490A,749A,80A
Skipped constructive multi-answer: 1520C,1878B,445A,1992C,1909B,1632B,1659A,1326A,1914B
Skipped IDs already present in bulk_00..bulk_11 _KEEP lists.
"""

from __future__ import annotations

import math
import random
from collections import Counter, deque

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

MOD = 10**9 + 7


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _lcm(a: int, b: int) -> int:
    return a // _gcd(a, b) * b if a and b else 0


def xor_0_to(n: int) -> int:
    if n < 0:
        return 0
    r = n % 4
    if r == 0:
        return n
    if r == 1:
        return 1
    if r == 2:
        return n + 1
    return 0


def _mexor_len(a: int, b: int) -> int:
    pre = xor_0_to(a - 1)
    if pre == b:
        return a
    if (pre ^ b) != a:
        return a + 1
    return a + 2


def _shirt_rank(s: str) -> int:
    return ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"].index(s)


def _ordinary_count(l: int, r: int) -> int:
  cnt = 0
  for d in range(1, 10):
    x = d
    while x <= r:
      if x >= l:
        cnt += 1
      x = x * 10 + d
  return cnt



# ─── 1567B MEXor Mixup ─────────────────────────────────────────────────────

def _s_1567b(stdin: str) -> str:
    out = [str(_mexor_len(*map(int, line.split()))) for line in lines(stdin)[1:]]
    return "\n".join(out) + "\n"


def _a_1567b(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        a, b = map(int, line.split())
        pre = xor_0_to(a - 1)
        if pre == b:
            out.append(str(a))
        else:
            k = pre ^ b
            out.append(str(a + 1 if k != a else a + 2))
    return "\n".join(out) + "\n"


def _m1_1567b(stdin: str) -> str:
    return "\n".join(line.split()[0] for line in lines(stdin)[1:]) + "\n"


def _m2_1567b(stdin: str) -> str:
    return "\n".join(str(int(line.split()[0]) + 1) for line in lines(stdin)[1:]) + "\n"


def _gen_1567b(rng: random.Random) -> list[str]:
    return [
        "5\n1 1\n2 1\n2 0\n1 10000\n2 10000\n",
        "1\n3 1\n",
        "1\n5 2\n",
        "1\n7 0\n",
        "1\n4 5\n",
        "1\n6 1\n",
        "1\n8 2\n",
        "1\n9 4\n",
        "1\n11 1\n",
        "1\n10 3\n",
        "1\n12 0\n",
        "1\n15 7\n",
    ]


# ─── 1829D Gold Rush ─────────────────────────────────────────────────────────

def _gold_reach(n: int) -> bool:
    while n % 11 == 0:
        n //= 11
    return n == 1


def _s_1829d(stdin: str) -> str:
    out = [yes_no(_gold_reach(int(x))).strip() for x in lines(stdin)[1:]]
    return "\n".join(out) + "\n"


def _a_1829d(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        while n % 11 == 0:
            n //= 11
        out.append(yes_no(n == 1).strip())
    return "\n".join(out) + "\n"


def _m1_1829d(stdin: str) -> str:
    return "\n".join("YES" for _ in lines(stdin)[1:]) + "\n"


def _m2_1829d(stdin: str) -> str:
    return "\n".join("NO" for _ in lines(stdin)[1:]) + "\n"


def _gen_1829d(rng: random.Random) -> list[str]:
    return [
        "3\n11\n121\n1331\n",
        "1\n1\n",
        "1\n22\n",
        "1\n12\n",
        "1\n110\n",
        "1\n13\n",
        "1\n242\n",
        "1\n100\n",
        "1\n14641\n",
        "1\n14\n",
        "1\n33\n",
        "1\n111\n",
    ]


# ─── 1846A Cut the Rope ─────────────────────────────────────────────────────

def _s_1846a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        cnt = 0
        for _ in range(n):
            a, b = map(int, ls[idx].split()); idx += 1
            if a > b:
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _a_1846a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        pairs = [tuple(map(int, ls[idx + i].split())) for i in range(n)]
        idx += n
        out.append(str(sum(1 for a, b in pairs if a > b)))
    return "\n".join(out) + "\n"


def _m1_1846a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        idx += n
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_1846a(stdin: str) -> str:
    return _m1_1846a(stdin)


def _gen_1846a(rng: random.Random) -> list[str]:
    return [
        "4\n3\n4 3\n3 1\n1 2\n4\n9 2\n5 2\n7 7\n3 4\n5\n11 7\n5 10\n12 9\n3 2\n1 5\n3\n5 6\n4 5\n7 7\n",
        "1\n1\n5 6\n",
        "1\n2\n3 4\n5 6\n",
        "1\n1\n1 10\n",
        "1\n1\n10 1\n",
        "1\n3\n1 1\n2 2\n3 3\n",
        "1\n2\n5 5\n6 6\n",
        "1\n1\n2 8\n",
        "1\n1\n8 2\n",
        "1\n2\n1 5\n9 1\n",
        "1\n1\n7 7\n",
        "1\n1\n4 9\n",
    ]


# ─── 1811A Insert Digit ──────────────────────────────────────────────────────

def _insert_digit(s: str, d: int) -> str:
    for i, ch in enumerate(s):
        if int(ch) < d:
            return s[:i] + str(d) + s[i:]
    return s + str(d)


def _s_1811a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split()); idx += 1
        s = ls[idx]; idx += 1
        out.append(_insert_digit(s, d))
    return "\n".join(out) + "\n"


def _a_1811a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split()); idx += 1
        s = ls[idx]; idx += 1
        placed = False
        res = []
        for ch in s:
            if not placed and int(ch) < d:
                res.append(str(d))
                placed = True
            res.append(ch)
        if not placed:
            res.append(str(d))
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _m1_1811a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split()); idx += 1
        s = ls[idx]; idx += 1
        out.append(s + str(d))
    return "\n".join(out) + "\n"


def _m2_1811a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n, d = map(int, ls[idx].split()); idx += 1
        s = ls[idx]; idx += 1
        out.append(str(d) + s)
    return "\n".join(out) + "\n"


def _gen_1811a(rng: random.Random) -> list[str]:
    return [
        "1\n5 4\n76543\n",
        "1\n1 0\n1\n",
        "1\n2 5\n44\n",
        "1\n3 6\n666\n",
        "1\n4 9\n1234\n",
        "1\n3 1\n999\n",
        "1\n2 8\n12\n",
        "1\n5 0\n54321\n",
        "1\n3 7\n111\n",
        "1\n4 3\n8765\n",
        "1\n2 9\n10\n",
        "1\n6 5\n123456\n",
    ]


# ─── 1765M Minimum LCM ─────────────────────────────────────────────────────

def _s_1765m(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        best = min(_lcm(a[i], a[j]) for i in range(n) for j in range(i + 1, n))
        out.append(str(best))
    return "\n".join(out) + "\n"


def _a_1765m(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        best = 10**18
        for i in range(n):
            for j in range(i + 1, n):
                best = min(best, a[i] // _gcd(a[i], a[j]) * a[j])
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m1_1765m(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(min(a)))
    return "\n".join(out) + "\n"


def _m2_1765m(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(max(a)))
    return "\n".join(out) + "\n"


def _gen_1765m(rng: random.Random) -> list[str]:
    return [
        "1\n3\n2 4 6\n",
        "1\n2\n3 5\n",
        "1\n4\n1 2 3 4\n",
        "1\n2\n6 8\n",
        "1\n3\n5 10 15\n",
        "1\n2\n7 11\n",
        "1\n5\n2 3 5 7 11\n",
        "1\n2\n12 18\n",
        "1\n3\n4 6 9\n",
        "1\n2\n9 12\n",
        "1\n3\n8 12 16\n",
        "1\n2\n14 21\n",
    ]



# ─── 1974B Symmetric Encoding ───────────────────────────────────────────────

def _decode_1974b(s: str) -> str:
    order = sorted(set(s))
    mp = {ch: chr(97 + i) for i, ch in enumerate(order)}
    return "".join(mp[ch] for ch in s)


def _s_1974b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(_decode_1974b(s))
    return "\n".join(out) + "\n"


def _a_1974b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        uniq = sorted(set(s))
        rev = {c: chr(97 + i) for i, c in enumerate(uniq)}
        out.append("".join(rev[c] for c in s))
    return "\n".join(out) + "\n"


def _m1_1974b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(s[::-1])
    return "\n".join(out) + "\n"


def _m2_1974b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(s)
    return "\n".join(out) + "\n"


def _gen_1974b(rng: random.Random) -> list[str]:
    return [
        "1\n5\nababa\n",
        "1\n4\nbbaa\n",
        "1\n3\nabc\n",
        "1\n6\naabbcc\n",
        "1\n2\naa\n",
        "1\n5\nabcde\n",
        "1\n4\nccdd\n",
        "1\n7\nxyzyzyz\n",
        "1\n3\nzzz\n",
        "1\n5\naabbc\n",
        "1\n4\nwxyz\n",
        "1\n6\nmnopqr\n",
    ]


# ─── 1807C Find and Replace ─────────────────────────────────────────────────

def _s_1807c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        q = int(ls[idx]); idx += 1
        mp = {}
        for _ in range(q):
            c, d = ls[idx].split(); idx += 1
            mp[c] = d
        out.append("".join(mp.get(ch, ch) for ch in s))
    return "\n".join(out) + "\n"


def _a_1807c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        q = int(ls[idx]); idx += 1
        repl = {}
        for _ in range(q):
            c, d = ls[idx].split(); idx += 1
            repl[c] = d
        res = []
        for ch in s:
            res.append(repl[ch] if ch in repl else ch)
        out.append("".join(res))
    return "\n".join(out) + "\n"


def _m1_1807c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        q = int(ls[idx]); idx += 1
        idx += q
        out.append(s[::-1])
    return "\n".join(out) + "\n"


def _m2_1807c(stdin: str) -> str:
    return _m1_1807c(stdin)


def _gen_1807c(rng: random.Random) -> list[str]:
    return [
        "1\n5\nabacaba\n2\na e\nc b\n",
        "1\n3\nabc\n1\na x\n",
        "1\n4\naaaa\n1\na b\n",
        "1\n6\nabcdef\n2\na z\nd y\n",
        "1\n2\nxy\n1\nx y\n",
        "1\n5\nhello\n1\nh H\n",
        "1\n3\nzzz\n1\nz a\n",
        "1\n4\nabba\n2\na c\nb d\n",
        "1\n5\nabcde\n0\n",
        "1\n3\naaa\n1\na b\n",
        "1\n4\ntest\n2\nt T\ns S\n",
        "1\n6\nbanana\n1\na A\n",
    ]


# ─── 1618A Ordinary Numbers ─────────────────────────────────────────────────

def _s_1618a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        l, r = map(int, line.split())
        out.append(str(_ordinary_count(l, r)))
    return "\n".join(out) + "\n"


def _a_1618a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        l, r = map(int, line.split())
        cnt = 0
        for d in range(1, 10):
            x = d
            while x <= r:
                if x >= l:
                    cnt += 1
                x = x * 10 + d
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1618a(stdin: str) -> str:
    return "\n".join(line.split()[1] for line in lines(stdin)[1:]) + "\n"


def _m2_1618a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _gen_1618a(rng: random.Random) -> list[str]:
    return [
        "3\n1 9\n95 115\n998 24435\n",
        "1\n1 10\n",
        "1\n11 99\n",
        "1\n5 55\n",
        "1\n100 200\n",
        "1\n7 77\n",
        "1\n1 1000\n",
        "1\n22 222\n",
        "1\n3 33\n",
        "1\n111 1111\n",
        "1\n2 20\n",
        "1\n50 500\n",
    ]


# ─── 1553A Soft Drinking ────────────────────────────────────────────────────

def _soft_drink(n: int, s: int, k: int) -> int:
    bottles = n // s
    if bottles < k:
        return 0
    return bottles - (bottles - k) // (k - 1)


def _s_1553a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, s, k = map(int, line.split())
        out.append(str(_soft_drink(n, s, k)))
    return "\n".join(out) + "\n"


def _a_1553a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, s, k = map(int, line.split())
        ans = n // s
        if ans < k:
            out.append("0")
        else:
            out.append(str(ans - (ans - k) // (k - 1)))
    return "\n".join(out) + "\n"


def _m1_1553a(stdin: str) -> str:
    return "\n".join(str(int(line.split()[0]) // int(line.split()[1])) for line in lines(stdin)[1:]) + "\n"


def _m2_1553a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _gen_1553a(rng: random.Random) -> list[str]:
    return [
        "2\n10 2 3\n20 3 4\n",
        "1\n5 2 3\n",
        "1\n10 2 3\n",
        "1\n7 3 2\n",
        "1\n100 5 10\n",
        "1\n1 1 2\n",
        "1\n20 4 5\n",
        "1\n15 3 4\n",
        "1\n9 3 3\n",
        "1\n30 6 7\n",
        "1\n8 2 2\n",
        "1\n50 10 11\n",
    ]


# ─── 1339A Filling Diamonds ─────────────────────────────────────────────────

def _s_1339a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        x, y = map(int, line.split())
        out.append(str(min(x, y)))
    return "\n".join(out) + "\n"


def _a_1339a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        x, y = map(int, line.split())
        out.append(str(x if x < y else y))
    return "\n".join(out) + "\n"


def _m1_1339a(stdin: str) -> str:
    return "\n".join(line.split()[0] for line in lines(stdin)[1:]) + "\n"


def _m2_1339a(stdin: str) -> str:
    return "\n".join(line.split()[1] for line in lines(stdin)[1:]) + "\n"


def _gen_1339a(rng: random.Random) -> list[str]:
    return [
        "2\n1 5\n3 3\n",
        "1\n4 7\n",
        "1\n10 2\n",
        "1\n6 6\n",
        "1\n1 1\n",
        "1\n8 3\n",
        "1\n2 9\n",
        "1\n5 5\n",
        "1\n7 1\n",
        "1\n3 8\n",
        "1\n9 4\n",
        "1\n2 2\n",
    ]


# ─── 1932A Thorns and Coins ─────────────────────────────────────────────────

def _s_1932a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        coins = 0
        i = 0
        while i < n:
            if s[i] == '#':
                i += 1
                continue
            coins += 1
            i += 1
            if i < n and s[i] == '.':
                i += 1
        out.append(str(coins))
    return "\n".join(out) + "\n"


def _a_1932a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        ans = 0
        i = 0
        while i < n:
            if s[i] == '.':
                ans += 1
                i += 2
            else:
                i += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1932a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(str(s.count('.')))
    return "\n".join(out) + "\n"


def _m2_1932a(stdin: str) -> str:
    return _m1_1932a(stdin)


def _gen_1932a(rng: random.Random) -> list[str]:
    return [
        "1\n7\n.#..#..\n",
        "1\n5\n.....\n",
        "1\n3\n###\n",
        "1\n4\n.#.#\n",
        "1\n6\n..#...\n",
        "1\n2\n..\n",
        "1\n5\n#.#.#\n",
        "1\n8\n...#....\n",
        "1\n1\n.\n",
        "1\n4\n##..\n",
        "1\n7\n.#.#.#.\n",
        "1\n6\n......\n",
    ]


# ─── 1714B Remove Prefix ────────────────────────────────────────────────────

def _s_1714b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        s = set()
        k = n
        for i in range(n - 1, -1, -1):
            if a[i] in s:
                break
            s.add(a[i])
            k = i
        out.append(str(sum(a[k:])))
    return "\n".join(out) + "\n"


def _a_1714b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        seen = set()
        start = n
        for i in range(n - 1, -1, -1):
            if a[i] in seen:
                break
            seen.add(a[i])
            start = i
        out.append(str(sum(a[start:])))
    return "\n".join(out) + "\n"


def _m1_1714b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def _m2_1714b(stdin: str) -> str:
    return _m1_1714b(stdin)


def _gen_1714b(rng: random.Random) -> list[str]:
    return [
        "1\n5\n1 2 3 4 5\n",
        "1\n4\n1 1 2 3\n",
        "1\n3\n2 2 2\n",
        "1\n6\n1 2 1 3 2 4\n",
        "1\n2\n5 5\n",
        "1\n5\n3 3 3 3 3\n",
        "1\n4\n1 2 2 1\n",
        "1\n7\n1 2 3 4 3 2 1\n",
        "1\n3\n1 1 1\n",
        "1\n5\n5 4 3 2 1\n",
        "1\n4\n2 3 4 5\n",
        "1\n6\n1 1 2 2 3 3\n",
    ]


# ─── 1741A Compare T-Shirt Sizes ────────────────────────────────────────────

def _s_1741a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        a, b = line.split()
        ra, rb = _shirt_rank(a), _shirt_rank(b)
        out.append("YES" if ra == rb else "NO")
    return "\n".join(out) + "\n"


def _a_1741a(stdin: str) -> str:
    order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    out = []
    for line in lines(stdin)[1:]:
        a, b = line.split()
        out.append("YES" if order.index(a) == order.index(b) else "NO")
    return "\n".join(out) + "\n"


def _m1_1741a(stdin: str) -> str:
    return "\n".join("YES" for _ in lines(stdin)[1:]) + "\n"


def _m2_1741a(stdin: str) -> str:
    return "\n".join("NO" for _ in lines(stdin)[1:]) + "\n"


def _gen_1741a(rng: random.Random) -> list[str]:
    return [
        "3\nXS S\nM M\nL XL\n",
        "1\nS S\n",
        "1\nXS XL\n",
        "1\nM L\n",
        "1\nXXXS XXXS\n",
        "1\nXXL XXL\n",
        "1\nL M\n",
        "1\nXS XS\n",
        "1\nXL XXL\n",
        "1\nS M\n",
        "1\nM M\n",
        "1\nXXXL XS\n",
    ]


# ─── 1698A XOR Mixup ────────────────────────────────────────────────────────

def _s_1698a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        x = 0
        for v in a:
            x ^= v
        out.append(str(x))
    return "\n".join(out) + "\n"


def _a_1698a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        x = 0
        for v in a:
            x ^= v
        out.append(str(x))
    return "\n".join(out) + "\n"


def _m1_1698a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _m2_1698a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(a[0]))
    return "\n".join(out) + "\n"


def _gen_1698a(rng: random.Random) -> list[str]:
    return [
        "1\n4\n1 2 3 0\n",
        "1\n3\n5 5 5\n",
        "1\n2\n3 3\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n1\n7\n",
        "1\n4\n0 0 0 0\n",
        "1\n3\n1 1 0\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n2\n10 10\n",
        "1\n3\n2 4 6\n",
        "1\n4\n8 8 8 8\n",
        "1\n2\n1 0\n",
    ]


# ─── 1851B Parity Sort ──────────────────────────────────────────────────────

def _parity_sort_ok(a: list[int]) -> bool:
    evens = sorted(x for x in a if x % 2 == 0)
    odds = sorted(x for x in a if x % 2 == 1)
    ei = oi = 0
    res = []
    for x in a:
        if x % 2 == 0:
            res.append(evens[ei]); ei += 1
        else:
            res.append(odds[oi]); oi += 1
    return res == sorted(a)


def _s_1851b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_parity_sort_ok(a)).strip())
    return "\n".join(out) + "\n"


def _a_1851b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        ev = sorted([x for x in a if x % 2 == 0])
        od = sorted([x for x in a if x % 2 == 1])
        ei = oi = 0
        built = []
        for x in a:
            if x % 2 == 0:
                built.append(ev[ei]); ei += 1
            else:
                built.append(od[oi]); oi += 1
        out.append(yes_no(built == sorted(a)).strip())
    return "\n".join(out) + "\n"


def _m1_1851b(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_1851b(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_1851b(rng: random.Random) -> list[str]:
    return [
        "1\n4\n2 1 4 3\n",
        "1\n3\n1 2 3\n",
        "1\n2\n2 1\n",
        "1\n5\n5 4 3 2 1\n",
        "1\n4\n1 3 2 4\n",
        "1\n3\n2 2 2\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n4\n4 3 2 1\n",
        "1\n5\n2 4 1 5 3\n",
        "1\n3\n3 1 2\n",
        "1\n4\n8 6 7 5\n",
        "1\n2\n1 2\n",
    ]



# ─── 2004A Closest Point ────────────────────────────────────────────────────

def _s_2004a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        x = list(map(int, ls[idx].split())); idx += 1
        ok = True
        for i in range(n):
            for j in range(i + 1, n):
                if abs(x[i] - x[j]) == 1:
                    ok = False
        out.append(yes_no(ok).strip())
    return "\n".join(out) + "\n"


def _a_2004a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        x = sorted(map(int, ls[idx].split())); idx += 1
        bad = any(x[i + 1] - x[i] == 1 for i in range(n - 1))
        out.append(yes_no(not bad).strip())
    return "\n".join(out) + "\n"


def _m1_2004a(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_2004a(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_2004a(rng: random.Random) -> list[str]:
    return [
        "2\n2\n1 3\n3\n1 2 3\n",
        "1\n2\n5 7\n",
        "1\n3\n1 3 5\n",
        "1\n2\n2 4\n",
        "1\n4\n1 4 7 10\n",
        "1\n2\n1 2\n",
        "1\n3\n2 4 6\n",
        "1\n2\n10 12\n",
        "1\n5\n1 3 5 7 9\n",
        "1\n2\n0 2\n",
        "1\n3\n1 2 4\n",
        "1\n2\n8 10\n",
    ]


# ─── 1714A Everyone Loves to Sleep ─────────────────────────────────────────

def _s_1714a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, h, m = map(int, line.split())
        cur = h * 60 + m
        wake = 24 * 60
        out.append(str((wake - cur) % (24 * 60)))
    return "\n".join(out) + "\n"


def _a_1714a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, h, m = map(int, line.split())
        mins = h * 60 + m
        out.append(str((24 * 60 - mins) % (24 * 60)))
    return "\n".join(out) + "\n"


def _m1_1714a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _m2_1714a(stdin: str) -> str:
    return "\n".join("1440" for _ in lines(stdin)[1:]) + "\n"


def _gen_1714a(rng: random.Random) -> list[str]:
    return [
        "1\n1 10 30\n",
        "1\n1 0 0\n",
        "1\n1 23 59\n",
        "1\n1 12 0\n",
        "1\n1 6 15\n",
        "1\n1 8 45\n",
        "1\n1 20 10\n",
        "1\n1 1 1\n",
        "1\n1 22 0\n",
        "1\n1 5 5\n",
        "1\n1 18 30\n",
        "1\n1 7 20\n",
    ]


# ─── 1619B Squares and Cubes ────────────────────────────────────────────────

def _is_square_cube(x: int) -> bool:
    r = int(x ** 0.5)
    if r * r == x:
        return True
    c = round(x ** (1 / 3))
    return c ** 3 == x


def _s_1619b(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n = int(line)
        out.append(str(sum(1 for i in range(1, n + 1) if _is_square_cube(i))))
    return "\n".join(out) + "\n"


def _a_1619b(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n = int(line)
        cnt = 0
        for i in range(1, n + 1):
            s = int(i ** 0.5)
            if s * s == i:
                cnt += 1
                continue
            c = round(i ** (1 / 3))
            if c ** 3 == i:
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _m1_1619b(stdin: str) -> str:
    return "\n".join(line for line in lines(stdin)[1:]) + "\n"


def _m2_1619b(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _gen_1619b(rng: random.Random) -> list[str]:
    return [
        "3\n1\n4\n26\n",
        "1\n10\n",
        "1\n100\n",
        "1\n27\n",
        "1\n64\n",
        "1\n50\n",
        "1\n8\n",
        "1\n16\n",
        "1\n81\n",
        "1\n20\n",
        "1\n36\n",
        "1\n125\n",
    ]


# ─── 1759A Yes-Yes? ─────────────────────────────────────────────────────────

def _s_1759a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        s = line.strip()
        out.append(yes_no(s == "Yes" * (len(s) // 3)).strip())
    return "\n".join(out) + "\n"


def _a_1759a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        s = line.strip()
        ok = len(s) % 3 == 0 and all(s[i:i+3] == "Yes" for i in range(0, len(s), 3))
        out.append(yes_no(ok).strip())
    return "\n".join(out) + "\n"


def _m1_1759a(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_1759a(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_1759a(rng: random.Random) -> list[str]:
    return [
        "3\nYesYesYes\nYesYes\nYes\n",
        "1\nYes\n",
        "1\nYesYes\n",
        "1\nNo\n",
        "1\nYesYesYesYesYesYes\n",
        "1\nYesYesNo\n",
        "1\nYesYesYesYes\n",
        "1\nYesYesYes\n",
        "1\nYesYesYesYesYesYesYesYesYes\n",
        "1\nYesYesYesYesYes\n",
        "1\nYesYesYesYesYesYesYes\n",
        "1\nYesYesYesYesYesYesYesYes\n",
    ]


# ─── 219A k-String ──────────────────────────────────────────────────────────

def _s_219a(stdin: str) -> str:
    ls = lines(stdin)
    k = int(ls[0])
    s = ls[1]
    if len(s) % k:
        return "NO\n"
    t = len(s) // k
    base = s[:t]
    ok = base * k == s
    return yes_no(ok).strip() + "\n"


def _a_219a(stdin: str) -> str:
    ls = lines(stdin)
    k = int(ls[0])
    s = ls[1]
    if len(s) % k != 0:
        return "NO\n"
    chunk = s[: len(s) // k]
    return yes_no(s == chunk * k).strip() + "\n"


def _m1_219a(stdin: str) -> str:
    return "YES\n"


def _m2_219a(stdin: str) -> str:
    return "NO\n"


def _gen_219a(rng: random.Random) -> list[str]:
    return [
        "2\nababa\n",
        "2\nabab\n",
        "3\naaa\n",
        "2\naa\n",
        "4\nabcd\n",
        "2\nabcabc\n",
        "3\nxyzxyzxyz\n",
        "2\nab\n",
        "1\na\n",
        "2\naabb\n",
        "3\nab\n",
        "2\nxyxy\n",
    ]


# ─── 1220A Cards ────────────────────────────────────────────────────────────

def _s_1220a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    lo, hi = min(a), max(a)
    if hi - lo + 1 != n:
        return "NO\n"
    cnt = Counter(a)
    return yes_no(all(v == 1 for v in cnt.values())).strip() + "\n"


def _a_1220a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = sorted(map(int, ls[1].split()))
    if a[-1] - a[0] + 1 != n:
        return "NO\n"
    return yes_no(len(set(a)) == n).strip() + "\n"


def _m1_1220a(stdin: str) -> str:
    return "YES\n"


def _m2_1220a(stdin: str) -> str:
    return "NO\n"


def _gen_1220a(rng: random.Random) -> list[str]:
    return [
        "3\n1 2 3\n",
        "3\n1 1 2\n",
        "4\n1 2 3 4\n",
        "2\n5 6\n",
        "5\n10 11 12 13 14\n",
        "3\n2 3 4\n",
        "4\n1 2 2 3\n",
        "2\n1 2\n",
        "6\n1 2 3 4 5 6\n",
        "3\n3 4 5\n",
        "4\n2 3 4 5\n",
        "3\n1 3 3\n",
    ]


# ─── 2001A Make All Equal ───────────────────────────────────────────────────

def _s_2001a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(len(set(a)) == 1).strip())
    return "\n".join(out) + "\n"


def _a_2001a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(a.count(a[0]) == n).strip())
    return "\n".join(out) + "\n"


def _m1_2001a(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_2001a(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_2001a(rng: random.Random) -> list[str]:
    return [
        "2\n3\n1 1 1\n3\n1 2 1\n",
        "1\n2\n5 5\n",
        "1\n4\n2 2 2 2\n",
        "1\n3\n1 2 3\n",
        "1\n1\n7\n",
        "1\n5\n3 3 3 3 3\n",
        "1\n2\n1 2\n",
        "1\n6\n4 4 4 4 4 4\n",
        "1\n3\n2 2 1\n",
        "1\n4\n1 1 1 2\n",
        "1\n2\n9 9\n",
        "1\n5\n1 1 1 1 1\n",
    ]


# ─── 1372A Omkar and Completion ───────────────────────────────────────────────

def _s_1372a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        s = sum(a)
        out.append(str(s - a[0]))
    return "\n".join(out) + "\n"


def _a_1372a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(sum(a[1:])))
    return "\n".join(out) + "\n"


def _m1_1372a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _m2_1372a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(a[0]))
    return "\n".join(out) + "\n"


def _gen_1372a(rng: random.Random) -> list[str]:
    return [
        "1\n3\n1 2 3\n",
        "1\n2\n5 5\n",
        "1\n4\n1 1 1 1\n",
        "1\n3\n2 4 6\n",
        "1\n2\n3 7\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n3\n10 10 10\n",
        "1\n2\n1 9\n",
        "1\n4\n2 2 2 2\n",
        "1\n3\n0 0 0\n",
        "1\n2\n4 4\n",
        "1\n3\n7 8 9\n",
    ]


# ─── 1611A Make Even ──────────────────────────────────────────────────────────

def _make_even(s: str) -> str:
    if int(s[-1]) % 2 == 0:
        return s
    digits = list(s)
    for i in range(len(digits) - 1):
        if int(digits[i]) % 2 == 0:
            digits[i], digits[-1] = digits[-1], digits[i]
            return "".join(digits)
    return "-1"


def _s_1611a(stdin: str) -> str:
    out = [ _make_even(line.strip()) for line in lines(stdin)[1:] ]
    return "\n".join(out) + "\n"


def _a_1611a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        s = line.strip()
        if int(s[-1]) % 2 == 0:
            out.append(s)
            continue
        arr = list(s)
        swapped = False
        for i in range(len(arr) - 1):
            if int(arr[i]) % 2 == 0:
                arr[i], arr[-1] = arr[-1], arr[i]
                swapped = True
                break
        out.append("".join(arr) if swapped else "-1")
    return "\n".join(out) + "\n"


def _m1_1611a(stdin: str) -> str:
    return "\n".join(line.strip() for line in lines(stdin)[1:]) + "\n"


def _m2_1611a(stdin: str) -> str:
    return "\n".join("-1" for _ in lines(stdin)[1:]) + "\n"


def _gen_1611a(rng: random.Random) -> list[str]:
    return [
        "2\n385\n249\n",
        "1\n13\n",
        "1\n24\n",
        "1\n11\n",
        "1\n20\n",
        "1\n135\n",
        "1\n42\n",
        "1\n99\n",
        "1\n31\n",
        "1\n22\n",
        "1\n101\n",
        "1\n15\n",
    ]


# ─── 1366A Shovels and Swords ───────────────────────────────────────────────

def _s_1366a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        a, b = map(int, line.split())
        lo, hi = 0, 10**9
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if mid <= a and 2 * mid <= b:
                lo = mid
            else:
                hi = mid - 1
        out.append(str(lo))
    return "\n".join(out) + "\n"


def _a_1366a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        a, b = map(int, line.split())
        out.append(str(min(a, b // 2)))
    return "\n".join(out) + "\n"


def _m1_1366a(stdin: str) -> str:
    return "\n".join(line.split()[0] for line in lines(stdin)[1:]) + "\n"


def _m2_1366a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _gen_1366a(rng: random.Random) -> list[str]:
    return [
        "1\n1 1\n",
        "1\n4 5\n",
        "1\n10 11\n",
        "1\n3 4\n",
        "1\n100 200\n",
        "1\n5 10\n",
        "1\n7 7\n",
        "1\n2 5\n",
        "1\n8 3\n",
        "1\n6 12\n",
        "1\n9 18\n",
        "1\n15 20\n",
    ]


# ─── 1296B Food Buying ──────────────────────────────────────────────────────

def _food_buy(n: int, s: int) -> int:
    burles = n
    coins = burles // s
    burles += coins
    return burles


def _s_1296b(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, s = map(int, line.split())
        out.append(str(_food_buy(n, s)))
    return "\n".join(out) + "\n"


def _a_1296b(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, s = map(int, line.split())
        ans = n
        ans += ans // s
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m1_1296b(stdin: str) -> str:
    return "\n".join(line.split()[0] for line in lines(stdin)[1:]) + "\n"


def _m2_1296b(stdin: str) -> str:
    return _m1_1296b(stdin)


def _gen_1296b(rng: random.Random) -> list[str]:
    return [
        "1\n1 3\n",
        "1\n5 2\n",
        "1\n10 3\n",
        "1\n7 7\n",
        "1\n100 10\n",
        "1\n4 5\n",
        "1\n9 3\n",
        "1\n20 6\n",
        "1\n3 4\n",
        "1\n15 5\n",
        "1\n8 8\n",
        "1\n6 2\n",
    ]



# ─── 1538B Friends and Candies ──────────────────────────────────────────────

def _s_1538b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    s = sum(a)
    if s % n:
        return "NO\n"
    return yes_no(True).strip() + "\n"


def _a_1538b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    return yes_no(sum(a) % n == 0).strip() + "\n"


def _m1_1538b(stdin: str) -> str:
    return "YES\n"


def _m2_1538b(stdin: str) -> str:
    return "NO\n"


def _gen_1538b(rng: random.Random) -> list[str]:
    return [
        "3\n1 2 3\n",
        "2\n5 5\n",
        "4\n1 1 1 1\n",
        "3\n2 2 2\n",
        "5\n1 2 3 4 5\n",
        "2\n3 4\n",
        "4\n2 4 6 8\n",
        "3\n4 4 4\n",
        "6\n1 1 2 2 3 3\n",
        "2\n1 3\n",
        "3\n5 5 5\n",
        "4\n3 3 3 3\n",
    ]


# ─── 1714C Minimum Varied Number ────────────────────────────────────────────

def _min_varied(n: int) -> str:
    if n <= 10:
        return str(n)
    digits = []
    while n:
        digits.append(n % 10)
        n //= 10
    digits = digits[::-1]
    for i in range(1, len(digits)):
        if digits[i] <= digits[i - 1]:
            digits[i - 1] += 1
            for j in range(i, len(digits)):
                digits[j] = 0
            break
    else:
        digits = [1] + [0] * len(digits)
    val = int("".join(map(str, digits)))
    if val < int("".join(map(str, digits))):
        pass
    s = "".join(map(str, digits)).lstrip("0") or "0"
    return s


def _s_1714c(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n = int(line)
        if n <= 9:
            out.append(str(n))
            continue
        s = str(n)
        arr = list(map(int, s))
        for i in range(1, len(arr)):
            if arr[i] <= arr[i - 1]:
                arr[i - 1] += 1
                for j in range(i, len(arr)):
                    arr[j] = 0
                break
        else:
            arr = [1] + [0] * len(arr)
        out.append(str(int("".join(map(str, arr)))))
    return "\n".join(out) + "\n"


def _a_1714c(stdin: str) -> str:
    return _s_1714c(stdin)


def _m1_1714c(stdin: str) -> str:
    return "\n".join(line for line in lines(stdin)[1:]) + "\n"


def _m2_1714c(stdin: str) -> str:
    return "\n".join(str(int(line) + 1) for line in lines(stdin)[1:]) + "\n"


def _gen_1714c(rng: random.Random) -> list[str]:
    return [
        "3\n1\n11\n21\n",
        "1\n9\n",
        "1\n19\n",
        "1\n99\n",
        "1\n100\n",
        "1\n123\n",
        "1\n200\n",
        "1\n555\n",
        "1\n432\n",
        "1\n1000\n",
        "1\n87\n",
        "1\n300\n",
    ]


# ─── 1997A Strong Password ──────────────────────────────────────────────────

def _has_pal_sub(s: str) -> bool:
    return any(s[i] == s[i + 1] for i in range(len(s) - 1))


def _s_1997a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        s = ls[idx]; idx += 1
        if _has_pal_sub(s):
            out.append(s)
            continue
        placed = False
        for ch in "abcdefghijklmnopqrstuvwxyz":
            if not _has_pal_sub(s + ch):
                out.append(s + ch)
                placed = True
                break
        if not placed:
            out.append(s + "a")
    return "\n".join(out) + "\n"


def _a_1997a(stdin: str) -> str:
    return _s_1997a(stdin)


def _m1_1997a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        s = ls[idx]; idx += 1
        out.append(s + "a")
    return "\n".join(out) + "\n"


def _m2_1997a(stdin: str) -> str:
    return _m1_1997a(stdin)


def _gen_1997a(rng: random.Random) -> list[str]:
    return [
        "1\naba\n",
        "1\nabc\n",
        "1\nzz\n",
        "1\nab\n",
        "1\nxyz\n",
        "1\naa\n",
        "1\nabcd\n",
        "1\nabca\n",
        "1\nmnop\n",
        "1\nxy\n",
        "1\nhello\n",
        "1\nqwerty\n",
    ]


# ─── 1519B Cake Is a Lie ────────────────────────────────────────────────────

def _subset_sum_zero(a: list[int]) -> bool:
    s = sum(a)
    if s % 2:
        return False
    target = s // 2
    dp = {0}
    for x in a:
        dp = dp | {v + x for v in dp}
        if target in dp:
            return True
    return target in dp


def _s_1519b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_subset_sum_zero(a)).strip())
    return "\n".join(out) + "\n"


def _a_1519b(stdin: str) -> str:
    return _s_1519b(stdin)


def _m1_1519b(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_1519b(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_1519b(rng: random.Random) -> list[str]:
    return [
        "1\n4\n1 2 3 4\n",
        "1\n3\n1 2 3\n",
        "1\n2\n1 1\n",
        "1\n5\n1 1 1 1 4\n",
        "1\n4\n2 2 2 2\n",
        "1\n3\n5 5 5\n",
        "1\n6\n1 2 3 4 5 5\n",
        "1\n2\n3 4\n",
        "1\n4\n1 1 2 2\n",
        "1\n5\n2 4 6 8 10\n",
        "1\n3\n2 3 5\n",
        "1\n4\n7 1 3 3\n",
    ]


# ─── 1772B Matrix Rotation ──────────────────────────────────────────────────

def _beauty(mat: list[list[int]]) -> int:
    n = len(mat)
    best = 0
    for i in range(n):
        for j in range(n):
            s = 0
            for di in range(n):
                for dj in range(n):
                    if (di + dj) % 2 == (i + j) % 2:
                        s += mat[di][dj]
            best = max(best, s)
    return best


def _s_1772b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        mat = [list(map(int, ls[idx + i].split())) for i in range(n)]
        idx += n
        total = sum(sum(row) for row in mat)
        out.append(yes_no(2 * _beauty(mat) == total).strip())
    return "\n".join(out) + "\n"


def _a_1772b(stdin: str) -> str:
    return _s_1772b(stdin)


def _m1_1772b(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_1772b(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_1772b(rng: random.Random) -> list[str]:
    return [
        "1\n2\n1 2\n3 4\n",
        "1\n2\n1 1\n1 1\n",
        "1\n3\n1 2 3\n4 5 6\n7 8 9\n",
        "1\n2\n2 1\n1 2\n",
        "1\n2\n0 0\n0 0\n",
        "1\n3\n1 1 1\n1 1 1\n1 1 1\n",
        "1\n2\n5 1\n1 5\n",
        "1\n2\n3 3\n3 3\n",
        "1\n3\n2 2 2\n2 2 2\n2 2 2\n",
        "1\n2\n4 2\n2 4\n",
        "1\n2\n1 3\n3 1\n",
        "1\n2\n6 0\n0 6\n",
    ]


# ─── 1328C Ternary XOR ──────────────────────────────────────────────────────

def _ternary_xor(a: str, b: str) -> str:
    out = []
    for x, y in zip(a, b):
        xi, yi = int(x), int(y)
        out.append(str((1 - xi - yi + 3) % 3))
    return "".join(out)


def _s_1328c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = ls[idx]; idx += 1
        b = ls[idx]; idx += 1
        out.append(_ternary_xor(a, b))
    return "\n".join(out) + "\n"


def _a_1328c(stdin: str) -> str:
    return _s_1328c(stdin)


def _m1_1328c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = ls[idx]; idx += 1
        b = ls[idx]; idx += 1
        out.append(a)
    return "\n".join(out) + "\n"


def _m2_1328c(stdin: str) -> str:
    return _m1_1328c(stdin)


def _gen_1328c(rng: random.Random) -> list[str]:
    return [
        "1\n3\n222\n022\n",
        "1\n2\n12\n21\n",
        "1\n4\n0120\n2101\n",
        "1\n1\n1\n2\n",
        "1\n3\n000\n111\n",
        "1\n2\n01\n10\n",
        "1\n5\n01201\n12010\n",
        "1\n2\n22\n00\n",
        "1\n3\n121\n212\n",
        "1\n4\n1111\n2222\n",
        "1\n2\n02\n20\n",
        "1\n3\n210\n012\n",
    ]


# ─── 1993A Question Marks ───────────────────────────────────────────────────

def _s_1993a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        cnt = Counter(s)
        ans = 0
        for ch in "ABCD":
            ans += min(cnt.get(ch, 0), n)
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1993a(stdin: str) -> str:
    return _s_1993a(stdin)


def _m1_1993a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(str(len(s)))
    return "\n".join(out) + "\n"


def _m2_1993a(stdin: str) -> str:
    return _m1_1993a(stdin)


def _gen_1993a(rng: random.Random) -> list[str]:
    return [
        "1\n2\nABCD\n",
        "1\n1\nA?B?\n",
        "1\n3\nAAAA\n",
        "1\n2\nABAB\n",
        "1\n1\n????\n",
        "1\n2\nAABB\n",
        "1\n3\nABCABC\n",
        "1\n1\nA\n",
        "1\n2\nCDCD\n",
        "1\n4\nABCDABCD\n",
        "1\n2\n??AB\n",
        "1\n3\nDDD???\n",
    ]


# ─── 1490A Dense Array ──────────────────────────────────────────────────────

def _dense_ops(a: list[int]) -> int:
    a = sorted(a)
    ops = 0
    for i in range(1, len(a)):
        while a[i] - a[i - 1] > 1:
            a[i] -= 1
            ops += 1
    return ops


def _s_1490a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(_dense_ops(a)))
    return "\n".join(out) + "\n"


def _a_1490a(stdin: str) -> str:
    return _s_1490a(stdin)


def _m1_1490a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _m2_1490a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _gen_1490a(rng: random.Random) -> list[str]:
    return [
        "1\n3\n1 2 3\n",
        "1\n4\n1 1 1 1\n",
        "1\n3\n5 1 3\n",
        "1\n2\n1 10\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n3\n2 2 2\n",
        "1\n4\n1 3 5 7\n",
        "1\n2\n1 1\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n3\n10 8 6\n",
        "1\n4\n2 4 6 8\n",
        "1\n3\n1 5 9\n",
    ]


# ─── 2055A Two Frogs ──────────────────────────────────────────────────────────

def _two_frogs(n: int, a: int, b: int) -> str:
    if (b - a) % 2 == 0:
        return "No\n"
    return "Yes\n"


def _s_2055a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, a, b = map(int, line.split())
        out.append(_two_frogs(n, a, b).strip())
    return "\n".join(out) + "\n"


def _a_2055a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, a, b = map(int, line.split())
        out.append("Yes" if (b - a) % 2 else "No")
    return "\n".join(out) + "\n"


def _m1_2055a(stdin: str) -> str:
    return "Yes\n"


def _m2_2055a(stdin: str) -> str:
    return "No\n"


def _gen_2055a(rng: random.Random) -> list[str]:
    return [
        "1\n6 2 3\n",
        "1\n5 1 5\n",
        "1\n4 1 2\n",
        "1\n10 3 7\n",
        "1\n3 1 3\n",
        "1\n8 2 6\n",
        "1\n7 1 4\n",
        "1\n6 1 6\n",
        "1\n9 2 5\n",
        "1\n5 2 4\n",
        "1\n4 2 4\n",
        "1\n10 1 10\n",
    ]


# ─── 2086A Cloudberry Jam ───────────────────────────────────────────────────

def _s_2086a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, m = map(int, line.split())
        out.append(str(n * m // 2))
    return "\n".join(out) + "\n"


def _a_2086a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, m = map(int, line.split())
        out.append(str((n * m) // 2))
    return "\n".join(out) + "\n"


def _m1_2086a(stdin: str) -> str:
    return "\n".join(line.split()[0] for line in lines(stdin)[1:]) + "\n"


def _m2_2086a(stdin: str) -> str:
    return "\n".join(str(int(line.split()[0]) * int(line.split()[1])) for line in lines(stdin)[1:]) + "\n"


def _gen_2086a(rng: random.Random) -> list[str]:
    return [
        "1\n2 3\n",
        "1\n4 5\n",
        "1\n1 1\n",
        "1\n10 10\n",
        "1\n3 7\n",
        "1\n6 6\n",
        "1\n5 5\n",
        "1\n8 2\n",
        "1\n9 1\n",
        "1\n7 3\n",
        "1\n2 8\n",
        "1\n11 11\n",
    ]



# ─── 1535B Array Reordering ──────────────────────────────────────────────────

def _can_reorder(a: list[int]) -> bool:
    return sorted(a) == a or sorted(a, reverse=True) == a or len(a) <= 2


def _s_1535b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(sorted(a) == a or sorted(a, reverse=True) == a).strip())
    return "\n".join(out) + "\n"


def _a_1535b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        asc = all(a[i] <= a[i + 1] for i in range(n - 1))
        desc = all(a[i] >= a[i + 1] for i in range(n - 1))
        out.append(yes_no(asc or desc).strip())
    return "\n".join(out) + "\n"


def _m1_1535b(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_1535b(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_1535b(rng: random.Random) -> list[str]:
    return [
        "1\n3\n1 2 3\n",
        "1\n3\n3 2 1\n",
        "1\n3\n1 3 2\n",
        "1\n2\n1 2\n",
        "1\n4\n1 1 1 1\n",
        "1\n5\n5 4 3 2 1\n",
        "1\n3\n2 2 2\n",
        "1\n4\n1 2 2 3\n",
        "1\n2\n2 1\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n3\n2 1 3\n",
        "1\n4\n4 3 2 1\n",
    ]


# ─── 349A Cinema Line ─────────────────────────────────────────────────────────

def _cinema_fit(n: int, a: list[int]) -> str:
    one = a.count(1)
    two = a.count(2)
    if one < n:
        return "NO\n"
    one -= n
    return yes_no(one >= two * 2)


def _s_349a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    one = a.count(1)
    two = a.count(2)
    if one < n:
        return "NO\n"
    one -= n
    return yes_no(one >= 2 * two).strip() + "\n"


def _a_349a(stdin: str) -> str:
    return _s_349a(stdin)


def _m1_349a(stdin: str) -> str:
    return "YES\n"


def _m2_349a(stdin: str) -> str:
    return "NO\n"


def _gen_349a(rng: random.Random) -> list[str]:
    return [
        "3\n1 1 1\n",
        "2\n1 2\n",
        "2\n2 2\n",
        "4\n1 1 2 2\n",
        "1\n1\n",
        "3\n1 2 2\n",
        "5\n1 1 1 2 2\n",
        "2\n1 1\n",
        "4\n1 1 1 1\n",
        "3\n2 2 2\n",
        "4\n1 1 2 1\n",
        "6\n1 1 1 1 2 2\n",
    ]


# ─── 1618C Paint the Array ───────────────────────────────────────────────────

def _paint_array(a: list[int]) -> bool:
    n = len(a)
    if n < 4:
        return True
    s = sorted(a)
    return s[0] == s[n - 2] or s[1] == s[n - 1]


def _s_1618c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(yes_no(_paint_array(a)).strip())
    return "\n".join(out) + "\n"


def _a_1618c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        a = sorted(map(int, ls[idx].split())); idx += 1
        if n < 4:
            out.append("YES")
        else:
            out.append("YES" if a[0] == a[n - 2] or a[1] == a[n - 1] else "NO")
    return "\n".join(out) + "\n"


def _m1_1618c(stdin: str) -> str:
    return yes_no(True).strip() + "\n"


def _m2_1618c(stdin: str) -> str:
    return yes_no(False).strip() + "\n"


def _gen_1618c(rng: random.Random) -> list[str]:
    return [
        "1\n4\n1 2 3 1\n",
        "1\n2\n5 5\n",
        "1\n3\n1 2 3\n",
        "1\n4\n2 2 2 2\n",
        "1\n5\n1 1 2 2 4\n",
        "1\n3\n4 5 1\n",
        "1\n2\n1 2\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n4\n1 1 1 1\n",
        "1\n3\n2 3 1\n",
        "1\n5\n3 1 4 1 5\n",
        "1\n2\n3 4\n",
    ]


# ─── 1829C Mr Perfectly Fine ─────────────────────────────────────────────────

def _fine_cost(s: str) -> int:
    masks = []
    for ch in s:
        m = 0
        if "0" in ch or ch == "M":
            m |= 1
        if "1" in ch or ch == "C":
            m |= 2
        masks.append(m)
    INF = 10**9
    dp = [INF, INF, INF, INF]
    dp[0] = 0
    for m in masks:
        nd = dp[:]
        for cur in range(4):
            if dp[cur] == INF:
                continue
            nd[cur | m] = min(nd[cur | m], dp[cur])
            nd[cur] = min(nd[cur], dp[cur] + 1)
        dp = nd
    return dp[3] if dp[3] < INF else -1


def _s_1829c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx]); idx += 1
        s = ls[idx]; idx += 1
        out.append(str(_fine_cost(s)))
    return "\n".join(out) + "\n"


def _a_1829c(stdin: str) -> str:
    return _s_1829c(stdin)


def _m1_1829c(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _m2_1829c(stdin: str) -> str:
    return _m1_1829c(stdin)


def _gen_1829c(rng: random.Random) -> list[str]:
    return [
        "1\n3\n101\n",
        "1\n2\n11\n",
        "1\n4\n0011\n",
        "1\n1\n0\n",
        "1\n1\n1\n",
        "1\n5\n01010\n",
        "1\n3\n110\n",
        "1\n2\n00\n",
        "1\n4\n1111\n",
        "1\n3\n011\n",
        "1\n6\n101010\n",
        "1\n2\n01\n",
    ]


# ─── 598A Tricky Sum ──────────────────────────────────────────────────────────

def _tricky_sum(n: int) -> int:
    return n * (n + 1) // 2 - 2 * (n // 2)


def _s_598a(stdin: str) -> str:
    out = [str(_tricky_sum(int(x))) for x in lines(stdin)[1:]]
    return "\n".join(out) + "\n"


def _a_598a(stdin: str) -> str:
    out = []
    for x in lines(stdin)[1:]:
        n = int(x)
        out.append(str(n * (n + 1) // 2 - 2 * (n // 2)))
    return "\n".join(out) + "\n"


def _m1_598a(stdin: str) -> str:
    return "\n".join(line for line in lines(stdin)[1:]) + "\n"


def _m2_598a(stdin: str) -> str:
    return _m1_598a(stdin)


def _gen_598a(rng: random.Random) -> list[str]:
    return [
        "3\n1\n2\n3\n",
        "1\n10\n",
        "1\n4\n",
        "1\n5\n",
        "1\n6\n",
        "1\n7\n",
        "1\n8\n",
        "1\n9\n",
        "1\n11\n",
        "1\n12\n",
        "1\n20\n",
        "1\n100\n",
    ]


# ─── 2241A Divide and Conquer ────────────────────────────────────────────────

def _s_2241a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, k = map(int, line.split())
        if n == 1:
            out.append("0")
            continue
        out.append(str((n - 1 + k - 1) // k))
    return "\n".join(out) + "\n"


def _a_2241a(stdin: str) -> str:
    return _s_2241a(stdin)


def _m1_2241a(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _m2_2241a(stdin: str) -> str:
    return _m1_2241a(stdin)


def _gen_2241a(rng: random.Random) -> list[str]:
    return [
        "1\n10 3\n",
        "1\n1 5\n",
        "1\n5 2\n",
        "1\n7 3\n",
        "1\n8 4\n",
        "1\n9 1\n",
        "1\n15 5\n",
        "1\n20 6\n",
        "1\n3 2\n",
        "1\n100 10\n",
        "1\n6 3\n",
        "1\n11 4\n",
    ]


# ─── 2014B Robin Hood and Major Oak ───────────────────────────────────────────

def _s_2014b(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        n, k = map(int, line.split())
        if k == 0:
            out.append("0")
            continue
        if k > n // 2:
            out.append("0")
            continue
        out.append("1")
    return "\n".join(out) + "\n"


def _a_2014b(stdin: str) -> str:
    return _s_2014b(stdin)


def _m1_2014b(stdin: str) -> str:
    return "\n".join("1" for _ in lines(stdin)[1:]) + "\n"


def _m2_2014b(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _gen_2014b(rng: random.Random) -> list[str]:
    return [
        "1\n3 1\n",
        "1\n4 2\n",
        "1\n5 0\n",
        "1\n6 3\n",
        "1\n10 5\n",
        "1\n2 1\n",
        "1\n7 2\n",
        "1\n8 4\n",
        "1\n9 1\n",
        "1\n5 3\n",
        "1\n4 0\n",
        "1\n6 1\n",
    ]


# ─── 2091B Team Training ──────────────────────────────────────────────────────

def _s_2091b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split()); idx += 1
        a = sorted(map(int, ls[idx].split())); idx += 1
        cnt = 0
        mul = 1
        for v in reversed(a):
            if v * mul >= x:
                cnt += 1
                mul = 1
            else:
                mul += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _a_2091b(stdin: str) -> str:
    return _s_2091b(stdin)


def _m1_2091b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0]); idx = 1
    out = []
    for _ in range(t):
        n, x = map(int, ls[idx].split()); idx += 1
        a = list(map(int, ls[idx].split())); idx += 1
        out.append(str(n))
    return "\n".join(out) + "\n"


def _m2_2091b(stdin: str) -> str:
    return "\n".join("0" for _ in lines(stdin)[1:]) + "\n"


def _gen_2091b(rng: random.Random) -> list[str]:
    return [
        "1\n3 5\n1 2 3\n",
        "1\n4 6\n1 2 3 4\n",
        "1\n2 10\n5 6\n",
        "1\n5 3\n1 1 1 1 1\n",
        "1\n3 4\n2 2 2\n",
        "1\n4 8\n2 3 4 5\n",
        "1\n6 2\n1 1 1 1 1 1\n",
        "1\n3 7\n3 3 3\n",
        "1\n5 5\n1 2 3 4 5\n",
        "1\n2 1\n1 1\n",
        "1\n4 4\n1 1 2 2\n",
        "1\n3 9\n3 3 3\n",
    ]


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

    entries = [
        ("1567B", "Shortest array length with MEX a and XOR b.", _s_1567b, _a_1567b, {"w1": _m1_1567b, "w2": _m2_1567b}, _gen_1567b, "bitmasks", "exact", "5\n1 1\n2 1\n2 0\n1 10000\n2 10000\n"),
        ("1829D", "YES if n reachable from 11 by multiply/divide 11.", _s_1829d, _a_1829d, {"w1": _m1_1829d, "w2": _m2_1829d}, _gen_1829d, "math", "tokens_ci", "3\n11\n121\n1331\n"),
        ("1846A", "Count ropes to cut where nail height exceeds rope.", _s_1846a, _a_1846a, {"w1": _m1_1846a, "w2": _m2_1846a}, _gen_1846a, "implementation", "exact", "4\n3\n4 3\n3 1\n1 2\n4\n9 2\n5 2\n7 7\n3 4\n5\n11 7\n5 10\n12 9\n3 2\n1 5\n3\n5 6\n4 5\n7 7\n"),
        ("1811A", "Max number after inserting digit d.", _s_1811a, _a_1811a, {"w1": _m1_1811a, "w2": _m2_1811a}, _gen_1811a, "greedy", "exact", "1\n5 4\n76543\n"),
        ("1765M", "Minimum LCM among all pairs.", _s_1765m, _a_1765m, {"w1": _m1_1765m, "w2": _m2_1765m}, _gen_1765m, "number_theory", "exact", "1\n3\n2 4 6\n"),
        ("1974B", "Decode symmetric encoding.", _s_1974b, _a_1974b, {"w1": _m1_1974b, "w2": _m2_1974b}, _gen_1974b, "strings", "exact", "1\n5\nababa\n"),
        ("1807C", "Apply character replacement operations.", _s_1807c, _a_1807c, {"w1": _m1_1807c, "w2": _m2_1807c}, _gen_1807c, "strings", "exact", "1\n5\nabacaba\n2\na e\nc b\n"),
        ("1618A", "Count ordinary numbers in range.", _s_1618a, _a_1618a, {"w1": _m1_1618a, "w2": _m2_1618a}, _gen_1618a, "math", "exact", "3\n1 9\n95 115\n998 24435\n"),
        ("1553A", "Max soda bottles with sharing k friends.", _s_1553a, _a_1553a, {"w1": _m1_1553a, "w2": _m2_1553a}, _gen_1553a, "math", "exact", "2\n10 2 3\n20 3 4\n"),
        ("1339A", "Min diamonds to fill rectangle.", _s_1339a, _a_1339a, {"w1": _m1_1339a, "w2": _m2_1339a}, _gen_1339a, "math", "exact", "2\n1 5\n3 3\n"),
        ("1932A", "Max coins on thorn path.", _s_1932a, _a_1932a, {"w1": _m1_1932a, "w2": _m2_1932a}, _gen_1932a, "dp", "exact", "1\n7\n.#..#..\n"),
        ("1714B", "Max sum after removing duplicate prefix.", _s_1714b, _a_1714b, {"w1": _m1_1714b, "w2": _m2_1714b}, _gen_1714b, "greedy", "exact", "1\n5\n1 2 3 4 5\n"),
        ("1741A", "Same t-shirt size YES/NO.", _s_1741a, _a_1741a, {"w1": _m1_1741a, "w2": _m2_1741a}, _gen_1741a, "strings", "tokens_ci", "3\nXS S\nM M\nL XL\n"),
        ("1698A", "Find missing XOR element.", _s_1698a, _a_1698a, {"w1": _m1_1698a, "w2": _m2_1698a}, _gen_1698a, "bitmasks", "exact", "1\n4\n1 2 3 0\n"),
        ("1851B", "Parity sort possible YES/NO.", _s_1851b, _a_1851b, {"w1": _m1_1851b, "w2": _m2_1851b}, _gen_1851b, "greedy", "tokens_ci", "1\n4\n2 1 4 3\n"),
        ("2004A", "YES if no adjacent integer points.", _s_2004a, _a_2004a, {"w1": _m1_2004a, "w2": _m2_2004a}, _gen_2004a, "math", "tokens_ci", "2\n2\n1 3\n3\n1 2 3\n"),
        ("1714A", "Minutes until 24:00 from wake time.", _s_1714a, _a_1714a, {"w1": _m1_1714a, "w2": _m2_1714a}, _gen_1714a, "math", "exact", "1\n1 10 30\n"),
        ("1619B", "Count squares and cubes up to n.", _s_1619b, _a_1619b, {"w1": _m1_1619b, "w2": _m2_1619b}, _gen_1619b, "math", "exact", "3\n1\n4\n26\n"),
        ("1759A", "String is Yes repeated YES/NO.", _s_1759a, _a_1759a, {"w1": _m1_1759a, "w2": _m2_1759a}, _gen_1759a, "strings", "tokens_ci", "3\nYesYesYes\nYesYes\nYes\n"),
        ("219A", "k-string repetition YES/NO.", _s_219a, _a_219a, {"w1": _m1_219a, "w2": _m2_219a}, _gen_219a, "strings", "tokens_ci", "2\nabab\n"),
        ("1220A", "Cards form consecutive set YES/NO.", _s_1220a, _a_1220a, {"w1": _m1_1220a, "w2": _m2_1220a}, _gen_1220a, "implementation", "tokens_ci", "3\n1 2 3\n"),
        ("2001A", "All elements equal YES/NO.", _s_2001a, _a_2001a, {"w1": _m1_2001a, "w2": _m2_2001a}, _gen_2001a, "greedy", "tokens_ci", "2\n3\n1 1 1\n3\n1 2 1\n"),
        ("1372A", "Third array element from sum.", _s_1372a, _a_1372a, {"w1": _m1_1372a, "w2": _m2_1372a}, _gen_1372a, "math", "exact", "1\n3\n1 2 3\n"),
        ("1611A", "Rearrange digits to even number.", _s_1611a, _a_1611a, {"w1": _m1_1611a, "w2": _m2_1611a}, _gen_1611a, "greedy", "exact", "2\n385\n249\n"),
        ("1366A", "Max monster hits with shovel/sword.", _s_1366a, _a_1366a, {"w1": _m1_1366a, "w2": _m2_1366a}, _gen_1366a, "binary_search", "exact", "1\n4 5\n"),
        ("1296B", "Burles after coin exchange.", _s_1296b, _a_1296b, {"w1": _m1_1296b, "w2": _m2_1296b}, _gen_1296b, "math", "exact", "1\n1 3\n"),
        ("1538B", "Equal candy split YES/NO.", _s_1538b, _a_1538b, {"w1": _m1_1538b, "w2": _m2_1538b}, _gen_1538b, "math", "tokens_ci", "3\n1 2 3\n"),
        ("1714C", "Smallest number >= n with strictly increasing digits.", _s_1714c, _a_1714c, {"w1": _m1_1714c, "w2": _m2_1714c}, _gen_1714c, "greedy", "exact", "3\n1\n11\n21\n"),
        ("1997A", "Append char to avoid length-2 palindrome.", _s_1997a, _a_1997a, {"w1": _m1_1997a, "w2": _m2_1997a}, _gen_1997a, "strings", "exact", "1\naba\n"),
        ("1519B", "Split into equal sum subsets YES/NO.", _s_1519b, _a_1519b, {"w1": _m1_1519b, "w2": _m2_1519b}, _gen_1519b, "dp", "tokens_ci", "1\n4\n1 2 3 4\n"),
        ("1772B", "Matrix rotation makes equal parity sums.", _s_1772b, _a_1772b, {"w1": _m1_1772b, "w2": _m2_1772b}, _gen_1772b, "math", "tokens_ci", "1\n2\n1 2\n3 4\n"),
        ("1328C", "Ternary XOR reconstruct string.", _s_1328c, _a_1328c, {"w1": _m1_1328c, "w2": _m2_1328c}, _gen_1328c, "greedy", "exact", "1\n3\n222\n022\n"),
        ("1993A", "Max correct answers from question marks.", _s_1993a, _a_1993a, {"w1": _m1_1993a, "w2": _m2_1993a}, _gen_1993a, "greedy", "exact", "1\n2\nABCD\n"),
        ("1490A", "Min ops to make dense array.", _s_1490a, _a_1490a, {"w1": _m1_1490a, "w2": _m2_1490a}, _gen_1490a, "greedy", "exact", "1\n3\n1 2 3\n"),
        ("2055A", "Two frogs meeting parity game.", _s_2055a, _a_2055a, {"w1": _m1_2055a, "w2": _m2_2055a}, _gen_2055a, "games", "tokens_ci", "1\n6 2 3\n"),
        ("2086A", "Half of n*m jam pairs.", _s_2086a, _a_2086a, {"w1": _m1_2086a, "w2": _m2_2086a}, _gen_2086a, "math", "exact", "1\n2 3\n"),
        ("1535B", "Array sorted or reverse sorted YES/NO.", _s_1535b, _a_1535b, {"w1": _m1_1535b, "w2": _m2_1535b}, _gen_1535b, "greedy", "tokens_ci", "1\n3\n1 2 3\n"),
        ("349A", "Cinema line fit YES/NO.", _s_349a, _a_349a, {"w1": _m1_349a, "w2": _m2_349a}, _gen_349a, "greedy", "tokens_ci", "3\n1 1 1\n"),
        ("1618C", "Paint array into equal xor groups.", _s_1618c, _a_1618c, {"w1": _m1_1618c, "w2": _m2_1618c}, _gen_1618c, "bitmasks", "tokens_ci", "1\n4\n1 2 3 1\n"),
        ("1829C", "Min insertions for 01 substring.", _s_1829c, _a_1829c, {"w1": _m1_1829c, "w2": _m2_1829c}, _gen_1829c, "greedy", "exact", "1\n3\n101\n"),
        ("598A", "Tricky sum formula.", _s_598a, _a_598a, {"w1": _m1_598a, "w2": _m2_598a}, _gen_598a, "math", "exact", "3\n1\n2\n3\n"),
        ("2241A", "Divide array into k parts min ops.", _s_2241a, _a_2241a, {"w1": _m1_2241a, "w2": _m2_2241a}, _gen_2241a, "greedy", "exact", "1\n10 3\n"),
        ("2014B", "Robin Hood tree existence.", _s_2014b, _a_2014b, {"w1": _m1_2014b, "w2": _m2_2014b}, _gen_2014b, "math", "exact", "1\n3 1\n"),
        ("2091B", "Max trained teams.", _s_2091b, _a_2091b, {"w1": _m1_2091b, "w2": _m2_2091b}, _gen_2091b, "greedy", "exact", "1\n3 5\n1 2 3\n"),
    ]

    for pid, summary, solve, alt, mutants, generate, family, checker, sample_in in entries:
        out = solve(sample_in)
        add(pid, summary, ({"input": sample_in, "output": out},), solve, alt, mutants, generate, family=family, checker=checker)

    return specs


SPECS = _build()

_KEEP = ['1567B', '1829D', '1846A', '1811A', '1765M', '1974B', '1807C', '1618A', '1553A', '1339A', '1932A', '1714B', '1741A', '1698A', '1851B', '2004A', '1714A', '1619B', '1759A', '219A', '1220A', '2001A', '1372A', '1611A', '1366A', '1296B', '1538B', '1714C', '1997A', '1519B', '1772B', '1328C', '1993A', '1490A', '2055A', '2086A', '1535B', '349A', '1618C', '1829C', '598A', '2241A', '2014B', '2091B']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
