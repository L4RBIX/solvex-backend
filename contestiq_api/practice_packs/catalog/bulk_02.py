"""High-priority Div2-A/B dual-oracle specs (unique-answer beginners)."""

from __future__ import annotations

import random

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

SPECS = []


def _append(**kwargs):
    SPECS.append(make_spec(**kwargs))


# 490A Team Olympiad
def _490a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    t = list(map(int, ls[1].split()))
    buckets = {1: [], 2: [], 3: []}
    for i, x in enumerate(t, 1):
        buckets[x].append(i)
    w = min(len(buckets[1]), len(buckets[2]), len(buckets[3]))
    out = [str(w)]
    for i in range(w):
        out.append(f"{buckets[1][i]} {buckets[2][i]} {buckets[3][i]}")
    return "\n".join(out) + "\n"


def _490a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = list(map(int, ls[1].split()))
    a = [[], [], []]
    for i, x in enumerate(t, 1):
        a[x - 1].append(i)
    w = min(map(len, a))
    rows = [str(w)] + [f"{a[0][i]} {a[1][i]} {a[2][i]}" for i in range(w)]
    return "\n".join(rows) + "\n"


_append(
    problem_id="490A",
    summary="Form the maximum number of teams with one programmer, one mathematician, and one PE student.",
    samples=({"input": "7\n1 3 1 3 2 1 2\n", "output": "2\n3 5 2\n6 7 4\n"},),
    solve=_490a,
    alt=_490a_alt,
    mutants={
        "ignore_third": lambda s: (
            lambda t: (
                (lambda a: (str(min(len(a[0]), len(a[1]))) + "\n"))(
                    [[i for i, x in enumerate(t, 1) if x == k] for k in (1, 2)]
                )
            )
        )(list(map(int, lines(s)[1].split()))),
        "zero": lambda s: "0\n",
    },
    generate=lambda rng: [
        "7\n1 3 1 3 2 1 2\n",
        "4\n2 1 1 2\n",
        "3\n1 2 3\n",
        "6\n1 1 1 1 1 1\n",
    ]
    + [
        str(n)
        + "\n"
        + " ".join(str(rng.randint(1, 3)) for _ in range(n))
        + "\n"
        for n in [rng.randint(3, 12) for _ in range(8)]
    ],
    family="greedy",
    checker="tokens",
)


# 472A Design Tutorial: Learn from Math
def _472a(stdin: str) -> str:
    n = int(stdin.strip())

    def composite(x: int) -> bool:
        if x < 4:
            return False
        d = 2
        while d * d <= x:
            if x % d == 0:
                return True
            d += 1
        return False

    for a in range(4, n):
        b = n - a
        if composite(a) and composite(b):
            return f"{a} {b}\n"
    return "4 4\n"


def _472a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    # Goldbach-style for even/odd composites
    if n % 2 == 0:
        return f"4 {n - 4}\n"
    return f"9 {n - 9}\n"


_append(
    problem_id="472A",
    summary="Represent n as sum of two composite numbers.",
    samples=({"input": "12\n", "output": "4 8\n"},),
    solve=_472a,
    alt=_472a_alt,
    mutants={
        "primes": lambda s: f"2 {int(s.strip())-2}\n",
        "one": lambda s: f"1 {int(s.strip())-1}\n",
    },
    generate=lambda rng: [f"{n}\n" for n in [12, 15, 8, 9, 10, 11, 100, 23, 24, 25, 999999]],
    family="math",
    checker="tokens",  # any valid pair OK — WAIT unique? Multiple answers valid!
)


# 472A has multiple valid outputs - SKIP by removing
SPECS.pop()


# 432A Choosing teams
def _432a(stdin: str) -> str:
    ls = lines(stdin)
    n, k = map(int, ls[0].split())
    y = list(map(int, ls[1].split()))
    return f"{sum(1 for v in y if v + k <= 5) // 3}\n"


def _432a_alt(stdin: str) -> str:
    ls = lines(stdin)
    n, k = map(int, ls[0].split())
    y = list(map(int, ls[1].split()))
    able = [v for v in y if 5 - v >= k]
    return f"{len(able) // 3}\n"


_append(
    problem_id="432A",
    summary="How many teams of 3 can participate if each member needs k more participations without exceeding 5.",
    samples=({"input": "5 2\n0 4 5 1 0\n", "output": "1\n"},),
    solve=_432a,
    alt=_432a_alt,
    mutants={
        "no_div": lambda s: (
            lambda ls: (
                f"{sum(1 for v in map(int, ls[1].split()) if v + int(ls[0].split()[1]) <= 5)}\n"
            )
        )(lines(s)),
        "k0": lambda s: (
            lambda ls: f"{sum(1 for v in map(int, ls[1].split()) if v <= 5) // 3}\n"
        )(lines(s)),
    },
    generate=lambda rng: [
        "5 2\n0 4 5 1 0\n",
        "6 4\n0 1 2 3 4 5\n",
        "3 1\n5 5 5\n",
    ]
    + [
        f"{n} {k}\n" + " ".join(str(rng.randint(0, 5)) for _ in range(n)) + "\n"
        for n, k in [(rng.randint(1, 15), rng.randint(1, 5)) for _ in range(8)]
    ],
    family="greedy",
)


