"""Verified unique-answer oracles — expansion batch 10."""
from __future__ import annotations

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no

SPECS = []


def add(**kw):
    SPECS.append(make_spec(**kw))


def _isp(x: int) -> bool:
    if x < 2:
        return False
    d = 2
    while d * d <= x:
        if x % d == 0:
            return False
        d += 1
    return True


def _next_prime(n: int) -> int:
    x = n + 1
    while not _isp(x):
        x += 1
    return x


add(
    problem_id="80A",
    summary="Is m the next prime after n?",
    samples=({"input": "3 5\n", "output": "YES\n"}, {"input": "7 11\n", "output": "YES\n"}),
    solve=lambda s: yes_no(_next_prime(int(s.split()[0])) == int(s.split()[1])),
    alt=lambda s: yes_no(next(x for x in range(int(s.split()[0]) + 1, 200) if _isp(x)) == int(s.split()[1])),
    mutants={
        "gt": lambda s: yes_no(int(s.split()[1]) > int(s.split()[0])),
        "prime_m": lambda s: yes_no(_isp(int(s.split()[1]))),
    },
    generate=lambda rng: [
        "3 5\n", "7 11\n", "2 3\n", "11 13\n", "5 7\n", "13 17\n",
        "17 19\n", "19 23\n", "23 29\n", "2 4\n", "11 12\n", "3 7\n",
    ],
    family="math",
    checker="tokens_ci",
)


