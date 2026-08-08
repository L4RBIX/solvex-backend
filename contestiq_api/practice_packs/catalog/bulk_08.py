"""Additional unique-answer beginner oracles (compact, validated-oriented)."""

from __future__ import annotations

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no

SPECS: list = []


def add(**kw) -> None:
    SPECS.append(make_spec(**kw))


# 520A Pangram
add(
    problem_id="520A",
    summary="Is the string a pangram?",
    samples=(
        {"input": "12\ntoosmallword\n", "output": "NO\n"},
        {"input": "35\nTheQuickBrownFoxJumpsOverTheLazyDog\n", "output": "YES\n"},
    ),
    solve=lambda s: yes_no(len({c.lower() for c in lines(s)[1] if c.isalpha()}) == 26),
    alt=lambda s: yes_no(set("abcdefghijklmnopqrstuvwxyz") <= {c.lower() for c in lines(s)[1]}),
    mutants={
        "len26": lambda s: yes_no(len(lines(s)[1]) >= 26),
        "ascii": lambda s: yes_no(len(set(lines(s)[1])) >= 26),
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


def _32b(stdin: str) -> str:
    code = stdin.strip()
    i = 0
    out = []
    while i < len(code):
        if code[i] == ".":
            out.append("0")
            i += 1
        elif i + 1 < len(code) and code[i : i + 2] == "-.":
            out.append("1")
            i += 2
        else:
            out.append("2")
            i += 2
    return "".join(out) + "\n"


add(
    problem_id="32B",
    summary="Decode Borze code where .=0, -.=1, --=2.",
    samples=(
        {"input": ".--\n", "output": "01\n"},
        {"input": "...--.\n", "output": "012\n"},
    ),
    solve=_32b,
    alt=lambda s: s.strip().replace("--", "2").replace("-.", "1").replace(".", "0") + "\n",
    mutants={
        "all0": lambda s: "0" * len(s.strip()) + "\n",
        "as_is": lambda s: s.strip() + "\n",
    },
    generate=lambda rng: [
        ".--\n",
        "...--.\n",
        ".\n",
        "--\n",
        "-.\n",
        "......\n",
        "--.--.\n",
        ".-.-.--\n",
        "...\n",
        "-.--.\n",
        ".--.--\n",
    ],
    family="strings",
)


def _230a(stdin: str) -> str:
    ls = lines(stdin)
    s, n = map(int, ls[0].split())
    for x, y in sorted(tuple(map(int, ls[i].split())) for i in range(1, n + 1)):
        if s <= x:
            return "NO\n"
        s += y
    return "YES\n"


def _230a_alt(stdin: str) -> str:
    ls = lines(stdin)
    s, n = map(int, ls[0].split())
    for x, y in sorted(tuple(map(int, ls[i].split())) for i in range(1, n + 1)):
        if s > x:
            s += y
        else:
            return "NO\n"
    return "YES\n"


add(
    problem_id="230A",
    summary="Can Kirito defeat dragons in some order?",
    samples=({"input": "2 2\n1 99\n100 0\n", "output": "YES\n"},),
    solve=_230a,
    alt=_230a_alt,
    mutants={"always_yes": lambda s: "YES\n", "always_no": lambda s: "NO\n"},
    generate=lambda rng: [
        "2 2\n1 99\n100 0\n",
        "10 1\n100 100\n",
        "100 1\n100 0\n",
        "1 1\n1 1\n",
    ]
    + [
        f"{s} {n}\n"
        + "\n".join(f"{rng.randint(1, 50)} {rng.randint(0, 20)}" for _ in range(n))
        + "\n"
        for s, n in [(rng.randint(1, 30), rng.randint(1, 5)) for _ in range(8)]
    ],
    family="greedy",
    checker="tokens_ci",
)


add(
    problem_id="2044A",
    summary="Count pairs (a,b) with a+b=n, a,b>=1.",
    samples=({"input": "5\n2\n4\n6\n8\n10\n", "output": "1\n3\n5\n7\n9\n"},),
    solve=lambda s: "\n".join(str(int(x) - 1) for x in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join(
        str(sum(1 for a in range(1, int(x)) if int(x) - a >= 1)) for x in lines(s)[1:]
    )
    + "\n",
    mutants={
        "n": lambda s: "\n".join(lines(s)[1:]) + "\n",
        "n2": lambda s: "\n".join(str(int(x) // 2) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["5\n2\n4\n6\n8\n10\n", "1\n2\n", "1\n3\n"]
    + [f"1\n{rng.randint(2, 100)}\n" for _ in range(8)],
    family="math",
)


add(
    problem_id="1624A",
    summary="Minimum plus-one-on-subset ops to equalize array = max-min.",
    samples=(
        {
            "input": "3\n5\n1 1 1 1 1\n2\n3 4\n6\n1 2 3 4 5 6\n",
            "output": "0\n1\n5\n",
        },
    ),
    solve=lambda s: "\n".join(
        str(max(map(int, lines(s)[i].split())) - min(map(int, lines(s)[i].split())))
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    alt=lambda s: "\n".join(
        str(sorted(map(int, lines(s)[i].split()))[-1] - sorted(map(int, lines(s)[i].split()))[0])
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    mutants={
        "max": lambda s: "\n".join(
            str(max(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)
        )
        + "\n",
        "zero": lambda s: "0\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "3\n5\n1 1 1 1 1\n2\n3 4\n6\n1 2 3 4 5 6\n",
        "1\n1\n7\n",
        "1\n3\n10 1 5\n",
    ]
    + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(1, 50)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="math",
)


add(
    problem_id="1971A",
    summary="Print min(x,y) then max(x,y).",
    samples=({"input": "3\n4 5\n3 3\n10 1\n", "output": "4 5\n3 3\n1 10\n"},),
    solve=lambda s: "\n".join(
        f"{min(map(int, line.split()))} {max(map(int, line.split()))}" for line in lines(s)[1:]
    )
    + "\n",
    alt=lambda s: "\n".join(
        (lambda a, b: f"{a} {b}" if a <= b else f"{b} {a}")(*map(int, line.split()))
        for line in lines(s)[1:]
    )
    + "\n",
    mutants={
        "as_is": lambda s: "\n".join(lines(s)[1:]) + "\n",
        "swap": lambda s: "\n".join(
            f"{max(map(int, line.split()))} {min(map(int, line.split()))}"
            for line in lines(s)[1:]
        )
        + "\n",
    },
    generate=lambda rng: [
        "3\n4 5\n3 3\n10 1\n",
        "1\n0 0\n",
        "1\n100 1\n",
    ]
    + [f"1\n{rng.randint(0, 100)} {rng.randint(0, 100)}\n" for _ in range(8)],
    family="implementation",
    checker="tokens",
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
        str(
            sum(map(int, lines(s)[i].split()))
            - min(map(int, lines(s)[i].split())) * int(lines(s)[i - 1])
        )
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    mutants={
        "sum": lambda s: "\n".join(
            str(sum(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)
        )
        + "\n",
        "min": lambda s: "\n".join(
            str(min(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)
        )
        + "\n",
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


def _1520a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        s = ls[i + 1]
        i += 2
        seen = set()
        prev = None
        ok = True
        for ch in s:
            if ch != prev:
                if ch in seen:
                    ok = False
                    break
                seen.add(ch)
            prev = ch
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1520A",
    summary="Suspicious if any task letter reappears after another task.",
    samples=(
        {
            "input": "5\n3\nABA\n5\nZZZAA\n3\nABC\n4\nAABA\n1\nZ\n",
            "output": "NO\nYES\nYES\nNO\nYES\n",
        },
    ),
    solve=_1520a,
    alt=lambda s: "\n".join(
        (
            lambda st: (
                "YES"
                if len([ch for i, ch in enumerate(st) if i == 0 or ch != st[i - 1]])
                == len(set(ch for i, ch in enumerate(st) if i == 0 or ch != st[i - 1]))
                else "NO"
            )
        )(lines(s)[i])
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    mutants={
        "always_yes": lambda s: "YES\n" * int(lines(s)[0]),
        "always_no": lambda s: "NO\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "5\n3\nABA\n5\nZZZAA\n3\nABC\n4\nAABA\n1\nZ\n",
        "1\n4\nAABB\n",
        "1\n4\nABAB\n",
    ]
    + [
        "1\n" + str(n) + "\n" + "".join(rng.choice("ABC") for _ in range(n)) + "\n"
        for n in [rng.randint(1, 10) for _ in range(8)]
    ],
    family="implementation",
    checker="tokens_ci",
)


add(
    problem_id="1996A",
    summary="Minimum animals (cows=4 legs, chickens=2) for n legs.",
    samples=({"input": "4\n2\n4\n6\n8\n", "output": "1\n1\n2\n2\n"},),
    solve=lambda s: "\n".join(str((int(x) + 2) // 4) for x in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join(
        str(int(x) // 4 + (0 if int(x) % 4 == 0 else 1)) for x in lines(s)[1:]
    )
    + "\n",
    mutants={
        "div2": lambda s: "\n".join(str(int(x) // 2) for x in lines(s)[1:]) + "\n",
        "div4": lambda s: "\n".join(str(int(x) // 4) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["4\n2\n4\n6\n8\n", "1\n2\n", "1\n100\n"]
    + [f"1\n{2 * rng.randint(1, 50)}\n" for _ in range(8)],
    family="math",
)


add(
    problem_id="1955A",
    summary="Min cost for n yogurts with single price a and promo 2 for b.",
    samples=(
        {
            "input": "4\n5 2 3\n4 2 3\n3 4 5\n1 100 1\n",
            "output": "8\n6\n12\n100\n",
        },
    ),
    solve=lambda s: "\n".join(
        str((n // 2) * min(2 * a, b) + (n % 2) * a)
        for n, a, b in (map(int, line.split()) for line in lines(s)[1:])
    )
    + "\n",
    alt=lambda s: "\n".join(
        str(min(n * a, (n // 2) * b + (n % 2) * a))
        for n, a, b in (map(int, line.split()) for line in lines(s)[1:])
    )
    + "\n",
    mutants={
        "only_a": lambda s: "\n".join(
            str(int(line.split()[0]) * int(line.split()[1])) for line in lines(s)[1:]
        )
        + "\n",
        "only_b": lambda s: "\n".join(
            str((int(line.split()[0]) // 2) * int(line.split()[2])) for line in lines(s)[1:]
        )
        + "\n",
    },
    generate=lambda rng: [
        "4\n5 2 3\n4 2 3\n3 4 5\n1 100 1\n",
        "1\n2 5 1\n",
        "1\n1 1 100\n",
    ]
    + [
        f"1\n{rng.randint(1, 20)} {rng.randint(1, 10)} {rng.randint(1, 20)}\n"
        for _ in range(8)
    ],
    family="math",
)


add(
    problem_id="2126A",
    summary="Smallest digit present in decimal representation of x.",
    samples=({"input": "4\n5\n100\n999\n123456789\n", "output": "5\n0\n9\n1\n"},),
    solve=lambda s: "\n".join(str(min(map(int, x))) for x in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join(min(x) for x in lines(s)[1:]) + "\n",
    mutants={
        "first": lambda s: "\n".join(x[0] for x in lines(s)[1:]) + "\n",
        "maxd": lambda s: "\n".join(str(max(map(int, x))) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["4\n5\n100\n999\n123456789\n", "1\n0\n", "1\n10\n"]
    + [f"1\n{rng.randint(0, 10**6)}\n" for _ in range(8)],
    family="math",
)


add(
    problem_id="1371A",
    summary="Maximum equal-length sticks by joining 1..n.",
    samples=({"input": "5\n1\n2\n3\n4\n5\n", "output": "1\n1\n2\n2\n3\n"},),
    solve=lambda s: "\n".join(str((int(x) + 1) // 2) for x in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join(str(int(x) // 2 + int(x) % 2) for x in lines(s)[1:]) + "\n",
    mutants={
        "n": lambda s: "\n".join(lines(s)[1:]) + "\n",
        "div2": lambda s: "\n".join(str(int(x) // 2) for x in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["5\n1\n2\n3\n4\n5\n"]
    + [f"1\n{rng.randint(1, 100)}\n" for _ in range(10)],
    family="math",
)


def _1807b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        even = sum(x for x in a if x % 2 == 0)
        odd = sum(x for x in a if x % 2 == 1)
        out.append("YES" if even > odd else "NO")
    return "\n".join(out) + "\n"


add(
    problem_id="1807B",
    summary="Mihai wins if sum of even bags > sum of odd bags.",
    samples=(
        {
            "input": "4\n4\n1 1 1 2\n3\n2 2 1\n1\n100\n5\n1 2 3 4 5\n",
            "output": "NO\nYES\nYES\nNO\n",
        },
    ),
    solve=_1807b,
    alt=lambda s: "\n".join(
        (
            "YES"
            if sum(x for x in map(int, lines(s)[i].split()) if x % 2 == 0)
            > sum(x for x in map(int, lines(s)[i].split()) if x % 2 == 1)
            else "NO"
        )
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    mutants={
        "always_yes": lambda s: "YES\n" * int(lines(s)[0]),
        "always_no": lambda s: "NO\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "4\n4\n1 1 1 2\n3\n2 2 1\n1\n100\n5\n1 2 3 4 5\n",
        "1\n2\n2 1\n",
    ]
    + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(1, 20)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="greedy",
    checker="tokens_ci",
)


add(
    problem_id="233A",
    summary="Permutation where p[p[i]]=i and p[i]!=i, or -1.",
    samples=(
        {"input": "1\n", "output": "-1\n"},
        {"input": "2\n", "output": "2 1\n"},
        {"input": "4\n", "output": "2 1 4 3\n"},
    ),
    solve=lambda s: (
        "-1\n"
        if int(s.strip()) % 2
        else " ".join(str(i + 1 if i % 2 == 0 else i - 1) for i in range(1, int(s.strip()) + 1))
        + "\n"
    ),
    alt=lambda s: (
        "-1\n"
        if int(s.strip()) % 2
        else " ".join(f"{i + 1} {i}" for i in range(1, int(s.strip()) + 1, 2)) + "\n"
    ),
    mutants={
        "id": lambda s: " ".join(str(i) for i in range(1, int(s.strip()) + 1)) + "\n",
        "neg": lambda s: "-1\n",
    },
    generate=lambda rng: [f"{n}\n" for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20]],
    family="constructive",
    checker="tokens",
)


add(
    problem_id="1296A",
    summary="Can array sum be made odd by replacing values?",
    samples=(
        {
            "input": "5\n2\n2 3\n4\n2 2 8 8\n3\n4 4 4\n3\n1 1 1\n5\n1 1 1 1 1\n",
            "output": "YES\nNO\nNO\nYES\nYES\n",
        },
    ),
    solve=lambda s: "\n".join(
        (
            "YES"
            if sum(map(int, lines(s)[i].split())) % 2 == 1
            or (
                any(int(x) % 2 == 0 for x in lines(s)[i].split())
                and any(int(x) % 2 == 1 for x in lines(s)[i].split())
            )
            else "NO"
        )
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    alt=lambda s: "\n".join(
        (
            lambda a: (
                "YES"
                if sum(a) % 2 == 1 or (any(x % 2 == 0 for x in a) and any(x % 2 for x in a))
                else "NO"
            )
        )(list(map(int, lines(s)[i].split())))
        for i in range(2, len(lines(s)), 2)
    )
    + "\n",
    mutants={
        "sum_odd": lambda s: "\n".join(
            "YES" if sum(map(int, lines(s)[i].split())) % 2 else "NO"
            for i in range(2, len(lines(s)), 2)
        )
        + "\n",
        "always": lambda s: "YES\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "5\n2\n2 3\n4\n2 2 8 8\n3\n4 4 4\n3\n1 1 1\n5\n1 1 1 1 1\n",
        "1\n1\n2\n",
    ]
    + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(1, 10)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="math",
    checker="tokens_ci",
)


add(
    problem_id="935A",
    summary="Count ways to choose team leaders so each leads same non-zero count.",
    samples=(
        {"input": "6\n", "output": "3\n"},
        {"input": "4\n", "output": "2\n"},
        {"input": "2\n", "output": "1\n"},
    ),
    solve=lambda s: f"{sum(1 for i in range(1, int(s.strip())) if int(s.strip()) % i == 0)}\n",
    alt=lambda s: f"{sum(1 for i in range(1, int(s.strip())) if (int(s.strip()) - i) % i == 0)}\n",
    mutants={"n": lambda s: s if s.endswith("\n") else s + "\n", "half": lambda s: f"{int(s.strip()) // 2}\n"},
    generate=lambda rng: [f"{n}\n" for n in [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 100]],
    family="math",
)


def _1399b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        b = list(map(int, ls[i + 2].split()))
        i += 3
        mina, minb = min(a), min(b)
        out.append(str(sum(max(a[j] - mina, b[j] - minb) for j in range(n))))
    return "\n".join(out) + "\n"


def _1399b_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        a = list(map(int, ls[i + 1].split()))
        b = list(map(int, ls[i + 2].split()))
        i += 3
        da = [x - min(a) for x in a]
        db = [x - min(b) for x in b]
        out.append(str(sum(max(x, y) for x, y in zip(da, db))))
    return "\n".join(out) + "\n"


add(
    problem_id="1399B",
    summary="Min moves to make all candies equal and all oranges equal.",
    samples=(
        {
            "input": "5\n3\n3 5 6\n3 2 3\n1\n0\n0\n4\n2 4 6 1\n1 1 1 1\n2\n0 0\n0 0\n3\n1 1 1\n1 1 1\n",
            "output": "4\n0\n9\n0\n0\n",
        },
    ),
    solve=_1399b,
    alt=_1399b_alt,
    mutants={
        "zero": lambda s: "0\n" * int(lines(s)[0]),
        "one": lambda s: "1\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "5\n3\n3 5 6\n3 2 3\n1\n0\n0\n4\n2 4 6 1\n1 1 1 1\n2\n0 0\n0 0\n3\n1 1 1\n1 1 1\n",
        "1\n2\n5 1\n3 2\n",
    ]
    + [
        (
            lambda n: (
                f"1\n{n}\n"
                + " ".join(str(rng.randint(0, 10)) for _ in range(n))
                + "\n"
                + " ".join(str(rng.randint(0, 10)) for _ in range(n))
                + "\n"
            )
        )(rng.randint(1, 6))
        for _ in range(8)
    ],
    family="greedy",
)


def _1368a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for line in ls[1 : 1 + int(ls[0])]:
        a, b, n = map(int, line.split())
        steps = 0
        while a <= n and b <= n:
            if a < b:
                a += b
            else:
                b += a
            steps += 1
        out.append(str(steps))
    return "\n".join(out) + "\n"


def _1368a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for line in ls[1 : 1 + int(ls[0])]:
        a, b, n = map(int, line.split())
        if a > b:
            a, b = b, a
        steps = 0
        while b <= n:
            a, b = b, a + b
            steps += 1
        out.append(str(steps))
    return "\n".join(out) + "\n"


add(
    problem_id="1368A",
    summary="Min C+= operations until one variable exceeds n.",
    samples=({"input": "3\n1 2 3\n5 4 100\n2 2 1\n", "output": "2\n6\n1\n"},),
    solve=_1368a,
    alt=_1368a_alt,
    mutants={
        "one": lambda s: "1\n" * int(lines(s)[0]),
        "n": lambda s: "\n".join(line.split()[-1] for line in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "3\n1 2 3\n5 4 100\n2 2 1\n",
        "1\n1 1 1\n",
        "1\n3 3 10\n",
    ]
    + [
        f"1\n{rng.randint(1, 10)} {rng.randint(1, 10)} {rng.randint(1, 100)}\n"
        for _ in range(8)
    ],
    family="greedy",
)


def _149a(stdin: str) -> str:
    ls = lines(stdin)
    k = int(ls[0])
    a = sorted(map(int, ls[1].split()), reverse=True)
    if k == 0:
        return "0\n"
    total = 0
    for i, v in enumerate(a, 1):
        total += v
        if total >= k:
            return f"{i}\n"
    return "-1\n"


def _149a_alt(stdin: str) -> str:
    ls = lines(stdin)
    k = int(ls[0])
    a = sorted(map(int, ls[1].split()), reverse=True)
    if k == 0:
        return "0\n"
    total = 0
    months = 0
    for v in a:
        if total >= k:
            break
        total += v
        months += 1
    return f"{months if total >= k else -1}\n"


add(
    problem_id="149A",
    summary="Minimum months watered to grow k cm.",
    samples=({"input": "5\n1 1 1 1 2 2 3 2 2 1 1 1\n", "output": "2\n"},),
    solve=_149a,
    alt=_149a_alt,
    mutants={"twelve": lambda s: "12\n", "k": lambda s: lines(s)[0] + "\n"},
    generate=lambda rng: [
        "5\n1 1 1 1 2 2 3 2 2 1 1 1\n",
        "0\n1 1 1 1 1 1 1 1 1 1 1 1\n",
        "100\n1 1 1 1 1 1 1 1 1 1 1 1\n",
        "12\n1 1 1 1 1 1 1 1 1 1 1 1\n",
    ]
    + [
        f"{rng.randint(0, 30)}\n"
        + " ".join(str(rng.randint(0, 10)) for _ in range(12))
        + "\n"
        for _ in range(8)
    ],
    family="greedy",
)


# 1873B Good Kid
def _1873b(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        best = 0
        for j in range(len(a)):
            b = a[:]
            b[j] += 1
            prod = 1
            for x in b:
                prod *= x
            best = max(best, prod)
        out.append(str(best))
    return "\n".join(out) + "\n"


def _1873b_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        a = list(map(int, ls[i + 1].split()))
        i += 2
        j = min(range(len(a)), key=lambda idx: a[idx])
        a[j] += 1
        prod = 1
        for x in a:
            prod *= x
        out.append(str(prod))
    return "\n".join(out) + "\n"


add(
    problem_id="1873B",
    summary="Add 1 to one digit to maximize product.",
    samples=(
        {
            "input": "4\n4\n2 2 1 2\n3\n0 1 2\n5\n4 3 2 3 4\n1\n9\n",
            "output": "16\n2\n432\n10\n",
        },
    ),
    solve=_1873b,
    alt=_1873b_alt,
    mutants={
        "no_add": lambda s: "1\n" * int(lines(s)[0]),
        "sum": lambda s: "\n".join(
            str(sum(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)
        )
        + "\n",
    },
    generate=lambda rng: [
        "4\n4\n2 2 1 2\n3\n0 1 2\n5\n4 3 2 3 4\n1\n9\n",
        "1\n2\n1 1\n",
    ]
    + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(0, 9)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 6) for _ in range(8)]
    ],
    family="greedy",
)


# 1766A Extremely Round
def _1766a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for n in map(int, ls[1:]):
        s = str(n)
        out.append(str(9 * (len(s) - 1) + int(s[0])))
    return "\n".join(out) + "\n"


def _1766a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    for n in map(int, ls[1:]):
        count = 0
        for d in range(1, 10):
            x = d
            while x <= n:
                count += 1
                x *= 10
        out.append(str(count))
    return "\n".join(out) + "\n"


add(
    problem_id="1766A",
    summary="Count extremely round positive integers <= n.",
    samples=({"input": "5\n9\n42\n13\n100\n111\n", "output": "9\n13\n10\n19\n19\n"},),
    solve=_1766a,
    alt=_1766a_alt,
    mutants={
        "digits": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n",
        "n": lambda s: "\n".join(lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["5\n9\n42\n13\n100\n111\n", "1\n1\n", "1\n10\n"]
    + [f"1\n{rng.randint(1, 10000)}\n" for _ in range(8)],
    family="math",
)


# 1921A Square
def _1921a(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        pts = [tuple(map(int, ls[i + j].split())) for j in range(4)]
        i += 4
        xs = sorted(p[0] for p in pts)
        side = xs[-1] - xs[0]
        out.append(str(side * side))
    return "\n".join(out) + "\n"


def _1921a_alt(stdin: str) -> str:
    ls = lines(stdin)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        pts = [tuple(map(int, ls[i + j].split())) for j in range(4)]
        i += 4
        ys = sorted(p[1] for p in pts)
        side = ys[-1] - ys[0]
        out.append(str(side * side))
    return "\n".join(out) + "\n"


add(
    problem_id="1921A",
    summary="Area of axis-aligned square given 4 corners.",
    samples=(
        {
            "input": "3\n1 2\n3 2\n1 4\n3 4\n1 2\n1 2\n1 2\n1 2\n0 0\n0 10\n10 0\n10 10\n",
            "output": "4\n0\n100\n",
        }
        if False
        else {
            "input": "3\n1 2\n3 2\n1 4\n3 4\n1 2\n1 2\n1 2\n1 2\n0 0\n0 10\n10 0\n10 10\n",
            "output": "4\n0\n100\n",
        },
    ),
    solve=_1921a,
    alt=_1921a_alt,
    mutants={"side": lambda s: "1\n" * int(lines(s)[0]), "zero": lambda s: "0\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "3\n1 2\n3 2\n1 4\n3 4\n1 2\n1 2\n1 2\n1 2\n0 0\n0 10\n10 0\n10 10\n",
        "1\n0 0\n0 1\n1 0\n1 1\n",
        "1\n2 2\n2 5\n5 2\n5 5\n",
        "1\n-1 -1\n-1 1\n1 -1\n1 1\n",
        "1\n3 3\n3 3\n3 3\n3 3\n",
        "1\n0 0\n0 2\n2 0\n2 2\n",
        "1\n5 1\n5 4\n8 1\n8 4\n",
        "1\n10 10\n10 20\n20 10\n20 20\n",
        "1\n-5 0\n-5 3\n-2 0\n-2 3\n",
        "1\n0 0\n0 7\n7 0\n7 7\n",
    ],
    family="math",
)

_KEEP = ['230A', '2044A', '1624A', '1971A', '1520A', '1996A', '2126A', '1371A', '1807B', '1296A', '935A', '149A', '1873B', '1766A', '1921A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
