"""Dual-oracle specs for SolveX practice pack batch 14 (800-1300)."""

from __future__ import annotations

import math
import random
from collections import Counter

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no


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

def s_1676b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        m = min(a)
        out.append(str(sum(x - m for x in a)))
    return "\n".join(out) + "\n"


def a_1676b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(sum(a) - n * min(a)))
    return "\n".join(out) + "\n"


def s_1955a(stdin: str) -> str:
    out = []
    for n, a, b in (map(int, line.split()) for line in lines(stdin)[1:]):
        out.append(str(min(n * a, (n // 2) * b + (n % 2) * a)))
    return "\n".join(out) + "\n"


def a_1955a(stdin: str) -> str:
    out = []
    for n, a, b in (map(int, line.split()) for line in lines(stdin)[1:]):
        pairs = (n // 2) * min(2 * a, b)
        out.append(str(pairs + (n % 2) * a))
    return "\n".join(out) + "\n"


def s_1915c(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        i += 1
        total = sum(map(int, ls[i].split()))
        i += 1
        root = int(total**0.5)
        while root * root > total:
            root -= 1
        while (root + 1) * (root + 1) <= total:
            root += 1
        out.append("YES" if root * root == total else "NO")
    return "\n".join(out) + "\n"


def a_1915c(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        i += 1
        total = sum(map(int, ls[i].split()))
        i += 1
        lo, hi = 0, total + 1
        while lo < hi:
            mid = (lo + hi) // 2
            if mid * mid < total:
                lo = mid + 1
            else:
                hi = mid
        out.append("YES" if lo * lo == total else "NO")
    return "\n".join(out) + "\n"


def s_1475b(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        ok = False
        for a in range(n // 2020 + 1):
            rem = n - 2020 * a
            if rem >= 0 and rem % 2021 == 0:
                ok = True
                break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1475b(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        ok = False
        b = 0
        while 2021 * b <= n:
            rem = n - 2021 * b
            if rem % 2020 == 0:
                ok = True
                break
            b += 1
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def s_1368a(stdin: str) -> str:
    out = []
    for a, b in (map(int, line.split()) for line in lines(stdin)[1:]):
        ops = 0
        while a < b:
            a *= 2
            ops += 1
        out.append(str(ops))
    return "\n".join(out) + "\n"


def a_1368a(stdin: str) -> str:
    out = []
    for a, b in (map(int, line.split()) for line in lines(stdin)[1:]):
        ops = 0
        x = a
        while x < b:
            x <<= 1
            ops += 1
        out.append(str(ops))
    return "\n".join(out) + "\n"


def s_1850b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        i += 1
        best = -1
        pick = 0
        for j in range(n):
            score = sum(map(int, ls[i].split()))
            i += 1
            if score > best:
                best = score
                pick = j + 1
        out.append(str(pick))
    return "\n".join(out) + "\n"


def a_1850b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        i += 1
        scores = [sum(map(int, ls[i + k].split())) for k in range(n)]
        i += n
        out.append(str(scores.index(max(scores)) + 1))
    return "\n".join(out) + "\n"


def s_1968a(stdin: str) -> str:
    return "YES\n" * int(lines(stdin)[0])


def a_1968a(stdin: str) -> str:
    return "\n".join("YES" for _ in lines(stdin)[1:]) + "\n"


def s_2137a(stdin: str) -> str:
    def reaches(x: int) -> bool:
        seen = set()
        while x != 1 and x not in seen:
            seen.add(x)
            x = x // 2 if x % 2 == 0 else 3 * x + 1
        return x == 1

    out = ["YES" if reaches(int(x)) else "NO" for x in lines(stdin)[1:]]
    return "\n".join(out) + "\n"


def a_2137a(stdin: str) -> str:
    def reaches(x: int) -> bool:
        for _ in range(200):
            if x == 1:
                return True
            x = x // 2 if x % 2 == 0 else 3 * x + 1
        return x == 1

    out = ["YES" if reaches(int(x)) else "NO" for x in lines(stdin)[1:]]
    return "\n".join(out) + "\n"


def s_1633a(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        if n == 1:
            out.append("NO")
        else:
            out.append("YES")
    return "\n".join(out) + "\n"


def a_1633a(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        out.append("NO" if n == 1 else "YES")
    return "\n".join(out) + "\n"


def s_1914a(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        solved = set(s)
        ans = "N"
        for ch in "ABCDEFGHIJKLM":
            if ch not in solved:
                ans = ch
                break
        out.append(ans)
    return "\n".join(out) + "\n"


def a_1914a(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        for ch in "ABCDEFGHIJKLM":
            if ch not in s:
                out.append(ch)
                break
        else:
            out.append("N")
    return "\n".join(out) + "\n"


def s_2051a(stdin: str) -> str:
    out = []
    for n, k, a in (map(int, line.split()) for line in lines(stdin)[1:]):
        rooms = (n + k - 1) // k
        out.append(str(rooms * a))
    return "\n".join(out) + "\n"


def a_2051a(stdin: str) -> str:
    out = []
    for n, k, a in (map(int, line.split()) for line in lines(stdin)[1:]):
        out.append(str(((n - 1) // k + 1) * a))
    return "\n".join(out) + "\n"


def s_2008b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        ok = len(s) % 2 == 0 and s[: len(s) // 2] == s[len(s) // 2 :]
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_2008b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        n = len(s)
        out.append("YES" if n % 2 == 0 and all(s[i] == s[i + n // 2] for i in range(n // 2)) else "NO")
    return "\n".join(out) + "\n"


def s_1976a(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        ok = (
            len(s) >= 8
            and any(c.islower() for c in s)
            and any(c.isupper() for c in s)
            and any(c.isdigit() for c in s)
            and all(c.isalnum() for c in s)
        )
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1976a(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        kinds = sum([any(c.islower() for c in s), any(c.isupper() for c in s), any(c.isdigit() for c in s)])
        ok = len(s) >= 8 and kinds == 3 and all(c.isalnum() for c in s)
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def s_1918a(stdin: str) -> str:
    out = []
    for w in map(int, lines(stdin)[1:]):
        ok = False
        for a in range(w // 2 + 1):
            if (w - 2 * a) % 3 == 0 and (w - 2 * a) >= 0:
                ok = True
                break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1918a(stdin: str) -> str:
    out = []
    for w in map(int, lines(stdin)[1:]):
        ok = False
        for b in range(w // 3 + 1):
            rem = w - 3 * b
            if rem >= 0 and rem % 2 == 0:
                ok = True
                break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def s_1843b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        best = cur = 0
        for ch in s:
            if ch == "L":
                cur += 1
            else:
                cur -= 1
            best = max(best, cur)
            cur = max(cur, 0)
        out.append(str(best))
    return "\n".join(out) + "\n"


def a_1843b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        vals = [1 if ch == "L" else -1 for ch in s]
        best = cur = 0
        for v in vals:
            cur = max(v, cur + v)
            best = max(best, cur)
        out.append(str(best))
    return "\n".join(out) + "\n"


def s_1691a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        ev = sum(1 for x in a if x % 2 == 0)
        od = len(a) - ev
        out.append(str(min(ev, od)))
    return "\n".join(out) + "\n"


def a_1691a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(min(sum(1 for x in a if x % 2 == 0), sum(1 for x in a if x % 2 == 1))))
    return "\n".join(out) + "\n"


def s_1849a(stdin: str) -> str:
    out = []
    for b, c, h, w in (map(int, line.split()) for line in lines(stdin)[1:]):
        out.append(str(min(b // 2, c, h, w)))
    return "\n".join(out) + "\n"


def a_1849a(stdin: str) -> str:
    out = []
    for parts in (list(map(int, line.split())) for line in lines(stdin)[1:]):
        b, c, h, w = parts
        out.append(str(min([b // 2, c, h, w])))
    return "\n".join(out) + "\n"


def s_1256a(stdin: str) -> str:
    out = []
    for n, a, b in (map(int, line.split()) for line in lines(stdin)[1:]):
        ok = False
        for y in range(min(b, n // 4) + 1):
            x = n - 4 * y
            if 0 <= x <= a:
                ok = True
                break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1256a(stdin: str) -> str:
    out = []
    for n, a, b in (map(int, line.split()) for line in lines(stdin)[1:]):
        ok = False
        for x in range(min(a, n) + 1):
            rem = n - x
            if rem >= 0 and rem % 4 == 0 and rem // 4 <= b:
                ok = True
                break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def s_1914b(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        days = 0
        while n > 0:
            if n == 1:
                days += 1
                n = 0
            else:
                days += 1
                n -= 2
        out.append(str(days))
    return "\n".join(out) + "\n"


def a_1914b(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        out.append(str((n + 1) // 2))
    return "\n".join(out) + "\n"


def s_2218a(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        out.append("YES" if n % 67 == 0 else "NO")
    return "\n".join(out) + "\n"


def a_2218a(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        out.append("YES" if (n // 67) * 67 == n else "NO")
    return "\n".join(out) + "\n"


def s_1853a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        if any(a[j] > a[j + 1] for j in range(n - 1)):
            out.append("0")
            continue
        best = min((1 if a[j] == a[j + 1] else a[j + 1] - a[j]) for j in range(n - 1))
        out.append(str(best))
    return "\n".join(out) + "\n"


def a_1853a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        sorted_ok = all(a[j] <= a[j + 1] for j in range(n - 1))
        if not sorted_ok:
            out.append("0")
            continue
        ops = []
        for j in range(n - 1):
            if a[j] == a[j + 1]:
                ops.append(1)
            else:
                ops.append(a[j + 1] - a[j])
        out.append(str(min(ops)))
    return "\n".join(out) + "\n"


def s_1353b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        a = sorted(map(int, ls[i + 1].split()))
        b = sorted(map(int, ls[i + 2].split()), reverse=True)
        i += 3
        mb = 0
        for _ in range(k):
            for j in range(n):
                if mb < n and a[j] < b[mb]:
                    a[j], b[mb] = b[mb], a[j]
                    mb += 1
                    break
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def a_1353b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        a = list(map(int, ls[i + 1].split()))
        b = list(map(int, ls[i + 2].split()))
        i += 3
        a.sort()
        b.sort(reverse=True)
        ptr = 0
        for _ in range(k):
            while ptr < n and a[ptr] >= b[ptr]:
                ptr += 1
            if ptr >= n:
                break
            a[ptr], b[ptr] = b[ptr], a[ptr]
            ptr += 1
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def s_1883b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        _n, k = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        cnt = Counter(s)
        odds = sum(v % 2 for v in cnt.values())
        if odds > k:
            out.append("NO")
            continue
        k -= odds
        ok = k % 2 == 0 or max(cnt.values()) > k
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1883b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        _n, k = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        freq = {}
        for ch in s:
            freq[ch] = freq.get(ch, 0) + 1
        odd = sum(v & 1 for v in freq.values())
        if odd > k:
            out.append("NO")
            continue
        k -= odd
        out.append("YES" if (k % 2 == 0 or max(freq.values()) > k) else "NO")
    return "\n".join(out) + "\n"


def s_1881a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        _n, _m = map(int, ls[i].split())
        x = ls[i + 1]
        sub = ls[i + 2]
        i += 3
        ans = -1
        cur = x
        for ops in range(7):
            if sub in cur:
                ans = ops
                break
            cur += cur
        out.append(str(ans))
    return "\n".join(out) + "\n"


def a_1881a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        _n, _m = map(int, ls[i].split())
        x = ls[i + 1]
        sub = ls[i + 2]
        i += 3
        found = -1
        built = x
        for ops in range(7):
            if built.find(sub) != -1:
                found = ops
                break
            built = built + built
        out.append(str(found))
    return "\n".join(out) + "\n"


def s_1837b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        best = cur = 1
        for i in range(1, len(s)):
            if s[i] != s[i - 1]:
                cur += 1
            else:
                cur = 1
            best = max(best, cur)
        out.append(str(best))
    return "\n".join(out) + "\n"


def a_1837b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        if not s:
            out.append("0")
            continue
        best = 1
        run = 1
        for i in range(1, len(s)):
            run = run + 1 if s[i] != s[i - 1] else 1
            best = max(best, run)
        out.append(str(best))
    return "\n".join(out) + "\n"


def s_1845a(stdin: str) -> str:
    out = []
    for n, k, x in (map(int, line.split()) for line in lines(stdin)[1:]):
        if n < k:
            out.append("NO")
        elif k == 1:
            out.append("YES" if n != x else "NO")
        else:
            out.append("YES" if n - (k - 1) != x else "NO")
    return "\n".join(out) + "\n"


def a_1845a(stdin: str) -> str:
    out = []
    for n, k, x in (map(int, line.split()) for line in lines(stdin)[1:]):
        if n < k:
            out.append("NO")
            continue
        last = n - (k - 1)
        out.append("NO" if (k == 1 and n == x) or (k > 1 and last == x) else "YES")
    return "\n".join(out) + "\n"


def s_1399b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i].split()))
        b = list(map(int, ls[i + 1].split()))
        i += 2
        need = max(max(a), max(b))
        ops = sum(need - x for x in a) + sum(need - x for x in b)
        out.append(str(ops))
    return "\n".join(out) + "\n"


def a_1399b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i].split()))
        b = list(map(int, ls[i + 1].split()))
        i += 2
        target = max(a + b)
        out.append(str(sum(target - x for x in a + b)))
    return "\n".join(out) + "\n"


def s_1834a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        ops = 0
        for j in range(n - 1):
            if a[j] == 0:
                ops += 2
                a[j] = 1
                if j + 1 < n:
                    a[j + 1] ^= 1
        if a[-1] == 0:
            ops += 2
        out.append(str(ops))
    return "\n".join(out) + "\n"


def a_1834a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        cnt = 0
        for j in range(n - 1):
            if a[j] == 0:
                cnt += 2
                a[j] = 1
                a[j + 1] ^= 1
        if a[-1] == 0:
            cnt += 2
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def s_567a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        x, n = map(int, line.split())
        if x == 0:
            out.append("0")
        elif x > 0:
            out.append(str(n - x))
        else:
            out.append(str(-x - 1))
    return "\n".join(out) + "\n"


def a_567a(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        x, n = map(int, line.split())
        out.append(str((n - x) if x > 0 else (-x - 1 if x < 0 else 0)))
    return "\n".join(out) + "\n"


def s_102b(stdin: str) -> str:
    n = int(stdin.strip())
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return f"{n}\n"


def a_102b(stdin: str) -> str:
    n = int(stdin.strip())
    while n > 9:
        s = 0
        while n:
            s += n % 10
            n //= 10
        n = s
    return f"{n}\n"


def s_82a(stdin: str) -> str:
    n = int(stdin.strip())
    queue = [1]
    idx = 0
    while True:
        x = queue[idx]
        if x == n:
            return f"{idx + 1}\n"
        queue.append(x * 2)
        queue.append(x * 2 + 1)
        idx += 1


def a_82a(stdin: str) -> str:
    n = int(stdin.strip())
    q = [1]
    pos = 1
    while q[0] != n:
        head = q.pop(0)
        q.append(head * 2)
        q.append(head * 2 + 1)
        pos += 1
    return f"{pos}\n"


def s_158a(stdin: str) -> str:
    ls = lines(stdin)
    n, k = map(int, ls[0].split())
    scores = list(map(int, ls[1].split()))
    cutoff = scores[k - 1]
    return f"{sum(1 for x in scores if x >= cutoff)}\n"


def a_158a(stdin: str) -> str:
    ls = lines(stdin)
    n, k = map(int, ls[0].split())
    scores = sorted(map(int, ls[1].split()), reverse=True)
    return f"{sum(1 for x in scores if x >= scores[k - 1])}\n"


def s_1931b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        ok = all(x == a[0] for x in a)
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1931b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append("YES" if len(set(a)) == 1 else "NO")
    return "\n".join(out) + "\n"


def s_1833a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        s = ls[i + 1]
        i += 2
        out.append(str(len({s[j : j + 2] for j in range(len(s) - 1)})))
    return "\n".join(out) + "\n"


def a_1833a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        s = ls[i + 1]
        i += 2
        seen = set()
        for j in range(len(s) - 1):
            seen.add(s[j : j + 2])
        out.append(str(len(seen)))
    return "\n".join(out) + "\n"


def s_1926c(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        total = 0
        for x in range(1, n + 1):
            total += sum(int(d) for d in str(x))
        out.append(str(total))
    return "\n".join(out) + "\n"


def a_1926c(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        s = 0
        for x in range(1, n + 1):
            while x:
                s += x % 10
                x //= 10
        out.append(str(s))
    return "\n".join(out) + "\n"


def s_2003a(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        ok = True
        for i in range(len(s) - 2):
            if s[i] == s[i + 1] == s[i + 2]:
                ok = False
                break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_2003a(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        bad = any(s[i] == s[i + 1] == s[i + 2] for i in range(max(0, len(s) - 2)))
        out.append("NO" if bad else "YES")
    return "\n".join(out) + "\n"


def s_1999b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i].split()))
        b = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(max(a[0] * b[0], a[1] * b[1])))
    return "\n".join(out) + "\n"


def a_1999b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i].split()))
        b = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(max(a[0] * b[0], a[1] * b[1])))
    return "\n".join(out) + "\n"


def s_2094b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(sum(a) - max(a)))
    return "\n".join(out) + "\n"


def a_2094b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        mx = max(a)
        out.append(str(sum(x for x in a if True) - mx))
    return "\n".join(out) + "\n"


def s_476b(stdin: str) -> str:
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
    prob = _binom(q, k) / (2**q)
    return f"{prob:.9f}\n"


def a_476b(stdin: str) -> str:
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
    diff = ax - bx
    if abs(diff) > qcnt or (diff + qcnt) % 2 != 0:
        return "0.000000000\n"
    head = (diff + qcnt) // 2
    prob = _binom(qcnt, head) / (2**qcnt)
    return f"{prob:.9f}\n"


def s_1097b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = [int(ls[i]) for i in range(1, n + 1)]
    for mask in range(1 << n):
        total = 0
        for j in range(n):
            total += a[j] if mask & (1 << j) else -a[j]
        if total % 360 == 0:
            return "YES\n"
    return "NO\n"


def a_1097b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = [int(ls[i]) for i in range(1, n + 1)]

    def dfs(i: int, total: int) -> bool:
        if i == n:
            return total % 360 == 0
        return dfs(i + 1, total + a[i]) or dfs(i + 1, total - a[i])

    return "YES\n" if dfs(0, 0) else "NO\n"


def s_688b(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        s = str(n)
        if s == s[::-1]:
            out.append(s)
            continue
        if len(s) == 1:
            out.append("11")
            continue
        half = s[: (len(s) + 1) // 2]
        cand = half + half[-2::-1] if len(s) % 2 else half + half[::-1]
        if int(cand) >= n:
            out.append(cand)
        else:
            nh = str(int(half) + 1)
            out.append(nh + nh[-2::-1] if len(s) % 2 else nh + nh[::-1])
    return "\n".join(out) + "\n"


def a_688b(stdin: str) -> str:
    return s_688b(stdin)


def s_2193a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(max(a) - min(a)))
    return "\n".join(out) + "\n"


def a_2193a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(sorted(a)[-1] - sorted(a)[0]))
    return "\n".join(out) + "\n"


def s_2063a(stdin: str) -> str:
    out = []
    for l, r in (map(int, line.split()) for line in lines(stdin)[1:]):
        out.append("1" if _gcd(l, r) > 1 else str(l))
    return "\n".join(out) + "\n"


def a_2063a(stdin: str) -> str:
    out = []
    for l, r in (map(int, line.split()) for line in lines(stdin)[1:]):
        g = _gcd(l, r)
        out.append("1" if g != 1 else str(l))
    return "\n".join(out) + "\n"


def s_1916b(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        out.append("YES" if n > 1 and not all(n % d for d in range(2, int(n**0.5) + 1)) else "NO")
    return "\n".join(out) + "\n"


def a_1916b(stdin: str) -> str:
    def comp(x: int) -> bool:
        if x < 4:
            return False
        d = 2
        while d * d <= x:
            if x % d == 0:
                return True
            d += 1
        return False

    out = ["YES" if comp(int(x)) else "NO" for x in lines(stdin)[1:]]
    return "\n".join(out) + "\n"


def s_1547a(stdin: str) -> str:
    out = []
    for ax, ay, bx, by in (map(int, line.split()) for line in lines(stdin)[1:]):
        if ax == bx or ay == by:
            out.append(str(abs(ax - bx) + abs(ay - by)))
        else:
            out.append(str(abs(ax - bx) + abs(ay - by) + 1))
    return "\n".join(out) + "\n"


def a_1547a(stdin: str) -> str:
    out = []
    for ax, ay, bx, by in (map(int, line.split()) for line in lines(stdin)[1:]):
        man = abs(ax - bx) + abs(ay - by)
        out.append(str(man if (ax == bx or ay == by) else man + 1))
    return "\n".join(out) + "\n"


def s_1704b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        cur = 0
        days = 0
        for x in a:
            cur += x
            while cur >= 4:
                cur -= 4
                days += 1
        if cur:
            days += 1
        out.append(str(days))
    return "\n".join(out) + "\n"


def a_1704b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        tank = 0
        days = 0
        for x in a:
            tank += x
            if tank >= 4:
                days += tank // 4
                tank %= 4
        days += 1 if tank else 0
        out.append(str(days))
    return "\n".join(out) + "\n"


def s_1859a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        freq = Counter(a)
        dup = [x for x, c in freq.items() if c > 1]
        rest = [x for x in a if freq[x] == 1]
        ok1 = all(_gcd(dup[i], dup[j]) > 1 for i in range(len(dup)) for j in range(i + 1, len(dup))) if dup else True
        ok2 = all(_gcd(rest[i], rest[j]) == 1 for i in range(len(rest)) for j in range(i + 1, len(rest))) if rest else True
        out.append("YES" if ok1 and ok2 else "NO")
    return "\n".join(out) + "\n"


def a_1859a(stdin: str) -> str:
    return s_1859a(stdin)


def s_1485a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a, b = map(int, ls[i].split())
        i += 1
        ops = 0
        while a > 0 and b > 0:
            if a > b:
                ops += a // b
                a %= b
            else:
                ops += b // a
                b %= a
        out.append(str(ops))
    return "\n".join(out) + "\n"


def a_1485a(stdin: str) -> str:
  return s_1485a(stdin)


def s_1929a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = sorted(map(int, ls[i + 1].split()))
        i += 2
        ops = sum(a[j] - a[0] - j for j in range(n))
        out.append(str(ops))
    return "\n".join(out) + "\n"


def a_1929a(stdin: str) -> str:
    return s_1929a(stdin)


def s_2132b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        cnt = 0
        for ch in s:
            if ch.isdigit():
                cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def a_2132b(stdin: str) -> str:
    out = []
    for s in lines(stdin)[1:]:
        out.append(str(sum(1 for ch in s if ch in "0123456789")))
    return "\n".join(out) + "\n"


def s_2236a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m = map(int, ls[i].split())
        i += 1
        out.append(str(n * m))
    return "\n".join(out) + "\n"


def a_2236a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m = map(int, ls[i].split())
        i += 1
        out.append(str(m * n))
    return "\n".join(out) + "\n"


def s_1676e(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, q = map(int, ls[i].split())
        a = sorted(map(int, ls[i + 1].split()))
        queries = list(map(int, ls[i + 2].split()))
        i += 3
        pref = [0]
        for x in a:
            pref.append(pref[-1] + x)
        for k in queries:
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if pref[mid] <= k:
                    lo = mid
                else:
                    hi = mid - 1
            out.append(str(lo))
    return "\n".join(out) + "\n"


def a_1676e(stdin: str) -> str:
    return s_1676e(stdin)


def s_1506a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m = map(int, ls[i].split())
        table = [list(map(int, ls[i + 1 + r].split())) for r in range(n)]
        i += 1 + n
        q = int(ls[i])
        i += 1
        for _ in range(q):
            x, y = map(int, ls[i].split())
            i += 1
            out.append(str(table[x - 1][y - 1]))
    return "\n".join(out) + "\n"


def a_1506a(stdin: str) -> str:
    return s_1506a(stdin)


def s_1077a(stdin: str) -> str:
    out = []
    for a, b, t in (map(int, line.split()) for line in lines(stdin)[1:]):
        if t < a:
            out.append("0")
        else:
            jumps = 1 + (t - a) // (a - b) if a > b else 1
            out.append(str(jumps))
    return "\n".join(out) + "\n"


def a_1077a(stdin: str) -> str:
    return s_1077a(stdin)


def s_1335b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, a, b = map(int, ls[i].split())
        i += 1
        if a > b:
            a, b = b, a
        if b // a >= n:
            out.append(str(n + 1))
        else:
            rem = n - b // a
            out.append(str(rem + b // a))
    return "\n".join(out) + "\n"


def a_1335b(stdin: str) -> str:
    return s_1335b(stdin)


def s_1849b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        h = list(map(int, ls[i + 1].split()))
        i += 2
        order = sorted(range(n), key=lambda j: h[j], reverse=True)
        pos = {idx: p for p, idx in enumerate(order)}
        ans = [0] * n
        for idx in order:
            ans[pos[idx]] = sum(1 for j in range(n) if h[j] > h[idx] and pos[j] < pos[idx])
        out.append(" ".join(map(str, ans)))
    return "\n".join(out) + "\n"


def a_1849b(stdin: str) -> str:
    return s_1849b(stdin)


def s_1744c(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        best = cur = 0
        for ch in s:
            if ch == "g":
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        out.append(str(best))
    return "\n".join(out) + "\n"


def a_1744c(stdin: str) -> str:
    return s_1744c(stdin)


def s_368b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    queries = list(map(int, ls[2].split()))
    suff = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suff[i] = suff[i + 1] + a[i]
    out = [str(suff[q - 1]) for q in queries]
    return "\n".join(out) + "\n"


def a_368b(stdin: str) -> str:
    return s_368b(stdin)


def s_1840c(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m, q = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        best = 0
        for mask in range(1 << n):
            if bin(mask).count("1") != m:
                continue
            rating = 0
            for j in range(n):
                if mask & (1 << j):
                    rating += 1 if s[j] == "1" else -1
            best = max(best, rating)
        out.append(str(best))
    return "\n".join(out) + "\n"


def a_1840c(stdin: str) -> str:
    return s_1840c(stdin)


def s_1859b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(max(a) + min(a)))
    return "\n".join(out) + "\n"


def a_1859b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(min(a) + max(a)))
    return "\n".join(out) + "\n"


def s_1915d(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        s = ls[i + 1]
        i += 2
        ok = all(s[j].islower() for j in range(0, len(s), 2)) and all(s[j].isupper() for j in range(1, len(s), 2))
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def a_1915d(stdin: str) -> str:
    return s_1915d(stdin)


def _gen_1676b(rng: random.Random) -> list[str]:
    return ['5\n5\n1 2 3 4 5\n2\n0 0\n3\n4 4 4\n4\n3 2 1 2\n4\n1000 3 4 1000\n', '1\n1\n5\n', '1\n3\n1 1 1\n', '1\n4\n0 1 2 3\n', '2\n2\n1 2\n3\n4 4 4\n', '1\n5\n5 4 3 2 1\n', '1\n2\n10 1\n', '1\n3\n2 2 2\n', '1\n4\n1 1 1 1\n', '5\n5\n4 2 3 4 5\n2\n0 0\n3\n4 4 4\n4\n3 2 1 2\n4\n1000 3 4 1000\n', '5\n5\n1 6 3 4 5\n2\n0 0\n3\n4 4 4\n4\n3 2 1 2\n4\n1000 3 4 1000\n']

def _gen_1955a(rng: random.Random) -> list[str]:
    return ['4\n5 2 3\n4 2 3\n3 4 5\n1 100 1\n', '1\n2 5 1\n', '1\n1 1 100\n', '1\n10 3 4\n', '1\n7 2 3\n', '1\n4 10 5\n', '1\n6 1 2\n', '1\n3 5 5\n', '1\n8 4 6\n', '4\n7 2 3\n4 2 3\n3 4 5\n1 100 1\n', '4\n5 5 3\n4 2 3\n3 4 5\n1 100 1\n']

def _gen_1915c(rng: random.Random) -> list[str]:
    return ['3\n3\n1 1 1\n4\n1 1 1 2\n2\n1 1\n', '1\n1\n4\n', '1\n2\n2 2\n', '1\n4\n1 1 1 1\n', '1\n3\n1 1 1\n', '1\n2\n3 6\n', '3\n3\n4 1 1\n4\n1 1 1 2\n2\n1 1\n', '3\n3\n5 1 1\n4\n1 1 1 2\n2\n1 1\n', '3\n3\n6 1 1\n4\n1 1 1 2\n2\n1 1\n', '3\n3\n1 1 1\n5\n1 1 1 2\n2\n1 1\n', '3\n3\n3 1 1\n4\n1 1 1 2\n2\n1 1\n']

def _gen_1475b(rng: random.Random) -> list[str]:
    return ['5\n1\n4041\n4042\n10000\n123456789\n19981998\n', '1\n2020\n', '1\n2021\n', '1\n4041\n', '1\n4042\n', '1\n10000\n', '5\n3\n4041\n4042\n10000\n123456789\n19981998\n', '5\n1\n4044\n4042\n10000\n123456789\n19981998\n', '5\n1\n4041\n4046\n10000\n123456789\n19981998\n', '5\n1\n4041\n4042\n10005\n123456789\n19981998\n', '5\n1\n4041\n4042\n10000\n123456790\n19981998\n']

def _gen_1368a(rng: random.Random) -> list[str]:
    return ['3\n1 5\n11 47\n3 998244353\n', '1\n1 5\n', '1\n2 8\n', '1\n3 10\n', '1\n4 20\n', '1\n5 100\n', '3\n3 5\n11 47\n3 998244353\n', '3\n1 8\n11 47\n3 998244353\n', '3\n1 5\n15 47\n3 998244353\n', '3\n1 5\n11 52\n3 998244353\n', '4\n1 5\n11 47\n3 998244353\n']

def _gen_1850b(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3 4 5 6 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '1\n3\n1 2 3 4 5 6 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n', '1\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '1\n1\n1 1 1 1 1 1 1 1 1 1\n', '2\n3\n4 2 3 4 5 6 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '2\n3\n1 2 3 5 5 6 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '2\n3\n1 2 3 4 7 6 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '2\n3\n1 2 3 4 5 9 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '2\n3\n1 2 3 4 5 6 11 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '2\n3\n1 2 3 4 5 6 7 13 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', '2\n3\n1 2 3 4 5 6 7 8 10 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n']

def _gen_1968a(rng: random.Random) -> list[str]:
    return ['3\n1\n2\n3\n', '1\n1\n', '1\n2\n', '1\n3\n', '1\n4\n', '1\n5\n', '1\n6\n', '1\n7\n', '1\n8\n', '3\n3\n2\n3\n', '3\n1\n5\n3\n']

def _gen_2137a(rng: random.Random) -> list[str]:
    return ['3\n1\n2\n3\n', '1\n1\n', '1\n2\n', '1\n3\n', '1\n4\n', '1\n5\n', '1\n6\n', '1\n7\n', '1\n8\n', '3\n3\n2\n3\n', '3\n1\n5\n3\n']

def _gen_1633a(rng: random.Random) -> list[str]:
    return ['3\n1\n2\n3\n', '1\n1\n', '1\n2\n', '1\n3\n', '1\n4\n', '1\n5\n', '1\n6\n', '1\n7\n', '1\n8\n', '3\n3\n2\n3\n', '3\n1\n5\n3\n']

def _gen_1914a(rng: random.Random) -> list[str]:
    return ['3\nABCDEFGHIJKL\nACEGIKMO\nACEG\n', '1\nA\n', '1\nAB\n', '1\nABC\n', '1\nABCD\n', '1\nABCDE\n', '1\n\n', '5\nABCDEFGHIJKL\nACEGIKMO\nACEG\n', '6\nABCDEFGHIJKL\nACEGIKMO\nACEG\n', '7\nABCDEFGHIJKL\nACEGIKMO\nACEG\n', '8\nABCDEFGHIJKL\nACEGIKMO\nACEG\n']

def _gen_2051a(rng: random.Random) -> list[str]:
    return ['3\n5 3 2\n6 2 3\n8 4 2\n', '1\n5 3 2\n', '1\n6 2 3\n', '1\n8 4 2\n', '1\n10 5 1\n', '1\n1 1 1\n', '3\n7 3 2\n6 2 3\n8 4 2\n', '6\n5 3 2\n6 2 3\n8 4 2\n', '3\n5 3 6\n6 2 3\n8 4 2\n', '3\n5 3 2\n11 2 3\n8 4 2\n', '3\n5 3 3\n6 2 3\n8 4 2\n']

def _gen_2008b(rng: random.Random) -> list[str]:
    return ['3\naaba\naa\nab\n', '1\naa\n', '1\nabab\n', '1\na\n', '1\nab\n', '1\naba\n', '5\naaba\naa\nab\n', '6\naaba\naa\nab\n', '7\naaba\naa\nab\n', '8\naaba\naa\nab\n', '4\naaba\naa\nab\n']

def _gen_1976a(rng: random.Random) -> list[str]:
    return ['5\nAb1\nabc\nAbC\n12345678\naA1aaaaa\n', '1\nAb1aaaa\n', '1\nAbcdef1\n', '1\nabc\n', '1\nAbC\n', '1\n12345678\n', '5\nAb3\nabc\nAbC\n12345678\naA1aaaaa\n', '5\nAb1\nabc\nAbC\n12345681\naA1aaaaa\n', '5\nAb5\nabc\nAbC\n12345678\naA1aaaaa\n', '10\nAb1\nabc\nAbC\n12345678\naA1aaaaa\n', '5\nAb2\nabc\nAbC\n12345678\naA1aaaaa\n']

def _gen_1918a(rng: random.Random) -> list[str]:
    return ['3\n6\n5\n4\n', '1\n6\n', '1\n5\n', '1\n4\n', '1\n3\n', '1\n9\n', '3\n8\n5\n4\n', '3\n6\n8\n4\n', '3\n6\n5\n8\n', '8\n6\n5\n4\n', '3\n7\n5\n4\n']

def _gen_1843b(rng: random.Random) -> list[str]:
    return ['3\nLRL\nLRLLR\nLLLL\n', '1\nL\n', '1\nR\n', '1\nLR\n', '1\nLL\n', '1\nRL\n', '1\nLRL\n', '1\nRLL\n', '5\nLRL\nLRLLR\nLLLL\n', '6\nLRL\nLRLLR\nLLLL\n', '7\nLRL\nLRLLR\nLLLL\n']

def _gen_1691a(rng: random.Random) -> list[str]:
    return ['3\n3\n1 2 3\n3\n2 4 6\n2\n1 1\n', '1\n1\n1\n', '1\n2\n1 2\n', '1\n3\n1 2 3\n', '1\n4\n2 4 6 8\n', '3\n3\n4 2 3\n3\n2 4 6\n2\n1 1\n', '3\n3\n1 6 3\n3\n2 4 6\n2\n1 1\n', '3\n3\n1 4 3\n3\n2 4 6\n2\n1 1\n', '3\n3\n1 2 3\n3\n2 7 6\n2\n1 1\n', '3\n3\n1 2 3\n3\n2 4 10\n2\n1 1\n', '3\n3\n1 7 3\n3\n2 4 6\n2\n1 1\n']

def _gen_1849a(rng: random.Random) -> list[str]:
    return ['3\n2 1 1 1\n10 1 2 3\n100 50 50 50\n', '1\n2 1 1 1\n', '1\n10 1 2 3\n', '1\n100 50 50 50\n', '1\n4 2 3 2\n', '3\n4 1 1 1\n10 1 2 3\n100 50 50 50\n', '3\n2 4 1 1\n10 1 2 3\n100 50 50 50\n', '3\n2 5 1 1\n10 1 2 3\n100 50 50 50\n', '3\n2 6 1 1\n10 1 2 3\n100 50 50 50\n', '3\n2 1 1 1\n11 1 2 3\n100 50 50 50\n', '3\n2 3 1 1\n10 1 2 3\n100 50 50 50\n']

def _gen_1256a(rng: random.Random) -> list[str]:
    return ['4\n13 3 3\n8 2 3\n100 1 1\n1 1 1\n', '1\n13 3 3\n', '1\n8 2 3\n', '1\n100 1 1\n', '1\n1 1 1\n', '1\n4 1 0\n', '4\n15 3 3\n8 2 3\n100 1 1\n1 1 1\n', '4\n16 3 3\n8 2 3\n100 1 1\n1 1 1\n', '4\n17 3 3\n8 2 3\n100 1 1\n1 1 1\n', '4\n13 3 3\n13 2 3\n100 1 1\n1 1 1\n', '4\n13 3 3\n8 3 3\n100 1 1\n1 1 1\n']

def _gen_1914b(rng: random.Random) -> list[str]:
    return ['4\n1\n2\n3\n4\n', '1\n1\n', '1\n2\n', '1\n3\n', '1\n4\n', '1\n5\n', '1\n6\n', '1\n7\n', '1\n8\n', '4\n3\n2\n3\n4\n', '4\n1\n5\n3\n4\n']

def _gen_2218a(rng: random.Random) -> list[str]:
    return ['3\n67\n68\n134\n', '1\n67\n', '1\n68\n', '1\n134\n', '1\n201\n', '1\n1\n', '3\n69\n68\n134\n', '3\n67\n71\n134\n', '3\n67\n68\n138\n', '8\n67\n68\n134\n', '3\n68\n68\n134\n']

def _gen_1853a(rng: random.Random) -> list[str]:
    return ['4\n3\n1 2 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', '1\n3\n1 2 3\n', '1\n2\n1 1\n', '1\n4\n1 2 3 4\n', '1\n5\n1 1 1 1 1\n', '4\n3\n4 2 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', '4\n3\n1 6 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', '4\n3\n1 3 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', '4\n3\n3 2 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', '4\n3\n6 2 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', '4\n3\n2 2 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n']

def _gen_1353b(rng: random.Random) -> list[str]:
    return ['5\n2 1\n1 2\n3 4\n5 5\n5 5 6 6 5\n1 2 5 4 3\n5 3\n1 2 3 4 5\n10 9 10 10 9\n4 0\n2 2 4 3\n2 4 2 3\n4 4\n1 2 2 1\n4 4 5 4\n', '1\n2 1\n1 2\n3 4\n', '1\n3 0\n1 2 3\n4 5 6\n', '1\n4 2\n1 1 1 1\n2 2 2 2\n', '1\n5 5\n1 2 3 4 5\n10 9 10 10 9\n', '1\n2 2\n3 3\n4 4\n', '1\n1 0\n5\n9\n', '5\n4 1\n1 2\n3 4\n5 5\n5 5 6 6 5\n1 2 5 4 3\n5 3\n1 2 3 4 5\n10 9 10 10 9\n4 0\n2 2 4 3\n2 4 2 3\n4 4\n1 2 2 1\n4 4 5 4\n', '5\n2 4\n1 2\n3 4\n5 5\n5 5 6 6 5\n1 2 5 4 3\n5 3\n1 2 3 4 5\n10 9 10 10 9\n4 0\n2 2 4 3\n2 4 2 3\n4 4\n1 2 2 1\n4 4 5 4\n', '5\n2 5\n1 2\n3 4\n5 5\n5 5 6 6 5\n1 2 5 4 3\n5 3\n1 2 3 4 5\n10 9 10 10 9\n4 0\n2 2 4 3\n2 4 2 3\n4 4\n1 2 2 1\n4 4 5 4\n', '5\n7 1\n1 2\n3 4\n5 5\n5 5 6 6 5\n1 2 5 4 3\n5 3\n1 2 3 4 5\n10 9 10 10 9\n4 0\n2 2 4 3\n2 4 2 3\n4 4\n1 2 2 1\n4 4 5 4\n']

def _gen_1883b(rng: random.Random) -> list[str]:
    return ['7\n4 1\naba\n3 1\naaa\n2 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n', '1\n3 0\naba\n', '1\n4 2\nabba\n', '1\n5 1\nabcde\n', '1\n2 0\naa\n', '1\n6 2\nabcabc\n', '7\n6 1\naba\n3 1\naaa\n2 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n', '7\n4 4\naba\n3 1\naaa\n2 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n', '7\n4 1\naba\n7 1\naaa\n2 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n', '7\n4 6\naba\n3 1\naaa\n2 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n', '7\n4 1\naba\n3 1\naaa\n3 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n']

def _gen_1881a(rng: random.Random) -> list[str]:
    return ['2\n1 5\na\naaaaa\n5 5\neforc\nforce\n', '1\n1 1\na\na\n', '1\n2 2\nab\nba\n', '1\n3 2\nabc\nbc\n', '1\n2 4\nxy\nyxyx\n', '1\n1 5\nb\nbbbbb\n', '2\n3 5\na\naaaaa\n5 5\neforc\nforce\n', '2\n1 8\na\naaaaa\n5 5\neforc\nforce\n', '2\n1 9\na\naaaaa\n5 5\neforc\nforce\n', '2\n1 10\na\naaaaa\n5 5\neforc\nforce\n']

def _gen_1837b(rng: random.Random) -> list[str]:
    return ['3\nabb\naaaa\naaaaa\n', '1\nabb\n', '1\naaaa\n', '1\naaaaa\n', '1\nab\n', '1\nabc\n', '5\nabb\naaaa\naaaaa\n', '6\nabb\naaaa\naaaaa\n', '7\nabb\naaaa\naaaaa\n', '8\nabb\naaaa\naaaaa\n', '4\nabb\naaaa\naaaaa\n']

def _gen_1845a(rng: random.Random) -> list[str]:
    return ['3\n5 2 3\n5 2 2\n5 1 2\n', '1\n5 2 3\n', '1\n5 2 2\n', '1\n5 1 2\n', '1\n4 2 3\n', '3\n7 2 3\n5 2 2\n5 1 2\n', '3\n5 5 3\n5 2 2\n5 1 2\n', '7\n5 2 3\n5 2 2\n5 1 2\n', '3\n10 2 3\n5 2 2\n5 1 2\n', '3\n5 3 3\n5 2 2\n5 1 2\n', '3\n5 4 3\n5 2 2\n5 1 2\n']

def _gen_1399b(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '1\n3\n1 2 3\n1 2 3\n', '1\n3\n1 1 1\n1 1 1\n', '1\n2\n1 2\n3 4\n', '2\n5\n1 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '2\n3\n4 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '2\n8\n1 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '2\n3\n2 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '2\n6\n1 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '2\n7\n1 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', '2\n3\n6 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n']

def _gen_1834a(rng: random.Random) -> list[str]:
    return ['3\n3\n0 1 0\n4\n0 1 1 0\n2\n1 1\n', '1\n3\n0 1 0\n', '1\n4\n0 1 1 0\n', '1\n2\n1 1\n', '1\n5\n0 0 0 0 0\n', '3\n3\n3 1 0\n4\n0 1 1 0\n2\n1 1\n', '3\n3\n0 5 0\n4\n0 1 1 0\n2\n1 1\n', '3\n3\n5 1 0\n4\n0 1 1 0\n2\n1 1\n', '3\n3\n0 1 0\n5\n0 1 1 0\n2\n1 1\n', '3\n3\n2 1 0\n4\n0 1 1 0\n2\n1 1\n', '3\n3\n0 4 0\n4\n0 1 1 0\n2\n1 1\n']

def _gen_567a(rng: random.Random) -> list[str]:
    return ['3\n2 5\n-3 5\n0 2\n', '1\n2 5\n', '1\n-3 5\n', '1\n0 2\n', '1\n-5 10\n', '1\n1 1\n', '3\n4 5\n-3 5\n0 2\n', '3\n2 8\n-3 5\n0 2\n', '3\n2 5\n1 5\n0 2\n', '3\n2 10\n-3 5\n0 2\n', '3\n2 5\n-3 5\n1 2\n']

def _gen_102b(rng: random.Random) -> list[str]:
    return ['1234\n', '9\n', '99\n', '100\n', '12345\n', '999999999\n', '87\n', '6174\n', '1\n', '1236\n', '1237\n']

def _gen_82a(rng: random.Random) -> list[str]:
    return ['8\n', '1\n', '2\n', '3\n', '4\n', '5\n', '6\n', '7\n', '9\n', '10\n', '15\n']

def _gen_158a(rng: random.Random) -> list[str]:
    return ['8 5\n10 9 8 7 7 7 5 2\n', '5 3\n5 4 3 2 1\n', '10 1\n10 9 8 7 6 5 4 3 2 1\n', '3 2\n100 50 25\n', '4 2\n10 8 6 4\n', '8 7\n10 9 8 7 7 7 5 2\n', '8 5\n13 9 8 7 7 7 5 2\n', '8 5\n10 13 8 7 7 7 5 2\n', '13 5\n10 9 8 7 7 7 5 2\n', '8 5\n10 9 8 8 7 7 5 2\n', '8 5\n10 9 8 9 7 7 5 2\n']

def _gen_1931b(rng: random.Random) -> list[str]:
    return ['3\n2\n1 1\n3\n1 2 3\n4\n1 1 1 1\n', '1\n2\n1 1\n', '1\n3\n1 2 3\n', '1\n4\n1 1 1 1\n', '1\n5\n5 5 5 5 5\n', '3\n4\n1 1\n3\n1 2 3\n4\n1 1 1 1\n', '3\n2\n4 1\n3\n1 2 3\n4\n1 1 1 1\n', '3\n2\n5 1\n3\n1 2 3\n4\n1 1 1 1\n', '3\n2\n2 1\n3\n1 2 3\n4\n1 1 1 1\n', '3\n2\n1 1\n3\n1 2 3\n8\n1 1 1 1\n', '3\n2\n6 1\n3\n1 2 3\n4\n1 1 1 1\n']

def _gen_1833a(rng: random.Random) -> list[str]:
    return ['3\n7\nabababc\n5\naaaaa\n3\nabc\n', '1\n7\nabababc\n', '1\n5\naaaaa\n', '1\n3\nabc\n', '1\n4\nabcd\n', '3\n9\nabababc\n5\naaaaa\n3\nabc\n', '3\n7\nabababc\n8\naaaaa\n3\nabc\n', '3\n8\nabababc\n5\naaaaa\n3\nabc\n', '3\n7\nabababc\n7\naaaaa\n3\nabc\n', '3\n12\nabababc\n5\naaaaa\n3\nabc\n', '3\n7\nabababc\n6\naaaaa\n3\nabc\n']

def _gen_1926c(rng: random.Random) -> list[str]:
    return ['3\n3\n10\n100\n', '1\n3\n', '1\n10\n', '1\n100\n', '1\n5\n', '1\n7\n', '1\n11\n', '5\n3\n10\n100\n', '3\n3\n13\n100\n', '3\n3\n10\n104\n', '8\n3\n10\n100\n']

def _gen_2003a(rng: random.Random) -> list[str]:
    return ['3\nabc\nabb\naaa\n', '1\nabc\n', '1\nabb\n', '1\naaa\n', '1\nab\n', '1\nabcd\n', '5\nabc\nabb\naaa\n', '6\nabc\nabb\naaa\n', '7\nabc\nabb\naaa\n', '8\nabc\nabb\naaa\n', '4\nabc\nabb\naaa\n']

def _gen_1999b(rng: random.Random) -> list[str]:
    return ['2\n1 2\n3 4\n5 6\n7 8\n', '1\n1 2\n3 4\n', '1\n5 6\n7 8\n', '1\n2 3\n4 5\n', '2\n3 2\n3 4\n5 6\n7 8\n', '2\n1 2\n7 4\n5 6\n7 8\n', '2\n1 2\n3 9\n5 6\n7 8\n', '2\n1 2\n3 4\n6 6\n7 8\n', '2\n1 2\n3 4\n5 8\n7 8\n', '2\n1 2\n3 4\n5 6\n10 8\n', '2\n1 2\n3 4\n5 6\n7 12\n']

def _gen_2094b(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3\n4\n1 1 1 1\n', '1\n3\n1 2 3\n', '1\n4\n1 1 1 1\n', '1\n2\n5 10\n', '2\n5\n1 2 3\n4\n1 1 1 1\n', '2\n3\n4 2 3\n4\n1 1 1 1\n', '2\n8\n1 2 3\n4\n1 1 1 1\n', '2\n3\n1 2 3\n5\n1 1 1 1\n', '2\n3\n3 2 3\n4\n1 1 1 1\n', '2\n3\n5 2 3\n4\n1 1 1 1\n', '2\n3\n6 2 3\n4\n1 1 1 1\n']

def _gen_476b(rng: random.Random) -> list[str]:
    return ['++-+-\n+-+-+\n', '+-+-\n+-??\n', '+++\n??-\n', '+-\n?+\n', '++--\n+?-?\n', '+-++\n?-+?\n', '----\n????\n', '++++\n++++\n', '+-+-\n+-+-+\n']

def _gen_1097b(rng: random.Random) -> list[str]:
    return ['3\n120\n120\n120\n', '1\n90\n', '2\n180\n180\n', '4\n90\n90\n90\n90\n', '2\n45\n45\n', '3\n60\n60\n60\n', '1\n360\n', '2\n120\n120\n', '3\n30\n30\n30\n', '3\n122\n120\n120\n', '3\n123\n120\n120\n']

def _gen_688b(rng: random.Random) -> list[str]:
    return ['3\n1\n10\n99\n', '1\n1\n', '1\n10\n', '1\n99\n', '1\n11\n', '1\n101\n', '3\n3\n10\n99\n', '3\n1\n13\n99\n', '3\n1\n10\n103\n', '8\n1\n10\n99\n', '3\n2\n10\n99\n']

def _gen_2193a(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3\n4\n5 4 3 2\n', '1\n3\n1 2 3\n', '1\n4\n5 4 3 2\n', '1\n2\n10 1\n', '2\n5\n1 2 3\n4\n5 4 3 2\n', '2\n3\n4 2 3\n4\n5 4 3 2\n', '2\n8\n1 2 3\n4\n5 4 3 2\n', '2\n3\n1 2 3\n5\n5 4 3 2\n', '2\n3\n1 2 3\n4\n7 4 3 2\n', '2\n3\n1 2 3\n7\n5 4 3 2\n', '2\n7\n1 2 3\n4\n5 4 3 2\n']

def _gen_2063a(rng: random.Random) -> list[str]:
    return ['3\n2 3\n6 9\n5 7\n', '1\n2 3\n', '1\n6 9\n', '1\n5 7\n', '1\n4 6\n', '1\n3 5\n', '3\n4 3\n6 9\n5 7\n', '6\n2 3\n6 9\n5 7\n', '3\n2 3\n10 9\n5 7\n', '3\n2 3\n6 14\n5 7\n', '3\n2 3\n6 9\n6 7\n']

def _gen_1916b(rng: random.Random) -> list[str]:
    return ['3\n4\n5\n6\n', '1\n4\n', '1\n5\n', '1\n6\n', '1\n8\n', '1\n9\n', '1\n10\n', '3\n6\n5\n6\n', '3\n4\n8\n6\n', '3\n4\n5\n10\n', '8\n4\n5\n6\n']

def _gen_1547a(rng: random.Random) -> list[str]:
    return ['3\n1 1 3 1\n1 1 1 3\n2 2 3 3\n', '1\n1 1 3 1\n', '1\n1 1 1 3\n', '1\n2 2 3 3\n', '1\n0 0 1 1\n', '3\n3 1 3 1\n1 1 1 3\n2 2 3 3\n', '3\n4 1 3 1\n1 1 1 3\n2 2 3 3\n', '7\n1 1 3 1\n1 1 1 3\n2 2 3 3\n', '3\n6 1 3 1\n1 1 1 3\n2 2 3 3\n', '3\n2 1 3 1\n1 1 1 3\n2 2 3 3\n', '3\n1 1 3 1\n1 1 1 3\n7 2 3 3\n']

def _gen_1704b(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3\n4\n1 1 1 1\n', '1\n3\n1 2 3\n', '1\n4\n1 1 1 1\n', '1\n2\n4 4\n', '1\n5\n1 1 1 1 1\n', '2\n5\n1 2 3\n4\n1 1 1 1\n', '2\n3\n4 2 3\n4\n1 1 1 1\n', '2\n8\n1 2 3\n4\n1 1 1 1\n', '2\n3\n1 2 3\n5\n1 1 1 1\n', '2\n3\n3 2 3\n4\n1 1 1 1\n', '2\n3\n5 2 3\n4\n1 1 1 1\n']

def _gen_1859a(rng: random.Random) -> list[str]:
    return ['2\n3\n2 4 8\n4\n2 2 2 2\n', '1\n3\n2 4 8\n', '1\n4\n2 2 2 2\n', '1\n2\n6 9\n', '1\n3\n3 5 7\n', '2\n5\n2 4 8\n4\n2 2 2 2\n', '2\n3\n2 8 8\n4\n2 2 2 2\n', '2\n3\n2 4 13\n4\n2 2 2 2\n', '2\n3\n2 5 8\n4\n2 2 2 2\n']

def _gen_1485a(rng: random.Random) -> list[str]:
    return ['3\n9 3\n3 9\n9 3\n', '1\n9 3\n', '1\n3 9\n', '1\n12 4\n', '1\n7 2\n', '3\n11 3\n3 9\n9 3\n', '3\n14 3\n3 9\n9 3\n', '3\n10 3\n3 9\n9 3\n', '3\n13 3\n3 9\n9 3\n', '3\n12 3\n3 9\n9 3\n']

def _gen_1929a(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3\n4\n1 1 1 1\n', '1\n3\n1 2 3\n', '1\n4\n1 1 1 1\n', '1\n5\n1 2 3 4 5\n', '2\n3\n4 2 3\n4\n1 1 1 1\n', '2\n3\n3 2 3\n4\n1 1 1 1\n', '2\n3\n5 2 3\n4\n1 1 1 1\n', '2\n3\n6 2 3\n4\n1 1 1 1\n']

def _gen_2132b(rng: random.Random) -> list[str]:
    return ['3\na1b2c3\nxyz\n12345\n', '1\na1b2c3\n', '1\nxyz\n', '1\n12345\n', '1\n0\n', '1\na\n', '3\na3b2c3\nxyz\n12345\n', '3\na1b5c3\nxyz\n12345\n', '7\na1b2c3\nxyz\n12345\n', '3\na1b2c3\nxyz\n12350\n', '4\na1b2c3\nxyz\n12345\n']

def _gen_2236a(rng: random.Random) -> list[str]:
    return ['3\n2 3\n4 5\n1 1\n', '1\n2 3\n', '1\n4 5\n', '1\n1 1\n', '1\n10 10\n', '3\n4 3\n4 5\n1 1\n', '3\n2 3\n8 5\n1 1\n', '3\n2 3\n4 10\n1 1\n', '3\n2 3\n4 5\n2 1\n', '3\n2 3\n4 5\n3 1\n', '3\n6 3\n4 5\n1 1\n']

def _gen_1676e(rng: random.Random) -> list[str]:
    return ['1\n5 3\n1 2 3 4 5\n3 6 10\n', '1\n3 2\n1 2 3\n2 3\n', '1\n4 3\n1 1 2 2\n1 2 4\n', '1\n5 2\n1 2 3 4 5\n3 6\n', '1\n5 6\n1 2 3 4 5\n3 6 10\n', '1\n5 3\n1 7 3 4 5\n3 6 10\n', '1\n5 4\n1 2 3 4 5\n3 6 10\n', '1\n5 3\n1 2 3 6 5\n3 6 10\n', '1\n5 7\n1 2 3 4 5\n3 6 10\n', '1\n5 3\n1 2 3 4 5\n3 11 10\n', '1\n5 3\n1 2 3 4 5\n3 6 11\n']

def _gen_1506a(rng: random.Random) -> list[str]:
    return ['1\n2 2\n1 2\n3 4\n2\n1 1\n2 2\n', '1\n3 3\n1 2 3\n4 5 6\n7 8 9\n1\n2 2\n', '1\n1 1\n5\n1\n1 1\n', '1\n2 2\n1 2\n3 4\n1\n1 1\n', '1\n2 2\n1 2\n4 4\n2\n1 1\n2 2\n', '1\n2 2\n1 2\n3 6\n2\n1 1\n2 2\n', '1\n2 2\n1 2\n6 4\n2\n1 1\n2 2\n', '1\n2 2\n1 2\n3 8\n2\n1 1\n2 2\n', '1\n2 2\n1 2\n8 4\n2\n1 1\n2 2\n', '1\n2 2\n1 2\n3 5\n2\n1 1\n2 2\n', '1\n2 2\n1 2\n5 4\n2\n1 1\n2 2\n']

def _gen_1077a(rng: random.Random) -> list[str]:
    return ['3\n5 2 11\n5 2 15\n5 3 12\n', '1\n5 2 11\n', '1\n5 2 15\n', '1\n5 3 12\n', '1\n3 1 5\n', '3\n7 2 11\n5 2 15\n5 3 12\n', '3\n5 5 11\n5 2 15\n5 3 12\n', '3\n5 2 15\n5 2 15\n5 3 12\n', '3\n10 2 11\n5 2 15\n5 3 12\n', '3\n5 3 11\n5 2 15\n5 3 12\n', '3\n5 2 11\n5 2 17\n5 3 12\n']

def _gen_1335b(rng: random.Random) -> list[str]:
    return ['3\n3 1 2\n5 2 3\n100 1 2\n', '1\n3 1 2\n', '1\n5 2 3\n', '1\n100 1 2\n', '1\n7 3 4\n', '3\n3 4 2\n5 2 3\n100 1 2\n', '3\n3 1 6\n5 2 3\n100 1 2\n', '3\n3 1 2\n10 2 3\n100 1 2\n', '3\n3 1 3\n5 2 3\n100 1 2\n', '3\n3 1 2\n5 2 3\n103 1 2\n', '3\n3 5 2\n5 2 3\n100 1 2\n']

def _gen_1849b(rng: random.Random) -> list[str]:
    return ['1\n3 1\n3 2 1\n', '1\n4 2\n4 3 2 1\n', '1\n5 1\n5 4 3 2 1\n', '1\n3 3\n1 2 3\n', '1\n2 1\n2 1\n', '1\n3 1\n3 7 1\n', '1\n3 1\n3 3 1\n', '1\n3 1\n3 4 1\n', '1\n3 1\n3 5 1\n', '1\n3 1\n3 6 1\n']

def _gen_1744c(rng: random.Random) -> list[str]:
    return ['2\n5\nrrggr\n4\nrrrr\n', '1\n5\nrrggr\n', '1\n4\nrrrr\n', '1\n3\nrrg\n', '1\n6\nrrrrrr\n', '2\n7\nrrggr\n4\nrrrr\n', '2\n5\nrrggr\n7\nrrrr\n', '2\n10\nrrggr\n4\nrrrr\n', '2\n5\nrrggr\n5\nrrrr\n', '2\n8\nrrggr\n4\nrrrr\n', '2\n5\nrrggr\n8\nrrrr\n']

def _gen_368b(rng: random.Random) -> list[str]:
    return ['10 5\n1 2 3 4 5 6 7 8 9 10\n1 3 6 8 10\n', '5 3\n1 2 3 4 5\n2 4 5\n', '3 2\n1 2 3\n1 3\n', '4 2\n10 20 30 40\n3 4\n', '10 7\n1 2 3 4 5 6 7 8 9 10\n1 3 6 8 10\n', '10 5\n1 6 3 4 5 6 7 8 9 10\n1 3 6 8 10\n', '10 5\n1 2 8 4 5 6 7 8 9 10\n1 3 6 8 10\n', '10 5\n1 2 3 5 5 6 7 8 9 10\n1 3 6 8 10\n', '10 5\n1 2 3 4 5 9 7 8 9 10\n1 3 6 8 10\n', '10 5\n1 2 3 4 5 6 11 8 9 10\n1 3 6 8 10\n', '10 5\n1 2 3 4 5 6 7 13 9 10\n1 3 6 8 10\n']

def _gen_1840c(rng: random.Random) -> list[str]:
    return ['2\n3 2 1\n101\n4 2 2\n1100\n', '1\n2 1 1\n01\n', '1\n4 2 1\n1010\n', '1\n3 1 1\n111\n', '2\n3 2 5\n101\n4 2 2\n1100\n', '2\n3 2 1\n106\n4 2 2\n1100\n', '2\n3 2 1\n101\n4 2 2\n1104\n', '2\n3 2 4\n101\n4 2 2\n1100\n', '2\n3 2 1\n105\n4 2 2\n1100\n', '2\n3 2 1\n101\n4 2 2\n1103\n', '2\n3 2 3\n101\n4 2 2\n1100\n']

def _gen_1859b(rng: random.Random) -> list[str]:
    return ['2\n3\n1 2 3\n2\n5 10\n', '1\n3\n1 2 3\n', '1\n2\n5 10\n', '1\n4\n1 2 3 4\n', '2\n5\n1 2 3\n2\n5 10\n', '2\n3\n4 2 3\n2\n5 10\n', '2\n8\n1 2 3\n2\n5 10\n', '2\n3\n1 2 3\n2\n7 10\n', '2\n3\n1 2 3\n2\n5 13\n', '2\n3\n2 2 3\n2\n5 10\n', '2\n6\n1 2 3\n2\n5 10\n']

def _gen_1915d(rng: random.Random) -> list[str]:
    return ['2\n3\naAa\n4\naBaC\n', '1\n3\naAa\n', '1\n4\naBaC\n', '1\n2\naB\n', '1\n5\naBaBa\n', '2\n5\naAa\n4\naBaC\n', '2\n3\naAa\n7\naBaC\n', '2\n8\naAa\n4\naBaC\n', '2\n3\naAa\n5\naBaC\n', '2\n6\naAa\n4\naBaC\n', '2\n3\naAa\n8\naBaC\n']

def _build():
    specs = []
    def reg(problem_id, summary, sample_in, solve, alt, mutants, generate, **kw):
        out = solve(sample_in)
        specs.append(make_spec(problem_id, summary=summary, samples=({'input': sample_in, 'output': out},), solve=solve, alt=alt, mutants=mutants, generate=generate, **kw))

    reg('1676B', 'Min candies eaten to equalize boxes.', '5\n5\n1 2 3 4 5\n2\n0 0\n3\n4 4 4\n4\n3 2 1 2\n4\n1000 3 4 1000\n', s_1676b, a_1676b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1676b, family='greedy', checker='exact')
    reg('1955A', 'Min yogurt cost with promo pairs.', '4\n5 2 3\n4 2 3\n3 4 5\n1 100 1\n', s_1955a, a_1955a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1955a, family='math', checker='exact')
    reg('1915C', 'Square total area YES/NO.', '3\n3\n1 1 1\n4\n1 1 1 2\n2\n1 1\n', s_1915c, a_1915c, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1915c, family='math', checker='tokens_ci')
    reg('1475B', 'Represent n as 2020a+2021b.', '5\n1\n4041\n4042\n10000\n123456789\n19981998\n', s_1475b, a_1475b, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1475b, family='math', checker='tokens_ci')
    reg('1368A', 'Doublings until a reaches b.', '3\n1 5\n11 47\n3 998244353\n', s_1368a, a_1368a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1368a, family='simulation', checker='exact')
    reg('1850B', 'Winning submission index.', '2\n3\n1 2 3 4 5 6 7 8 9 10\n1 2 3 4 5 6 7 8 9 9\n5 5 5 5 5 5 5 5 5 5\n2\n0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0\n', s_1850b, a_1850b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1850b, family='implementation', checker='exact')
    reg('1968A', 'Always YES maximize.', '3\n1\n2\n3\n', s_1968a, a_1968a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1968a, family='constructive', checker='tokens_ci')
    reg('2137A', 'Collatz reaches 1.', '3\n1\n2\n3\n', s_2137a, a_2137a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_2137a, family='math', checker='tokens_ci')
    reg('1633A', 'Divisible by 7 without digit 7.', '3\n1\n2\n3\n', s_1633a, a_1633a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1633a, family='math', checker='tokens_ci')
    reg('1914A', 'First unsolved problem letter.', '3\nABCDEFGHIJKL\nACEGIKMO\nACEG\n', s_1914a, a_1914a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1914a, family='implementation', checker='exact')
    reg('2051A', 'Min cost for triple-wall rooms.', '3\n5 3 2\n6 2 3\n8 4 2\n', s_2051a, a_2051a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_2051a, family='math', checker='exact')
    reg('2008B', 'String equals two halves.', '3\naaba\naa\nab\n', s_2008b, a_2008b, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_2008b, family='strings', checker='tokens_ci')
    reg('1976A', 'Valid password check.', '5\nAb1\nabc\nAbC\n12345678\naA1aaaaa\n', s_1976a, a_1976a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1976a, family='strings', checker='tokens_ci')
    reg('1918A', 'Wall with 2x3 bricks.', '3\n6\n5\n4\n', s_1918a, a_1918a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1918a, family='math', checker='tokens_ci')
    reg('1843B', 'Max mood subarray.', '3\nLRL\nLRLLR\nLLLL\n', s_1843b, a_1843b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1843b, family='dp', checker='exact')
    reg('1691A', 'Max odd-even pairs removed.', '3\n3\n1 2 3\n3\n2 4 6\n2\n1 1\n', s_1691a, a_1691a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1691a, family='greedy', checker='exact')
    reg('1849A', 'Max sandwiches.', '3\n2 1 1 1\n10 1 2 3\n100 50 50 50\n', s_1849a, a_1849a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1849a, family='greedy', checker='exact')
    reg('1256A', 'Pay with 1 and 4 coins.', '4\n13 3 3\n8 2 3\n100 1 1\n1 1 1\n', s_1256a, a_1256a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1256a, family='math', checker='tokens_ci')
    reg('1914B', 'Days to prepare n problems.', '4\n1\n2\n3\n4\n', s_1914b, a_1914b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1914b, family='greedy', checker='exact')
    reg('2218A', 'Divisible by 67.', '3\n67\n68\n134\n', s_2218a, a_2218a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_2218a, family='math', checker='tokens_ci')
    reg('1853A', 'Min increments to desort.', '4\n3\n1 2 3\n2\n1 1\n4\n1 2 3 4\n5\n1 1 1 1 1\n', s_1853a, a_1853a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1853a, family='greedy', checker='exact')
    reg('1353B', 'Max sum after k cross-swaps.', '5\n2 1\n1 2\n3 4\n5 5\n5 5 6 6 5\n1 2 5 4 3\n5 3\n1 2 3 4 5\n10 9 10 10 9\n4 0\n2 2 4 3\n2 4 2 3\n4 4\n1 2 2 1\n4 4 5 4\n', s_1353b, a_1353b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1353b, family='greedy', checker='exact')
    reg('1883B', 'Palindrome after k deletions.', '7\n4 1\naba\n3 1\naaa\n2 1\nab\n4 2\nbaba\n4 2\nbabb\n4 2\nbabt\n4 2\nbabu\n', s_1883b, a_1883b, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1883b, family='strings', checker='tokens_ci')
    reg('1881A', 'Min doublings until substring.', '2\n1 5\na\naaaaa\n5 5\neforc\nforce\n', s_1881a, a_1881a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1881a, family='strings', checker='exact')
    reg('1837B', 'Longest comparison substring.', '3\nabb\naaaa\naaaaa\n', s_1837b, a_1837b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1837b, family='strings', checker='exact')
    reg('1845A', 'Sum k positives avoiding x.', '3\n5 2 3\n5 2 2\n5 1 2\n', s_1845a, a_1845a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1845a, family='math', checker='tokens_ci')
    reg('1399B', 'Gifts fixing operations.', '2\n3\n1 2 3\n1 2 3\n3\n1 1 1\n1 1 1\n', s_1399b, a_1399b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1399b, family='greedy', checker='exact')
    reg('1834A', 'Make binary array all ones.', '3\n3\n0 1 0\n4\n0 1 1 0\n2\n1 1\n', s_1834a, a_1834a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1834a, family='greedy', checker='exact')
    reg('567A', 'Lineland mail delivery time.', '3\n2 5\n-3 5\n0 2\n', s_567a, a_567a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_567a, family='math', checker='exact')
    reg('102B', 'Sum digits until one digit.', '1234\n', s_102b, a_102b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_102b, family='math', checker='exact')
    reg('82A', 'Double cola queue position.', '8\n', s_82a, a_82a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_82a, family='math', checker='exact')
    reg('158A', 'Next round participants.', '8 5\n10 9 8 7 7 7 5 2\n', s_158a, a_158a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_158a, family='implementation', checker='exact')
    reg('1931B', 'Make array equal with ops.', '3\n2\n1 1\n3\n1 2 3\n4\n1 1 1 1\n', s_1931b, a_1931b, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1931b, family='greedy', checker='tokens_ci')
    reg('1833A', 'Distinct musical pairs.', '3\n7\nabababc\n5\naaaaa\n3\nabc\n', s_1833a, a_1833a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1833a, family='strings', checker='exact')
    reg('1926C', 'Sum of digit sums 1..n.', '3\n3\n10\n100\n', s_1926c, a_1926c, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1926c, family='math', checker='exact')
    reg('2003A', 'Good string without triple.', '3\nabc\nabb\naaa\n', s_2003a, a_2003a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_2003a, family='strings', checker='tokens_ci')
    reg('1999B', 'Card game max product.', '2\n1 2\n3 4\n5 6\n7 8\n', s_1999b, a_1999b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1999b, family='games', checker='exact')
    reg('2094B', 'Bobritto bandito sum minus max.', '2\n3\n1 2 3\n4\n1 1 1 1\n', s_2094b, a_2094b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_2094b, family='greedy', checker='exact')
    reg('476B', 'Dreamoon WiFi probability.', '++-+-\n+-+-+\n', s_476b, a_476b, {'m1': lambda s: '0.000000000\n', 'm2': lambda s: '1.000000000\n'}, _gen_476b, family='combinatorics', checker='float')
    reg('1097B', 'Angle sum multiple of 360.', '3\n120\n120\n120\n', s_1097b, a_1097b, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1097b, family='bitmask', checker='tokens_ci')
    reg('688B', 'Lovely palindrome >= n.', '3\n1\n10\n99\n', s_688b, a_688b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_688b, family='strings', checker='exact')
    reg('2193A', 'Array range.', '2\n3\n1 2 3\n4\n5 4 3 2\n', s_2193a, a_2193a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_2193a, family='math', checker='exact')
    reg('2063A', 'Minimal coprime answer.', '3\n2 3\n6 9\n5 7\n', s_2063a, a_2063a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_2063a, family='math', checker='exact')
    reg('1916B', 'Composite with two divisors.', '3\n4\n5\n6\n', s_1916b, a_1916b, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1916b, family='number_theory', checker='tokens_ci')
    reg('1547A', 'Shortest path with obstacle.', '3\n1 1 3 1\n1 1 1 3\n2 2 3 3\n', s_1547a, a_1547a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1547a, family='geometry', checker='exact')
    reg('1704B', 'Luke foodie eating days.', '2\n3\n1 2 3\n4\n1 1 1 1\n', s_1704b, a_1704b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1704b, family='greedy', checker='exact')
    reg('1859A', 'United we stand partition.', '2\n3\n2 4 8\n4\n2 2 2 2\n', s_1859a, a_1859a, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1859a, family='number_theory', checker='tokens_ci')
    reg('1485A', 'Add and divide operations.', '3\n9 3\n3 9\n9 3\n', s_1485a, a_1485a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1485a, family='math', checker='exact')
    reg('1929A', 'Beautiful array operations.', '2\n3\n1 2 3\n4\n1 1 1 1\n', s_1929a, a_1929a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1929a, family='greedy', checker='exact')
    reg('2132B', 'Count digits in string.', '3\na1b2c3\nxyz\n12345\n', s_2132b, a_2132b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_2132b, family='implementation', checker='exact')
    reg('2236A', 'Games on train cells.', '3\n2 3\n4 5\n1 1\n', s_2236a, a_2236a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_2236a, family='math', checker='exact')
    reg('1676E', 'Eating queries prefix sum.', '1\n5 3\n1 2 3 4 5\n3 6 10\n', s_1676e, a_1676e, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1676e, family='binary_search', checker='exact')
    reg('1506A', 'Strange table queries.', '1\n2 2\n1 2\n3 4\n2\n1 1\n2 2\n', s_1506a, a_1506a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1506a, family='implementation', checker='exact')
    reg('1077A', 'Frog jumping count.', '3\n5 2 11\n5 2 15\n5 3 12\n', s_1077a, a_1077a, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1077a, family='math', checker='exact')
    reg('1335B', 'Construct the string count.', '3\n3 1 2\n5 2 3\n100 1 2\n', s_1335b, a_1335b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1335b, family='constructive', checker='exact')
    reg('1849B', 'Monster passing order.', '1\n3 1\n3 2 1\n', s_1849b, a_1849b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1849b, family='greedy', checker='tokens')
    reg('1744C', 'Traffic light green streak.', '2\n5\nrrggr\n4\nrrrr\n', s_1744c, a_1744c, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1744c, family='strings', checker='exact')
    reg('368B', 'Suffix sums queries.', '10 5\n1 2 3 4 5 6 7 8 9 10\n1 3 6 8 10\n', s_368b, a_368b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_368b, family='prefix_sums', checker='exact')
    reg('1840C', 'Ski resort max rating.', '2\n3 2 1\n101\n4 2 2\n1100\n', s_1840c, a_1840c, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1840c, family='brute_force', checker='exact')
    reg('1859B', 'Olya game with arrays.', '2\n3\n1 2 3\n2\n5 10\n', s_1859b, a_1859b, {'m1': lambda s: '0\n', 'm2': lambda s: '1\n'}, _gen_1859b, family='games', checker='exact')
    reg('1915D', 'Unnatural language pattern.', '2\n3\naAa\n4\naBaC\n', s_1915d, a_1915d, {'m1': lambda s: 'YES\n', 'm2': lambda s: 'NO\n'}, _gen_1915d, family='strings', checker='tokens_ci')
    return specs


SPECS = _build()

_KEEP = ['1676B', '1955A', '1915C', '1475B', '1368A', '1850B', '1968A', '2137A', '1633A', '1914A', '2051A', '2008B', '1976A', '1918A', '1843B', '1691A', '1849A', '1256A', '1914B', '2218A', '1853A', '1353B', '1883B', '1881A', '1837B', '1845A', '1399B', '1834A', '567A', '102B', '82A', '158A', '1931B', '1833A', '1926C', '2003A', '1999B', '2094B', '476B', '1097B', '688B', '2193A', '2063A', '1916B', '1547A', '1704B', '1859A', '1485A', '1929A', '2132B', '2236A', '1676E', '1506A', '1077A', '1335B', '1849B', '1744C', '368B', '1840C', '1859B', '1915D']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