add(
    problem_id="1433A",
    summary="Keypresses for boring apartments.",
    samples=({"input": "4\n22\n1\n777\n9999\n", "output": "13\n1\n66\n90\n"},),
    solve=lambda s: "\n".join(
        str(10 * (int(x[0]) - 1) + len(x) * (len(x) + 1) // 2) for x in lines(s)[1:]
    ) + "\n",
    alt=lambda s: "\n".join(
        str(
            sum(k for d in range(1, int(x[0])) for k in range(1, 5))
            + sum(range(1, len(x) + 1))
        )
        for x in lines(s)[1:]
    ) + "\n",
    mutants={
        "len": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n",
        "dig": lambda s: "\n".join(x[0] for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["4\n22\n1\n777\n9999\n"]
    + [f"1\n{str(d) * L}\n" for d in range(1, 10) for L in range(1, 5)],
    family="math",
)


add(
    problem_id="1374A",
    summary="Largest k <= n with k % x == y.",
    samples=(
        {
            "input": "5\n7 5 12345\n5 0 4\n10 5 15\n17 8 54321\n499999999 999999998 1000000000\n",
            "output": "12339\n0\n15\n54306\n999999998\n",
        },
    ),
    solve=lambda s: "\n".join(
        str((lambda x, y, n: n - (n - y) % x)(*map(int, line.split())))
        for line in lines(s)[1:]
    ) + "\n",
    alt=lambda s: "\n".join(
        str(
            (
                lambda x, y, n: (
                    k := n // x * x + y,
                    k if k <= n else k - x,
                )[1]
            )(*map(int, line.split()))
        )
        for line in lines(s)[1:]
    ) + "\n",
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
        f"1\n{rng.randint(2, 50)} {rng.randint(0, min(20, rng.randint(2,50)-1))} {rng.randint(50, 5000)}\n"
        for _ in range(10)
    ],
    family="math",
)


add(
    problem_id="1619A",
    summary="Is the string a square (tt)?",
    samples=(
        {
            "input": "6\naa\nab\nabab\naaaa\nabc\nxyxy\n",
            "output": "YES\nNO\nYES\nYES\nNO\nYES\n",
        },
    ),
    solve=lambda s: "\n".join(
        "YES" if len(x) % 2 == 0 and x[: len(x) // 2] == x[len(x) // 2 :] else "NO"
        for x in lines(s)[1:]
    ) + "\n",
    alt=lambda s: "\n".join(
        "YES"
        if len(x) % 2 == 0 and all(x[i] == x[i + len(x) // 2] for i in range(len(x) // 2))
        else "NO"
        for x in lines(s)[1:]
    ) + "\n",
    mutants={
        "even": lambda s: "\n".join("YES" if len(x) % 2 == 0 else "NO" for x in lines(s)[1:]) + "\n",
        "yes": lambda s: "YES\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "6\naa\nab\nabab\naaaa\nabc\nxyxy\n",
        "1\na\n",
        "1\nabab\n",
        "1\nabba\n",
        "1\nabcabc\n",
        "1\nxxxx\n",
        "1\naba\n",
        "1\nzzzzzz\n",
        "1\nab\n",
        "1\naaaa\n",
        "1\nabcdabcd\n",
    ],
    family="strings",
    checker="tokens_ci",
)


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


add(
    problem_id="492A",
    summary="Max pyramid height with n cubes.",
    samples=({"input": "10\n", "output": "3\n"}, {"input": "1\n", "output": "1\n"}),
    solve=_492a,
    alt=_492a_alt,
    mutants={
        "sqrt": lambda s: f"{int(int(s.strip()) ** 0.5)}\n",
        "half": lambda s: f"{int(s.strip()) // 2}\n",
    },
    generate=lambda rng: [f"{n}\n" for n in [1, 2, 3, 4, 10, 15, 20, 25, 100, 500, 10000]],
    family="math",
)


# 1722A Spell Check
def _1722a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        out.append("YES" if n == 5 and sorted(s) == sorted("Timur") else "NO")
    return "\n".join(out) + "\n"


def _1722a_alt(stdin: str) -> str:
    from collections import Counter
    ls = lines(stdin)
    out = []
    i = 1
    need = Counter("Timur")
    for _ in range(int(ls[0])):
        n = int(ls[i])
        s = ls[i + 1]
        i += 2
        out.append("YES" if n == 5 and Counter(s) == need else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1722A",
    summary="Is the string a permutation of Timur?",
    samples=(
        {
            "input": "5\n5\nTimur\n5\nmiurT\n5\nTrumi\n5\nhtymu\n4\nTimr\n",
            "output": "YES\nYES\nYES\nNO\nNO\n",
        },
    ),
    solve=_1722a,
    alt=_1722a_alt,
    mutants={
        "equals": lambda s: "\n".join(
            "YES" if lines(s)[i] == "Timur" else "NO" for i in range(2, len(lines(s)), 2)
        ) + "\n",
        "len5": lambda s: "\n".join(
            "YES" if lines(s)[i - 1] == "5" else "NO" for i in range(2, len(lines(s)), 2)
        ) + "\n",
    },
    generate=lambda rng: [
        "5\n5\nTimur\n5\nmiurT\n5\nTrumi\n5\nhtymu\n4\nTimr\n",
        "1\n5\nrimTu\n",
        "1\n5\nTimru\n",
        "1\n5\nTumir\n",
        "1\n5\nabcde\n",
        "1\n1\nT\n",
        "1\n6\nTimuur\n",
        "1\n5\nmitru\n",
        "1\n5\nTimuR\n",
        "1\n5\nmuriT\n",
        "1\n5\nmturi\n",
    ],
    family="strings",
    checker="tokens_ci",
)


# 313A Ilya and Bank Account
def _313a(stdin: str) -> str:
    n = int(stdin.strip())
    if n >= 0:
        return f"{n}\n"
    s = str(n)
    # delete last or second-last digit
    a = int(s[:-1])
    b = int(s[:-2] + s[-1]) if len(s) > 2 else int(s[-1])  # e.g. -1 -> edge
    return f"{max(a, b)}\n"


def _313a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    if n >= 0:
        return f"{n}\n"
    return f"{max(n // 10, n // 100 * 10 + n % 10)}\n"


add(
    problem_id="313A",
    summary="Delete one digit from negative balance to maximize.",
    samples=({"input": "-100\n", "output": "-10\n"}, {"input": "273\n", "output": "273\n"}),
    solve=_313a,
    alt=_313a_alt,
    mutants={
        "drop_last": lambda s: f"{int(s.strip()) // 10}\n",
        "abs": lambda s: f"{abs(int(s.strip()))}\n",
    },
    generate=lambda rng: [
        f"{x}\n" for x in [-100, -10, -11, -19, -99, 0, 5, -1234, -1000, 42, -20, -101]
    ],
    family="math",
)


# 1367B Even Array
def _1367b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        bad_even = sum(1 for idx, v in enumerate(a) if idx % 2 == 0 and v % 2 == 1)
        bad_odd = sum(1 for idx, v in enumerate(a) if idx % 2 == 1 and v % 2 == 0)
        out.append(str(bad_even if bad_even == bad_odd else -1))
    return "\n".join(out) + "\n"


add(
    problem_id="1367B",
    summary="Min swaps so a[i]%2 == i%2, or -1.",
    samples=(
        {
            "input": "4\n4\n3 2 7 6\n3\n3 2 6\n1\n7\n7\n4 9 2 1 18 3 0\n",
            "output": "2\n-1\n0\n3\n",
        },
    ),
    solve=_1367b,
    alt=_1367b,
    mutants={"zero": lambda s: "0\n" * int(lines(s)[0]), "neg": lambda s: "-1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "4\n4\n3 2 7 6\n3\n3 2 6\n1\n7\n7\n4 9 2 1 18 3 0\n",
        "1\n2\n1 2\n",
        "1\n2\n2 1\n",
        "1\n1\n1\n",
        "1\n1\n2\n",
        "1\n3\n1 2 3\n",
        "1\n3\n2 1 2\n",
        "1\n4\n1 1 1 1\n",
        "1\n4\n0 1 2 3\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n6\n0 0 0 0 0 0\n",
    ],
    family="greedy",
)
# need independent alt - fix
SPECS.pop()


def _1367b_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        i += 2
        e = o = 0
        for idx, v in enumerate(a):
            if idx % 2 != v % 2:
                if idx % 2 == 0:
                    e += 1
                else:
                    o += 1
        out.append(str(e if e == o else -1))
    return "\n".join(out) + "\n"


add(
    problem_id="1367B",
    summary="Min swaps so a[i]%2 == i%2, or -1.",
    samples=(
        {
            "input": "4\n4\n3 2 7 6\n3\n3 2 6\n1\n7\n7\n4 9 2 1 18 3 0\n",
            "output": "2\n-1\n0\n3\n",
        },
    ),
    solve=_1367b,
    alt=_1367b_alt,
    mutants={"zero": lambda s: "0\n" * int(lines(s)[0]), "neg": lambda s: "-1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "4\n4\n3 2 7 6\n3\n3 2 6\n1\n7\n7\n4 9 2 1 18 3 0\n",
        "1\n2\n1 2\n",
        "1\n2\n2 1\n",
        "1\n1\n1\n",
        "1\n1\n2\n",
        "1\n3\n1 2 3\n",
        "1\n3\n2 1 2\n",
        "1\n4\n1 1 1 1\n",
        "1\n4\n0 1 2 3\n",
        "1\n5\n1 2 3 4 5\n",
        "1\n6\n0 0 0 0 0 0\n",
    ],
    family="greedy",
)

_KEEP = ['492A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