# 80A Panoramix's Prediction
def _80a(stdin: str) -> str:
    n, m = map(int, stdin.split())

    def is_prime(x: int) -> bool:
        if x < 2:
            return False
        d = 2
        while d * d <= x:
            if x % d == 0:
                return False
            d += 1
        return True

    x = n + 1
    while not is_prime(x):
        x += 1
    return yes_no(x == m)


def _80a_alt(stdin: str) -> str:
    n, m = map(int, stdin.split())

    def primes_to(limit: int) -> list[int]:
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(limit**0.5) + 1):
            if sieve[i]:
                for j in range(i * i, limit + 1, i):
                    sieve[j] = False
        return [i for i, ok in enumerate(sieve) if ok]

    ps = primes_to(50)
    for i, p in enumerate(ps):
        if p == n:
            return yes_no(i + 1 < len(ps) and ps[i + 1] == m)
    return "NO\n"


_append(
    problem_id="80A",
    summary="Is m the next prime after n?",
    samples=({"input": "3 5\n", "output": "YES\n"},),
    solve=_80a,
    alt=_80a_alt,
    mutants={
        "any_prime": lambda s: yes_no(
            (lambda n, m: m > n and all(m % d for d in range(2, int(m**0.5) + 1)))(
                *map(int, s.split())
            )
        ),
        "equal": lambda s: yes_no((lambda n, m: n == m)(*map(int, s.split()))),
    },
    generate=lambda rng: [
        "3 5\n",
        "7 11\n",
        "2 3\n",
        "11 13\n",
        "2 2\n",
        "5 7\n",
        "13 17\n",
        "17 19\n",
        "19 23\n",
        "23 29\n",
    ],
    family="math",
    checker="tokens_ci",
)


# 703A Mishka and Game
def _703a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    m = c = 0
    for i in range(1, n + 1):
        a, b = map(int, ls[i].split())
        if a > b:
            m += 1
        elif b > a:
            c += 1
    if m > c:
        return "Mishka\n"
    if c > m:
        return "Chris\n"
    return "Friendship\n"


