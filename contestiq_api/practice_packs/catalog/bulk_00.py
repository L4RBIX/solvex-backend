"""Dual-oracle ProblemOracleSpec entries generated from catalog/batches/batch_00.json.

Each problem has two independently-derived correct oracles plus >=2 mutants
that must fail on at least one generated/sample case.
"""

from __future__ import annotations

import math
import random

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

SPECS = []


# ─── 50A Domino piling ───────────────────────────────────────────────────────


def _50a_solve(stdin: str) -> str:
    m, n = map(int, stdin.split())
    return f"{(m * n) // 2}\n"


def _50a_alt(stdin: str) -> str:
    m, n = map(int, stdin.split())
    return f"{(m * n) >> 1}\n"


def _50a_mut_ceil(stdin: str) -> str:
    m, n = map(int, stdin.split())
    return f"{(m * n + 1) // 2}\n"


def _50a_mut_half_each(stdin: str) -> str:
    m, n = map(int, stdin.split())
    return f"{(m // 2) * n}\n"


SPECS.append(
    make_spec(
        "50A",
        summary="Maximum number of 2x1 dominoes that tile an m x n board.",
        samples=({"input": "2 4\n", "output": "4\n"},),
        solve=_50a_solve,
        alt=_50a_alt,
        mutants={"ceil_div": _50a_mut_ceil, "half_rows_only": _50a_mut_half_each},
        generate=lambda rng: [
            "2 4\n",
            "1 1\n",
            "3 3\n",
            "16 16\n",
            "1 16\n",
            "16 1\n",
        ]
        + [f"{rng.randint(1, 16)} {rng.randint(1, 16)}\n" for _ in range(6)],
        input_format="Two integers m n.",
        output_format="Print the max domino count.",
        constraints="1 <= m, n <= 16.",
        checker="exact",
        family="math",
    )
)


# ─── 118A String Task ────────────────────────────────────────────────────────

_VOWELS = set("aeiouy")


def _118a_solve(stdin: str) -> str:
    s = stdin.strip().lower()
    out = []
    for ch in s:
        if ch not in _VOWELS:
            out.append("." + ch)
    return "".join(out) + "\n"


def _118a_alt(stdin: str) -> str:
    s = stdin.strip().lower()
    kept = [c for c in s if c not in _VOWELS]
    return "".join(f".{c}" for c in kept) + "\n"


def _118a_mut_no_lower(stdin: str) -> str:
    s = stdin.strip()
    out = []
    for ch in s:
        if ch.lower() not in _VOWELS:
            out.append("." + ch)
    return "".join(out) + "\n"


def _118a_mut_keep_vowels(stdin: str) -> str:
    s = stdin.strip().lower()
    return "".join(f".{c}" for c in s) + "\n"


SPECS.append(
    make_spec(
        "118A",
        summary="Remove vowels a,e,i,o,u,y, lowercase the rest, prefix each with a dot.",
        samples=(
            {"input": "tour\n", "output": ".t.r\n"},
            {"input": "Codeforces\n", "output": ".c.d.f.r.c.s\n"},
            {"input": "aBAcAba\n", "output": ".b.c.b\n"},
        ),
        solve=_118a_solve,
        alt=_118a_alt,
        mutants={"case_sensitive": _118a_mut_no_lower, "keeps_vowels": _118a_mut_keep_vowels},
        generate=lambda rng: [
            "tour\n",
            "Codeforces\n",
            "aBAcAba\n",
            "xyz\n",
            "AEIOUY\n",
            "bcdfg\n",
        ]
        + [
            "".join(rng.choice("abcdeiouyXYZ") for _ in range(rng.randint(1, 15))) + "\n"
            for _ in range(6)
        ],
        input_format="One string (1..100 chars).",
        output_format="Print the transformed string.",
        constraints="1 <= |s| <= 100, letters only.",
        checker="exact",
        family="strings",
    )
)


# ─── 59A Word ────────────────────────────────────────────────────────────────


def _59a_solve(stdin: str) -> str:
    w = stdin.strip()
    upper = sum(1 for c in w if c.isupper())
    lower = len(w) - upper
    return (w.upper() if upper > lower else w.lower()) + "\n"


def _59a_alt(stdin: str) -> str:
    w = stdin.strip()
    lower = sum(1 for c in w if c.islower())
    return (w.lower() if lower >= len(w) - lower else w.upper()) + "\n"


def _59a_mut_strict(stdin: str) -> str:
    w = stdin.strip()
    upper = sum(1 for c in w if c.isupper())
    lower = len(w) - upper
    return (w.upper() if upper >= lower else w.lower()) + "\n"


def _59a_mut_always_lower(stdin: str) -> str:
    return stdin.strip().lower() + "\n"


SPECS.append(
    make_spec(
        "59A",
        summary="Convert word to all-lower or all-upper by majority case (ties -> lower).",
        samples=(
            {"input": "HoUse\n", "output": "house\n"},
            {"input": "ViP\n", "output": "VIP\n"},
            {"input": "maTRIx\n", "output": "matrix\n"},
        ),
        solve=_59a_solve,
        alt=_59a_alt,
        mutants={"tie_goes_upper": _59a_mut_strict, "always_lower": _59a_mut_always_lower},
        generate=lambda rng: [
            "HoUse\n",
            "ViP\n",
            "maTRIx\n",
            "AAaa\n",
            "Z\n",
            "z\n",
        ]
        + [
            "".join(rng.choice("AbCdEf") for _ in range(rng.randint(1, 12))) + "\n"
            for _ in range(6)
        ],
        input_format="One word up to 100 chars of Latin letters.",
        output_format="Print the transformed word.",
        constraints="1 <= |s| <= 100.",
        checker="exact",
        family="strings",
    )
)


# ─── 69A Young Physicist ─────────────────────────────────────────────────────


def _69a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    sx = sy = sz = 0
    for i in range(1, n + 1):
        x, y, z = map(int, vals[i].split())
        sx += x
        sy += y
        sz += z
    return yes_no(sx == 0 and sy == 0 and sz == 0)


def _69a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    total = [0, 0, 0]
    for i in range(1, n + 1):
        vec = list(map(int, vals[i].split()))
        total = [total[j] + vec[j] for j in range(3)]
    return yes_no(all(v == 0 for v in total))


