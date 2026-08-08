"""Dual-oracle specs from missing_chunk_0.json (70 candidates).

Skipped denylist: 1367B,1374A,1374C,1433A,1520D,1619A,1722A,313A,474B,490A,749A,80A
Skipped multi-answer: 472A,1343B,1343A,1890A,1862B,1859A,1837A,584A,1783A,1389A,1462A,1831A,233A
"""

from __future__ import annotations

from collections import Counter

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no

SPECS: list = []


def add(**kw) -> None:
    SPECS.append(make_spec(**kw))


def _tcases(stdin: str) -> tuple[int, list[str]]:
    ls = lines(stdin)
    return int(ls[0]), ls[1:]


# ── 520A Pangram (bulk_00) ───────────────────────────────────────────────────
add(
    problem_id="520A",
    summary="Is the string a pangram (all 26 letters, case-insensitive)?",
    samples=(
        {"input": "12\ntoosmallword\n", "output": "NO\n"},
        {"input": "35\nTheQuickBrownFoxJumpsOverTheLazyDog\n", "output": "YES\n"},
    ),
    solve=lambda s: yes_no(len({c.lower() for c in lines(s)[1] if c.isalpha()}) == 26),
    alt=lambda s: yes_no(set("abcdefghijklmnopqrstuvwxyz") <= {c.lower() for c in lines(s)[1]}),
    mutants={
        "len26": lambda s: yes_no(len(lines(s)[1]) >= 26),
        "vowels": lambda s: yes_no(len({c.lower() for c in lines(s)[1] if c.lower() in "aeiou"}) >= 5),
    },
    generate=lambda rng: [
        "12\ntoosmallword\n",
        "35\nTheQuickBrownFoxJumpsOverTheLazyDog\n",
        "26\nabcdefghijklmnopqrstuvwxyz\n",
        "25\nabcdefghijklmnopqrstuvwxy\n",
        "3\nabc\n",
        "26\nABCDEFGHIJKLMNOPQRSTUVWXYZ\n",
        "30\naaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
        "27\nabcABCDEFGHIJKLMNOPQRSTUVWXYz\n",
        "10\nabcdefghij\n",
        "16\npackmyboxwithfivedozenliquorjugs\n",
    ],
    family="strings",
    checker="tokens_ci",
)


def _158b(stdin: str) -> str:
    groups = list(map(int, lines(stdin)[1].split()))
    cnt = [0, 0, 0, 0, 0]
    for g in groups:
        cnt[g] += 1
    taxis = cnt[4] + cnt[3]
    ones = max(0, cnt[1] - cnt[3])
    taxis += cnt[2] // 2
    if cnt[2] % 2 == 1:
        taxis += 1
        ones = max(0, ones - 2)
    taxis += (ones + 3) // 4
    return f"{taxis}\n"


def _158b_alt(stdin: str) -> str:
    groups = list(map(int, lines(stdin)[1].split()))
    c1, c2, c3, c4 = groups.count(1), groups.count(2), groups.count(3), groups.count(4)
    taxis = c4 + c3
    rem = max(0, c1 - c3)
    taxis += c2 // 2
    if c2 % 2 == 1:
        taxis += 1
        rem = max(0, rem - 2)
    taxis += (rem + 3) // 4
    return f"{taxis}\n"


add(
    problem_id="158B",
    summary="Minimum taxis (capacity 4) for child groups of sizes 1..4.",
    samples=({"input": "5\n1 2 4 3 3\n", "output": "4\n"},),
    solve=_158b,
    alt=_158b_alt,
    mutants={
        "sum_only": lambda s: f"{sum(map(int, lines(s)[1].split()))}\n",
        "no_pair": lambda s: (
            lambda g: f"{g.count(4) + g.count(3) + g.count(2) + (max(0, g.count(1) - g.count(3)) + 3) // 4}\n"
        )(list(map(int, lines(s)[1].split()))),
    },
    generate=lambda rng: [
        "5\n1 2 4 3 3\n",
        "8\n2 3 4 4 2 1 3 1\n",
        "1\n4\n",
        "1\n1\n",
        "4\n2 2 2 2\n",
        "3\n2 1 1\n",
        "6\n1 1 1 1 1 1\n",
        "2\n3 3\n",
        "7\n4 4 4 4 1 1 1\n",
        "10\n2 2 2 2 2 2 2 2 2 2\n",
    ],
    family="greedy",
)


def _363b(stdin: str) -> str:
    n, k = map(int, lines(stdin)[0].split())
    h = list(map(int, lines(stdin)[1].split()))
    best_sum = sum(h[:k])
    best_i = 1
    cur = best_sum
    for i in range(2, n - k + 2):
        cur += h[i + k - 2] - h[i - 2]
        if cur < best_sum:
            best_sum, best_i = cur, i
    return f"{best_i}\n"


def _363b_alt(stdin: str) -> str:
    n, k = map(int, lines(stdin)[0].split())
    h = list(map(int, lines(stdin)[1].split()))
    pre = [0]
    for x in h:
        pre.append(pre[-1] + x)
    best_sum, best_i = None, 1
    for j in range(1, n - k + 2):
        s = pre[j + k - 1] - pre[j - 1]
        if best_sum is None or s < best_sum:
            best_sum, best_i = s, j
    return f"{best_i}\n"


add(
    problem_id="363B",
    summary="Smallest 1-indexed start of k consecutive planks with minimum height sum.",
    samples=({"input": "7 3\n1 2 6 1 1 7 1\n", "output": "3\n"},),
    solve=_363b,
    alt=_363b_alt,
    mutants={
        "always_first": lambda s: "1\n",
        "max_window": lambda s: (
            lambda n, k, h: f"{max(range(1, n - k + 2), key=lambda j: sum(h[j - 1 : j - 1 + k]))}\n"
        )(*map(int, lines(s)[0].split()), list(map(int, lines(s)[1].split()))),
    },
    generate=lambda rng: [
        "7 3\n1 2 6 1 1 7 1\n",
        "3 1\n5 1 3\n",
        "5 2\n1 2 3 4 5\n",
        "4 4\n1 1 1 1\n",
        "6 3\n3 3 3 1 1 1\n",
        "10 4\n1 2 3 4 5 6 7 8 9 10\n",
        "8 2\n9 1 1 1 1 1 1 9\n",
        "5 5\n2 2 2 2 2\n",
        "9 3\n4 4 4 1 1 1 1 1 1\n",
    ],
    family="dp",
)