def _703a_alt(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    diff = 0
    for i in range(1, n + 1):
        a, b = map(int, ls[i].split())
        diff += (a > b) - (b > a)
    if diff > 0:
        return "Mishka\n"
    if diff < 0:
        return "Chris\n"
    return "Friendship\n"


_append(
    problem_id="703A",
    summary="Who wins more rounds, Mishka or Chris?",
    samples=({"input": "3\n3 5\n2 1\n4 2\n", "output": "Mishka\n"},),
    solve=_703a,
    alt=_703a_alt,
    mutants={
        "sum": lambda s: (
            "Mishka\n"
            if sum(int(lines(s)[i].split()[0]) for i in range(1, int(lines(s)[0]) + 1))
            >= sum(int(lines(s)[i].split()[1]) for i in range(1, int(lines(s)[0]) + 1))
            else "Chris\n"
        ),
        "first": lambda s: (
            "Mishka\n"
            if int(lines(s)[1].split()[0]) > int(lines(s)[1].split()[1])
            else "Chris\n"
        ),
    },
    generate=lambda rng: [
        "3\n3 5\n2 1\n4 2\n",
        "2\n1 1\n2 2\n",
        "1\n6 1\n",
    ]
    + [
        str(n)
        + "\n"
        + "\n".join(f"{rng.randint(1,6)} {rng.randint(1,6)}" for _ in range(n))
        + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="implementation",
    checker="tokens",
)


# 34B Sale
def _34b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = sorted(map(int, ls[1].split()))
    return f"{-sum(x for x in a[:m] if x < 0)}\n"


def _34b_alt(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    neg = sorted(x for x in a if x < 0)
    return f"{-sum(neg[:m])}\n"


_append(
    problem_id="34B",
    summary="Buy up to m TVs with negative prices to maximize earned money.",
    samples=({"input": "5 3\n-6 0 35 -2 4\n", "output": "8\n"},),
    solve=_34b,
    alt=_34b_alt,
    mutants={
        "all_neg": lambda s: f"{-sum(x for x in map(int, lines(s)[1].split()) if x < 0)}\n",
        "abs_m": lambda s: (
            lambda ls: f"{sum(abs(x) for x in sorted(map(int, ls[1].split()))[: int(ls[0].split()[1])])}\n"
        )(lines(s)),
    },
    generate=lambda rng: [
        "5 3\n-6 0 35 -2 4\n",
        "4 2\n-5 -4 0 1\n",
        "1 1\n-1\n",
        "3 3\n1 2 3\n",
    ]
    + [
        f"{n} {m}\n"
        + " ".join(str(rng.randint(-20, 20)) for _ in range(n))
        + "\n"
        for n, m in [(rng.randint(1, 10), rng.randint(1, 5)) for _ in range(8)]
    ],
    family="greedy",
)


# 431A Black Square
def _431a(stdin: str) -> str:
    ls = lines(stdin)
    a = list(map(int, ls[0].split()))
    s = ls[1]
    return f"{sum(a[int(ch) - 1] for ch in s)}\n"


def _431a_alt(stdin: str) -> str:
    ls = lines(stdin)
    a = list(map(int, ls[0].split()))
    total = 0
    for ch in ls[1]:
        total += a[ord(ch) - ord("1")]
    return f"{total}\n"


_append(
    problem_id="431A",
    summary="Calories burned for strip of black squares typed by digits 1..4.",
    samples=({"input": "1 2 3 4\n1234\n", "output": "10\n"},),
    solve=_431a,
    alt=_431a_alt,
    mutants={
        "zero_index": lambda s: (
            lambda ls: f"{sum(list(map(int, ls[0].split()))[int(ch)] for ch in ls[1] if ch!='4')}\n"
        )(lines(s)),
        "len_only": lambda s: f"{len(lines(s)[1])}\n",
    },
    generate=lambda rng: [
        "1 2 3 4\n1234\n",
        "1 5 3 2\n11221\n",
        "4 4 4 4\n4\n",
    ]
    + [
        f"{rng.randint(1,10)} {rng.randint(1,10)} {rng.randint(1,10)} {rng.randint(1,10)}\n"
        + "".join(str(rng.randint(1, 4)) for _ in range(rng.randint(1, 20)))
        + "\n"
        for _ in range(8)
    ],
    family="implementation",
)


# 1722A Spell Check
def _1722a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        out.append("YES" if sorted(s) == sorted("Timur") and n == 5 else "NO")
    return "\n".join(out) + "\n"


def _1722a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    idx = 1
    need = {"T": 1, "i": 1, "m": 1, "u": 1, "r": 1}
    for _ in range(t):
        n = int(ls[idx])
        s = ls[idx + 1]
        idx += 2
        from collections import Counter

        out.append("YES" if n == 5 and Counter(s) == need else "NO")
    return "\n".join(out) + "\n"


_append(
    problem_id="1722A",
    summary="Is the string a permutation of Timur?",
    samples=(
        {
            "input": "10\n5\nTimur\n5\nmiurT\n5\nTrumi\n5\nmturi\n5\nhtymu\n5\nTimur\n4\nTimr\n6\nTimuur\n5\nTimru\n5\nrimTu\n",
            "output": "YES\nYES\nYES\nYES\nNO\nYES\nNO\nNO\nYES\nYES\n",
        },
    ),
    solve=_1722a,
    alt=_1722a_alt,
    mutants={
        "casefold": lambda s: (
            "\n".join(
                "YES"
                if sorted(lines(s)[i + 1].lower()) == sorted("timur")
                else "NO"
                for i in range(1, len(lines(s)), 2)
            )
            + "\n"
        ),
        "equals": lambda s: (
            "\n".join(
                "YES" if lines(s)[i + 1] == "Timur" else "NO"
                for i in range(1, len(lines(s)), 2)
            )
            + "\n"
        ),
    },
    generate=lambda rng: [
        "10\n5\nTimur\n5\nmiurT\n5\nTrumi\n5\nmturi\n5\nhtymu\n5\nTimur\n4\nTimr\n6\nTimuur\n5\nTimru\n5\nrimTu\n",
        "3\n5\nTimur\n5\nrimuT\n5\nabcde\n",
        "1\n5\nTumir\n",
        "1\n1\nT\n",
        "2\n5\nmuriT\n5\nTimuR\n",
        "1\n5\nTi mur\n".replace(" ", ""),
        "1\n5\nTimru\n",
        "1\n5\nrimTu\n",
        "1\n5\nmitru\n",
        "1\n5\nTimuR\n",
    ],
    family="strings",
    checker="tokens_ci",
)


# 1370A Maximum GCD
def _1370a(stdin: str) -> str:
    t = int(lines(stdin)[0])
    out = []
    for n in map(int, lines(stdin)[1 : 1 + t]):
        out.append(str(n // 2))
    return "\n".join(out) + "\n"


def _1370a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        n = int(ls[i])
        out.append(str(max(1, n // 2)))
    return "\n".join(out) + "\n"


_append(
    problem_id="1370A",
    summary="Maximum gcd(a,b) for 1 <= a < b <= n.",
    samples=({"input": "2\n3\n5\n", "output": "1\n2\n"},),
    solve=_1370a,
    alt=_1370a_alt,
    mutants={
        "n": lambda s: "\n".join(lines(s)[1:]) + "\n",
        "n_minus": lambda s: "\n".join(str(int(x) - 1) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "2\n3\n5\n",
        "1\n2\n",
        "1\n4\n",
        "3\n2\n3\n100\n",
    ]
    + [
        str(t) + "\n" + "\n".join(str(rng.randint(2, 1000)) for _ in range(t)) + "\n"
        for t in [rng.randint(1, 5) for _ in range(6)]
    ],
    family="math",
)


# 313A Ilya and Bank Account
def _313a(stdin: str) -> str:
    n = int(stdin.strip())
    if n >= 0:
        return f"{n}\n"
    s = str(n)
    a = int(s[:-1])
    b = int(s[:-2] + s[-1])
    return f"{max(a, b)}\n"


def _313a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    if n >= 0:
        return f"{n}\n"
    return f"{max(n // 10, (n // 100) * 10 + (n % 10))}\n"


_append(
    problem_id="313A",
    summary="Delete one digit from a negative account balance to maximize it.",
    samples=({"input": "-100\n", "output": "0\n"},),
    solve=_313a,
    alt=_313a_alt,
    mutants={
        "always_drop_last": lambda s: f"{int(s.strip()) // 10}\n",
        "abs": lambda s: f"{abs(int(s.strip()))}\n",
    },
    generate=lambda rng: [f"{x}\n" for x in [-100, -10, -11, -19, -99, 0, 5, -1234, -1000, 42, -1]],
    family="math",
)


# 1367A Short Substrings
def _1367a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        b = ls[i]
        out.append(b[0] + b[1::2])
    return "\n".join(out) + "\n"


def _1367a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for i in range(1, t + 1):
        b = ls[i]
        a = [b[0]]
        for j in range(1, len(b), 2):
            a.append(b[j])
        out.append("".join(a))
    return "\n".join(out) + "\n"


_append(
    problem_id="1367A",
    summary="Recover string a from b where b concatenates consecutive pairs of a.",
    samples=({"input": "4\nabba\nac\nacc\naaaa\n", "output": "aba\nac\nac\naaa\n"},),
    solve=_1367a,
    alt=_1367a_alt,
    mutants={
        "all": lambda s: "\n".join(lines(s)[1:]) + "\n",
        "even": lambda s: "\n".join(x[::2] for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "4\nabba\nac\nacc\naaaa\n",
        "1\nab\n",
        "1\nabcd\n",
        "2\nzzzz\nxy\n",
    ]
    + [
        str(t)
        + "\n"
        + "\n".join(
            "".join(rng.choice("abc") for _ in range(rng.randint(2, 10))) for _ in range(t)
        )
        + "\n"
        for t in [rng.randint(1, 4) for _ in range(6)]
    ],
    family="strings",
)


# 1703B ICPC Balloons
def _1703b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        out.append(str(n + len(set(s))))
    return "\n".join(out) + "\n"


def _1703b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(ls[idx])
        s = ls[idx + 1]
        idx += 2
        seen = set()
        total = 0
        for ch in s:
            total += 2 if ch not in seen else 1
            seen.add(ch)
        out.append(str(total))
    return "\n".join(out) + "\n"


_append(
    problem_id="1703B",
    summary="Balloons: 2 for first solve of a problem letter, else 1.",
    samples=({"input": "3\n3\nABA\n1\nA\n5\nAAAAA\n", "output": "5\n2\n6\n"},),
    solve=_1703b,
    alt=_1703b_alt,
    mutants={
        "only_n": lambda s: "\n".join(lines(s)[1::2]) + "\n",
        "only_unique": lambda s: (
            "\n".join(str(len(set(lines(s)[i]))) for i in range(2, len(lines(s)), 2)) + "\n"
        ),
    },
    generate=lambda rng: [
        "3\n3\nABA\n1\nA\n5\nAAAAA\n",
        "1\n4\nABCD\n",
        "1\n2\nAA\n",
    ]
    + [
        "1\n"
        + str(n)
        + "\n"
        + "".join(rng.choice("ABCDE") for _ in range(n))
        + "\n"
        for n in [rng.randint(1, 15) for _ in range(8)]
    ],
    family="strings",
)


# 1520D Same Count One (actually 1520D Same Differences)
def _1520d(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        from collections import Counter

        c = Counter(v - idx for idx, v in enumerate(a))
        ans = sum(v * (v - 1) // 2 for v in c.values())
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _1520d_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        ans = 0
        for x in range(n):
            for y in range(x + 1, n):
                if a[y] - a[x] == y - x:
                    ans += 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


_append(
    problem_id="1520D",
    summary="Count pairs (i,j) with a_j - a_i = j - i.",
    samples=({"input": "4\n6\n3 5 1 4 6 6\n3\n1 2 3\n1\n1000000000\n2\n1 1\n", "output": "2\n3\n0\n0\n"},),
    solve=_1520d,
    alt=_1520d_alt,
    mutants={
        "eq_values": lambda s: "0\n" * int(lines(s)[0]),
        "n_choose_2": lambda s: (
            "\n".join(
                str(int(lines(s)[i]) * (int(lines(s)[i]) - 1) // 2)
                for i in range(1, len(lines(s)), 2)
            )
            + "\n"
        ),
    },
    generate=lambda rng: [
        "4\n6\n3 5 1 4 6 6\n3\n1 2 3\n1\n1000000000\n2\n1 1\n",
        "1\n4\n1 2 3 4\n",
        "1\n5\n5 4 3 2 1\n",
    ]
    + [
        "1\n"
        + str(n)
        + "\n"
        + " ".join(str(rng.randint(1, 20)) for _ in range(n))
        + "\n"
        for n in [rng.randint(1, 12) for _ in range(7)]
    ],
    family="math",
)


# 1374C Move Brackets
def _1374c(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        bal = 0
        need = 0
        for ch in s:
            bal += 1 if ch == "(" else -1
            if bal < 0:
                need += 1
                bal = 0
        out.append(str(need))
    return "\n".join(out) + "\n"


def _1374c_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(ls[idx])
        s = ls[idx + 1]
        idx += 2
        stack = 0
        moves = 0
        for ch in s:
            if ch == "(":
                stack += 1
            elif stack:
                stack -= 1
            else:
                moves += 1
        out.append(str(moves))
    return "\n".join(out) + "\n"


_append(
    problem_id="1374C",
    summary="Minimum moves to make a bracket sequence balanced.",
    samples=({"input": "4\n2\n)\n(\n4\n()()\n8\n())()()(\n4\n)))(\n", "output": "1\n0\n1\n2\n"},),
    solve=_1374c,
    alt=_1374c_alt,
    mutants={
        "half": lambda s: (
            "\n".join(str(int(lines(s)[i]) // 4) for i in range(1, len(lines(s)), 2)) + "\n"
        ),
        "count_close": lambda s: (
            "\n".join(str(lines(s)[i + 1].count(")")) for i in range(1, len(lines(s)), 2))
            + "\n"
        ),
    },
    generate=lambda rng: [
        "4\n2\n)(\n4\n()()\n8\n())()()(\n4\n)))(\n",
        "1\n2\n()\n",
        "1\n6\n)))(((\n",
    ]
    + [
        "1\n"
        + str(2 * k)
        + "\n"
        + "".join(rng.choice("()") for _ in range(2 * k))
        + "\n"
        for k in [rng.randint(1, 6) for _ in range(8)]
    ],
    family="strings",
)


# 1343B Balanced Array
def _1343b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for n in map(int, ls[1 : 1 + t]):
        if n % 4 != 0:
            out.append("NO")
            continue
        half = n // 2
        evens = [2 * i for i in range(1, half + 1)]
        odds = [2 * i - 1 for i in range(1, half)]
        odds.append(sum(evens) - sum(odds))
        out.append("YES")
        out.append(" ".join(map(str, evens + odds)))
    return "\n".join(out) + "\n"


def _1343b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for n in map(int, ls[1 : 1 + t]):
        if n % 4:
            out.append("NO")
            continue
        k = n // 2
        left = list(range(2, 2 * k + 1, 2))
        right = list(range(1, 2 * k - 1, 2)) + [3 * k - 1]
        out.append("YES")
        out.append(" ".join(map(str, left + right)))
    return "\n".join(out) + "\n"


_append(
    problem_id="1343B",
    summary="Construct an array of n elements, first half even, second half odd, equal sums.",
    samples=(
        {
            "input": "5\n2\n4\n6\n8\n10\n",
            "output": "NO\nYES\n2 4 1 5\nNO\nYES\n2 4 6 8 1 3 5 11\nNO\n",
        },
    ),
    solve=_1343b,
    alt=_1343b_alt,
    mutants={
        "always_yes": lambda s: "YES\n1 2 3 4\n" * int(lines(s)[0]),
        "mod2": lambda s: "\n".join("YES" if int(x) % 2 == 0 else "NO" for x in lines(s)[1:])
        + "\n",
    },
    generate=lambda rng: [
        "5\n2\n4\n6\n8\n10\n",
        "1\n4\n",
        "1\n8\n",
        "1\n12\n",
        "3\n2\n4\n16\n",
        "1\n100\n",
        "1\n3\n",
        "1\n7\n",
        "2\n4\n8\n",
        "1\n20\n",
    ],
    family="constructive",
    checker="tokens",  # YES/NO part unique; constructed arrays may differ!
)

# 1343B constructive multi-answer — remove
SPECS.pop()


# 474B Worms
def _474b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    m = int(ls[2])
    q = list(map(int, ls[3].split()))
    pref = []
    s = 0
    for x in a:
        s += x
        pref.append(s)
    import bisect

    out = []
    for x in q:
        out.append(str(bisect.bisect_left(pref, x) + 1))
    return "\n".join(out) + "\n"


def _474b_alt(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    m = int(ls[2])
    q = list(map(int, ls[3].split()))
    out = []
    for x in q:
        s = 0
        ans = n
        for i, v in enumerate(a, 1):
            s += v
            if s >= x:
                ans = i
                break
        out.append(str(ans))
    return "\n".join(out) + "\n"


_append(
    problem_id="474B",
    summary="Which pile contains the juicy worm numbered q_i?",
    samples=({"input": "5\n2 7 3 4 9\n3\n1 25 11\n", "output": "1\n5\n3\n"},),
    solve=_474b,
    alt=_474b_alt,
    mutants={
        "one": lambda s: "1\n" * int(lines(s)[2]),
        "n": lambda s: f"{lines(s)[0]}\n" * int(lines(s)[2]),
    },
    generate=lambda rng: [
        "5\n2 7 3 4 9\n3\n1 25 11\n",
        "1\n5\n3\n1 3 5\n",
        "3\n1 1 1\n3\n1 2 3\n",
    ]
    + [
        (
            lambda n: (
                f"{n}\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(n))
                + "\n"
                + "3\n1 2 3\n"
            )
        )(rng.randint(1, 8))
        for _ in range(7)
    ],
    family="binary_search",
)


# 1367B Even Array
def _1367b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        odd = even = 0
        for idx, v in enumerate(a):
            if idx % 2 != v % 2:
                if idx % 2 == 0:
                    even += 1
                else:
                    odd += 1
        out.append(str(even if even == odd else -1))
    return "\n".join(out) + "\n"


def _1367b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        bad_even = sum(1 for idx, v in enumerate(a) if idx % 2 == 0 and v % 2 == 1)
        bad_odd = sum(1 for idx, v in enumerate(a) if idx % 2 == 1 and v % 2 == 0)
        out.append(str(bad_even if bad_even == bad_odd else -1))
    return "\n".join(out) + "\n"


_append(
    problem_id="1367B",
    summary="Minimum swaps so a[i]%2 == i%2, or -1.",
    samples=({"input": "4\n4\n3 2 7 6\n3\n3 2 6\n1\n7\n7\n4 9 2 1 18 3 0\n", "output": "0\n-1\n0\n3\n"},),
    solve=_1367b,
    alt=_1367b_alt,
    mutants={
        "sum_bad": lambda s: "0\n",
        "always_neg": lambda s: "-1\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "4\n4\n3 2 7 6\n3\n3 2 6\n1\n7\n7\n4 9 2 1 18 3 0\n",
        "1\n2\n1 2\n",
        "1\n2\n2 1\n",
    ]
    + [
        "1\n"
        + str(n)
        + "\n"
        + " ".join(str(rng.randint(0, 20)) for _ in range(n))
        + "\n"
        for n in [rng.randint(1, 10) for _ in range(8)]
    ],
    family="greedy",
)


# 1374A Required Remainder
def _1374a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for line in ls[1 : 1 + t]:
        x, y, n = map(int, line.split())
        out.append(str(n - (n - y) % x))
    return "\n".join(out) + "\n"


def _1374a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for line in ls[1 : 1 + t]:
        x, y, n = map(int, line.split())
        k = n // x * x + y
        if k > n:
            k -= x
        out.append(str(k))
    return "\n".join(out) + "\n"


_append(
    problem_id="1374A",
    summary="Largest k <= n with k % x == y.",
    samples=({"input": "5\n7 5 12345\n5 0 4\n10 5 15\n17 8 54321\n499999999 999999998 1000000000\n", "output": "12339\n0\n15\n54306\n999999998\n"},),
    solve=_1374a,
    alt=_1374a_alt,
    mutants={
        "n": lambda s: "\n".join(line.split()[-1] for line in lines(s)[1:]) + "\n",
        "y": lambda s: "\n".join(line.split()[1] for line in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "5\n7 5 12345\n5 0 4\n10 5 15\n17 8 54321\n499999999 999999998 1000000000\n",
        "1\n3 1 10\n",
        "1\n2 0 1\n",
    ]
    + [
        "1\n"
        + f"{x} {y} {n}\n"
        for x, y, n in [
            (rng.randint(2, 50), rng.randint(0, 20), rng.randint(20, 5000)) for _ in range(8)
        ]
    ],
    family="math",
)


# 492A Vanya and Cubes
def _492a(stdin: str) -> str:
    n = int(stdin.strip())
    h = 0
    used = 0
    while True:
        h += 1
        need = h * (h + 1) // 2
        if used + need > n:
            return f"{h - 1}\n"
        used += need


def _492a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    h = 0
    total = 0
    while total + (h + 1) * (h + 2) // 2 <= n:
        h += 1
        total += h * (h + 1) // 2
    return f"{h}\n"


_append(
    problem_id="492A",
    summary="Maximum height of a cube pyramid with n cubes.",
    samples=({"input": "10\n", "output": "3\n"},),
    solve=_492a,
    alt=_492a_alt,
    mutants={
        "sqrt": lambda s: f"{int(int(s.strip()) ** 0.5)}\n",
        "div2": lambda s: f"{int(s.strip()) // 2}\n",
    },
    generate=lambda rng: [f"{n}\n" for n in [1, 2, 3, 4, 10, 15, 20, 25, 100, 500, 10000]],
    family="math",
)


# 1619A Square String?
def _1619a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for s in ls[1 : 1 + t]:
        out.append("YES" if len(s) % 2 == 0 and s[: len(s) // 2] == s[len(s) // 2 :] else "NO")
    return "\n".join(out) + "\n"


def _1619a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for s in ls[1 : 1 + t]:
        n = len(s)
        ok = n % 2 == 0 and all(s[i] == s[i + n // 2] for i in range(n // 2))
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


_append(
    problem_id="1619A",
    summary="Is the string a square (tt for some t)?",
    samples=({"input": "10\na\naa\nabc\nabab\naba\naaaaaa\nabacaba\nx\nxxx\nxyxyxy\n", "output": "NO\nYES\nNO\nYES\nNO\nYES\nNO\nNO\nNO\nYES\n"},),
    solve=_1619a,
    alt=_1619a_alt,
    mutants={
        "even_len": lambda s: "\n".join("YES" if len(x) % 2 == 0 else "NO" for x in lines(s)[1:])
        + "\n",
        "pal": lambda s: "\n".join("YES" if x == x[::-1] else "NO" for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "10\na\naa\nabc\nabab\naba\naaaaaa\nabacaba\nx\nxxx\nxyxyxy\n",
        "1\nabab\n",
        "1\nabba\n",
    ]
    + [
        "1\n" + "".join(rng.choice("ab") for _ in range(rng.randint(1, 12))) + "\n"
        for _ in range(8)
    ],
    family="strings",
    checker="tokens_ci",
)


# 1433A Boring Apartments
def _1433a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for x in ls[1 : 1 + t]:
        d = int(x[0])
        L = len(x)
        out.append(str((d - 1) * 10 + L * (L + 1) // 2))
    return "\n".join(out) + "\n"


def _1433a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for x in ls[1 : 1 + t]:
        total = 0
        for dig in range(1, 10):
            s = ""
            for _ in range(4):
                s += str(dig)
                total += len(s)
                if s == x:
                    out.append(str(total))
                    break
            else:
                continue
            break
    return "\n".join(out) + "\n"


_append(
    problem_id="1433A",
    summary="Keypresses to type apartment x on a broken keypad of repeated digits.",
    samples=({"input": "4\n22\n1\n777\n100\n".replace("100","9999") if False else "4\n22\n1\n777\n9999\n", "output": "13\n1\n24\n46\n"},),
    solve=_1433a,
    alt=_1433a_alt,
    mutants={
        "len": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n",
        "digit": lambda s: "\n".join(x[0] for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "4\n22\n1\n777\n9999\n",
        "1\n2\n",
        "1\n22\n",
        "1\n222\n",
        "1\n2222\n",
        "1\n5\n",
        "1\n55\n",
        "1\n555\n",
        "1\n5555\n",
        "1\n9\n",
        "1\n99\n",
    ],
    family="math",
)


# 1926A Vlad and the Best of Five
def _1926a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for s in ls[1 : 1 + t]:
        out.append("A" if s.count("A") > s.count("B") else "B")
    return "\n".join(out) + "\n"


def _1926a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for s in ls[1 : 1 + t]:
        out.append("A" if sum(1 for ch in s if ch == "A") >= 3 else "B")
    return "\n".join(out) + "\n"


_append(
    problem_id="1926A",
    summary="Which letter appears more in a string of five A/B characters?",
    samples=({"input": "4\nABABA\nBBBAA\nABABB\nAAAAA\n", "output": "A\nB\nB\nA\n"},),
    solve=_1926a,
    alt=_1926a_alt,
    mutants={
        "first": lambda s: "\n".join(x[0] for x in lines(s)[1:]) + "\n",
        "always_a": lambda s: "A\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "4\nABABA\nBBBAA\nABABB\nAAAAA\n",
        "1\nAAAAA\n",
        "1\nBBBBB\n",
        "1\nAABBB\n",
    ]
    + [
        "1\n" + "".join(rng.choice("AB") for _ in range(5)) + "\n" for _ in range(8)
    ],
    family="strings",
)


# 1742B Increasing
def _1742b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        out.append("YES" if len(set(a)) == n else "NO")
    return "\n".join(out) + "\n"


def _1742b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = sorted(map(int, ls[i + 1].split()))
        i += 2
        out.append("YES" if all(a[j] < a[j + 1] for j in range(n - 1)) else "NO")
    return "\n".join(out) + "\n"


_append(
    problem_id="1742B",
    summary="Can the array be rearranged to be strictly increasing?",
    samples=({"input": "3\n4\n1 1 2 3\n3\n1 2 3\n1\n100\n", "output": "NO\nYES\nYES\n"},),
    solve=_1742b,
    alt=_1742b_alt,
    mutants={
        "sorted": lambda s: "YES\n" * int(lines(s)[0]),
        "n1": lambda s: (
            "\n".join(
                "YES" if int(lines(s)[i]) == 1 else "NO" for i in range(1, len(lines(s)), 2)
            )
            + "\n"
        ),
    },
    generate=lambda rng: [
        "3\n4\n1 1 2 3\n3\n1 2 3\n1\n100\n",
        "1\n2\n1 1\n",
        "1\n2\n2 1\n",
    ]
    + [
        "1\n"
        + str(n)
        + "\n"
        + " ".join(str(rng.randint(1, 10)) for _ in range(n))
        + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="sortings",
    checker="tokens_ci",
)


# 1283A Minutes Before the New Year
def _1283a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for line in ls[1 : 1 + t]:
        h, m = map(int, line.split())
        out.append(str(24 * 60 - h * 60 - m))
    return "\n".join(out) + "\n"


def _1283a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for line in ls[1 : 1 + t]:
        h, m = map(int, line.split())
        out.append(str((23 - h) * 60 + (60 - m)))
    return "\n".join(out) + "\n"


_append(
    problem_id="1283A",
    summary="Minutes remaining until New Year from h:m.",
    samples=({"input": "5\n23 55\n23 0\n0 1\n4 20\n23 59\n", "output": "5\n60\n1439\n1180\n1\n"},),
    solve=_1283a,
    alt=_1283a_alt,
    mutants={
        "hours": lambda s: "\n".join(str(24 - int(x.split()[0])) for x in lines(s)[1:]) + "\n",
        "mins": lambda s: "\n".join(str(60 - int(x.split()[1])) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "5\n23 55\n23 0\n0 1\n4 20\n23 59\n",
        "1\n0 0\n",
        "1\n12 0\n",
    ]
    + [
        "1\n" + f"{rng.randint(0,23)} {rng.randint(0,59)}\n" for _ in range(8)
    ],
    family="math",
)


# 1772A Ordinary Numbers? wait 1772A A+B?
def _1772a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for expr in ls[1 : 1 + t]:
        a, b = expr.split("+")
        out.append(str(int(a) + int(b)))
    return "\n".join(out) + "\n"


def _1772a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for expr in ls[1 : 1 + t]:
        a, b = map(int, expr.split("+"))
        out.append(str(a + b))
    return "\n".join(out) + "\n"


_append(
    problem_id="1772A",
    summary="Evaluate expressions a+b with single digits.",
    samples=({"input": "4\n4+2\n0+0\n3+7\n8+9\n", "output": "6\n0\n10\n17\n"},),
    solve=_1772a,
    alt=_1772a_alt,
    mutants={
        "prod": lambda s: "\n".join(
            str(int(x.split("+")[0]) * int(x.split("+")[1])) for x in lines(s)[1:]
        )
        + "\n",
        "left": lambda s: "\n".join(x.split("+")[0] for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "4\n4+2\n0+0\n3+7\n8+9\n",
        "1\n1+1\n",
        "1\n9+9\n",
    ]
    + [
        "1\n" + f"{rng.randint(0,9)}+{rng.randint(0,9)}\n" for _ in range(8)
    ],
    family="math",
)


# 1472B Fair Division
def _1472b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        ones = a.count(1)
        twos = a.count(2)
        total = ones + 2 * twos
        if total % 2:
            out.append("NO")
        elif (total // 2) % 2 == 0 or ones > 0:
            # more precise:
            if twos % 2 == 0:
                out.append("YES")
            else:
                out.append("YES" if ones >= 2 else "NO")
        else:
            out.append("NO")
    return "\n".join(out) + "\n"


def _1472b_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    i = 1
    for _ in range(t):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        s = sum(a)
        if s % 2:
            out.append("NO")
            continue
        need = s // 2
        # knapsack tiny
        possible = {0}
        for x in a:
            possible |= {p + x for p in possible}
        out.append("YES" if need in possible else "NO")
    return "\n".join(out) + "\n"


_append(
    problem_id="1472B",
    summary="Can candies of weights 1 and 2 be split into two equal sums?",
    samples=({"input": "5\n2\n1 1\n2\n1 2\n4\n1 2 1 2\n3\n2 2 2\n4\n1 1 1 1\n", "output": "YES\nNO\nYES\nNO\nYES\n"},),
    solve=_1472b,
    alt=_1472b_alt,
    mutants={
        "sum_even": lambda s: (
            # wrong: only check total even
            "\n".join(["YES"] * int(lines(s)[0])) + "\n"
        ),
        "always_no": lambda s: "NO\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "5\n2\n1 1\n2\n1 2\n4\n1 2 1 2\n3\n2 2 2\n4\n1 1 1 1\n",
        "1\n1\n2\n",
        "1\n3\n1 1 2\n",
    ]
    + [
        "1\n"
        + str(n)
        + "\n"
        + " ".join(str(rng.choice([1, 2])) for _ in range(n))
        + "\n"
        for n in [rng.randint(1, 10) for _ in range(8)]
    ],
    family="math",
    checker="tokens_ci",
)


# 1551A Polycarp and Coins
def _1551a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for n in map(int, ls[1 : 1 + t]):
        c2 = n // 3
        c1 = n // 3
        if n % 3 == 1:
            c1 += 1
        elif n % 3 == 2:
            c2 += 1
        out.append(f"{c1} {c2}")
    return "\n".join(out) + "\n"


def _1551a_alt(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    out = []
    for n in map(int, ls[1 : 1 + t]):
        c1 = (n + 1) // 3
        c2 = n // 3
        if c1 + 2 * c2 != n:
            c1 = n // 3
            c2 = (n + 1) // 3
            if abs(c1 - c2) > 1:
                c2 = n // 3
                c1 = n - 2 * c2
        # Standard unique solution: minimize |c1-c2| with c1+2*c2=n
        best = None
        for x in range(n + 1):
            if (n - x) % 2 == 0:
                y = (n - x) // 2
                cand = (x, y)
                if best is None or abs(cand[0] - cand[1]) < abs(best[0] - best[1]):
                    best = cand
        out.append(f"{best[0]} {best[1]}")
    return "\n".join(out) + "\n"


_append(
    problem_id="1551A",
    summary="Split n into c1*1 + c2*2 minimizing |c1-c2|.",
    samples=({"input": "6\n1\n2\n3\n4\n5\n6\n", "output": "1 0\n0 1\n1 1\n2 1\n1 2\n2 2\n"},),
    solve=_1551a,
    alt=_1551a_alt,
    mutants={
        "all_ones": lambda s: "\n".join(f"{x} 0" for x in lines(s)[1:]) + "\n",
        "all_twos": lambda s: "\n".join(
            f"0 {int(x)//2}" if int(x) % 2 == 0 else f"1 {int(x)//2}" for x in lines(s)[1:]
        )
        + "\n",
    },
    generate=lambda rng: [
        "6\n1\n2\n3\n4\n5\n6\n",
        "1\n100\n",
        "1\n7\n",
    ]
    + ["1\n" + f"{rng.randint(1, 1000)}\n" for _ in range(8)],
    family="math",
    checker="tokens",
)


# 1837A Grass Field? 1837A is "Grasshopper" - actually 1837A Grasshopper
# Skip uncertain; add 749A Bachgold
def _749a(stdin: str) -> str:
    n = int(stdin.strip())
    if n % 2 == 0:
        k = n // 2
        return f"{k}\n" + " ".join(["2"] * k) + "\n"
    k = n // 2
    parts = ["2"] * (k - 1) + ["3"]
    return f"{k}\n" + " ".join(parts) + "\n"


def _749a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    parts = []
    if n % 2:
        parts.append(3)
        n -= 3
    parts.extend([2] * (n // 2))
    return f"{len(parts)}\n" + " ".join(map(str, parts)) + "\n"


_append(
    problem_id="749A",
    summary="Represent n as sum of maximum number of primes.",
    samples=({"input": "5\n", "output": "2\n2 3\n"},),
    solve=_749a,
    alt=_749a_alt,
    mutants={
        "all_n": lambda s: f"1\n{s.strip()}\n",
        "ones": lambda s: f"{s.strip()}\n" + " ".join(["1"] * int(s.strip())) + "\n",
    },
    generate=lambda rng: [f"{n}\n" for n in [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 100]],
    family="math",
    checker="tokens",
)

# 749A multi-answer order - tokens OK if same multiset. Good.

_KEEP = ['432A', '703A', '34B', '431A', '1370A', '1367A', '1703B', '492A', '1926A', '1742B', '1283A', '1772A', '1472B', '1551A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