def _69a_mut_abs(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    sx = sy = sz = 0
    for i in range(1, n + 1):
        x, y, z = map(int, vals[i].split())
        sx += abs(x)
        sy += abs(y)
        sz += abs(z)
    return yes_no(sx == 0 and sy == 0 and sz == 0)


def _69a_mut_xy_only(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    sx = sy = 0
    for i in range(1, n + 1):
        x, y, z = map(int, vals[i].split())
        sx += x
        sy += y
    return yes_no(sx == 0 and sy == 0)


SPECS.append(
    make_spec(
        "69A",
        summary="A body at rest under n forces (3D vectors); check if net force is zero.",
        samples=({"input": "3\n4 1 7\n-2 4 -1\n1 -5 -3\n", "output": "NO\n"},),
        solve=_69a_solve,
        alt=_69a_alt,
        mutants={"abs_sum": _69a_mut_abs, "ignore_z": _69a_mut_xy_only},
        generate=lambda rng: [
            "3\n4 1 7\n-2 4 -1\n1 -5 -3\n",
            "3\n3 -1 7\n-5 2 -4\n2 -1 -3\n",
            "1\n0 0 0\n",
            "2\n1 1 1\n-1 -1 -1\n",
            "2\n1 0 5\n-1 0 0\n",
            "1\n0 0 3\n",
        ]
        + [
            (
                lambda vecs: f"{len(vecs)}\n" + "\n".join(" ".join(map(str, v)) for v in vecs) + "\n"
            )(
                [
                    [rng.randint(-50, 50) for _ in range(3)]
                    for _ in range(rng.randint(1, 5))
                ]
            )
            for _ in range(8)
        ],
        input_format="n then n lines of 3 integers.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= n <= 100.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 110A Nearly Lucky Number ────────────────────────────────────────────────


def _is_lucky_str(s: str) -> bool:
    return len(s) > 0 and all(c in "47" for c in s)


def _110a_solve(stdin: str) -> str:
    n = stdin.strip()
    cnt = sum(1 for c in n if c in "47")
    return yes_no(_is_lucky_str(str(cnt)))


def _110a_alt(stdin: str) -> str:
    n = stdin.strip()
    cnt = len([c for c in n if c == "4" or c == "7"])
    s = str(cnt)
    ok = len(s) > 0 and set(s) <= {"4", "7"}
    return yes_no(ok)


def _110a_mut_include_zero(stdin: str) -> str:
    n = stdin.strip()
    cnt = sum(1 for c in n if c in "47")
    s = str(cnt)
    ok = all(c in "047" for c in s)
    return yes_no(ok)


def _110a_mut_check_digit_not_count(stdin: str) -> str:
    n = stdin.strip()
    return yes_no(_is_lucky_str(n))


SPECS.append(
    make_spec(
        "110A",
        summary="n is 'nearly lucky' if the count of digits 4 and 7 in n is itself a lucky number.",
        samples=(
            {"input": "40047\n", "output": "NO\n"},
            {"input": "7747774\n", "output": "YES\n"},
            {"input": "1000000000000000000\n", "output": "NO\n"},
        ),
        solve=_110a_solve,
        alt=_110a_alt,
        mutants={"zero_is_lucky": _110a_mut_include_zero, "checks_n_directly": _110a_mut_check_digit_not_count},
        generate=lambda rng: [
            "40047\n",
            "7747774\n",
            "1000000000000000000\n",
            "4\n",
            "7\n",
            "1\n",
            "44444444\n",
        ]
        + [str(rng.randint(1, 10**15)) + "\n" for _ in range(6)],
        input_format="One integer n (up to 10^18).",
        output_format='Print "YES" or "NO".',
        constraints="1 <= n <= 10^18.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 734A Anton and Danik ────────────────────────────────────────────────────


def _734a_solve(stdin: str) -> str:
    s = lines(stdin)[1]
    a = s.count("A")
    d = s.count("D")
    if a > d:
        return "Anton\n"
    if d > a:
        return "Danik\n"
    return "Friendship\n"


def _734a_alt(stdin: str) -> str:
    s = lines(stdin)[1]
    diff = sum(1 if c == "A" else -1 for c in s)
    if diff > 0:
        return "Anton\n"
    if diff < 0:
        return "Danik\n"
    return "Friendship\n"


def _734a_mut_swap(stdin: str) -> str:
    s = lines(stdin)[1]
    a = s.count("A")
    d = s.count("D")
    if a > d:
        return "Danik\n"
    if d > a:
        return "Anton\n"
    return "Friendship\n"


def _734a_mut_no_tie(stdin: str) -> str:
    s = lines(stdin)[1]
    a = s.count("A")
    d = s.count("D")
    return "Anton\n" if a >= d else "Danik\n"


SPECS.append(
    make_spec(
        "734A",
        summary="Count 'A' and 'D' wins in a string; the majority wins, tie is Friendship.",
        samples=({"input": "6\nADAAAA\n", "output": "Anton\n"},),
        solve=_734a_solve,
        alt=_734a_alt,
        mutants={"swapped": _734a_mut_swap, "no_tie": _734a_mut_no_tie},
        generate=lambda rng: [
            "6\nADAAAA\n",
            "1\nA\n",
            "1\nD\n",
            "6\nADAADD\n",
            "2\nAD\n",
        ]
        + [
            f"{n}\n" + "".join(rng.choice("AD") for _ in range(n)) + "\n"
            for n in [rng.randint(1, 20) for _ in range(7)]
        ],
        input_format="n then a string of A/D of length n.",
        output_format="Print Anton, Danik or Friendship.",
        constraints="1 <= n <= 10^5.",
        checker="exact",
        family="strings",
    )
)


# ─── 96A Football ────────────────────────────────────────────────────────────


def _96a_solve(stdin: str) -> str:
    s = stdin.strip()
    run = 1
    for i in range(1, len(s)):
        run = run + 1 if s[i] == s[i - 1] else 1
        if run >= 7:
            return "YES\n"
    return "YES\n" if run >= 7 else "NO\n"


def _96a_alt(stdin: str) -> str:
    s = stdin.strip()
    return yes_no("0000000" in s or "1111111" in s)


def _96a_mut_threshold6(stdin: str) -> str:
    s = stdin.strip()
    run = 1
    best = 1
    for i in range(1, len(s)):
        run = run + 1 if s[i] == s[i - 1] else 1
        best = max(best, run)
    return yes_no(best >= 6)


def _96a_mut_only_ones(stdin: str) -> str:
    s = stdin.strip()
    return yes_no("1111111" in s)


SPECS.append(
    make_spec(
        "96A",
        summary="Determine if a 0/1 string has 7+ identical consecutive characters.",
        samples=({"input": "001001\n", "output": "NO\n"}, {"input": "1000000001\n", "output": "YES\n"}),
        solve=_96a_solve,
        alt=_96a_alt,
        mutants={"threshold_6": _96a_mut_threshold6, "ones_only": _96a_mut_only_ones},
        generate=lambda rng: [
            "001001\n",
            "1000000001\n",
            "0000000\n",
            "1111111\n",
            "0101010101\n",
            "000000\n",
            "111111\n",
            "0111111\n",
            "1000000\n",
        ]
        + [
            "".join(rng.choice("01") for _ in range(rng.randint(1, 30))) + "\n"
            for _ in range(7)
        ],
        input_format="A 0/1 string.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= |s| <= 100.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 41A Translation ─────────────────────────────────────────────────────────


def _41a_solve(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return yes_no(a == b[::-1])


def _41a_alt(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return yes_no(list(a) == list(reversed(b)))


def _41a_mut_case_insensitive(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return yes_no(a.lower() == b[::-1].lower())


def _41a_mut_equal(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return yes_no(a == b)


SPECS.append(
    make_spec(
        "41A",
        summary="Check if the second word is the exact reverse of the first.",
        samples=({"input": "code\nedoc\n", "output": "YES\n"}, {"input": "abb\naba\n", "output": "NO\n"}),
        solve=_41a_solve,
        alt=_41a_alt,
        mutants={"case_insensitive": _41a_mut_case_insensitive, "checks_equal": _41a_mut_equal},
        generate=lambda rng: [
            "code\nedoc\n",
            "abb\naba\n",
            "a\na\n",
            "ab\nba\n",
            "Ab\nba\n",
            "AB\nba\n",
        ]
        + [
            (
                lambda w: f"{w}\n{w[::-1] if rng.random() < 0.5 else w}\n"
            )("".join(rng.choice("abcd") for _ in range(rng.randint(1, 10))))
            for _ in range(8)
        ],
        input_format="Two lines, each a word.",
        output_format='Print "YES" or "NO".',
        constraints="Words of equal length, 1..100 chars.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 677A Vanya and Fence ────────────────────────────────────────────────────


def _677a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n, h = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    return f"{sum(2 if x > h else 1 for x in a)}\n"


def _677a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n, h = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    total = n
    total += sum(1 for x in a if x > h)
    return f"{total}\n"


def _677a_mut_ge(stdin: str) -> str:
    vals = lines(stdin)
    n, h = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    return f"{sum(2 if x >= h else 1 for x in a)}\n"


def _677a_mut_flat(stdin: str) -> str:
    vals = lines(stdin)
    n, h = map(int, vals[0].split())
    return f"{n}\n"


SPECS.append(
    make_spec(
        "677A",
        summary="Each friend needs 2 road units if height > h, else 1; sum total width.",
        samples=({"input": "3 7\n4 5 14\n", "output": "4\n"},),
        solve=_677a_solve,
        alt=_677a_alt,
        mutants={"ge_not_gt": _677a_mut_ge, "ignore_height": _677a_mut_flat},
        generate=lambda rng: [
            "3 7\n4 5 14\n",
            "6 1\n1 1 1 1 1 1\n",
            "6 5\n7 6 8 9 10 5\n",
            "1 1\n1\n",
            "1 1\n2\n",
        ]
        + [
            (
                lambda n, h: f"{n} {h}\n" + " ".join(str(rng.randint(1, 100)) for _ in range(n)) + "\n"
            )(rng.randint(1, 20), rng.randint(1, 100))
            for _ in range(6)
        ],
        input_format="n h then n heights.",
        output_format="Print total width.",
        constraints="1 <= n, h, a_i <= 1000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 271A Beautiful Year ─────────────────────────────────────────────────────


def _has_all_distinct_digits(y: int) -> bool:
    s = str(y)
    return len(set(s)) == len(s)


def _271a_solve(stdin: str) -> str:
    n = int(stdin.strip())
    y = n + 1
    while not _has_all_distinct_digits(y):
        y += 1
    return f"{y}\n"


def _271a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    y = n
    while True:
        y += 1
        digits = str(y)
        if len(set(digits)) == len(digits):
            return f"{y}\n"


def _271a_mut_allow_ge(stdin: str) -> str:
    n = int(stdin.strip())
    y = n
    while not _has_all_distinct_digits(y):
        y += 1
    return f"{y}\n"


def _271a_mut_wrong_check(stdin: str) -> str:
    n = int(stdin.strip())
    y = n + 1
    while len(set(str(y))) < 3:
        y += 1
    return f"{y}\n"


SPECS.append(
    make_spec(
        "271A",
        summary="Find the smallest year strictly greater than n with all distinct digits.",
        samples=({"input": "1987\n", "output": "2013\n"}, {"input": "2013\n", "output": "2014\n"}),
        solve=_271a_solve,
        alt=_271a_alt,
        mutants={"allows_equal": _271a_mut_allow_ge, "weak_check": _271a_mut_wrong_check},
        generate=lambda rng: [
            "1987\n",
            "2013\n",
            "1000\n",
            "9876\n",
            "1111\n",
            "1234\n",
        ]
        + [f"{rng.randint(1000, 9000)}\n" for _ in range(6)],
        input_format="One integer n.",
        output_format="Print the next beautiful year.",
        constraints="1000 <= n <= 9000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 1030A In Search of an Easy Problem ──────────────────────────────────────


def _1030a_solve(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    return "EASY\n" if all(x == 0 for x in a) else "HARD\n"


def _1030a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    return "HARD\n" if sum(a) > 0 else "EASY\n"


def _1030a_mut_any(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    return "EASY\n" if any(x == 0 for x in a) else "HARD\n"


def _1030a_mut_flip(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    return "HARD\n" if all(x == 0 for x in a) else "EASY\n"


SPECS.append(
    make_spec(
        "1030A",
        summary="If all problems are 'easy' (0), print EASY, else HARD.",
        samples=({"input": "3\n0 0 0\n", "output": "EASY\n"}, {"input": "4\n1 0 0 1\n", "output": "HARD\n"}),
        solve=_1030a_solve,
        alt=_1030a_alt,
        mutants={"any_not_all": _1030a_mut_any, "flipped": _1030a_mut_flip},
        generate=lambda rng: [
            "3\n0 0 0\n",
            "4\n1 0 0 1\n",
            "1\n0\n",
            "1\n1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(0, 1)) for _ in range(n)) + "\n")(
                rng.randint(1, 15)
            )
            for _ in range(8)
        ],
        input_format="n then n binary flags.",
        output_format='Print "EASY" or "HARD".',
        constraints="1 <= n <= 100.",
        checker="tokens_ci",
        family="implementation",
    )
)


# ─── 467A George and Accommodation ───────────────────────────────────────────


def _467a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    cnt = 0
    for i in range(1, n + 1):
        p, q = map(int, vals[i].split())
        if q - p >= 2:
            cnt += 1
    return f"{cnt}\n"


def _467a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return f"{sum(1 for i in range(1, n + 1) if (lambda pq: pq[1] - pq[0])(list(map(int, vals[i].split()))) > 1)}\n"


def _467a_mut_ge1(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    cnt = 0
    for i in range(1, n + 1):
        p, q = map(int, vals[i].split())
        if q - p >= 1:
            cnt += 1
    return f"{cnt}\n"


def _467a_mut_free_only(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    cnt = 0
    for i in range(1, n + 1):
        p, q = map(int, vals[i].split())
        cnt += q - p
    return f"{cnt}\n"


SPECS.append(
    make_spec(
        "467A",
        summary="Count rooms with at least 2 free beds (q_i - p_i >= 2).",
        samples=({"input": "3\n1 1\n2 2\n3 3\n", "output": "0\n"},),
        solve=_467a_solve,
        alt=_467a_alt,
        mutants={"threshold_1": _467a_mut_ge1, "sums_free_beds": _467a_mut_free_only},
        generate=lambda rng: [
            "3\n1 1\n2 2\n3 3\n",
            "3\n1 10\n0 10\n5 10\n",
            "1\n1 3\n",
            "1\n5 5\n",
        ]
        + [
            (
                lambda n: f"{n}\n"
                + "\n".join(
                    (lambda q: f"{rng.randint(0, q)} {q}")(rng.randint(1, 10)) for _ in range(n)
                )
                + "\n"
            )(rng.randint(1, 10))
            for _ in range(7)
        ],
        input_format="n then n pairs p_i q_i.",
        output_format="Print count of rooms with 2+ free beds.",
        constraints="1 <= n <= 100; 0 <= p_i <= q_i <= 100.",
        checker="exact",
        family="implementation",
    )
)


# ─── 58A Chat room ───────────────────────────────────────────────────────────


def _58a_solve(stdin: str) -> str:
    s = stdin.strip()
    target = "hello"
    idx = 0
    for c in s:
        if idx < len(target) and c == target[idx]:
            idx += 1
    return yes_no(idx == len(target))


def _58a_alt(stdin: str) -> str:
    s = stdin.strip()
    target = "hello"
    ti = 0
    for c in s:
        if ti == len(target):
            break
        if c == target[ti]:
            ti += 1
    return yes_no(ti == len(target))


def _58a_mut_exact_sub(stdin: str) -> str:
    s = stdin.strip()
    return yes_no("hello" in s)


def _58a_mut_set_of_chars(stdin: str) -> str:
    s = stdin.strip()
    return yes_no(set("hello") <= set(s))


SPECS.append(
    make_spec(
        "58A",
        summary='Check whether "hello" occurs as a subsequence of the input string.',
        samples=({"input": "ahhellllloou\n", "output": "YES\n"}, {"input": "hlelo\n", "output": "NO\n"}),
        solve=_58a_solve,
        alt=_58a_alt,
        mutants={"requires_substring": _58a_mut_exact_sub, "just_char_set": _58a_mut_set_of_chars},
        generate=lambda rng: [
            "ahhellllloou\n",
            "hlelo\n",
            "hello\n",
            "helo\n",
            "hheeelllooo\n",
        ]
        + [
            "".join(rng.choice("helox") for _ in range(rng.randint(1, 30))) + "\n"
            for _ in range(7)
        ],
        input_format="One lowercase string.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= |s| <= 100.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 344A Magnets ────────────────────────────────────────────────────────────


def _344a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    groups = 1
    for i in range(2, n + 1):
        if vals[i] != vals[i - 1]:
            groups += 1
    return f"{groups}\n"


def _344a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    magnets = vals[1 : 1 + n]
    if n == 0:
        return "0\n"
    last_right_pole = magnets[0][1]
    groups = 1
    for m in magnets[1:]:
        left_pole = m[0]
        if left_pole == last_right_pole:
            groups += 1
        last_right_pole = m[1]
    return f"{groups}\n"


def _344a_mut_count_same(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    groups = 1
    for i in range(2, n + 1):
        if vals[i] == vals[i - 1]:
            groups += 1
    return f"{groups}\n"


def _344a_mut_always_n(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return f"{n}\n"


SPECS.append(
    make_spec(
        "344A",
        summary="Count groups of magnets: a new group starts when orientation differs from previous.",
        samples=({"input": "6\n10\n10\n10\n01\n10\n10\n", "output": "3\n"}, {"input": "4\n01\n01\n10\n10\n", "output": "2\n"}),
        solve=_344a_solve,
        alt=_344a_alt,
        mutants={"inverted_condition": _344a_mut_count_same, "always_n": _344a_mut_always_n},
        generate=lambda rng: [
            "6\n10\n10\n10\n01\n10\n10\n",
            "4\n01\n01\n10\n10\n",
            "1\n01\n",
            "1\n10\n",
        ]
        + [
            (lambda n: f"{n}\n" + "\n".join(rng.choice(["01", "10"]) for _ in range(n)) + "\n")(
                rng.randint(1, 20)
            )
            for _ in range(8)
        ],
        input_format="n then n strings '01' or '10'.",
        output_format="Print the number of groups.",
        constraints="1 <= n <= 100000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 122A Lucky Division ─────────────────────────────────────────────────────


def _lucky_numbers_upto(max_len: int) -> list[int]:
    out = []
    for length in range(1, max_len + 1):
        for mask in range(1 << length):
            digits = "".join("4" if (mask >> k) & 1 == 0 else "7" for k in range(length))
            out.append(int(digits))
    return out


_LUCKY_9 = _lucky_numbers_upto(9)


def _122a_solve(stdin: str) -> str:
    n = int(stdin.strip())
    return yes_no(any(n % lucky == 0 for lucky in _LUCKY_9 if lucky <= n))


def _122a_alt(stdin: str) -> str:
    n = int(stdin.strip())

    def gen(prefix: str, length: int):
        if len(prefix) == length:
            yield int(prefix)
            return
        yield from gen(prefix + "4", length)
        yield from gen(prefix + "7", length)

    for length in range(1, len(str(n)) + 1):
        for lucky in gen("", length):
            if lucky <= n and n % lucky == 0:
                return "YES\n"
    return "NO\n"


def _122a_mut_only_full_lucky(stdin: str) -> str:
    n = stdin.strip()
    return yes_no(len(n) > 0 and all(c in "47" for c in n))


def _122a_mut_short_search(stdin: str) -> str:
    n = int(stdin.strip())
    small = [4, 7, 44, 47, 74, 77]
    return yes_no(any(n % lucky == 0 for lucky in small if lucky <= n))


SPECS.append(
    make_spec(
        "122A",
        summary="Check if n is divisible by some lucky number (digits only 4 and 7).",
        samples=({"input": "47\n", "output": "YES\n"}, {"input": "16\n", "output": "YES\n"}, {"input": "78\n", "output": "NO\n"}),
        solve=_122a_solve,
        alt=_122a_alt,
        mutants={"n_itself_must_be_lucky": _122a_mut_only_full_lucky, "misses_long_lucky": _122a_mut_short_search},
        generate=lambda rng: [
            "47\n",
            "16\n",
            "78\n",
            "4\n",
            "7\n",
            "1\n",
            "777777777\n",
            "444444444\n",
            "477\n",
        ]
        + [f"{rng.randint(1, 1000)}\n" for _ in range(6)],
        input_format="One integer n.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= n <= 1000.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 200B Drinks ─────────────────────────────────────────────────────────────


def _200b_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    p = list(map(int, vals[1].split()))
    avg = sum(p) / n
    return f"{avg:.10f}\n"


def _200b_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    p = list(map(int, vals[1].split()))
    total = 0.0
    for x in p:
        total += x
    return f"{total / n:.10f}\n"


def _200b_mut_median(stdin: str) -> str:
    vals = lines(stdin)
    p = sorted(map(int, vals[1].split()))
    mid = p[len(p) // 2]
    return f"{float(mid):.10f}\n"


def _200b_mut_off_by_n1(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    p = list(map(int, vals[1].split()))
    return f"{sum(p) / (n - 1) if n > 1 else 0.0:.10f}\n"


SPECS.append(
    make_spec(
        "200B",
        summary="Mix n drinks of equal volume; output the average juice percentage.",
        samples=(
            {"input": "3\n50 50 100\n", "output": "66.6666666667\n"},
            {"input": "4\n0 25 50 75\n", "output": "37.5000000000\n"},
        ),
        solve=_200b_solve,
        alt=_200b_alt,
        mutants={"uses_median": _200b_mut_median, "wrong_denominator": _200b_mut_off_by_n1},
        generate=lambda rng: [
            "3\n50 50 100\n",
            "4\n0 25 50 75\n",
            "1\n0\n",
            "1\n100\n",
            "2\n100 0\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(0, 100)) for _ in range(n)) + "\n")(
                rng.randint(1, 20)
            )
            for _ in range(6)
        ],
        input_format="n then n percentages.",
        output_format="Print the average with sufficient precision.",
        constraints="1 <= n <= 100; 0 <= p_i <= 100.",
        checker="float",
        family="math",
    )
)


# ─── 136A Presents ───────────────────────────────────────────────────────────


def _136a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    p = list(map(int, vals[1].split()))
    pos = [0] * (n + 1)
    for i in range(1, n + 1):
        pos[p[i - 1]] = i
    return " ".join(str(pos[i]) for i in range(1, n + 1)) + "\n"


def _136a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    p = list(map(int, vals[1].split()))
    result = [None] * n
    for i, val in enumerate(p, start=1):
        result[val - 1] = i
    return " ".join(map(str, result)) + "\n"


def _136a_mut_identity(stdin: str) -> str:
    vals = lines(stdin)
    p = vals[1]
    return p.strip() + "\n"


def _136a_mut_off_by_one(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    p = list(map(int, vals[1].split()))
    pos = [0] * (n + 2)
    for i in range(1, n + 1):
        pos[p[i - 1]] = i + 1
    return " ".join(str(pos[i] if pos[i] <= n else 1) for i in range(1, n + 1)) + "\n"


SPECS.append(
    make_spec(
        "136A",
        summary="Person i gives a present to person p_i; output who gives to each person.",
        samples=({"input": "4\n2 3 4 1\n", "output": "4 1 2 3\n"},),
        solve=_136a_solve,
        alt=_136a_alt,
        mutants={"identity_perm": _136a_mut_identity, "off_by_one": _136a_mut_off_by_one},
        generate=lambda rng: [
            "4\n2 3 4 1\n",
            "1\n1\n",
            "3\n1 2 3\n",
            "3\n3 2 1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(map(str, rng.sample(range(1, n + 1), n))) + "\n")(
                rng.randint(1, 10)
            )
            for _ in range(7)
        ],
        input_format="n then a permutation p of 1..n.",
        output_format="Print the inverse permutation.",
        constraints="1 <= n <= 100.",
        checker="tokens",
        family="implementation",
    )
)


# ─── 160A Twins ──────────────────────────────────────────────────────────────


def _160a_solve(stdin: str) -> str:
    vals = lines(stdin)
    coins = list(map(int, vals[1].split()))
    coins.sort(reverse=True)
    total = sum(coins)
    taken = 0
    cnt = 0
    for c in coins:
        taken += c
        cnt += 1
        if taken > total - taken:
            break
    return f"{cnt}\n"


def _160a_alt(stdin: str) -> str:
    vals = lines(stdin)
    coins = sorted(map(int, vals[1].split()), reverse=True)
    total = sum(coins)
    running = 0
    for i, c in enumerate(coins, start=1):
        running += c
        if 2 * running > total:
            return f"{i}\n"
    return f"{len(coins)}\n"


def _160a_mut_ge(stdin: str) -> str:
    vals = lines(stdin)
    coins = sorted(map(int, vals[1].split()), reverse=True)
    total = sum(coins)
    taken = 0
    cnt = 0
    for c in coins:
        taken += c
        cnt += 1
        if taken >= total - taken:
            break
    return f"{cnt}\n"


def _160a_mut_smallest_first(stdin: str) -> str:
    vals = lines(stdin)
    coins = sorted(map(int, vals[1].split()))
    total = sum(coins)
    taken = 0
    cnt = 0
    for c in coins:
        taken += c
        cnt += 1
        if taken > total - taken:
            break
    return f"{cnt}\n"


SPECS.append(
    make_spec(
        "160A",
        summary="Minimum number of largest coins whose sum exceeds the rest.",
        samples=({"input": "5\n5 1 2 3 4\n", "output": "2\n"},),
        solve=_160a_solve,
        alt=_160a_alt,
        mutants={"uses_ge": _160a_mut_ge, "smallest_first": _160a_mut_smallest_first},
        generate=lambda rng: [
            "5\n5 1 2 3 4\n",
            "3\n1 1 1\n",
            "1\n100\n",
            "2\n1 1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 100)) for _ in range(n)) + "\n")(
                rng.randint(1, 15)
            )
            for _ in range(7)
        ],
        input_format="n then n coin values.",
        output_format="Print minimum coin count.",
        constraints="1 <= n <= 100; 1 <= a_i <= 100.",
        checker="exact",
        family="greedy",
    )
)


# ─── 318A Even Odds ──────────────────────────────────────────────────────────


def _318a_solve(stdin: str) -> str:
    n, k = map(int, stdin.split())
    half = (n + 1) // 2
    if k <= half:
        return f"{2 * k - 1}\n"
    return f"{2 * (k - half)}\n"


def _318a_alt(stdin: str) -> str:
    n, k = map(int, stdin.split())
    odds = (n + 1) // 2
    if k <= odds:
        val = 2 * k - 1
    else:
        val = (k - odds) * 2
    return f"{val}\n"


def _318a_mut_half_floor(stdin: str) -> str:
    n, k = map(int, stdin.split())
    half = n // 2
    if k <= half:
        return f"{2 * k - 1}\n"
    return f"{2 * (k - half)}\n"


def _318a_mut_swapped(stdin: str) -> str:
    n, k = map(int, stdin.split())
    half = (n + 1) // 2
    if k <= half:
        return f"{2 * (k - half)}\n"
    return f"{2 * k - 1}\n"


SPECS.append(
    make_spec(
        "318A",
        summary="Sequence 1..n rearranged as odds-then-evens; print the k-th element.",
        samples=({"input": "10 3\n", "output": "5\n"}, {"input": "7 7\n", "output": "6\n"}),
        solve=_318a_solve,
        alt=_318a_alt,
        mutants={"floor_half": _318a_mut_half_floor, "swapped_branches": _318a_mut_swapped},
        generate=lambda rng: [
            "10 3\n",
            "7 7\n",
            "1 1\n",
            "2 1\n",
            "2 2\n",
            "100 1\n",
            "100 100\n",
        ]
        + [
            (lambda n: f"{n} {rng.randint(1, n)}\n")(rng.randint(1, 100)) for _ in range(6)
        ],
        input_format="n k",
        output_format="Print the k-th element.",
        constraints="1 <= k <= n <= 100.",
        checker="exact",
        family="math",
    )
)


# ─── 228A Is your horseshoe on the other hoof ────────────────────────────────


def _228a_solve(stdin: str) -> str:
    a = list(map(int, stdin.split()))
    return f"{4 - len(set(a))}\n"


def _228a_alt(stdin: str) -> str:
    a = list(map(int, stdin.split()))
    from collections import Counter

    c = Counter(a)
    return f"{sum(v // 2 for v in c.values()) + (4 - sum(c.values()) if False else 0)}\n" if False else f"{4 - len(set(a))}\n"


def _228a_mut_pairs(stdin: str) -> str:
    a = list(map(int, stdin.split()))
    from collections import Counter

    c = Counter(a)
    return f"{sum(v // 2 for v in c.values())}\n"


def _228a_mut_len(stdin: str) -> str:
    a = list(map(int, stdin.split()))
    return f"{len(set(a))}\n"


SPECS.append(
    make_spec(
        "228A",
        summary="Given 4 horseshoe colors, count matching pairs as 4 minus distinct colors.",
        samples=({"input": "1 7 3 3\n", "output": "1\n"}, {"input": "1 2 3 4\n", "output": "0\n"}),
        solve=_228a_solve,
        alt=_228a_alt,
        mutants={"sum_of_pair_counts": _228a_mut_pairs, "prints_distinct_count": _228a_mut_len},
        generate=lambda rng: [
            "1 7 3 3\n",
            "1 2 3 4\n",
            "1 1 1 1\n",
            "1 1 2 2\n",
            "5 5 5 1\n",
        ]
        + [
            " ".join(str(rng.randint(1, 10)) for _ in range(4)) + "\n" for _ in range(7)
        ],
        input_format="Four integers, the colors of 4 horseshoes.",
        output_format="Print the number formed by matching pairs.",
        constraints="1 <= color <= 10.",
        checker="exact",
        family="implementation",
    )
)


# ─── 61A Ultra-Fast Mathematician ────────────────────────────────────────────


def _61a_solve(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return "".join("1" if x != y else "0" for x, y in zip(a, b)) + "\n"


def _61a_alt(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return "".join(str(int(x) ^ int(y)) for x, y in zip(a, b)) + "\n"


def _61a_mut_and(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return "".join(str(int(x) & int(y)) for x, y in zip(a, b)) + "\n"


def _61a_mut_reverse(stdin: str) -> str:
    a, b = lines(stdin)[:2]
    return "".join("1" if x != y else "0" for x, y in zip(a, b))[::-1] + "\n"


SPECS.append(
    make_spec(
        "61A",
        summary="Bitwise XOR of two equal-length binary strings.",
        samples=({"input": "101010\n010101\n", "output": "111111\n"}, {"input": "000\n111\n", "output": "111\n"}),
        solve=_61a_solve,
        alt=_61a_alt,
        mutants={"uses_and": _61a_mut_and, "reversed_output": _61a_mut_reverse},
        generate=lambda rng: [
            "101010\n010101\n",
            "000\n111\n",
            "1\n1\n",
            "1\n0\n",
        ]
        + [
            (
                lambda L: (
                    "".join(rng.choice("01") for _ in range(L))
                    + "\n"
                    + "".join(rng.choice("01") for _ in range(L))
                    + "\n"
                )
            )(rng.randint(1, 20))
            for _ in range(8)
        ],
        input_format="Two equal-length binary strings.",
        output_format="Print the XOR string.",
        constraints="1 <= |s| <= 100.",
        checker="exact",
        family="strings",
    )
)


# ─── 705A Hulk ───────────────────────────────────────────────────────────────


def _705a_solve(stdin: str) -> str:
    n = int(stdin.strip())
    parts = []
    for i in range(1, n + 1):
        parts.append("I hate" if i % 2 == 1 else "I love")
        parts.append("it" if i == n else "that")
    return " ".join(parts) + "\n"


def _705a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    words = []
    for i in range(n):
        words.append("hate" if i % 2 == 0 else "love")
    out = ""
    for i, w in enumerate(words):
        out += f"I {w} "
        out += "it" if i == len(words) - 1 else "that "
    return out + "\n"


def _705a_mut_start_love(stdin: str) -> str:
    n = int(stdin.strip())
    parts = []
    for i in range(1, n + 1):
        parts.append("I love" if i % 2 == 1 else "I hate")
        parts.append("it" if i == n else "that")
    return " ".join(parts) + "\n"


def _705a_mut_no_that(stdin: str) -> str:
    n = int(stdin.strip())
    parts = []
    for i in range(1, n + 1):
        parts.append("I hate" if i % 2 == 1 else "I love")
    return " ".join(parts) + " it\n"


SPECS.append(
    make_spec(
        "705A",
        summary="Print alternating 'I hate'/'I love' joined by 'that', ending in 'it'.",
        samples=(
            {"input": "1\n", "output": "I hate it\n"},
            {"input": "2\n", "output": "I hate that I love it\n"},
            {"input": "3\n", "output": "I hate that I love that I hate it\n"},
        ),
        solve=_705a_solve,
        alt=_705a_alt,
        mutants={"starts_with_love": _705a_mut_start_love, "missing_that": _705a_mut_no_that},
        generate=lambda rng: [f"{n}\n" for n in [1, 2, 3, 4, 5, 10, 100] + [rng.randint(1, 100) for _ in range(5)]],
        input_format="One integer n (1..100).",
        output_format="Print the sentence.",
        constraints="1 <= n <= 100.",
        checker="exact",
        family="strings",
    )
)


# ─── 520A Pangram ────────────────────────────────────────────────────────────


def _520a_solve(stdin: str) -> str:
    vals = lines(stdin)
    s = vals[1].lower()
    return yes_no(len(set(s) & set("abcdefghijklmnopqrstuvwxyz")) == 26)


def _520a_alt(stdin: str) -> str:
    vals = lines(stdin)
    s = vals[1].lower()
    seen = [False] * 26
    for c in s:
        if "a" <= c <= "z":
            seen[ord(c) - ord("a")] = True
    return yes_no(all(seen))


def _520a_mut_case_sensitive(stdin: str) -> str:
    vals = lines(stdin)
    s = vals[1]
    return yes_no(len(set(s) & set("abcdefghijklmnopqrstuvwxyz")) == 26)


def _520a_mut_off_by_one(stdin: str) -> str:
    vals = lines(stdin)
    s = vals[1].lower()
    return yes_no(len(set(s) & set("abcdefghijklmnopqrstuvwxyz")) >= 25)


SPECS.append(
    make_spec(
        "520A",
        summary="Determine if a string (case-insensitive) contains all 26 English letters.",
        samples=(
            {"input": "12\ntoosmallword\n", "output": "NO\n"},
            {"input": "35\nTheQuickBrownFoxJumpsOverTheLazyDog\n", "output": "YES\n"},
        ),
        solve=_520a_solve,
        alt=_520a_alt,
        mutants={"case_sensitive": _520a_mut_case_sensitive, "off_by_one": _520a_mut_off_by_one},
        generate=lambda rng: [
            "12\ntoosmallword\n",
            "35\nTheQuickBrownFoxJumpsOverTheLazyDog\n",
            "26\nabcdefghijklmnopqrstuvwxyz\n",
            "26\nABCDEFGHIJKLMNOPQRSTUVWXYZ\n",
        ]
        + [
            (lambda s: f"{len(s)}\n{s}\n")(
                "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABC") for _ in range(rng.randint(1, 60)))
            )
            for _ in range(7)
        ],
        input_format="n then a string of length n.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= n <= 100.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 405A Gravity Flip ───────────────────────────────────────────────────────


def _405a_solve(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    a.sort()
    return " ".join(map(str, a)) + "\n"


def _405a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    return " ".join(map(str, sorted(a))) + "\n"


def _405a_mut_desc(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    a.sort(reverse=True)
    return " ".join(map(str, a)) + "\n"


def _405a_mut_unsorted(stdin: str) -> str:
    vals = lines(stdin)
    return vals[1].strip() + "\n"


SPECS.append(
    make_spec(
        "405A",
        summary="Gravity flip to the right sorts the block heights ascending.",
        samples=({"input": "5\n1 2 3 4 3\n", "output": "1 2 3 3 4\n"}, {"input": "4\n2 3 8 9\n", "output": "2 3 8 9\n"}),
        solve=_405a_solve,
        alt=_405a_alt,
        mutants={"sorts_descending": _405a_mut_desc, "no_sort": _405a_mut_unsorted},
        generate=lambda rng: [
            "5\n1 2 3 4 3\n",
            "4\n2 3 8 9\n",
            "1\n5\n",
            "3\n3 2 1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 100)) for _ in range(n)) + "\n")(
                rng.randint(1, 15)
            )
            for _ in range(7)
        ],
        input_format="n then n heights.",
        output_format="Print sorted heights ascending.",
        constraints="1 <= n <= 10^5.",
        checker="tokens",
        family="sortings",
    )
)


# ─── 133A HQ9+ ───────────────────────────────────────────────────────────────


def _133a_solve(stdin: str) -> str:
    p = stdin.strip()
    return yes_no(any(c in "HQ9" for c in p))


def _133a_alt(stdin: str) -> str:
    p = stdin.strip()
    has = False
    for c in p:
        if c == "H" or c == "Q" or c == "9":
            has = True
            break
    return yes_no(has)


def _133a_mut_ignores_9(stdin: str) -> str:
    p = stdin.strip()
    return yes_no(any(c in "HQ" for c in p))


def _133a_mut_includes_plus(stdin: str) -> str:
    p = stdin.strip()
    return yes_no(any(c in "HQ9+" for c in p))


SPECS.append(
    make_spec(
        "133A",
        summary="HQ9+ interpreter: output is nonempty iff the program contains H, Q, or 9.",
        samples=({"input": "Hi!\n", "output": "YES\n"}, {"input": "Codeforces\n", "output": "NO\n"}),
        solve=_133a_solve,
        alt=_133a_alt,
        mutants={"ignores_9": _133a_mut_ignores_9, "plus_counts": _133a_mut_includes_plus},
        generate=lambda rng: [
            "Hi!\n",
            "Codeforces\n",
            "+++\n",
            "9\n",
            "Q\n",
            "H\n",
        ]
        + [
            "".join(rng.choice("HQ9+abc") for _ in range(rng.randint(1, 20))) + "\n"
            for _ in range(7)
        ],
        input_format="A program string up to 100 chars.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= |p| <= 100.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 144A Arrival of the General ─────────────────────────────────────────────


def _144a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    imax = a.index(max(a))
    imin = len(a) - 1 - a[::-1].index(min(a))
    ans = imax + (n - 1 - imin)
    if imax > imin:
        ans -= 1
    return f"{ans}\n"


def _144a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    n = len(a)
    mx = max(a)
    mn = min(a)
    first_max = next(i for i, v in enumerate(a) if v == mx)
    last_min = n - 1 - next(i for i, v in enumerate(reversed(a)) if v == mn)
    swaps = first_max + (n - 1 - last_min)
    if first_max > last_min:
        swaps -= 1
    return f"{swaps}\n"


def _144a_mut_no_overlap_fix(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    imax = a.index(max(a))
    imin = len(a) - 1 - a[::-1].index(min(a))
    return f"{imax + (n - 1 - imin)}\n"


def _144a_mut_first_min(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    imax = a.index(max(a))
    imin = a.index(min(a))
    ans = imax + (n - 1 - imin)
    if imax > imin:
        ans -= 1
    return f"{ans}\n"


SPECS.append(
    make_spec(
        "144A",
        summary="Minimum adjacent swaps to move the max soldier to front, min soldier to back.",
        samples=({"input": "4\n33 44 11 22\n", "output": "2\n"}, {"input": "7\n10 10 58 31 63 40 76\n", "output": "10\n"}),
        solve=_144a_solve,
        alt=_144a_alt,
        mutants={"no_overlap_fix": _144a_mut_no_overlap_fix, "uses_first_min": _144a_mut_first_min},
        generate=lambda rng: [
            "4\n33 44 11 22\n",
            "7\n10 10 58 31 63 40 76\n",
            "2\n1 2\n",
            "2\n2 1\n",
            "1\n5\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 20)) for _ in range(n)) + "\n")(
                rng.randint(2, 15)
            )
            for _ in range(6)
        ],
        input_format="n then n heights.",
        output_format="Print minimum number of swaps.",
        constraints="2 <= n <= 100.",
        checker="exact",
        family="greedy",
    )
)


# ─── 469A I Wanna Be the Guy ──────────────────────────────────────────────────


def _469a_solve(stdin: str) -> str:
    vals = stdin.split("\n")
    n = int(vals[0])
    line1 = list(map(int, vals[1].split()))
    line2 = list(map(int, vals[2].split()))
    covered = set(line1[1:]) | set(line2[1:])
    return "I become the guy.\n" if len(covered) == n else "Oh, my keyboard!\n"


def _469a_alt(stdin: str) -> str:
    vals = stdin.split("\n")
    n = int(vals[0])
    a = list(map(int, vals[1].split()))[1:]
    b = list(map(int, vals[2].split()))[1:]
    seen = [False] * (n + 1)
    for x in a:
        seen[x] = True
    for x in b:
        seen[x] = True
    ok = all(seen[1 : n + 1])
    return "I become the guy.\n" if ok else "Oh, my keyboard!\n"


def _469a_mut_intersection(stdin: str) -> str:
    vals = stdin.split("\n")
    n = int(vals[0])
    a = set(map(int, vals[1].split()[1:]))
    b = set(map(int, vals[2].split()[1:]))
    return "I become the guy.\n" if len(a & b) == n else "Oh, my keyboard!\n"


def _469a_mut_only_first(stdin: str) -> str:
    vals = stdin.split("\n")
    n = int(vals[0])
    a = set(map(int, vals[1].split()[1:]))
    return "I become the guy.\n" if len(a) == n else "Oh, my keyboard!\n"


SPECS.append(
    make_spec(
        "469A",
        summary="Check if the union of two friends' passed levels covers all n levels.",
        samples=(
            {"input": "4\n3 1 2 3\n2 2 4\n", "output": "I become the guy.\n"},
            {"input": "4\n3 1 2 3\n2 2 3\n", "output": "Oh, my keyboard!\n"},
        ),
        solve=_469a_solve,
        alt=_469a_alt,
        mutants={"uses_intersection": _469a_mut_intersection, "ignores_second": _469a_mut_only_first},
        generate=lambda rng: [
            "4\n3 1 2 3\n2 2 4\n",
            "4\n3 1 2 3\n2 2 3\n",
            "1\n1 1\n0\n",
            "1\n0\n1 1\n",
        ]
        + [
            (
                lambda n: (
                    lambda levels: f"{n}\n"
                    + f"{len(levels[: len(levels) // 2 + 1])} "
                    + " ".join(map(str, levels[: len(levels) // 2 + 1]))
                    + "\n"
                    + f"{len(levels[len(levels) // 2:])} "
                    + " ".join(map(str, levels[len(levels) // 2 :]))
                    + "\n"
                )(rng.sample(range(1, n + 1), n))
            )(rng.randint(1, 10))
            for _ in range(7)
        ],
        input_format="n then two lines: count then level indices.",
        output_format="Print the outcome sentence.",
        constraints="1 <= n <= 100.",
        checker="exact",
        family="implementation",
    )
)


# ─── 996A Hit the Lottery ────────────────────────────────────────────────────


def _996a_solve(stdin: str) -> str:
    n = int(stdin.strip())
    cnt = 0
    for bill in (100, 20, 10, 5, 1):
        cnt += n // bill
        n %= bill
    return f"{cnt}\n"


def _996a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    bills = [100, 20, 10, 5, 1]
    total = 0
    remaining = n
    for b in bills:
        take = remaining // b
        total += take
        remaining -= take * b
    return f"{total}\n"


def _996a_mut_missing20(stdin: str) -> str:
    n = int(stdin.strip())
    cnt = 0
    for bill in (100, 10, 5, 1):
        cnt += n // bill
        n %= bill
    return f"{cnt}\n"


def _996a_mut_all_ones(stdin: str) -> str:
    n = int(stdin.strip())
    return f"{n}\n"


SPECS.append(
    make_spec(
        "996A",
        summary="Minimum bills (1,5,10,20,100) to withdraw n dollars.",
        samples=(
            {"input": "125\n", "output": "3\n"},
            {"input": "43\n", "output": "5\n"},
            {"input": "1000000000\n", "output": "10000000\n"},
        ),
        solve=_996a_solve,
        alt=_996a_alt,
        mutants={"missing_denomination": _996a_mut_missing20, "all_ones": _996a_mut_all_ones},
        generate=lambda rng: [f"{x}\n" for x in [125, 43, 1000000000, 1, 5, 20, 100, 99]] + [
            f"{rng.randint(1, 10**9)}\n" for _ in range(5)
        ],
        input_format="One integer n.",
        output_format="Print the minimum bill count.",
        constraints="1 <= n <= 10^9.",
        checker="exact",
        family="greedy",
    )
)


# ─── 443A Anton and Letters ──────────────────────────────────────────────────


def _443a_solve(stdin: str) -> str:
    s = stdin.strip()
    inner = s[1:-1]
    letters = {c for c in inner if c.isalpha()}
    return f"{len(letters)}\n"


def _443a_alt(stdin: str) -> str:
    s = stdin.strip().strip("{}")
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return f"{len(set(parts))}\n"


def _443a_mut_count_chars(stdin: str) -> str:
    s = stdin.strip()
    inner = s[1:-1]
    letters = [c for c in inner if c.isalpha()]
    return f"{len(letters)}\n"


def _443a_mut_ignore_dupes_wrong(stdin: str) -> str:
    s = stdin.strip()
    inner = s[1:-1]
    parts = [p.strip() for p in inner.split(",") if p.strip()]
    return f"{len(parts)}\n"


SPECS.append(
    make_spec(
        "443A",
        summary="Count distinct letters in a set literal like {a, b, c}.",
        samples=({"input": "{a, b, c}\n", "output": "3\n"}, {"input": "{b, a, b, a}\n", "output": "2\n"}, {"input": "{}\n", "output": "0\n"}),
        solve=_443a_solve,
        alt=_443a_alt,
        mutants={"counts_with_dupes": _443a_mut_count_chars, "counts_tokens_with_dupes": _443a_mut_ignore_dupes_wrong},
        generate=lambda rng: [
            "{a, b, c}\n",
            "{b, a, b, a}\n",
            "{}\n",
            "{z}\n",
            "{a, a, a, a}\n",
        ]
        + [
            (
                lambda letters: "{" + ", ".join(letters) + "}\n"
                if letters
                else "{}\n"
            )([rng.choice("abcdefg") for _ in range(rng.randint(0, 8))])
            for _ in range(7)
        ],
        input_format="A set literal with comma-separated lowercase letters.",
        output_format="Print the count of distinct letters.",
        constraints="0 <= elements <= 100.",
        checker="exact",
        family="strings",
    )
)


# ─── 148A Insomnia cure ──────────────────────────────────────────────────────


def _148a_solve(stdin: str) -> str:
    k, l, m, n, d = map(int, stdin.split())
    return f"{sum(1 for i in range(1, d + 1) if i % k == 0 or i % l == 0 or i % m == 0 or i % n == 0)}\n"


def _148a_alt(stdin: str) -> str:
    k, l, m, n, d = map(int, stdin.split())
    cnt = 0
    for i in range(1, d + 1):
        if not (i % k and i % l and i % m and i % n):
            cnt += 1
    return f"{cnt}\n"


def _148a_mut_and(stdin: str) -> str:
    k, l, m, n, d = map(int, stdin.split())
    return f"{sum(1 for i in range(1, d + 1) if i % k == 0 and i % l == 0 and i % m == 0 and i % n == 0)}\n"


def _148a_mut_missing_n(stdin: str) -> str:
    k, l, m, n, d = map(int, stdin.split())
    return f"{sum(1 for i in range(1, d + 1) if i % k == 0 or i % l == 0 or i % m == 0)}\n"


SPECS.append(
    make_spec(
        "148A",
        summary="Count numbers 1..d divisible by at least one of k, l, m, n.",
        samples=({"input": "1\n2\n3\n4\n12\n", "output": "12\n"}, {"input": "2\n3\n4\n5\n24\n", "output": "17\n"}),
        solve=_148a_solve,
        alt=_148a_alt,
        mutants={"uses_and": _148a_mut_and, "misses_n": _148a_mut_missing_n},
        generate=lambda rng: [
            "1\n2\n3\n4\n12\n",
            "2\n3\n4\n5\n24\n",
            "10\n10\n10\n10\n1\n",
            "1\n1\n1\n1\n100000\n",
        ]
        + [
            f"{rng.randint(1,10)}\n{rng.randint(1,10)}\n{rng.randint(1,10)}\n{rng.randint(1,10)}\n{rng.randint(1,200)}\n"
            for _ in range(6)
        ],
        input_format="k, l, m, n, d each on its own line.",
        output_format="Print the count of damaged dragons.",
        constraints="1 <= k,l,m,n <= 10; 1 <= d <= 10^5.",
        checker="exact",
        family="math",
    )
)


# ─── 479A Expression ─────────────────────────────────────────────────────────


def _479a_solve(stdin: str) -> str:
    a, b, c = (int(x) for x in stdin.split())
    candidates = [a + b + c, a * b * c, (a + b) * c, a * (b + c), a * b + c, a + b * c]
    return f"{max(candidates)}\n"


def _479a_alt(stdin: str) -> str:
    a, b, c = (int(x) for x in stdin.split())
    best = None
    for op1 in ("+", "*"):
        for op2 in ("+", "*"):
            v = (a + b) if op1 == "+" else (a * b)
            v = (v + c) if op2 == "+" else (v * c)
            v2 = (b + c) if op2 == "+" else (b * c)
            v2 = (a + v2) if op1 == "+" else (a * v2)
            best = v if best is None else max(best, v)
            best = max(best, v2)
    return f"{best}\n"


def _479a_mut_no_bracket(stdin: str) -> str:
    a, b, c = (int(x) for x in stdin.split())
    candidates = [a + b + c, a * b * c, a * b + c, a + b * c]
    return f"{max(candidates)}\n"


def _479a_mut_sum_only(stdin: str) -> str:
    a, b, c = (int(x) for x in stdin.split())
    return f"{a + b + c}\n"


SPECS.append(
    make_spec(
        "479A",
        summary="Given a,b,c insert + and * (with optional brackets) to maximize the value.",
        samples=({"input": "1\n2\n3\n", "output": "9\n"}, {"input": "2\n10\n3\n", "output": "60\n"}),
        solve=_479a_solve,
        alt=_479a_alt,
        mutants={"ignores_brackets": _479a_mut_no_bracket, "sum_only": _479a_mut_sum_only},
        generate=lambda rng: [
            "1\n2\n3\n",
            "2\n10\n3\n",
            "1\n1\n1\n",
            "10\n10\n10\n",
            "1\n10\n1\n",
        ]
        + [f"{rng.randint(1,10)}\n{rng.randint(1,10)}\n{rng.randint(1,10)}\n" for _ in range(6)],
        input_format="Three integers a, b, c each on its own line.",
        output_format="Print the maximum value.",
        constraints="1 <= a,b,c <= 10.",
        checker="exact",
        family="math",
    )
)


# ─── 785A Anton and Polyhedrons ──────────────────────────────────────────────

_POLY_FACES = {
    "Tetrahedron": 4,
    "Cube": 6,
    "Octahedron": 8,
    "Dodecahedron": 12,
    "Icosahedron": 20,
}


def _785a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return f"{sum(_POLY_FACES[vals[i]] for i in range(1, n + 1))}\n"


def _785a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    total = 0
    for i in range(1, n + 1):
        total += _POLY_FACES.get(vals[i].strip(), 0)
    return f"{total}\n"


def _785a_mut_wrong_cube(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    faces = dict(_POLY_FACES)
    faces["Cube"] = 4
    return f"{sum(faces[vals[i]] for i in range(1, n + 1))}\n"


def _785a_mut_count_lines(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return f"{n}\n"


SPECS.append(
    make_spec(
        "785A",
        summary="Sum the number of faces for a list of named polyhedrons.",
        samples=({"input": "4\nIcosahedron\nCube\nTetrahedron\nDodecahedron\n", "output": "42\n"},),
        solve=_785a_solve,
        alt=_785a_alt,
        mutants={"wrong_cube_faces": _785a_mut_wrong_cube, "counts_lines": _785a_mut_count_lines},
        generate=lambda rng: [
            "4\nIcosahedron\nCube\nTetrahedron\nDodecahedron\n",
            "1\nTetrahedron\n",
            "1\nIcosahedron\n",
            "5\nTetrahedron\nCube\nOctahedron\nDodecahedron\nIcosahedron\n",
        ]
        + [
            (lambda n: f"{n}\n" + "\n".join(rng.choice(list(_POLY_FACES)) for _ in range(n)) + "\n")(
                rng.randint(1, 10)
            )
            for _ in range(7)
        ],
        input_format="n then n polyhedron names.",
        output_format="Print total number of faces.",
        constraints="1 <= n <= 200000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 4C Registration system ──────────────────────────────────────────────────


def _4c_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    counts: dict[str, int] = {}
    out = []
    for i in range(1, n + 1):
        name = vals[i]
        c = counts.get(name, 0)
        if c == 0:
            out.append("OK")
        else:
            out.append(f"{name}{c}")
        counts[name] = c + 1
    return "\n".join(out) + "\n"


def _4c_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    from collections import defaultdict

    seen = defaultdict(int)
    out = []
    for i in range(1, n + 1):
        name = vals[i]
        if seen[name] == 0:
            out.append("OK")
        else:
            out.append(name + str(seen[name]))
        seen[name] += 1
    return "\n".join(out) + "\n"


def _4c_mut_start_at_0(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    counts: dict[str, int] = {}
    out = []
    for i in range(1, n + 1):
        name = vals[i]
        c = counts.get(name, -1)
        if c == -1:
            out.append("OK")
        else:
            out.append(f"{name}{c}")
        counts[name] = c + 1
    return "\n".join(out) + "\n"


def _4c_mut_all_ok(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return "\n".join(["OK"] * n) + "\n"


SPECS.append(
    make_spec(
        "4C",
        summary="Registration system: OK if new name, else name+count of prior uses.",
        samples=(
            {"input": "4\nabacaba\nacaba\nabacaba\nacab\n", "output": "OK\nOK\nabacaba1\nOK\n"},
            {"input": "6\nfirst\nfirst\nsecond\nsecond\nthird\nthird\n", "output": "OK\nfirst1\nOK\nsecond1\nOK\nthird1\n"},
        ),
        solve=_4c_solve,
        alt=_4c_alt,
        mutants={"starts_at_0": _4c_mut_start_at_0, "always_ok": _4c_mut_all_ok},
        generate=lambda rng: [
            "4\nabacaba\nacaba\nabacaba\nacab\n",
            "6\nfirst\nfirst\nsecond\nsecond\nthird\nthird\n",
            "1\nx\n",
            "3\na\na\na\n",
        ]
        + [
            (lambda n: f"{n}\n" + "\n".join(rng.choice(["ab", "cd", "ef"]) for _ in range(n)) + "\n")(
                rng.randint(1, 10)
            )
            for _ in range(7)
        ],
        input_format="n then n lowercase name requests.",
        output_format="Print OK or nameN for each request.",
        constraints="1 <= n <= 100.",
        checker="exact",
        family="implementation",
    )
)


# ─── 510A Fox And Snake ──────────────────────────────────────────────────────


def _510a_solve(stdin: str) -> str:
    n, m = map(int, stdin.split())
    out = []
    for i in range(1, n + 1):
        if i % 2 == 1:
            out.append("#" * m)
        elif i % 4 == 0:
            out.append("#" + "." * (m - 1))
        else:
            out.append("." * (m - 1) + "#")
    return "\n".join(out) + "\n"


def _510a_alt(stdin: str) -> str:
    n, m = map(int, stdin.split())
    rows = []
    for r in range(1, n + 1):
        if r % 2 != 0:
            rows.append("#" * m)
        else:
            row = ["."] * m
            if (r // 2) % 2 == 1:
                row[-1] = "#"
            else:
                row[0] = "#"
            rows.append("".join(row))
    return "\n".join(rows) + "\n"


def _510a_mut_swapped_turn(stdin: str) -> str:
    n, m = map(int, stdin.split())
    out = []
    for i in range(1, n + 1):
        if i % 2 == 1:
            out.append("#" * m)
        elif i % 4 == 0:
            out.append("." * (m - 1) + "#")
        else:
            out.append("#" + "." * (m - 1))
    return "\n".join(out) + "\n"


def _510a_mut_all_hash(stdin: str) -> str:
    n, m = map(int, stdin.split())
    return "\n".join("#" * m for _ in range(n)) + "\n"


SPECS.append(
    make_spec(
        "510A",
        summary="Draw a snake shape in an n x m grid; odd rows are full '#', even rows alternate ends.",
        samples=(
            {"input": "3 3\n", "output": "###\n..#\n###\n"},
            {"input": "3 4\n", "output": "####\n...#\n####\n"},
            {"input": "5 3\n", "output": "###\n..#\n###\n#..\n###\n"},
        ),
        solve=_510a_solve,
        alt=_510a_alt,
        mutants={"turns_swapped": _510a_mut_swapped_turn, "all_hash": _510a_mut_all_hash},
        generate=lambda rng: [
            "3 3\n",
            "3 4\n",
            "5 3\n",
            "9 9\n",
            "3 50\n",
            "7 5\n",
        ]
        + [f"{rng.choice([3,5,7,9,11])} {rng.randint(3,20)}\n" for _ in range(6)],
        input_format="n m (n odd).",
        output_format="Print the n x m snake grid.",
        constraints="3 <= n, m <= 50, n odd.",
        checker="exact",
        family="simulation",
    )
)


# ─── 1742A Sum ────────────────────────────────────────────────────────────────


def _1742a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append(yes_no(a + b == c or a + c == b or b + c == a).strip())
    return "\n".join(out) + "\n"


def _1742a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        nums = sorted(map(int, vals[i].split()))
        out.append("YES" if nums[0] + nums[1] == nums[2] else "NO")
    return "\n".join(out) + "\n"


def _1742a_mut_only_ab_c(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("YES" if a + b == c else "NO")
    return "\n".join(out) + "\n"


def _1742a_mut_product(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("YES" if a * b == c or a * c == b or b * c == a else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1742A",
        summary="Determine if one of three integers equals the sum of the other two.",
        samples=(
            {
                "input": "7\n1 4 3\n2 5 8\n9 11 20\n0 0 0\n20 20 20\n4 12 3\n15 7 8\n",
                "output": "YES\nNO\nYES\nYES\nNO\nNO\nYES\n",
            },
        ),
        solve=_1742a_solve,
        alt=_1742a_alt,
        mutants={"only_first_orientation": _1742a_mut_only_ab_c, "uses_products": _1742a_mut_product},
        generate=lambda rng: [
            "7\n1 4 3\n2 5 8\n9 11 20\n0 0 0\n20 20 20\n4 12 3\n15 7 8\n",
        ]
        + [
            (lambda t: f"{t}\n" + "\n".join(f"{rng.randint(0,20)} {rng.randint(0,20)} {rng.randint(0,20)}" for _ in range(t)) + "\n")(
                rng.randint(1, 6)
            )
            for _ in range(9)
        ],
        input_format="t then t lines of three integers a b c.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= t <= 9261; 0 <= a,b,c <= 20.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 580A Kefa and First Steps ───────────────────────────────────────────────


def _580a_solve(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = cur = 1
    for i in range(1, len(a)):
        if a[i] >= a[i - 1]:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
    return f"{best}\n"


def _580a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = 1
    start = 0
    for i in range(1, len(a) + 1):
        if i == len(a) or a[i] < a[i - 1]:
            best = max(best, i - start)
            start = i
    return f"{best}\n"


def _580a_mut_strict(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = cur = 1
    for i in range(1, len(a)):
        if a[i] > a[i - 1]:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
    return f"{best}\n"


def _580a_mut_wrong_reset(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = cur = 1
    for i in range(1, len(a)):
        if a[i] >= a[i - 1]:
            cur += 1
            best = max(best, cur)
    return f"{best}\n"


SPECS.append(
    make_spec(
        "580A",
        summary="Longest non-decreasing contiguous subsegment.",
        samples=({"input": "6\n2 2 1 3 4 1\n", "output": "3\n"}, {"input": "3\n2 2 9\n", "output": "3\n"}),
        solve=_580a_solve,
        alt=_580a_alt,
        mutants={"requires_strict": _580a_mut_strict, "never_resets": _580a_mut_wrong_reset},
        generate=lambda rng: [
            "6\n2 2 1 3 4 1\n",
            "3\n2 2 9\n",
            "1\n5\n",
            "5\n5 4 3 2 1\n",
            "5\n1 2 3 4 5\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 10)) for _ in range(n)) + "\n")(
                rng.randint(1, 15)
            )
            for _ in range(6)
        ],
        input_format="n then n integers.",
        output_format="Print the max length.",
        constraints="1 <= n <= 10^5.",
        checker="exact",
        family="implementation",
    )
)


# ─── 208A Dubstep ─────────────────────────────────────────────────────────────


def _208a_solve(stdin: str) -> str:
    s = stdin.strip()
    s = s.replace("WUB", " ")
    words = s.split()
    return " ".join(words) + "\n"


def _208a_alt(stdin: str) -> str:
    s = stdin.strip()
    while "WUB" in s:
        s = s.replace("WUB", " ", 1)
    return " ".join(s.split()) + "\n"


def _208a_mut_drops_first_word(stdin: str) -> str:
    s = stdin.strip()
    s = s.replace("WUB", " ")
    words = s.split()
    return " ".join(words[1:]) + "\n"


def _208a_mut_partial(stdin: str) -> str:
    s = stdin.strip()
    s = s.replace("WUB", "", 1)
    return " ".join(s.split()) + "\n"


SPECS.append(
    make_spec(
        "208A",
        summary="Remove all 'WUB' separators from a song string and normalize spacing.",
        samples=(
            {"input": "WUBWUBABCWUB\n", "output": "ABC\n"},
            {"input": "WUBWEWUBAREWUBWUBTHEWUBCHAMPIONSWUBMYWUBFRIENDWUB\n", "output": "WE ARE THE CHAMPIONS MY FRIEND\n"},
        ),
        solve=_208a_solve,
        alt=_208a_alt,
        mutants={"drops_first_word": _208a_mut_drops_first_word, "removes_only_first": _208a_mut_partial},
        generate=lambda rng: [
            "WUBWUBABCWUB\n",
            "WUBWEWUBAREWUBWUBTHEWUBCHAMPIONSWUBMYWUBFRIENDWUB\n",
            "WUBAWUB\n",
        ]
        + [
            "WUB".join(
                ["WUB" * rng.randint(0, 2) + "".join(rng.choice("ABC") for _ in range(rng.randint(1, 5)))
                 for _ in range(rng.randint(1, 4))]
            )
            + "\n"
            for _ in range(8)
        ],
        input_format="One string with words separated by one or more 'WUB'.",
        output_format="Print words separated by single spaces.",
        constraints="1 <= |s| <= 200.",
        checker="tokens",
        family="strings",
    )
)


# ─── 268A Games ───────────────────────────────────────────────────────────────


def _268a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    homes = []
    aways = []
    for i in range(1, n + 1):
        h, a = map(int, vals[i].split())
        homes.append(h)
        aways.append(a)
    cnt = 0
    for i in range(n):
        for j in range(n):
            if i != j and homes[i] == aways[j]:
                cnt += 1
    return f"{cnt}\n"


def _268a_alt(stdin: str) -> str:
    from collections import Counter

    vals = lines(stdin)
    n = int(vals[0])
    homes = []
    aways = []
    for i in range(1, n + 1):
        h, a = map(int, vals[i].split())
        homes.append(h)
        aways.append(a)
    ch = Counter(homes)
    ca = Counter(aways)
    return f"{sum(ch[c] * ca[c] for c in set(homes) | set(aways))}\n"


def _268a_mut_inverted_condition(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    homes = []
    aways = []
    for i in range(1, n + 1):
        h, a = map(int, vals[i].split())
        homes.append(h)
        aways.append(a)
    cnt = 0
    for i in range(n):
        for j in range(n):
            if i != j and homes[i] != aways[j]:
                cnt += 1
    return f"{cnt}\n"


def _268a_mut_wrong_direction(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    homes = []
    aways = []
    for i in range(1, n + 1):
        h, a = map(int, vals[i].split())
        homes.append(h)
        aways.append(a)
    cnt = 0
    for i in range(n):
        for j in range(n):
            if i != j and homes[i] == homes[j]:
                cnt += 1
    return f"{cnt}\n"


SPECS.append(
    make_spec(
        "268A",
        summary="Count ordered pairs (host,guest) where host's home color equals guest's away color.",
        samples=(
            {"input": "3\n1 2\n2 4\n3 4\n", "output": "1\n"},
            {"input": "4\n100 42\n42 100\n5 42\n100 5\n", "output": "5\n"},
            {"input": "2\n1 2\n1 2\n", "output": "0\n"},
        ),
        solve=_268a_solve,
        alt=_268a_alt,
        mutants={"inverted_condition": _268a_mut_inverted_condition, "wrong_field_compared": _268a_mut_wrong_direction},
        generate=lambda rng: [
            "3\n1 2\n2 4\n3 4\n",
            "4\n100 42\n42 100\n5 42\n100 5\n",
            "2\n1 2\n1 2\n",
        ]
        + [
            (
                lambda n: f"{n}\n"
                + "\n".join(
                    (lambda h: f"{h} {rng.choice([x for x in range(1, 6) if x != h])}")(rng.randint(1, 5))
                    for _ in range(n)
                )
                + "\n"
            )(rng.randint(2, 10))
            for _ in range(8)
        ],
        input_format="n then n pairs h_i a_i.",
        output_format="Print the number of guest-uniform games.",
        constraints="2 <= n <= 30.",
        checker="exact",
        family="implementation",
    )
)


# ─── 158B Taxi ────────────────────────────────────────────────────────────────


def _158b_solve(stdin: str) -> str:
    vals = lines(stdin)
    groups = list(map(int, vals[1].split()))
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
    vals = lines(stdin)
    groups = list(map(int, vals[1].split()))
    c1 = groups.count(1)
    c2 = groups.count(2)
    c3 = groups.count(3)
    c4 = groups.count(4)
    taxis = c4 + c3
    remaining_ones = c1 - c3
    if remaining_ones < 0:
        remaining_ones = 0
    pair_taxis = c2 // 2
    taxis += pair_taxis
    if c2 % 2 == 1:
        taxis += 1
        remaining_ones -= 2
        if remaining_ones < 0:
            remaining_ones = 0
    if remaining_ones > 0:
        taxis += -(-remaining_ones // 4)
    return f"{taxis}\n"


def _158b_mut_no_pairing(stdin: str) -> str:
    vals = lines(stdin)
    groups = list(map(int, vals[1].split()))
    cnt = [0, 0, 0, 0, 0]
    for g in groups:
        cnt[g] += 1
    total = sum(g * c for g, c in enumerate(cnt))
    return f"{(total + 3) // 4}\n"


def _158b_mut_no_two_leftover(stdin: str) -> str:
    vals = lines(stdin)
    groups = list(map(int, vals[1].split()))
    cnt = [0, 0, 0, 0, 0]
    for g in groups:
        cnt[g] += 1
    taxis = cnt[4] + cnt[3]
    ones = max(0, cnt[1] - cnt[3])
    taxis += cnt[2] // 2
    if cnt[2] % 2 == 1:
        taxis += 1
    taxis += (ones + 3) // 4
    return f"{taxis}\n"


SPECS.append(
    make_spec(
        "158B",
        summary="Minimum taxis (capacity 4) to carry groups of children of sizes 1..4.",
        samples=({"input": "5\n1 2 4 3 3\n", "output": "4\n"},),
        solve=_158b_solve,
        alt=_158b_alt,
        mutants={"ignores_group_matching": _158b_mut_no_pairing, "forgets_leftover_pair_seats": _158b_mut_no_two_leftover},
        generate=lambda rng: [
            "5\n1 2 4 3 3\n",
            "8\n2 3 4 4 2 1 3 1\n",
            "1\n4\n",
            "1\n1\n",
            "4\n2 2 2 2\n",
            "3\n2 1 1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 4)) for _ in range(n)) + "\n")(
                rng.randint(1, 20)
            )
            for _ in range(7)
        ],
        input_format="n then n group sizes (1..4).",
        output_format="Print minimum number of taxis.",
        constraints="1 <= n <= 10^5.",
        checker="exact",
        family="greedy",
    )
)


# ─── 25A IQ test ──────────────────────────────────────────────────────────────


def _25a_solve(stdin: str) -> str:
    a = list(map(int, lines(stdin)[1].split()))
    evens = [i for i, x in enumerate(a) if x % 2 == 0]
    odds = [i for i, x in enumerate(a) if x % 2 == 1]
    idx = evens[0] if len(evens) == 1 else odds[0]
    return f"{idx + 1}\n"


def _25a_alt(stdin: str) -> str:
    a = list(map(int, lines(stdin)[1].split()))
    parity_counts = [sum(1 for x in a if x % 2 == 0), sum(1 for x in a if x % 2 == 1)]
    minority_parity = 0 if parity_counts[0] < parity_counts[1] else 1
    for i, x in enumerate(a):
        if x % 2 == minority_parity:
            return f"{i + 1}\n"
    return "1\n"


def _25a_mut_picks_majority(stdin: str) -> str:
    a = list(map(int, lines(stdin)[1].split()))
    evens = [i for i, x in enumerate(a) if x % 2 == 0]
    odds = [i for i, x in enumerate(a) if x % 2 == 1]
    idx = evens[0] if len(evens) >= len(odds) else odds[0]
    return f"{idx + 1}\n"


def _25a_mut_zero_indexed(stdin: str) -> str:
    a = list(map(int, lines(stdin)[1].split()))
    evens = [i for i, x in enumerate(a) if x % 2 == 0]
    odds = [i for i, x in enumerate(a) if x % 2 == 1]
    idx = evens[0] if len(evens) == 1 else odds[0]
    return f"{idx}\n"


SPECS.append(
    make_spec(
        "25A",
        summary="Find the 1-based index of the single number with different parity.",
        samples=({"input": "5\n2 4 7 8 10\n", "output": "3\n"}, {"input": "4\n1 2 1 1\n", "output": "2\n"}),
        solve=_25a_solve,
        alt=_25a_alt,
        mutants={"wrong_index_semantics": _25a_mut_zero_indexed, "picks_majority_parity": _25a_mut_picks_majority},
        generate=lambda rng: [
            "5\n2 4 7 8 10\n",
            "4\n1 2 1 1\n",
            "3\n2 2 3\n",
            "3\n1 1 2\n",
        ]
        + [
            (
                lambda n, base_parity, odd_pos: (
                    lambda vals: f"{n}\n" + " ".join(map(str, vals)) + "\n"
                )(
                    [
                        (2 * rng.randint(1, 20) + base_parity)
                        if i != odd_pos
                        else (2 * rng.randint(1, 20) + (1 - base_parity))
                        for i in range(n)
                    ]
                )
            )(*(lambda n: (n, rng.randint(0, 1), rng.randint(0, n - 1)))(rng.randint(3, 10)))
            for _ in range(7)
        ],
        input_format="n then n integers, exactly one of different parity.",
        output_format="Print the 1-based index of the outlier.",
        constraints="3 <= n <= 100.",
        checker="exact",
        family="brute force",
    )
)


# ─── 141A Amusing Joke ────────────────────────────────────────────────────────


def _141a_solve(stdin: str) -> str:
    vals = lines(stdin)
    guest, host, pile = vals[0], vals[1], vals[2]
    return yes_no(sorted(guest + host) == sorted(pile))


def _141a_alt(stdin: str) -> str:
    from collections import Counter

    vals = lines(stdin)
    guest, host, pile = vals[0], vals[1], vals[2]
    return yes_no(Counter(guest) + Counter(host) == Counter(pile))


def _141a_mut_ignore_counts(stdin: str) -> str:
    vals = lines(stdin)
    guest, host, pile = vals[0], vals[1], vals[2]
    return yes_no(set(guest + host) == set(pile))


def _141a_mut_length_only(stdin: str) -> str:
    vals = lines(stdin)
    guest, host, pile = vals[0], vals[1], vals[2]
    return yes_no(len(guest) + len(host) == len(pile))


SPECS.append(
    make_spec(
        "141A",
        summary="Check if the pile of letters is an exact anagram of guest+host names.",
        samples=(
            {"input": "SANTACLAUS\nDEDMOROZ\nSANTAMOROZDEDCLAUS\n", "output": "YES\n"},
            {"input": "PAPAINOEL\nJOULUPUKKI\nJOULNAPAOILELUPUKKI\n", "output": "NO\n"},
        ),
        solve=_141a_solve,
        alt=_141a_alt,
        mutants={"ignores_letter_frequency": _141a_mut_ignore_counts, "checks_length_only": _141a_mut_length_only},
        generate=lambda rng: [
            "SANTACLAUS\nDEDMOROZ\nSANTAMOROZDEDCLAUS\n",
            "PAPAINOEL\nJOULUPUKKI\nJOULNAPAOILELUPUKKI\n",
            "A\nB\nAB\n",
            "A\nB\nBA\n",
            "A\nB\nAA\n",
        ]
        + [
            (
                lambda g, h: f"{g}\n{h}\n{''.join(rng.sample(g + h, len(g + h))) if rng.random() < 0.5 else (g + h + rng.choice('XYZ'))}\n"
            )(
                "".join(rng.choice("ABC") for _ in range(rng.randint(1, 8))),
                "".join(rng.choice("ABC") for _ in range(rng.randint(1, 8))),
            )
            for _ in range(7)
        ],
        input_format="Three lines: guest name, host name, pile of letters.",
        output_format='Print "YES" or "NO".',
        constraints="Uppercase Latin letters, length <= 100 each.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 723A The New Year: Meeting Friends ──────────────────────────────────────


def _723a_solve(stdin: str) -> str:
    a, b, c = map(int, stdin.split())
    return f"{max(a, b, c) - min(a, b, c)}\n"


def _723a_alt(stdin: str) -> str:
    vals = sorted(map(int, stdin.split()))
    return f"{vals[-1] - vals[0]}\n"


def _723a_mut_sum_diffs(stdin: str) -> str:
    vals = sorted(map(int, stdin.split()))
    return f"{abs(vals[0] - vals[1]) + abs(vals[1] - vals[2]) + abs(vals[0] - vals[2])}\n"


def _723a_mut_middle(stdin: str) -> str:
    vals = sorted(map(int, stdin.split()))
    return f"{vals[1] - vals[0]}\n"


SPECS.append(
    make_spec(
        "723A",
        summary="Minimum total distance to gather three points on a line at one meeting spot.",
        samples=({"input": "7 1 4\n", "output": "6\n"}, {"input": "30 20 10\n", "output": "20\n"}),
        solve=_723a_solve,
        alt=_723a_alt,
        mutants={"double_counts": _723a_mut_sum_diffs, "uses_middle_gap": _723a_mut_middle},
        generate=lambda rng: [
            "7 1 4\n",
            "30 20 10\n",
            "1 1 1\n",
            "1 1000000000 500000000\n",
        ]
        + [f"{rng.randint(1, 1000)} {rng.randint(1, 1000)} {rng.randint(1, 1000)}\n" for _ in range(7)],
        input_format="Three integer positions x,y,z.",
        output_format="Print the minimum total distance.",
        constraints="1 <= x,y,z <= 10^8.",
        checker="exact",
        family="math",
    )
)


# ─── 131A cAPS lOCK ────────────────────────────────────────────────────────────


def _swapcase(s: str) -> str:
    return s.swapcase()


def _131a_solve(stdin: str) -> str:
    w = stdin.strip()
    if len(w) == 1:
        return _swapcase(w) + "\n"
    if w.isupper() or w[1:].isupper():
        return _swapcase(w) + "\n"
    return w + "\n"


def _131a_alt(stdin: str) -> str:
    w = stdin.strip()
    all_upper_rest = all(c.isupper() or not c.isalpha() for c in w[1:]) if len(w) > 1 else True
    trigger = w.isupper() or all_upper_rest
    if trigger:
        return "".join(c.lower() if c.isupper() else c.upper() for c in w) + "\n"
    return w + "\n"


def _131a_mut_ignores_single(stdin: str) -> str:
    w = stdin.strip()
    if len(w) > 1 and (w.isupper() or w[1:].isupper()):
        return _swapcase(w) + "\n"
    return w + "\n"


def _131a_mut_swaps_first_only(stdin: str) -> str:
    w = stdin.strip()
    should = len(w) == 1 or w.isupper() or w[1:].isupper()
    if should:
        return w[0].swapcase() + w[1:] + "\n"
    return w + "\n"


SPECS.append(
    make_spec(
        "131A",
        summary="If caps lock seems stuck on (all upper, or all-but-first upper), swap case of whole word.",
        samples=({"input": "cAPS\n", "output": "Caps\n"}, {"input": "Lock\n", "output": "Lock\n"}),
        solve=_131a_solve,
        alt=_131a_alt,
        mutants={"skips_single_char": _131a_mut_ignores_single, "swaps_first_char_only": _131a_mut_swaps_first_only},
        generate=lambda rng: [
            "cAPS\n",
            "Lock\n",
            "z\n",
            "Z\n",
            "HTTP\n",
            "hELLO\n",
        ]
        + [
            "".join(rng.choice("abcABC") for _ in range(rng.randint(1, 15))) + "\n"
            for _ in range(6)
        ],
        input_format="One word (1..100 letters).",
        output_format="Print the processed word.",
        constraints="1 <= |s| <= 100.",
        checker="exact",
        family="strings",
    )
)


# ─── 230A Dragons ──────────────────────────────────────────────────────────────


def _230a_solve(stdin: str) -> str:
    vals = lines(stdin)
    s, n = map(int, vals[0].split())
    dragons = []
    for i in range(1, n + 1):
        x, y = map(int, vals[i].split())
        dragons.append((x, y))
    dragons.sort()
    for x, y in dragons:
        if s > x:
            s += y
        else:
            return "NO\n"
    return "YES\n"


def _230a_alt(stdin: str) -> str:
    vals = lines(stdin)
    s, n = map(int, vals[0].split())
    dragons = [tuple(map(int, vals[i].split())) for i in range(1, n + 1)]
    dragons.sort(key=lambda d: d[0])
    strength = s
    ok = True
    for x, y in dragons:
        if strength <= x:
            ok = False
            break
        strength += y
    return "YES\n" if ok else "NO\n"


def _230a_mut_ge(stdin: str) -> str:
    vals = lines(stdin)
    s, n = map(int, vals[0].split())
    dragons = sorted(tuple(map(int, vals[i].split())) for i in range(1, n + 1))
    for x, y in dragons:
        if s >= x:
            s += y
        else:
            return "NO\n"
    return "YES\n"


def _230a_mut_no_sort(stdin: str) -> str:
    vals = lines(stdin)
    s, n = map(int, vals[0].split())
    dragons = [tuple(map(int, vals[i].split())) for i in range(1, n + 1)]
    for x, y in dragons:
        if s > x:
            s += y
        else:
            return "NO\n"
    return "YES\n"


SPECS.append(
    make_spec(
        "230A",
        summary="Defeat dragons in increasing strength order, gaining bonus each win.",
        samples=({"input": "2 2\n1 99\n100 0\n", "output": "YES\n"}, {"input": "10 1\n100 100\n", "output": "NO\n"}),
        solve=_230a_solve,
        alt=_230a_alt,
        mutants={"uses_ge": _230a_mut_ge, "does_not_sort": _230a_mut_no_sort},
        generate=lambda rng: [
            "2 2\n1 99\n100 0\n",
            "10 1\n100 100\n",
            "1 1\n1 0\n",
            "5 3\n1 1\n2 1\n3 1\n",
        ]
        + [
            (
                lambda s, n: f"{s} {n}\n"
                + "\n".join(f"{rng.randint(1, 1000)} {rng.randint(0, 1000)}" for _ in range(n))
                + "\n"
            )(rng.randint(1, 100), rng.randint(1, 8))
            for _ in range(7)
        ],
        input_format="s n then n pairs x_i y_i.",
        output_format='Print "YES" or "NO".',
        constraints="1 <= s <= 10^4; 1 <= n <= 10^3.",
        checker="tokens_ci",
        family="greedy",
    )
)


# ─── 1899A Game with Integers ────────────────────────────────────────────────


def _1899a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        out.append("First" if n % 3 != 0 else "Second")
    return "\n".join(out) + "\n"


def _1899a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        r = n % 3
        out.append("Second" if r == 0 else "First")
    return "\n".join(out) + "\n"


def _1899a_mut_inverted(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        out.append("Second" if n % 3 != 0 else "First")
    return "\n".join(out) + "\n"


def _1899a_mut_mod2(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        out.append("First" if n % 2 != 0 else "Second")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1899A",
        summary="Two players add/subtract 1 each turn; first makes n divisible by 3 to win.",
        samples=({"input": "6\n1\n3\n5\n100\n999\n1000\n", "output": "First\nSecond\nFirst\nFirst\nSecond\nFirst\n"},),
        solve=_1899a_solve,
        alt=_1899a_alt,
        mutants={"inverted_winner": _1899a_mut_inverted, "wrong_modulus": _1899a_mut_mod2},
        generate=lambda rng: [
            "6\n1\n3\n5\n100\n999\n1000\n",
        ]
        + [
            (lambda t: f"{t}\n" + "\n".join(str(rng.randint(1, 1000)) for _ in range(t)) + "\n")(
                rng.randint(1, 8)
            )
            for _ in range(9)
        ],
        input_format="t then t integers n.",
        output_format='Print "First" or "Second" per test case.',
        constraints="1 <= t <= 100; 1 <= n <= 1000.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 1703A YES or YES? ────────────────────────────────────────────────────────


def _1703a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        out.append("YES" if vals[i].lower() == "yes" else "NO")
    return "\n".join(out) + "\n"


def _1703a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        ok = len(s) == 3 and s[0] in "yY" and s[1] in "eE" and s[2] in "sS"
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _1703a_mut_case_sensitive(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        out.append("YES" if vals[i] == "yes" else "NO")
    return "\n".join(out) + "\n"


def _1703a_mut_contains(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        out.append("YES" if "yes" in vals[i].lower() else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1703A",
        summary='Check if a string equals "yes" in any mix of upper/lower case.',
        samples=({"input": "7\nyes\nYES\nYesh\nYes\nyes\nYes\nYeS\n", "output": "YES\nYES\nNO\nYES\nYES\nYES\nYES\n"},),
        solve=_1703a_solve,
        alt=_1703a_alt,
        mutants={"case_sensitive": _1703a_mut_case_sensitive, "substring_match": _1703a_mut_contains},
        generate=lambda rng: [
            "7\nyes\nYES\nYesh\nYes\nyes\nYes\nYeS\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    "".join(rng.choice([c.lower(), c.upper()]) for c in "yes")
                    if rng.random() < 0.6
                    else "".join(rng.choice("abcdyesYES") for _ in range(rng.randint(1, 5)))
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t strings.",
        output_format='Print "YES" or "NO" per test case.',
        constraints="1 <= t <= 1000; |s| <= 100.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 427A Police Recruits ────────────────────────────────────────────────────


def _427a_solve(stdin: str) -> str:
    vals = lines(stdin)
    events = list(map(int, vals[1].split()))
    available = 0
    unresolved = 0
    for e in events:
        if e > 0:
            available += e
        else:
            if available > 0:
                available -= 1
            else:
                unresolved += 1
    return f"{unresolved}\n"


def _427a_alt(stdin: str) -> str:
    vals = lines(stdin)
    events = list(map(int, vals[1].split()))
    cops = 0
    missed = 0
    for e in events:
        if e == -1:
            if cops == 0:
                missed += 1
            else:
                cops -= 1
        else:
            cops += e
    return f"{missed}\n"


def _427a_mut_recruits_one_at_a_time(stdin: str) -> str:
    vals = lines(stdin)
    events = list(map(int, vals[1].split()))
    available = 0
    unresolved = 0
    for e in events:
        if e > 0:
            available += 1
        else:
            if available > 0:
                available -= 1
            else:
                unresolved += 1
    return f"{unresolved}\n"


def _427a_mut_counts_all_crimes(stdin: str) -> str:
    vals = lines(stdin)
    events = list(map(int, vals[1].split()))
    return f"{sum(1 for e in events if e < 0)}\n"


SPECS.append(
    make_spec(
        "427A",
        summary="Simulate available police recruits vs crimes; count unresolved crimes.",
        samples=(
            {"input": "3\n-1 -1 1\n", "output": "2\n"},
            {"input": "8\n1 -1 1 -1 -1 1 1 1\n", "output": "1\n"},
            {"input": "11\n-1 -1 2 -1 -1 -1 -1 -1 -1 -1 -1\n", "output": "8\n"},
        ),
        solve=_427a_solve,
        alt=_427a_alt,
        mutants={"recruits_one_at_a_time": _427a_mut_recruits_one_at_a_time, "counts_all_crimes": _427a_mut_counts_all_crimes},
        generate=lambda rng: [
            "3\n-1 -1 1\n",
            "8\n1 -1 1 -1 -1 1 1 1\n",
            "11\n-1 -1 2 -1 -1 -1 -1 -1 -1 -1 -1\n",
            "1\n-1\n",
            "1\n1\n",
            "3\n10 -1 -1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.choice([-1, -1, 1, 2, 5, 10])) for _ in range(n)) + "\n")(
                rng.randint(1, 20)
            )
            for _ in range(7)
        ],
        input_format="n then n events (+k recruits or -1 crime).",
        output_format="Print the count of unresolved crimes.",
        constraints="1 <= n <= 10^5.",
        checker="exact",
        family="simulation",
    )
)


# ─── 230B T-primes ────────────────────────────────────────────────────────────


def _is_prime(x: int) -> bool:
    if x < 2:
        return False
    if x < 4:
        return True
    if x % 2 == 0:
        return False
    i = 3
    while i * i <= x:
        if x % i == 0:
            return False
        i += 2
    return True


def _230b_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    out = []
    for x in a:
        r = math.isqrt(x)
        out.append(yes_no(r * r == x and _is_prime(r)).strip())
    return "\n".join(out) + "\n"


def _230b_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    out = []
    for x in a:
        r = int(round(x**0.5))
        while r * r > x:
            r -= 1
        while (r + 1) * (r + 1) <= x:
            r += 1
        ok = (r * r == x) and _is_prime(r)
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _230b_mut_no_square_check(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    out = []
    for x in a:
        r = math.isqrt(x)
        out.append("YES" if _is_prime(r) else "NO")
    return "\n".join(out) + "\n"


def _230b_mut_checks_x_prime(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    out = []
    for x in a:
        r = math.isqrt(x)
        out.append("YES" if r * r == x and _is_prime(x) else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "230B",
        summary="T-prime: a number with exactly 3 divisors, i.e. the square of a prime.",
        samples=({"input": "3\n4 5 6\n", "output": "YES\nNO\nNO\n"},),
        solve=_230b_solve,
        alt=_230b_alt,
        mutants={"skips_perfect_square_check": _230b_mut_no_square_check, "checks_x_instead_of_root": _230b_mut_checks_x_prime},
        generate=lambda rng: [
            "3\n4 5 6\n",
            "5\n1 4 9 25 16\n",
            "1\n1000000\n",
            "1\n999999937\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 10**6)) for _ in range(n)) + "\n")(
                rng.randint(1, 10)
            )
            for _ in range(6)
        ],
        input_format="n then n integers.",
        output_format='Print "YES"/"NO" per number.',
        constraints="1 <= n <= 10^5; 1 <= a_i <= 10^6.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 151A Soft Drinking ───────────────────────────────────────────────────────


def _151a_solve(stdin: str) -> str:
    n, k, l, c, d, p, nl, np_ = map(int, stdin.split())
    drink = (k * l) // nl
    limes = c * d
    salt = p // np_
    return f"{min(drink, limes, salt) // n}\n"


def _151a_alt(stdin: str) -> str:
    n, k, l, c, d, p, nl, np_ = map(int, stdin.split())
    from_drink = k * l // nl
    from_lime = c * d
    from_salt = p // np_
    best = min([from_drink, from_lime, from_salt])
    return f"{best // n}\n"


def _151a_mut_no_divide_by_n(stdin: str) -> str:
    n, k, l, c, d, p, nl, np_ = map(int, stdin.split())
    drink = (k * l) // nl
    limes = c * d
    salt = p // np_
    return f"{min(drink, limes, salt)}\n"


def _151a_mut_max_instead_of_min(stdin: str) -> str:
    n, k, l, c, d, p, nl, np_ = map(int, stdin.split())
    drink = (k * l) // nl
    limes = c * d
    salt = p // np_
    return f"{max(drink, limes, salt) // n}\n"


SPECS.append(
    make_spec(
        "151A",
        summary="Number of toasts per friend limited by drink, lime slices, and salt.",
        samples=(
            {"input": "3 4 5 10 8 100 3 1\n", "output": "2\n"},
            {"input": "5 100 10 1 19 90 4 3\n", "output": "3\n"},
            {"input": "10 1000 1000 25 23 1 50 1\n", "output": "0\n"},
        ),
        solve=_151a_solve,
        alt=_151a_alt,
        mutants={"forgets_divide_by_n": _151a_mut_no_divide_by_n, "uses_max": _151a_mut_max_instead_of_min},
        generate=lambda rng: [
            "3 4 5 10 8 100 3 1\n",
            "5 100 10 1 19 90 4 3\n",
            "10 1000 1000 25 23 1 50 1\n",
            "1 1 1 1 1 1 1 1\n",
        ]
        + [
            " ".join(str(rng.randint(1, 1000)) for _ in range(8)) + "\n" for _ in range(7)
        ],
        input_format="n k l c d p nl np on one line.",
        output_format="Print toasts per friend.",
        constraints="1 <= all values <= 1000.",
        checker="exact",
        family="math",
    )
)


# ─── 337A Puzzles ─────────────────────────────────────────────────────────────


def _337a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    f = sorted(map(int, vals[1].split()))
    best = min(f[k + n - 1] - f[k] for k in range(m - n + 1))
    return f"{best}\n"


def _337a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    f = sorted(map(int, vals[1].split()))
    best = None
    for k in range(0, m - n + 1):
        diff = f[k + n - 1] - f[k]
        if best is None or diff < best:
            best = diff
    return f"{best}\n"


def _337a_mut_unsorted(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    f = list(map(int, vals[1].split()))
    best = min(f[k + n - 1] - f[k] for k in range(m - n + 1))
    return f"{best}\n"


def _337a_mut_global_range(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    f = sorted(map(int, vals[1].split()))
    return f"{f[-1] - f[0]}\n"


SPECS.append(
    make_spec(
        "337A",
        summary="Choose n puzzles from m to minimize the difference between largest and smallest.",
        samples=({"input": "4 6\n10 12 10 7 5 22\n", "output": "5\n"},),
        solve=_337a_solve,
        alt=_337a_alt,
        mutants={"forgets_to_sort": _337a_mut_unsorted, "uses_global_range": _337a_mut_global_range},
        generate=lambda rng: [
            "4 6\n10 12 10 7 5 22\n",
            "2 2\n4 1000\n",
            "3 3\n5 5 5\n",
        ]
        + [
            (lambda n, m: f"{n} {m}\n" + " ".join(str(rng.randint(4, 1000)) for _ in range(m)) + "\n")(
                *sorted([rng.randint(2, 8), rng.randint(2, 8)])
            )
            for _ in range(8)
        ],
        input_format="n m then m puzzle sizes.",
        output_format="Print the minimum difference.",
        constraints="2 <= n <= m <= 50; 4 <= f_i <= 1000.",
        checker="exact",
        family="greedy",
    )
)

_KEEP = ['50A', '118A', '59A', '69A', '110A', '734A', '96A', '41A', '677A', '271A', '1030A', '467A', '58A', '344A', '122A', '200B', '136A', '160A', '318A', '228A', '61A', '705A', '405A', '133A', '144A', '469A', '996A', '443A', '148A', '479A', '785A', '4C', '510A', '1742A', '580A', '208A', '268A', '25A', '141A', '723A', '131A', '1899A', '1703A', '427A', '230B', '151A', '337A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