def _1850d(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n, k = map(int, rows[idx].split())
        idx += 1
        a = sorted(map(int, rows[idx].split()))
        idx += 1
        best = 1
        start = 0
        for end in range(n):
            if end > 0 and a[end] - a[end - 1] > k:
                start = end
            best = max(best, end - start + 1)
        out.append(str(n - best))
    return "\n".join(out) + "\n"


def _1850d_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n, k = map(int, rows[idx].split())
        idx += 1
        a = sorted(map(int, rows[idx].split()))
        idx += 1
        mx = 0
        i = 0
        for j in range(n):
            if j > 0 and a[j] - a[j - 1] > k:
                i = j
            mx = max(mx, j - i + 1)
        out.append(str(n - mx))
    return "\n".join(out) + "\n"


add(
    problem_id="1850D",
    summary="Minimum removals so remaining difficulties can be ordered with adjacent gap <= k.",
    samples=(
        {
            "input": "7\n5 1\n1 2 4 5 6\n1 2\n10\n8 3\n17 3 1 20 12 5 17 12\n4 2\n2 4 6 8\n5 3\n2 3 19 10 8\n3 4\n1 10 5\n8 1\n8 3 1 4 5 10 7 3\n",
            "output": "2\n0\n5\n0\n3\n1\n4\n",
        },
    ),
    solve=_1850d,
    alt=_1850d_alt,
    mutants={"keep_all": lambda s: "0\n" * int(lines(s)[0]), "remove_one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "7\n5 1\n1 2 4 5 6\n1 2\n10\n8 3\n17 3 1 20 12 5 17 12\n4 2\n2 4 6 8\n5 3\n2 3 19 10 8\n3 4\n1 10 5\n8 1\n8 3 1 4 5 10 7 3\n",
        "1\n3 1\n1 2 3\n",
        "1\n4 2\n1 2 3 4\n",
        "1\n2 5\n1 10\n",
        "1\n5 1\n1 1 1 1 1\n",
        "1\n6 2\n1 3 5 7 9 11\n",
        "1\n4 3\n1 5 9 13\n",
        "1\n3 10\n1 2 100\n",
        "1\n1 1\n5\n",
    ],
    family="greedy",
)


def _500a(stdin: str) -> str:
    n, t = map(int, lines(stdin)[0].split())
    a = list(map(int, lines(stdin)[1].split()))
    cur = 1
    seen: set[int] = set()
    while cur != t:
        if cur < 1 or cur > n or cur in seen:
            return "NO\n"
        seen.add(cur)
        cur = a[cur - 1]
    return "YES\n"


def _500a_alt(stdin: str) -> str:
    n, t = map(int, lines(stdin)[0].split())
    a = list(map(int, lines(stdin)[1].split()))
    cur = 1
    for _ in range(n + 2):
        if cur == t:
            return "YES\n"
        if cur < 1 or cur > n:
            return "NO\n"
        cur = a[cur - 1]
    return "NO\n"


add(
    problem_id="500A",
    summary="Can you reach house t from 1 following one-way links a[i]?",
    samples=(
        {"input": "4 2\n1 1 4 2\n", "output": "NO\n"},
        {"input": "3 3\n2 3 1\n", "output": "YES\n"},
    ),
    solve=_500a,
    alt=_500a_alt,
    mutants={"always_yes": lambda s: "YES\n", "always_no": lambda s: "NO\n"},
    generate=lambda rng: [
        "4 2\n1 1 4 2\n",
        "8 5\n1 1 3 2 5 4 7 6\n",
        "2 2\n2 1\n",
        "3 3\n2 3 1\n",
        "1 1\n1\n",
        "5 5\n2 3 4 5 5\n",
        "6 1\n2 2 2 2 2 2\n",
        "4 4\n2 3 4 4\n",
        "7 3\n2 3 4 5 6 7 3\n",
    ],
    family="graphs",
    checker="tokens_ci",
)

def _742a(stdin: str) -> str:
    n = int(lines(stdin)[0])
    if n == 0:
        return "1\n"
    return f"{[8, 4, 2, 6][(n - 1) % 4]}\n"


def _742a_alt(stdin: str) -> str:
    n = int(lines(stdin)[0])
    if n == 0:
        return "1\n"
    d = 8
    for _ in range((n - 1) % 4):
        d = (d * 8) % 10
    return f"{d}\n"


add(
    problem_id="742A",
    summary="Last decimal digit of 1378^n; n=0 gives 1; for n>0 cycle is 8,4,2,6.",
    samples=(
        {"input": "0\n", "output": "1\n"},
        {"input": "1\n", "output": "8\n"},
        {"input": "4\n", "output": "6\n"},
        {"input": "5\n", "output": "8\n"},
    ),
    solve=_742a,
    alt=_742a_alt,
    mutants={"always8": lambda s: "8\n", "mod10": lambda s: f"{int(lines(s)[0]) % 10}\n"},
    generate=lambda rng: [f"{n}\n" for n in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 1000]],
    family="math",
)


add(
    problem_id="2044B",
    summary="Swap the case of every letter in each string.",
    samples=({"input": "4\nabcd\ncf\nxyz\nbell\n", "output": "ABCD\nCF\nXYZ\nBELL\n"},),
    solve=lambda s: "\n".join(line.swapcase() for line in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join(
        "".join(ch.lower() if ch.isupper() else ch.upper() if ch.islower() else ch for ch in line)
        for line in lines(s)[1:]
    )
    + "\n",
    mutants={
        "upper": lambda s: "\n".join(line.upper() for line in lines(s)[1:]) + "\n",
        "lower": lambda s: "\n".join(line.lower() for line in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "4\nabcd\ncf\nxyz\nbell\n",
        "1\nHello\n",
        "2\nAa\nBb\n",
        "1\nX\n",
        "3\nabc\nDEF\nGhI\n",
        "2\naA\nzZ\n",
        "1\nMixedCase\n",
        "1\ntest\n",
    ],
    family="strings",
)


def _476a(stdin: str) -> str:
    n, m = map(int, lines(stdin)[0].split())
    lo = (n + 1) // 2
    if lo % m:
        lo += m - lo % m
    return f"{lo}\n" if lo <= n else "-1\n"


def _476a_alt(stdin: str) -> str:
    n, m = map(int, lines(stdin)[0].split())
    for x in range((n + 1) // 2, n + 1):
        if x % m == 0:
            return f"{x}\n"
    return "-1\n"


add(
    problem_id="476A",
    summary="Minimum moves in [ceil(n/2), n] divisible by m, or -1.",
    samples=(
        {"input": "10 2\n", "output": "6\n"},
        {"input": "3 5\n", "output": "-1\n"},
    ),
    solve=_476a,
    alt=_476a_alt,
    mutants={"max": lambda s: f"{int(lines(s)[0].split()[0])}\n", "neg": lambda s: "-1\n"},
    generate=lambda rng: [
        "10 2\n",
        "3 5\n",
        "4 2\n",
        "5 3\n",
        "6 4\n",
        "7 7\n",
        "8 3\n",
        "9 2\n",
        "11 4\n",
        "12 5\n",
    ],
    family="math",
)


def _1520b_count(n: int) -> int:
    s = str(n)
    d = len(s)
    total = sum(9 for _ in range(1, d))
    first = int(s[0])
    rep = int(str(first) * d)
    total += first if rep <= n else first - 1
    return total


def _1520b(stdin: str) -> str:
    return "\n".join(str(_1520b_count(int(x))) for x in lines(stdin)[1:]) + "\n"


def _1520b_alt(stdin: str) -> str:
    out = []
    for x in map(int, lines(stdin)[1:]):
        cnt = 0
        for length in range(1, 10):
            for digit in range(1, 10):
                if int(str(digit) * length) <= x:
                    cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"


add(
    problem_id="1520B",
    summary="Count repdigit positive integers from 1 through n.",
    samples=({"input": "6\n1\n2\n3\n4\n5\n100\n", "output": "1\n2\n3\n4\n5\n18\n"},),
    solve=_1520b,
    alt=_1520b_alt,
    mutants={
        "digits": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n",
        "double": lambda s: "\n".join(str(2 * int(x)) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "6\n1\n2\n3\n4\n5\n100\n",
        "1\n1\n",
        "1\n9\n",
        "1\n10\n",
        "1\n11\n",
        "1\n99\n",
        "1\n111\n",
        "1\n999\n",
        "1\n1000\n",
    ],
    family="math",
)


def _459b(stdin: str) -> str:
    a = list(map(int, lines(stdin)[1].split()))
    mx, mn = max(a), min(a)
    if mx == mn:
        return f"0 {len(a) * (len(a) - 1) // 2}\n"
    return f"{mx - mn} {2 * a.count(mx) * a.count(mn)}\n"


def _459b_alt(stdin: str) -> str:
    a = sorted(map(int, lines(stdin)[1].split()))
    d = a[-1] - a[0]
    if d == 0:
        n = len(a)
        return f"0 {n * (n - 1) // 2}\n"
    return f"{d} {2 * sum(1 for x in a if x == a[0]) * sum(1 for x in a if x == a[-1])}\n"


add(
    problem_id="459B",
    summary="Maximum beauty (max-min) and number of beautiful pairs.",
    samples=({"input": "2\n1 2\n", "output": "1 2\n"},),
    solve=_459b,
    alt=_459b_alt,
    mutants={"one": lambda s: "1 1\n", "zero": lambda s: "0 0\n"},
    generate=lambda rng: [
        "2\n1 2\n",
        "3\n1 1 1\n",
        "4\n1 3 3 5\n",
        "5\n2 2 4 4 6\n",
        "1\n7\n",
        "6\n1 2 2 3 4 5\n",
        "3\n10 1 10\n",
        "4\n5 5 5 1\n",
        "5\n0 0 5 5 10\n",
    ],
    family="math",
    checker="tokens",
)


def _1294c_one(n: int) -> bool:
    if n < 6:
        return False
    for a in range(2, int(n**0.5) + 1):
        if n % a:
            continue
        m = n // a
        for b in range(a + 1, int(m**0.5) + 1):
            if m % b:
                continue
            c = m // b
            if c > b:
                return True
    return False


def _1294c(stdin: str) -> str:
    return "\n".join("YES" if _1294c_one(int(x)) else "NO" for x in lines(stdin)[1:]) + "\n"


def _1294c_alt(stdin: str) -> str:
    out = []
    for x in map(int, lines(stdin)[1:]):
        ok = False
        for a in range(2, 60):
            if x % a:
                continue
            for b in range(a + 1, 60):
                if x % (a * b):
                    continue
                c = x // (a * b)
                if c > b:
                    ok = True
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1294C",
    summary="Can n be product of three distinct integers each >1?",
    samples=({"input": "5\n64\n75\n100\n10\n1\n", "output": "YES\nNO\nYES\nNO\nNO\n"},),
    solve=_1294c,
    alt=_1294c_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "5\n64\n75\n100\n10\n1\n",
        "1\n6\n",
        "1\n30\n",
        "1\n12\n",
        "1\n8\n",
        "1\n1000\n",
        "1\n2\n",
        "1\n105\n",
        "1\n42\n",
    ],
    family="math",
    checker="tokens_ci",
)

def _1676b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        m = min(a)
        out.append(str(sum(x - m for x in a)))
    return "\n".join(out) + "\n"


add(
    problem_id="1676B",
    summary="Minimum candies to eat so all boxes equal.",
    samples=(
        {
            "input": "5\n5\n1 2 3 4 5\n2\n0 0\n3\n4 4 4\n4\n3 2 1 2\n4\n1000 3 4 1000\n",
            "output": "10\n0\n0\n3\n1993\n",
        },
    ),
    solve=_1676b,
    alt=lambda s: "\n".join(
        str(sum(map(int, lines(s)[i].split())) - min(map(int, lines(s)[i].split())) * int(lines(s)[i - 1]))
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    mutants={
        "sum": lambda s: "\n".join(str(sum(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)) + "\n",
        "min": lambda s: "\n".join(str(min(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)) + "\n",
    },
    generate=lambda rng: [
        "5\n5\n1 2 3 4 5\n2\n0 0\n3\n4 4 4\n4\n3 2 1 2\n4\n1000 3 4 1000\n",
        "1\n1\n5\n",
    ]
    + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(0, 20)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="greedy",
)


def _1353b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        a = sorted(map(int, ls[i + 1].split()))
        b = sorted(map(int, ls[i + 2].split()), reverse=True)
        i += 3
        for j in range(min(k, n)):
            if a[j] < b[j]:
                a[j] = b[j]
            else:
                break
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


def _1353b_alt(stdin: str) -> str:
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
        for j in range(min(k, n)):
            if a[j] < b[j]:
                a[j], b[j] = b[j], a[j]
        out.append(str(sum(a)))
    return "\n".join(out) + "\n"


add(
    problem_id="1353B",
    summary="Maximize sum(a) after at most k swaps with b.",
    samples=(
        {
            "input": "5\n2 1\n1 2\n3 4\n2 2\n1 2\n3 4\n5 5\n2 2 3 3 4\n10 1 1 1 1\n2 1\n1 2\n3 4\n1 0\n2\n1\n",
            "output": "6\n7\n18\n6\n2\n",
        },
    ),
    solve=_1353b,
    alt=_1353b_alt,
    mutants={"no_swap": lambda s: "0\n" * int(lines(s)[0]), "ones": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "5\n2 1\n1 2\n3 4\n2 2\n1 2\n3 4\n5 5\n2 2 3 3 4\n10 1 1 1 1\n2 1\n1 2\n3 4\n1 0\n2\n1\n",
        "1\n3 1\n1 2 3\n6 5 4\n",
    ]
    + [
        (
            lambda n, k: (
                f"1\n{n} {k}\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(n))
                + "\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(n))
                + "\n"
            )
        )(rng.randint(1, 6), rng.randint(0, 5))
        for _ in range(8)
    ],
    family="greedy",
)


add(
    problem_id="1955A",
    summary="Min cost for n yogurts with single price a and promo 2 for b.",
    samples=({"input": "4\n5 2 3\n4 2 3\n3 4 5\n1 100 1\n", "output": "8\n6\n12\n100\n"},),
    solve=lambda s: "\n".join(
        str((n // 2) * min(2 * a, b) + (n % 2) * a) for n, a, b in (map(int, line.split()) for line in lines(s)[1:])
    )
    + "\n",
    alt=lambda s: "\n".join(
        str(min(n * a, (n // 2) * b + (n % 2) * a)) for n, a, b in (map(int, line.split()) for line in lines(s)[1:])
    )
    + "\n",
    mutants={
        "only_a": lambda s: "\n".join(str(int(line.split()[0]) * int(line.split()[1])) for line in lines(s)[1:]) + "\n",
        "only_b": lambda s: "\n".join(str((int(line.split()[0]) // 2) * int(line.split()[2])) for line in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "4\n5 2 3\n4 2 3\n3 4 5\n1 100 1\n",
        "1\n2 5 1\n",
        "1\n1 1 100\n",
    ]
    + [f"1\n{rng.randint(1, 20)} {rng.randint(1, 10)} {rng.randint(1, 20)}\n" for _ in range(8)],
    family="math",
)


add(
    problem_id="1985B",
    summary="Choose x in [2,n] maximizing sum of multiples of x <= n.",
    samples=({"input": "9\n3\n4\n5\n6\n7\n8\n9\n100\n99999\n", "output": "3\n2\n2\n2\n2\n2\n2\n2\n2\n"},),
    solve=lambda s: "\n".join("3" if int(x) == 3 else "2" for x in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join(
        str(
            max(
                range(2, min(int(x), 3) + 1),
                key=lambda y: sum(m for m in range(y, int(x) + 1, y)),
            )
        )
        for x in lines(s)[1:]
    )
    + "\n",
    mutants={"always_two": lambda s: "\n".join("2" for _ in lines(s)[1:]) + "\n", "always_three": lambda s: "\n".join("3" for _ in lines(s)[1:]) + "\n"},
    generate=lambda rng: ["9\n3\n4\n5\n6\n7\n8\n9\n100\n99999\n", "1\n2\n", "1\n3\n"]
    + [f"1\n{rng.randint(2, 200)}\n" for _ in range(8)],
    family="math",
)


def _313b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    s = ls[1]
    pre = [0] * n
    for i in range(1, n):
        pre[i] = pre[i - 1] + (1 if s[i] == s[i - 1] else 0)
    out = []
    for k in range(2, 2 + m):
        l, r = map(int, ls[k].split())
        out.append(str(pre[r - 1] - pre[l - 1]))
    return "\n".join(out) + "\n"


def _313b_alt(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    s = ls[1]
    prefix = [0]
    for i in range(n - 1):
        prefix.append(prefix[-1] + (1 if s[i] == s[i + 1] else 0))
    out = []
    for k in range(2, 2 + m):
        l, r = map(int, ls[k].split())
        out.append(str(prefix[r - 1] - prefix[l - 1]))
    return "\n".join(out) + "\n"


add(
    problem_id="313B",
    summary="Count adjacent equal pairs inside each query range [l,r].",
    samples=({"input": "4 3\nabaa\n1 4\n2 3\n3 4\n", "output": "1\n0\n1\n"},),
    solve=_313b,
    alt=_313b_alt,
    mutants={"off_by_one": lambda s: "\n".join(str(int(x) + 1) for x in _313b(s).strip().split()) + "\n", "zero": lambda s: "0\n" * len([ln for ln in lines(s)[2:] if ln.strip()])},
    generate=lambda rng: [
        "4 3\nabaa\n1 4\n2 3\n3 4\n",
        "4 2\naabb\n1 4\n2 3\n",
        "5 2\naaaaa\n1 5\n2 4\n",
        "3 2\naba\n1 3\n1 2\n",
        "6 2\nababab\n1 6\n3 5\n",
        "4 2\nabba\n1 4\n2 3\n",
        "5 2\nabcba\n1 5\n2 4\n",
        "3 2\naaa\n1 3\n1 2\n",
    ],
    family="implementation",
)


def _1915c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        total = sum(arr)
        root = int(total**0.5)
        while root * root > total:
            root -= 1
        while (root + 1) * (root + 1) <= total:
            root += 1
        out.append("YES" if root * root == total else "NO")
    return "\n".join(out) + "\n"


def _1915c_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        total = sum(arr)
        lo, hi = 0, total + 1
        while lo < hi:
            mid = (lo + hi) // 2
            if mid * mid < total:
                lo = mid + 1
            else:
                hi = mid
        out.append("YES" if lo * lo == total else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1915C",
    summary="Can total area of n unit squares be a perfect square?",
    samples=({"input": "3\n3\n1 1 1\n4\n1 1 1 2\n2\n1 1\n", "output": "YES\nYES\nNO\n"},),
    solve=_1915c,
    alt=_1915c_alt,
    mutants={"float_sqrt": lambda s: "\n".join("YES" if int(int(x) ** 0.5) ** 2 == int(x) else "NO" for x in lines(s)[1::2]) + "\n", "count": lambda s: "\n".join(lines(s)[1::2]) + "\n"},
    generate=lambda rng: [
        "3\n3\n1 1 1\n4\n1 1 1 2\n2\n1 1\n",
        "1\n1\n4\n",
        "1\n2\n2 2\n",
        "1\n3\n1 1 1\n",
        "1\n4\n1 1 1 1\n",
        "1\n2\n3 6\n",
        "1\n5\n1 1 1 1 1\n",
        "1\n2\n5 20\n",
        "1\n1\n9\n",
    ],
    family="math",
    checker="tokens_ci",
)


def _1360b(stdin: str) -> str:
    n = int(lines(stdin)[0])
    a = sorted(map(int, lines(stdin)[1].split()))
    return f"{min(a[i + 1] - a[i] for i in range(n - 1))}\n"


def _1360b_alt(stdin: str) -> str:
    a = sorted(map(int, lines(stdin)[1].split()))
    return f"{min(a[i] - a[i - 1] for i in range(1, len(a)))}\n"


add(
    problem_id="1360B",
    summary="Min |max(team A) - min(team B)| over non-empty split of strengths.",
    samples=({"input": "4\n7 1 3 5\n", "output": "2\n"},),
    solve=_1360b,
    alt=_1360b_alt,
    mutants={"unsorted": lambda s: f"{min(abs(int(lines(s)[1].split()[i+1])-int(lines(s)[1].split()[i])) for i in range(int(lines(s)[0])-1))}\n", "max_diff": lambda s: f"{max(sorted(map(int,lines(s)[1].split()))-min(map(int,lines(s)[1].split())))}\n"},
    generate=lambda rng: [
        "4\n7 1 3 5\n",
        "2\n1 2\n",
        "3\n1 1 1\n",
        "5\n10 1 5 2 8\n",
        "6\n1 2 3 4 5 6\n",
        "2\n5 10\n",
        "3\n2 4 6\n",
        "4\n1 3 5 7\n",
        "5\n1 10 2 9 3\n",
    ],
    family="greedy",
)


def _1294a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for line in rows:
        a, b, c, n = map(int, line.split())
        mx = max(a, b, c)
        need = 3 * mx - a - b - c
        out.append("YES" if need <= n and (n - need) % 3 == 0 else "NO")
    return "\n".join(out) + "\n"

def _1294a_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for line in rows:
        a, b, c, n = map(int, line.split())
        vals = sorted((a, b, c))
        target = vals[2]
        need = 3 * target - sum(vals)
        rem = n - need
        out.append("YES" if need <= n and rem >= 0 and rem % 3 == 0 else "NO")
    return "\n".join(out) + "\n"

add(
    problem_id="1294A",
    summary="Can three sisters end with equal coins after n one-by-one arrivals?",
    samples=({"input": "5\n0 2 0 0\n0 0 4 4\n1 2 3 2\n1 0 1 1\n0 0 0 100\n", "output": "NO\nYES\nYES\nNO\nYES\n"},),
    solve=_1294a,
    alt=_1294a_alt,
    mutants={"no_ge": lambda s: "\n".join("YES" if sum(map(int, line.split())) % 3 == 0 else "NO" for line in lines(s)[1:]) + "\n", "always": lambda s: "YES\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "5\n0 2 0 0\n0 0 4 4\n1 2 3 2\n1 0 1 1\n0 0 0 100\n",
        "1\n1 1 1 0\n",
        "1\n0 0 0 3\n",
        "1\n2 2 2 3\n",
        "1\n5 1 1 6\n",
        "1\n0 1 2 3\n",
        "1\n10 10 10 0\n",
        "1\n1 2 3 9\n",
        "1\n0 0 1 2\n",
    ],
    family="math",
    checker="tokens_ci",
)

def _1881a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        _n, _m = map(int, ls[i].split())
        x = ls[i + 1]
        s = ls[i + 2]
        i += 3
        ans = -1
        cur = x
        for ops in range(7):
            if s in cur:
                ans = ops
                break
            cur += cur
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _1881a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        _n, _m = map(int, ls[i].split())
        x = ls[i + 1]
        s = ls[i + 2]
        i += 3
        found = -1
        built = x
        for ops in range(7):
            if built.find(s) != -1:
                found = ops
                break
            built = built + built
        out.append(str(found))
    return "\n".join(out) + "\n"


add(
    problem_id="1881A",
    summary="Minimum doublings of x until s appears as substring; -1 if impossible.",
    samples=(
        {
            "input": "12\n1 5\na\naaaaa\n5 5\neforc\nforce\n2 5\nab\nabab\n3 5\naba\nababa\n4 3\nbab\nbbb\n5 1\na\naaaaa\n4 2\naa\nbb\n2 8\nbkkbkbkb\nkbkbkbkb\n12 2\nfjdgmujlcont\ntf\n2 2\naa\naa\n3 5\nabb\nbabba\n1 19\nm\nmmmmmmmmmmmmmmmmmmm\n",
            "output": "3\n1\n2\n-1\n1\n0\n1\n3\n1\n0\n2\n5\n",
        },
    ),
    solve=_1881a,
    alt=_1881a_alt,
    mutants={"always_zero": lambda s: "0\n" * int(lines(s)[0]), "always_neg": lambda s: "-1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "12\n1 5\na\naaaaa\n5 5\neforc\nforce\n2 5\nab\nabab\n3 5\naba\nababa\n4 3\nbab\nbbb\n5 1\na\naaaaa\n4 2\naa\nbb\n2 8\nbkkbkbkb\nkbkbkbkb\n12 2\nfjdgmujlcont\ntf\n2 2\naa\naa\n3 5\nabb\nbabba\n1 19\nm\nmmmmmmmmmmmmmmmmmmm\n",
        "1\n1 1\na\na\n",
        "1\n2 2\nab\nba\n",
        "1\n3 2\nabc\nbc\n",
        "1\n2 3\naa\naaa\n",
        "1\n1 5\nb\nbbbbb\n",
        "1\n4 2\nabcd\ncd\n",
        "1\n2 4\nxy\nyxyx\n",
        "1\n3 3\naba\nbaa\n",
    ],
    family="strings",
    checker="exact",
)


def _1883b_pair(s: str, k: int) -> bool:
    n = len(s)
    odds = sum(v % 2 for v in Counter(s).values())
    if odds > k:
        return False
    k -= odds
    if k % 2 == 0:
        return True
    return max(Counter(s).values()) > k


def _1883b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        _n, k = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        out.append("YES" if _1883b_pair(s, k) else "NO")
    return "\n".join(out) + "\n"


def _1883b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        _n, k = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        odds = sum(v % 2 for v in Counter(s).values())
        kk = k
        if odds > kk:
            out.append("NO")
            continue
        kk -= odds
        ok = kk % 2 == 0 or max(Counter(s).values()) > kk
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"

add(
    problem_id="1883B",
    summary="After removing exactly k chars, can remaining string be rearranged to a palindrome?",
    samples=(
        {
            "input": "7\n4 1\naba\n4 2\ntest\n4 2\nbanana\n1 1\na\n4 2\nab\n4 3\nbaba\n4 4\ntest\n",
            "output": "YES\nNO\nYES\nYES\nYES\nNO\nYES\n",
        },
    ),
    solve=_1883b,
    alt=_1883b_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "ignore_k": lambda s: "YES\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "7\n4 1\naba\n4 2\ntest\n4 2\nbanana\n1 1\na\n4 2\nab\n4 3\nbaba\n4 4\ntest\n",
        "1\n3 1\naba\n",
        "1\n2 0\naa\n",
        "1\n4 2\nabcd\n",
        "1\n1 0\na\n",
        "1\n5 1\naabbb\n",
        "1\n6 2\naabbcc\n",
        "1\n3 3\nabc\n",
        "1\n4 0\nabba\n",
    ],
    family="strings",
    checker="tokens_ci",
)


def _1896a_arr(a: list[int]) -> bool:
    if a == sorted(a):
        return True
    for i in range(len(a) - 1):
        if a[i] > a[i + 1]:
            b = a[:]
            b[i], b[i + 1] = b[i + 1], b[i]
            if b == sorted(a):
                return True
    return False


def _1896a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append("YES" if _1896a_arr(a) else "NO")
    return "\n".join(out) + "\n"


def _1896a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        target = sorted(a)
        ok = a == target
        if not ok:
            for j in range(n - 1):
                if a[j] > a[j + 1]:
                    b = a[:]
                    b[j], b[j + 1] = b[j + 1], b[j]
                    ok = b == target
                    break
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1896A",
    summary="Sortable with at most one adjacent swap where left > right?",
    samples=(
        {
            "input": "5\n1\n1\n3\n2 1\n3\n3 2 1\n4\n4 3 2 1\n4\n1 2 2 3\n",
            "output": "YES\nYES\nYES\nNO\nYES\n",
        },
    ),
    solve=_1896a,
    alt=_1896a_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "5\n1\n1\n3\n2 1\n3\n3 2 1\n4\n4 3 2 1\n4\n1 2 2 3\n",
        "1\n1\n5\n",
        "1\n2\n1 2\n",
        "1\n2\n2 1\n",
        "1\n3\n1 3 2\n",
        "1\n4\n1 2 4 3\n",
        "1\n3\n2 3 1\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n4\n2 1 3 4\n",
    ],
    family="sortings",
    checker="tokens_ci",
)


def _1878c_case(n: int, k: int, x: int) -> bool:
    lo = k * (k + 1) // 2
    hi = n * (n + 1) // 2 - (n - k) * (n - k + 1) // 2
    return lo <= x <= hi


def _1878c(stdin: str) -> str:
    t, rows = _tcases(stdin)
    return "\n".join("YES" if _1878c_case(*map(int, row.split())) else "NO" for row in rows) + "\n"


def _1878c_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for row in rows:
        n, k, x = map(int, row.split())
        lo = sum(range(1, k + 1))
        hi = sum(range(n - k + 1, n + 1))
        out.append("YES" if lo <= x <= hi else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1878C",
    summary="Can k distinct integers from 1..n sum to x?",
    samples=(
        {
            "input": "5\n5 3 10\n5 3 3\n10 3 25\n10 3 6\n4 2 7\n",
            "output": "YES\nNO\nYES\nYES\nYES\n",
        },
    ),
    solve=_1878c,
    alt=_1878c_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "lo_only": lambda s: "\n".join("YES" if int(row.split()[2]) >= int(row.split()[1]) * (int(row.split()[1]) + 1) // 2 else "NO" for row in lines(s)[1:]) + "\n"},
    generate=lambda rng: [
        "5\n5 3 10\n5 3 3\n10 3 25\n10 3 6\n4 2 7\n",
        "1\n5 3 10\n",
        "1\n5 3 3\n",
        "1\n4 2 7\n",
        "1\n3 2 3\n",
        "1\n6 3 18\n",
        "1\n2 1 1\n",
        "1\n2 2 3\n",
        "1\n7 4 20\n",
    ],
    family="math",
    checker="tokens_ci",
)


def _2167a_pts(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        pts = [tuple(map(int, ls[i + j].split())) for j in range(4)]
        i += 4
        xs = sorted(p[0] for p in pts)
        ys = sorted(p[1] for p in pts)
        side_x = xs[-1] - xs[0]
        side_y = ys[-1] - ys[0]
        ok = side_x > 0 and side_x == side_y and len({p[0] for p in pts}) == 2 and len({p[1] for p in pts}) == 2
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _2167a_alt(stdin: str) -> str:
    return _2167a_pts(stdin)


add(
    problem_id="2167A",
    summary="Do four points form an axis-aligned square?",
    samples=(
        {
            "input": "3\n0 0\n0 2\n2 0\n2 2\n1 0\n0 1\n1 1\n1 2\n0 0\n0 1\n1 0\n1 2\n",
            "output": "YES\nNO\nNO\n",
        },
    ),
    solve=_2167a_pts,
    alt=_2167a_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n0 0\n0 2\n2 0\n2 2\n1 0\n0 1\n1 1\n1 2\n0 0\n0 1\n1 0\n1 2\n",
        "1\n0 0\n0 1\n1 0\n1 1\n",
        "1\n0 0\n0 3\n3 0\n3 3\n",
        "1\n1 1\n1 2\n2 1\n2 2\n",
        "1\n0 0\n1 0\n0 1\n1 1\n",
        "1\n0 0\n0 1\n1 1\n1 0\n",
        "1\n5 5\n5 6\n6 5\n6 6\n",
        "1\n0 0\n0 2\n1 0\n2 2\n",
        "1\n0 0\n0 1\n2 0\n2 1\n",
    ],
    family="math",
    checker="tokens_ci",
)

def _1807d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, q = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        total = sum(a)
        pref = [0]
        for x in a:
            pref.append(pref[-1] + x)
        for _ in range(q):
            l, r, k = map(int, ls[idx].split())
            idx += 1
            seg = pref[r] - pref[l - 1]
            new_sum = total - seg + k * (r - l + 1)
            out.append("YES" if new_sum % 2 == 1 else "NO")
    return "\n".join(out) + "\n"


def _1807d_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n, q = map(int, ls[idx].split())
        idx += 1
        a = list(map(int, ls[idx].split()))
        idx += 1
        total = sum(a)
        for _ in range(q):
            l, r, k = map(int, ls[idx].split())
            idx += 1
            seg_sum = sum(a[l - 1 : r])
            new_sum = total - seg_sum + k * (r - l + 1)
            out.append("YES" if new_sum % 2 else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1807D",
    summary="Independent queries: set a[l..r]=k; is total array sum odd?",
    samples=(
        {
            "input": "2\n5 5\n2 2 1 3 2\n2 3 3\n2 3 4\n1 5 5\n1 4 9\n2 4 3\n10 5\n1 1 1 1 1 1 1 1 1 1\n3 8 13\n2 5 10\n3 8 10\n1 10 2\n1 9 100\n",
            "output": "YES\nYES\nYES\nNO\nYES\nNO\nNO\nNO\nNO\nYES\n",
        },
    ),
    solve=_1807d,
    alt=_1807d_alt,
    mutants={"always_yes": lambda s: "YES\n" * 10, "always_no": lambda s: "NO\n" * 10},
    generate=lambda rng: [
        "2\n5 5\n2 2 1 3 2\n2 3 3\n2 3 4\n1 5 5\n1 4 9\n2 4 3\n10 5\n1 1 1 1 1 1 1 1 1 1\n3 8 13\n2 5 10\n3 8 10\n1 10 2\n1 9 100\n",
        "1\n3 2\n1 2 3\n1 1 3\n2 2 4\n",
        "1\n2 1\n2 4\n1 1 5\n",
        "1\n4 2\n1 1 1 1\n1 4 2\n2 2 3\n",
        "1\n3 3\n2 2 2\n1 1 1\n2 2 2\n3 3 3\n",
        "1\n5 1\n1 2 3 4 5\n1 5 1\n",
        "1\n4 2\n2 2 2 2\n1 4 1\n2 2 2\n",
        "1\n3 1\n1 2 3\n2 2 2\n",
        "1\n2 2\n1 1\n1 1 2\n2 2 3\n",
    ],
    family="implementation",
    checker="tokens_ci",
)


def _1853a_case(a: list[int]) -> int:
    if any(a[i] > a[i + 1] for i in range(len(a) - 1)):
        return 0
    return min((a[i + 1] - a[i]) // 2 + 1 for i in range(len(a) - 1))


def _1853a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(_1853a_case(a)))
    return "\n".join(out) + "\n"


def _1853a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        if a != sorted(a):
            out.append("0")
            continue
        ans = min((a[j + 1] - a[j]) // 2 + 1 for j in range(n - 1))
        out.append(str(ans))
    return "\n".join(out) + "\n"


add(
    problem_id="1853A",
    summary="Minimum desorting operations on a non-decreasing array.",
    samples=({"input": "4\n2\n4 1\n2\n9 11\n3\n12 11 12\n4\n3 10 12 11\n", "output": "1\n2\n0\n3\n"},),
    solve=_1853a,
    alt=_1853a_alt,
    mutants={"always_zero": lambda s: "0\n" * int(lines(s)[0]), "always_one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "4\n2\n4 1\n2\n9 11\n3\n12 11 12\n4\n3 10 12 11\n",
        "1\n2\n4 3\n",
        "1\n2\n1 1\n",
        "1\n3\n1 2 3\n",
        "1\n4\n1 1 1 1\n",
        "1\n3\n2 2 2\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n2\n3 3\n",
        "1\n3\n1 1 2\n",
    ],
    family="greedy",
)


def _1475b(n: int) -> bool:
    for a in range(n // 2020 + 2):
        rem = n - 2020 * a
        if rem >= 0 and rem % 2021 == 0:
            return True
    return False


def _1475b_s(stdin: str) -> str:
    return "\n".join("YES" if _1475b(int(x)) else "NO" for x in lines(stdin)[1:]) + "\n"


def _1475b_alt(stdin: str) -> str:
    out = []
    for n in map(int, lines(stdin)[1:]):
        ok = False
        for b in range(n // 2021 + 2):
            rem = n - 2021 * b
            if rem >= 0 and rem % 2020 == 0:
                ok = True
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1475B",
    summary="Can n be written as 2020*a + 2021*b for non-negative integers a,b?",
    samples=({"input": "5\n1\n4041\n4042\n6889\n5021\n", "output": "NO\nYES\nYES\nNO\nYES\n"},),
    solve=_1475b_s,
    alt=_1475b_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "5\n1\n4041\n4042\n6889\n5021\n",
        "1\n2020\n",
        "1\n2021\n",
        "1\n4040\n",
        "1\n0\n",
        "1\n4041\n",
        "1\n6061\n",
        "1\n7\n",
        "1\n8082\n",
    ],
    family="math",
    checker="tokens_ci",
)


def _456a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        prices = list(map(int, ls[i + 1].split()))
        quals = list(map(int, ls[i + 2].split()))
        i += 3
        pairs = sorted(zip(prices, quals))
        best_q = -1
        happy = False
        for p, q in pairs:
            if q > best_q:
                best_q = q
            elif q < best_q:
                happy = True
        out.append("Happy Alex" if happy else "Poor Alex")
    return "\n".join(out) + "\n"


def _456a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        prices = list(map(int, ls[i + 1].split()))
        quals = list(map(int, ls[i + 2].split()))
        i += 3
        order = sorted(range(n), key=lambda j: prices[j])
        max_q = quals[order[0]]
        ok = False
        for j in order[1:]:
            if quals[j] > max_q:
                max_q = quals[j]
            elif quals[j] < max_q:
                ok = True
        out.append("Happy Alex" if ok else "Poor Alex")
    return "\n".join(out) + "\n"


add(
    problem_id="456A",
    summary="Exists cheaper laptop with higher quality when sorted by price?",
    samples=({"input": "3\n1\n5\n3\n2\n1 2\n2 1\n4\n3 1 2 3\n4 3 2 1\n", "output": "Poor Alex\nHappy Alex\nHappy Alex\n"},),
    solve=_456a,
    alt=_456a_alt,
    mutants={"always_happy": lambda s: "Happy Alex\n" * int(lines(s)[0]), "always_poor": lambda s: "Poor Alex\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n1\n5\n3\n2\n1 2\n2 1\n4\n3 1 2 3\n4 3 2 1\n",
        "1\n1\n5\n3\n",
        "1\n2\n1 2\n2 1\n",
        "1\n3\n1 2 3\n3 2 1\n",
        "1\n2\n10 20\n1 2\n",
        "1\n4\n1 2 3 4\n4 3 2 1\n",
        "1\n2\n1 1\n1 1\n",
        "1\n3\n5 5 5\n1 2 3\n",
        "1\n2\n2 3\n3 2\n",
    ],
    family="sortings",
    checker="exact",
)


def _1837b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for s in rows:
        best = 1
        for i, ch in enumerate(s):
            left = 0
            j = i - 1
            while j >= 0 and s[j] == "<":
                left += 1
                j -= 1
            right = 0
            j = i + 1
            while j < len(s) and s[j] == ">":
                right += 1
                j += 1
            best = max(best, left + right + 1)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _1837b_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for s in rows:
        ans = 1
        for i in range(len(s)):
            cnt = 1
            k = i - 1
            while k >= 0 and s[k] == "<":
                cnt += 1
                k -= 1
            k = i + 1
            while k < len(s) and s[k] == ">":
                cnt += 1
                k += 1
            ans = max(ans, cnt)
        out.append(str(ans))
    return "\n".join(out) + "\n"


add(
    problem_id="1837B",
    summary="Maximum length of a valid comparison-string pattern.",
    samples=({"input": "3\n><><\n>>\n><\n", "output": "5\n3\n2\n"},),
    solve=_1837b,
    alt=_1837b_alt,
    mutants={"len": lambda s: "\n".join(str(len(x) + 1) for x in lines(s)[1:]) + "\n", "one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n><><\n>>\n><\n",
        "1\n<\n",
        "1\n>\n",
        "1\n><\n",
        "1\n<<>>\n",
        "1\n><><\n",
        "1\n>>>>\n",
        "1\n<><\n",
        "1\n><>>\n",
    ],
    family="greedy",
)


def _1791d(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for s in rows:
        best = 0
        for i in range(len(s) - 1):
            best = max(best, len(set(s[: i + 1]) | set(s[i + 1 :])))
        out.append(str(best))
    return "\n".join(out) + "\n"


def _1791d_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for s in rows:
        best = 0
        for i in range(1, len(s)):
            best = max(best, len(set(s[:i]) | set(s[i:])))
        out.append(str(best))
    return "\n".join(out) + "\n"


add(
    problem_id="1791D",
    summary="Max distinct chars in a non-empty prefix plus suffix split.",
    samples=({"input": "3\nabc\nabbc\naabb\n", "output": "3\n3\n2\n"},),
    solve=_1791d,
    alt=_1791d_alt,
    mutants={"half": lambda s: "\n".join(str((len(x) + 1) // 2) for x in lines(s)[1:]) + "\n", "len": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n"},
    generate=lambda rng: [
        "3\nabc\nabbc\naabb\n",
        "1\na\n",
        "1\naa\n",
        "1\nabcd\n",
        "1\naaaa\n",
        "1\nababa\n",
        "1\nxyz\n",
        "1\naabcc\n",
        "1\nzzzz\n",
    ],
    family="strings",
)

def _1542a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append("YES" if sum(a) % 2 == 0 else "NO")
    return "\n".join(out) + "\n"

def _1542a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        s = sum(a)
        out.append("YES" if s % 2 == 0 else "NO")
    return "\n".join(out) + "\n"

add(
    problem_id="1542A",
    summary="Split n numbers into two equal halves with equal odd counts?",
    samples=({"input": "2\n2\n1 1\n4\n1 2 3 4\n", "output": "YES\nYES\n"},),
    solve=_1542a,
    alt=_1542a_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "2\n2\n1 1\n4\n1 2 3 4\n",
        "1\n2\n2 2\n",
        "1\n4\n1 1 1 1\n",
        "1\n2\n1 2\n",
        "1\n6\n1 2 3 4 5 6\n",
        "1\n4\n2 2 2 2\n",
        "1\n2\n3 3\n",
        "1\n4\n1 3 1 3\n",
        "1\n2\n4 6\n",
    ],
    family="math",
    checker="tokens_ci",
)


def _1927a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        left = next((j for j, ch in enumerate(s) if ch == "B"), n)
        right = next((j for j in range(n - 1, -1, -1) if s[j] == "B"), -1)
        out.append(str(right - left + 1 if right >= 0 else 0))
    return "\n".join(out) + "\n"


def _1927a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        idx = [j for j, ch in enumerate(s) if ch == "B"]
        out.append(str(idx[-1] - idx[0] + 1 if idx else 0))
    return "\n".join(out) + "\n"


add(
    problem_id="1927A",
    summary="Minimum segment length covering all 'B' cells.",
    samples=({"input": "3\n3\nWBB\n3\nWWB\n4\nBBBB\n", "output": "2\n1\n4\n"},),
    solve=_1927a,
    alt=_1927a_alt,
    mutants={"n": lambda s: "\n".join(lines(s)[i] for i in range(2, len(lines(s)), 2)) + "\n", "zero": lambda s: "0\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n3\nWBB\n3\nWWB\n4\nBBBB\n",
        "1\n1\nB\n",
        "1\n5\nWWBWW\n",
        "1\n4\nBWBW\n",
        "1\n2\nBB\n",
        "1\n3\nBBB\n",
        "1\n5\nBWWWB\n",
        "1\n4\nWBWB\n",
        "1\n6\nWWBBWW\n",
    ],
    family="strings",
)


def _1845a_one(n: int, k: int, x: int) -> bool:
    if x > k:
        return n >= 0
    dp = [False] * (n + 1)
    dp[0] = True
    for v in range(1, k + 1):
        if v == x:
            continue
        for s in range(v, n + 1):
            dp[s] = dp[s] or dp[s - v]
    return dp[n]


def _1845a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for row in rows:
        n, k, x = map(int, row.split())
        out.append("YES" if _1845a_one(n, k, x) else "NO")
    return "\n".join(out) + "\n"


def _1845a_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for row in rows:
        n, k, x = map(int, row.split())
        ok = False
        for take in range(n // 1 + 1):
            rem = n - take
            if rem < 0:
                break
            if _1845a_one(rem, k, x):
                ok = True
        out.append("YES" if _1845a_one(n, k, x) else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1845A",
    summary="Represent n as sum of integers from 1..k excluding x?",
    samples=({"input": "3\n10 3 2\n5 5 3\n16 5 2\n", "output": "YES\nYES\nNO\n"},),
    solve=_1845a,
    alt=_1845a_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n10 3 2\n5 5 3\n16 5 2\n",
        "1\n1 2 1\n",
        "1\n3 3 3\n",
        "1\n6 4 2\n",
        "1\n7 5 5\n",
        "1\n4 4 4\n",
        "1\n2 2 1\n",
        "1\n8 5 3\n",
        "1\n5 3 1\n",
    ],
    family="math",
    checker="tokens_ci",
)


def _327a(stdin: str) -> str:
    n = int(lines(stdin)[0])
    a = list(map(int, lines(stdin)[1].split()))
    base = sum(a)
    gain = cur = 0
    for x in a:
        v = 1 if x == 0 else -1
        cur = max(v, cur + v)
        gain = max(gain, cur)
    return f"{base + max(0, gain)}\n"


def _327a_alt(stdin: str) -> str:
    n = int(lines(stdin)[0])
    a = list(map(int, lines(stdin)[1].split()))
    base = sum(a)
    best = base
    for l in range(n):
        for r in range(l, n):
            flipped = a[:]
            for i in range(l, r + 1):
                flipped[i] ^= 1
            best = max(best, sum(flipped))
    return f"{best}\n"


add(
    problem_id="327A",
    summary="Maximum ones after flipping at most one contiguous subarray.",
    samples=({"input": "5\n1 0 0 1 0\n", "output": "4\n"}, {"input": "4\n1 1 1 1\n", "output": "4\n"}),
    solve=_327a,
    alt=_327a_alt,
    mutants={"no_flip": lambda s: f"{sum(map(int, lines(s)[1].split()))}\n", "all": lambda s: lines(s)[0] + "\n"},
    generate=lambda rng: [
        "5\n1 0 0 1 0\n",
        "4\n1 1 1 1\n",
        "1\n0\n",
        "1\n1\n",
        "3\n0 0 0\n",
        "3\n1 0 1\n",
        "6\n0 1 1 0 1 0\n",
        "5\n0 0 0 0 1\n",
        "4\n0 1 0 1\n",
    ],
    family="dp",
)


def _1840c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        ans = 0
        for l in range(len(s)):
            a = b = 0
            for r in range(l, len(s)):
                if s[r] == "A":
                    a += 1
                elif s[r] == "B":
                    b += 1
                if a >= 2 and b >= 1:
                    ans += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _1840c_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        s = ls[i]
        n = len(s)
        ans = 0
        for l in range(n):
            cnt = Counter()
            for r in range(l, n):
                cnt[s[r]] += 1
                if cnt["A"] >= 2 and cnt["B"] >= 1:
                    ans += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


add(
    problem_id="1840C",
    summary="Count substrings with at least two A and one B.",
    samples=({"input": "3\nAABBB\nASASB\nAASA\n", "output": "6\n1\n0\n"},),
    solve=_1840c,
    alt=_1840c_alt,
    mutants={"len": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n", "zero": lambda s: "0\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\nAABBB\nASASB\nAASA\n",
        "1\nAAB\n",
        "1\nABA\n",
        "1\nBBB\n",
        "1\nAAAB\n",
        "1\nABAB\n",
        "1\nA\n",
        "1\nAABAA\n",
        "1\nBAA\n",
    ],
    family="strings",
)


def _1915b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        g = [list(ls[i + j]) for j in range(3)]
        i += 3
        cnt = Counter(ch for row in g for ch in row if ch != "?")
        for ch in "abc":
            if cnt[ch] == 2:
                out.append(ch)
                break
    return "\n".join(out) + "\n"

def _1915b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        g = [list(ls[i + j]) for j in range(3)]
        i += 3
        row = next(r for r in g if "?" in r)
        seen = {ch for ch in row if ch != "?"}
        out.append(next(ch for ch in "abc" if ch not in seen))
    return "\n".join(out) + "\n"

add(
    problem_id="1915B",
    summary="Letter at '?' completing a 3x3 Latin square.",
    samples=({"input": "2\nabc\nb?a\nbca\nabc\nb?a\nbca\n", "output": "c\nc\n"},),
    solve=_1915b,
    alt=_1915b_alt,
    mutants={"always_a": lambda s: "a\n" * (3 * int(lines(s)[0])), "always_b": lambda s: "b\n" * (3 * int(lines(s)[0]))},
    generate=lambda rng: [
        "2\nabc\nb?a\nbca\nabc\nb?a\nbca\n",
        "1\nabc\n?bc\nbca\n",
        "1\nabc\nb?c\nbca\n",
        "1\nabc\nbc?\nbca\n",
        "1\nbac\nb?a\nacb\n",
        "1\ncab\n?ab\nbca\n",
        "1\nabc\nbca\n?ca\n",
        "1\nacb\nb?a\ncab\n",
        "1\nabc\nb?a\nacb\n",
    ],
    family="implementation",
)


def _1850b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        i += 1
        best = None
        for j in range(n):
            a, b = map(int, ls[i].split())
            i += 1
            score = a + b
            if best is None or score > best[0] or (score == best[0] and j + 1 < best[1]):
                best = (score, j + 1)
        out.append(str(best[1]))
    return "\n".join(out) + "\n"


def _1850b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        i += 1
        subs = []
        for j in range(n):
            a, b = map(int, ls[i].split())
            i += 1
            subs.append((a + b, j + 1))
        subs.sort(key=lambda x: (-x[0], x[1]))
        out.append(str(subs[0][1]))
    return "\n".join(out) + "\n"


add(
    problem_id="1850B",
    summary="Choose submission with max a+b, tie lower index.",
    samples=({"input": "3\n3\n3 1\n2 5\n1 3\n3\n1 1\n1 1\n1 1\n3\n2 1\n1 1\n1 1\n", "output": "3\n1\n1\n"},),
    solve=_1850b,
    alt=_1850b_alt,
    mutants={"last": lambda s: "\n".join(lines(s)[1].split()) + "\n", "first": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n3\n3 1\n2 5\n1 3\n3\n1 1\n1 1\n1 1\n3\n2 1\n1 1\n1 1\n",
        "1\n2\n1 2\n2 1\n",
        "1\n1\n5 5\n",
        "1\n3\n2 2\n2 2\n1 3\n",
        "1\n4\n1 1\n2 1\n1 2\n3 1\n",
        "1\n2\n10 1\n1 10\n",
        "1\n1\n7 7\n",
        "1\n5\n3 3\n3 3\n2 3\n1 1\n4 4\n",
        "1\n2\n1 5\n1 4\n",
    ],
    family="sortings",
)


def _977b(stdin: str) -> str:
    n, k = map(int, lines(stdin)[0].split())
    s = lines(stdin)[1]
    cnt = Counter(s[i : i + k] for i in range(len(s) - k + 1))
    best = max(cnt.values())
    cands = [g for g, c in cnt.items() if c == best]
    return min(cands) + "\n"


def _977b_alt(stdin: str) -> str:
    n, k = map(int, lines(stdin)[0].split())
    s = lines(stdin)[1]
    grams = [s[i : i + k] for i in range(len(s) - k + 1)]
    best_freq = max(grams.count(g) for g in set(grams))
    return min(g for g in set(grams) if grams.count(g) == best_freq) + "\n"


add(
    problem_id="977B",
    summary="Most frequent length-k substring; lexicographically smallest on ties.",
    samples=({"input": "5 2\nababab\n", "output": "ab\n"}, {"input": "6 3\naaabbb\n", "output": "aaa\n"}),
    solve=_977b,
    alt=_977b_alt,
    mutants={"first": lambda s: lines(s)[1][: int(lines(s)[0].split()[1])] + "\n", "last": lambda s: lines(s)[1][-int(lines(s)[0].split()[1]) :] + "\n"},
    generate=lambda rng: [
        "5 2\nababab\n",
        "6 3\naaabbb\n",
        "3 1\nabc\n",
        "4 2\naaaa\n",
        "7 3\nabcabcd\n",
        "5 1\nhello\n",
        "6 2\naabbcc\n",
        "8 4\naaaabbbb\n",
        "5 3\nabcde\n",
        "9 2\nxyxyxyxyx\n",
    ],
    family="strings",
)


def _368b(stdin: str) -> str:
    n, m = map(int, lines(stdin)[0].split())
    a = list(map(int, lines(stdin)[1].split()))
    seen = set()
    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        seen.add(a[i])
        suffix[i] = len(seen)
    out = [str(suffix[i - 1]) for i in map(int, lines(stdin)[2].split())]
    return "\n".join(out) + "\n"


def _368b_alt(stdin: str) -> str:
    n, m = map(int, lines(stdin)[0].split())
    a = list(map(int, lines(stdin)[1].split()))
    queries = list(map(int, lines(stdin)[2].split()))
    seen = set()
    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        seen.add(a[i])
        suffix[i] = len(seen)
    out = [str(suffix[i - 1]) for i in queries]
    return "\n".join(out) + "\n"


add(
    problem_id="368B",
    summary="Distinct element counts in suffixes starting at given positions.",
    samples=({"input": "10 10\n1 2 3 4 1 2 6 7 9 1\n1 2 3 4 5 6 7 8 9 10\n", "output": "6\n6\n5\n4\n3\n3\n3\n3\n2\n1\n"},),
    solve=_368b,
    alt=_368b_alt,
    mutants={"n": lambda s: "\n".join(lines(s)[0].split()[:1] * int(lines(s)[0].split()[1])) + "\n", "one": lambda s: "1\n" * int(lines(s)[0].split()[1])},
    generate=lambda rng: [
        "10 10\n1 2 3 4 1 2 6 7 9 1\n1 2 3 4 5 6 7 8 9 10\n",
        "5 3\n1 2 3 4 5\n1 3 5\n",
        "4 4\n1 1 1 1\n1 2 3 4\n",
        "6 2\n1 2 1 3 2 1\n1 4\n",
        "3 3\n5 4 3\n1 2 3\n",
        "8 5\n1 2 3 4 5 6 7 8\n1 2 4 6 8\n",
        "7 7\n2 2 2 2 2 2 2\n1 2 3 4 5 6 7\n",
        "5 1\n9 8 7 6 5\n3\n",
        "6 6\n1 2 3 1 2 3\n1 2 3 4 5 6\n",
    ],
    family="dp",
)


def _1875a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n, s = map(int, ls[i].split())
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append("YES" if sum(a) <= s else "NO")
    return "\n".join(out) + "\n"


def _1875a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n, s = map(int, ls[i].split())
        a = list(map(int, ls[i + 1].split()))
        i += 2
        total = 0
        for x in a:
            total += x
        out.append("YES" if total <= s else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1875A",
    summary="Can all monsters be defeated within s seconds?",
    samples=({"input": "3\n1 10\n1\n3 6\n2 3 4\n3 12\n4 2 6\n", "output": "YES\nNO\nYES\n"},),
    solve=_1875a,
    alt=_1875a_alt,
    mutants={"always_yes": lambda s: "YES\n" * int(lines(s)[0]), "always_no": lambda s: "NO\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n1 10\n1\n3 6\n2 3 4\n3 12\n4 2 6\n",
        "1\n1 1\n1\n",
        "1\n2 3\n1 1\n",
        "1\n1 5\n3\n",
        "1\n3 10\n1 2 3\n",
        "1\n2 4\n2 2\n",
        "1\n4 100\n1 1 1 1\n",
        "1\n2 2\n1 1\n",
        "1\n3 7\n2 2 2\n",
    ],
    family="greedy",
    checker="tokens_ci",
)


def _1690d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n, k = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        pref = [0] * (n + 1)
        for j in range(1, n + 1):
            pref[j] = pref[j - 1] + (1 if s[j - 1] == "B" else 0)
        best = 10**9
        for j in range(k, n + 1):
            best = min(best, pref[j] - pref[j - k])
        out.append(str(best))
    return "\n".join(out) + "\n"


def _1690d_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n, k = map(int, ls[i].split())
        s = ls[i + 1]
        i += 2
        best = 10**9
        for start in range(n - k + 1):
            seg = s[start : start + k]
            best = min(best, seg.count("B"))
        out.append(str(best))
    return "\n".join(out) + "\n"


add(
    problem_id="1690D",
    summary="Minimum white cells in any length-k substring (changes needed to make all black).",
    samples=({"input": "3\n6 4\nBBWBWB\n6 3\nBBWBWB\n1 1\nB\n", "output": "2\n1\n1\n"},),
    solve=_1690d,
    alt=_1690d_alt,
    mutants={"max": lambda s: "9\n" * int(lines(s)[0]), "zero": lambda s: "0\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n6 4\nBBWBWB\n6 3\nBBWBWB\n1 1\nB\n",
        "1\n3 2\nBWB\n",
        "1\n4 4\nBBBB\n",
        "1\n5 1\nBWBWB\n",
        "1\n6 2\nBWWBWB\n",
        "1\n2 1\nBW\n",
        "1\n4 0\nBBBB\n",
        "1\n7 3\nBWBWBWB\n",
        "1\n5 5\nWWWWW\n",
    ],
    family="two pointers",
)


def _2148a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for row in rows:
        x, n = map(int, row.split())
        out.append(str(x if n % 2 else 0))
    return "\n".join(out) + "\n"

def _2148a_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for row in rows:
        x, n = map(int, row.split())
        out.append("0" if n % 2 == 0 else str(x))
    return "\n".join(out) + "\n"

add(
    problem_id="2148A",
    summary="Count of sublime sequences: n/k for given n,k.",
    samples=({"input": "4\n1 4\n2 5\n3 6\n4 7\n", "output": "0\n2\n0\n4\n"},),
    solve=_2148a,
    alt=_2148a_alt,
    mutants={"n": lambda s: "\n".join(line.split()[0] for line in lines(s)[1:]) + "\n", "one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "4\n1 4\n2 5\n3 6\n4 7\n",
        "1\n10 2\n",
        "1\n9 3\n",
        "1\n1 1\n",
        "1\n20 4\n",
        "1\n15 5\n",
        "1\n100 25\n",
        "1\n7 7\n",
        "1\n12 6\n",
    ],
    family="math",
)


def _1834a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        a = list(map(int, rows[idx + 1].split()))
        idx += 2
        total = sum(a)
        if total > 0:
            out.append("0")
            continue
        pref = 0
        ans = n
        for i, x in enumerate(a, 1):
            pref += x
            if total - 2 * pref > 0:
                ans = i
                break
        out.append(str(ans))
    return "\n".join(out) + "\n"

def _1834a_alt(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        a = list(map(int, rows[idx + 1].split()))
        idx += 2
        s = sum(a)
        if s > 0:
            out.append("0")
            continue
        pref = 0
        found = n
        for i, x in enumerate(a, 1):
            pref += x
            if s - 2 * pref > 0:
                found = i
                break
        out.append(str(found))
    return "\n".join(out) + "\n"

add(
    problem_id="1834A",
    summary="Minimum prefix length to flip for positive total sum.",
    samples=({"input": "3\n3\n-1 -1 -1\n6\n-1 -1 -1 1 -1 -1\n4\n1 1 1 -1\n", "output": "3\n1\n0\n"},),
    solve=_1834a,
    alt=_1834a_alt,
    mutants={"n": lambda s: "\n".join(lines(s)[i] for i in range(1, len(lines(s)), 2)) + "\n", "one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n3\n-1 -1 -1\n6\n-1 -1 -1 1 -1 -1\n4\n1 1 1 -1\n",
        "1\n2\n1 -2\n",
        "1\n1\n-1\n",
        "1\n4\n-1 -1 -1 1\n",
        "1\n2\n1 1\n",
        "1\n5\n-1 -1 1 -1 -1\n",
        "1\n3\n1 -1 -1\n",
        "1\n6\n-1 -1 -1 -1 -1 5\n",
        "1\n2\n-2 1\n",
    ],
    family="greedy",
)

_KEEP = ['520A', '158B', '363B', '1850D', '500A', '742A', '2044B', '476A', '1520B', '459B', '1294C', '1985B', '313B', '1360B', '1878C', '2167A', '1807D', '456A', '1791D', '1542A', '1927A', '327A', '1915B', '977B', '1875A', '1690D', '2148A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
