"""Dual-oracle ProblemOracleSpec entries generated from catalog/batches/batch_01.json.

Each problem has two independently-derived correct oracles plus >=2 mutants
that must fail on at least one generated/sample case.
"""

from __future__ import annotations

import math
import random
from collections import Counter

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

SPECS = []


# ─── 630A Again Twenty Five! ─────────────────────────────────────────────────


def _630a_solve(stdin: str) -> str:
    return "25\n"


def _630a_alt(stdin: str) -> str:
    n = int(stdin.strip())
    return f"{pow(25, n, 100):02d}\n"


def _630a_mut_first_only(stdin: str) -> str:
    n = int(stdin.strip())
    return "25\n" if n == 1 else "00\n"


def _630a_mut_wrong_base(stdin: str) -> str:
    n = int(stdin.strip())
    return f"{pow(5, n, 100):02d}\n"


SPECS.append(
    make_spec(
        "630A",
        summary="Last two digits of 25^n are always 25 for n >= 1.",
        samples=({"input": "1\n", "output": "25\n"}, {"input": "2\n", "output": "25\n"}),
        solve=_630a_solve,
        alt=_630a_alt,
        mutants={"only_correct_for_n1": _630a_mut_first_only, "wrong_base": _630a_mut_wrong_base},
        generate=lambda rng: [
            "1\n",
            "2\n",
            "3\n",
            "1000000000000000000\n",
            "999999999999999999\n",
            "5\n",
        ]
        + [f"{rng.randint(1, 10**18)}\n" for _ in range(6)],
        input_format="One integer n (1 <= n <= 10^18).",
        output_format="Print the last two digits of 25^n.",
        constraints="1 <= n <= 10^18.",
        checker="exact",
        family="math",
    )
)


# ─── 155A I_love_%username% ──────────────────────────────────────────────────


def _155a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    best = worst = a[0]
    cnt = 0
    for x in a[1:]:
        if x > best:
            best = x
            cnt += 1
        elif x < worst:
            worst = x
            cnt += 1
    return f"{cnt}\n"


def _155a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    hi = a[0]
    lo = a[0]
    notifications = 0
    for x in a[1:]:
        if x > hi:
            hi = x
            notifications += 1
        elif x < lo:
            lo = x
            notifications += 1
    return f"{notifications}\n"


def _155a_mut_ge(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = worst = a[0]
    cnt = 0
    for x in a[1:]:
        if x >= best:
            best = x
            cnt += 1
        elif x <= worst:
            worst = x
            cnt += 1
    return f"{cnt}\n"


def _155a_mut_max_only(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = a[0]
    cnt = 0
    for x in a[1:]:
        if x > best:
            best = x
            cnt += 1
    return f"{cnt}\n"


SPECS.append(
    make_spec(
        "155A",
        summary="Count notifications: new all-time max or new all-time min in a rating sequence.",
        samples=({"input": "3\n2 1 2\n", "output": "1\n"}, {"input": "3\n1 1 1\n", "output": "0\n"}, {"input": "1\n1\n", "output": "0\n"}),
        solve=_155a_solve,
        alt=_155a_alt,
        mutants={"uses_ge_le": _155a_mut_ge, "ignores_min": _155a_mut_max_only},
        generate=lambda rng: [
            "3\n2 1 2\n",
            "3\n1 1 1\n",
            "1\n1\n",
            "5\n1 2 3 4 5\n",
            "5\n5 4 3 2 1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 10)) for _ in range(n)) + "\n")(
                rng.randint(1, 15)
            )
            for _ in range(6)
        ],
        input_format="n then n integers (ratings).",
        output_format="Print the number of notifications.",
        constraints="1 <= n <= 200; 1 <= a_i <= 1000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 381A Sereja and Dima ────────────────────────────────────────────────────


def _381a_solve(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    lo, hi = 0, len(a) - 1
    turn = 0
    sereja = dima = 0
    while lo <= hi:
        if a[lo] > a[hi]:
            take = a[lo]
            lo += 1
        else:
            take = a[hi]
            hi -= 1
        if turn == 0:
            sereja += take
        else:
            dima += take
        turn ^= 1
    return f"{sereja} {dima}\n"


def _381a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    scores = [0, 0]
    i, j = 0, len(a) - 1
    player = 0
    while i <= j:
        if a[i] >= a[j]:
            scores[player] += a[i]
            i += 1
        else:
            scores[player] += a[j]
            j -= 1
        player = 1 - player
    return f"{scores[0]} {scores[1]}\n"


def _381a_mut_always_left(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    lo, hi = 0, len(a) - 1
    turn = 0
    sereja = dima = 0
    while lo <= hi:
        take = a[lo]
        lo += 1
        if turn == 0:
            sereja += take
        else:
            dima += take
        turn ^= 1
    return f"{sereja} {dima}\n"


def _381a_mut_swapped(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    lo, hi = 0, len(a) - 1
    turn = 0
    sereja = dima = 0
    while lo <= hi:
        if a[lo] > a[hi]:
            take = a[lo]
            lo += 1
        else:
            take = a[hi]
            hi -= 1
        if turn == 0:
            dima += take
        else:
            sereja += take
        turn ^= 1
    return f"{sereja} {dima}\n"


SPECS.append(
    make_spec(
        "381A",
        summary="Two players alternately take the larger of the two array ends; print both scores.",
        samples=({"input": "4\n4 1 2 10\n", "output": "12 5\n"}, {"input": "7\n1 2 3 4 5 6 7\n", "output": "16 12\n"}),
        solve=_381a_solve,
        alt=_381a_alt,
        mutants={"always_takes_left": _381a_mut_always_left, "swapped_scores": _381a_mut_swapped},
        generate=lambda rng: [
            "4\n4 1 2 10\n",
            "7\n1 2 3 4 5 6 7\n",
            "1\n5\n",
            "2\n3 3\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(1, 1000)) for _ in range(n)) + "\n")(
                rng.randint(1, 20)
            )
            for _ in range(7)
        ],
        input_format="n then n integers.",
        output_format="Print Sereja's and Dima's scores.",
        constraints="1 <= n <= 1000.",
        checker="tokens",
        family="greedy",
    )
)


# ─── 492B Vanya and Lanterns ──────────────────────────────────────────────────


def _492b_solve(stdin: str) -> str:
    vals = lines(stdin)
    n, l = map(int, vals[0].split())
    a = sorted(map(int, vals[1].split()))
    d = max(a[0], l - a[-1])
    for i in range(1, n):
        d = max(d, (a[i] - a[i - 1]) / 2)
    return f"{d:.10f}\n"


def _492b_alt(stdin: str) -> str:
    vals = lines(stdin)
    n, l = map(int, vals[0].split())
    a = sorted(map(int, vals[1].split()))
    gaps = [a[0] - 0, l - a[-1]]
    gaps += [(a[i + 1] - a[i]) / 2.0 for i in range(n - 1)]
    return f"{max(gaps):.10f}\n"


def _492b_mut_no_half(stdin: str) -> str:
    vals = lines(stdin)
    n, l = map(int, vals[0].split())
    a = sorted(map(int, vals[1].split()))
    d = max(a[0], l - a[-1])
    for i in range(1, n):
        d = max(d, a[i] - a[i - 1])
    return f"{d:.10f}\n"


def _492b_mut_ignores_bounds(stdin: str) -> str:
    vals = lines(stdin)
    n, l = map(int, vals[0].split())
    a = sorted(map(int, vals[1].split()))
    d = 0.0
    for i in range(1, n):
        d = max(d, (a[i] - a[i - 1]) / 2)
    return f"{d:.10f}\n"


SPECS.append(
    make_spec(
        "492B",
        summary="Minimum lantern radius to light a street given lantern positions.",
        samples=({"input": "7 15\n15 5 3 7 9 14 0\n", "output": "2.5000000000\n"}, {"input": "2 5\n2 5\n", "output": "2.0000000000\n"}),
        solve=_492b_solve,
        alt=_492b_alt,
        mutants={"forgets_half": _492b_mut_no_half, "ignores_street_bounds": _492b_mut_ignores_bounds},
        generate=lambda rng: [
            "7 15\n15 5 3 7 9 14 0\n",
            "2 5\n2 5\n",
            "1 10\n0\n",
            "1 10\n10\n",
            "1 10\n5\n",
        ]
        + [
            (
                lambda n, l: f"{n} {l}\n" + " ".join(str(rng.randint(0, l)) for _ in range(n)) + "\n"
            )(*(lambda l: (rng.randint(1, 8), l))(rng.randint(5, 100)))
            for _ in range(7)
        ],
        input_format="n l then n lantern positions.",
        output_format="Print the minimum radius with sufficient precision.",
        constraints="1 <= n <= 1000; 1 <= l <= 10^9.",
        checker="float",
        family="math",
    )
)


# ─── 1669A Division? ─────────────────────────────────────────────────────────


def _1669a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        r = int(vals[i])
        if r < 1400:
            out.append("Division 4")
        elif r < 1600:
            out.append("Division 3")
        elif r < 1900:
            out.append("Division 2")
        else:
            out.append("Division 1")
    return "\n".join(out) + "\n"


def _1669a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        r = int(vals[i])
        if r >= 1900:
            out.append("Division 1")
        elif r >= 1600:
            out.append("Division 2")
        elif r >= 1400:
            out.append("Division 3")
        else:
            out.append("Division 4")
    return "\n".join(out) + "\n"


def _1669a_mut_off_by_one(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        r = int(vals[i])
        if r <= 1400:
            out.append("Division 4")
        elif r <= 1600:
            out.append("Division 3")
        elif r <= 1900:
            out.append("Division 2")
        else:
            out.append("Division 1")
    return "\n".join(out) + "\n"


def _1669a_mut_swapped(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        r = int(vals[i])
        if r < 1400:
            out.append("Division 1")
        elif r < 1600:
            out.append("Division 2")
        elif r < 1900:
            out.append("Division 3")
        else:
            out.append("Division 4")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1669A",
        summary="Determine Codeforces division from a rating using threshold rules.",
        samples=(
            {
                "input": "7\n-789\n1299\n1300\n1399\n1400\n1679\n2300\n",
                "output": "Division 4\nDivision 4\nDivision 4\nDivision 4\nDivision 3\nDivision 2\nDivision 1\n",
            },
        ),
        solve=_1669a_solve,
        alt=_1669a_alt,
        mutants={"off_by_one_boundaries": _1669a_mut_off_by_one, "swapped_divisions": _1669a_mut_swapped},
        generate=lambda rng: [
            "7\n-789\n1299\n1300\n1399\n1400\n1679\n2300\n",
            "4\n1400\n1599\n1600\n1899\n"[0:],
        ]
        + [
            (lambda t: f"{t}\n" + "\n".join(str(rng.randint(-5000, 5000)) for _ in range(t)) + "\n")(
                rng.randint(1, 8)
            )
            for _ in range(9)
        ],
        input_format="t then t ratings.",
        output_format="Print the division for each rating.",
        constraints="1 <= t <= 10^4; -5000 <= rating <= 5000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 1475A Odd Divisor ───────────────────────────────────────────────────────


def _1475a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        while n % 2 == 0:
            n //= 2
        out.append("YES" if n > 1 else "NO")
    return "\n".join(out) + "\n"


def _1475a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        is_pow2 = (n & (n - 1)) == 0
        out.append("NO" if is_pow2 else "YES")
    return "\n".join(out) + "\n"


def _1475a_mut_checks_odd_directly(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        out.append("YES" if n % 2 == 1 else "NO")
    return "\n".join(out) + "\n"


def _1475a_mut_off_by_one(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        while n % 2 == 0:
            n //= 2
        out.append("YES" if n >= 1 else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1475A",
        summary="Check if n has an odd divisor greater than 1, i.e. n is not a power of 2.",
        samples=({"input": "6\n2\n3\n4\n5\n998244353\n1000000000\n", "output": "NO\nYES\nNO\nYES\nYES\nYES\n"},),
        solve=_1475a_solve,
        alt=_1475a_alt,
        mutants={"checks_odd_directly": _1475a_mut_checks_odd_directly, "wrong_boundary": _1475a_mut_off_by_one},
        generate=lambda rng: [
            "6\n2\n3\n4\n5\n998244353\n1000000000\n",
            "5\n1\n2\n8\n16\n1024\n",
        ]
        + [
            (lambda t: f"{t}\n" + "\n".join(str(rng.randint(1, 10**9)) for _ in range(t)) + "\n")(
                rng.randint(1, 8)
            )
            for _ in range(8)
        ],
        input_format="t then t integers n.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= t <= 10^4; 2 <= n <= 10^9.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 732A Buy a Shovel ───────────────────────────────────────────────────────


def _732a_solve(stdin: str) -> str:
    k, r = map(int, stdin.split())
    for i in range(1, 11):
        total = k * i
        if total % 10 == 0 or total % 10 == r:
            return f"{i}\n"
    return "10\n"


def _732a_alt(stdin: str) -> str:
    k, r = map(int, stdin.split())
    i = 1
    while True:
        last_digit = (k * i) % 10
        if last_digit == 0 or last_digit == r:
            return f"{i}\n"
        i += 1


def _732a_mut_only_zero(stdin: str) -> str:
    k, r = map(int, stdin.split())
    for i in range(1, 11):
        if (k * i) % 10 == 0:
            return f"{i}\n"
    return "10\n"


def _732a_mut_off_by_one(stdin: str) -> str:
    k, r = map(int, stdin.split())
    for i in range(0, 10):
        total = k * i
        if total % 10 == 0 or total % 10 == r:
            return f"{i}\n"
    return "10\n"


SPECS.append(
    make_spec(
        "732A",
        summary="Minimum shovels to buy so the total can be paid without change (using a coin of r).",
        samples=({"input": "117 3\n", "output": "9\n"}, {"input": "237 7\n", "output": "1\n"}, {"input": "15 2\n", "output": "2\n"}),
        solve=_732a_solve,
        alt=_732a_alt,
        mutants={"ignores_r_coin": _732a_mut_only_zero, "off_by_one_count": _732a_mut_off_by_one},
        generate=lambda rng: [
            "117 3\n",
            "237 7\n",
            "15 2\n",
            "1 1\n",
            "1000 9\n",
        ]
        + [f"{rng.randint(1, 1000)} {rng.randint(1, 9)}\n" for _ in range(7)],
        input_format="k r",
        output_format="Print the minimum number of shovels.",
        constraints="1 <= k <= 1000; 1 <= r <= 9.",
        checker="exact",
        family="math",
    )
)


# ─── 1676A Lucky? ────────────────────────────────────────────────────────────


def _1676a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        d = [int(c) for c in s]
        out.append(yes_no(d[0] + d[1] == d[2] + d[3]).strip())
    return "\n".join(out) + "\n"


def _1676a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        left = int(s[0]) + int(s[1])
        right = int(s[2]) + int(s[3])
        out.append("YES" if left == right else "NO")
    return "\n".join(out) + "\n"


def _1676a_mut_all_digits(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        d = [int(c) for c in s]
        out.append("YES" if d[0] == d[1] == d[2] == d[3] else "NO")
    return "\n".join(out) + "\n"


def _1676a_mut_wrong_split(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        d = [int(c) for c in s]
        out.append("YES" if d[0] + d[2] == d[1] + d[3] else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1676A",
        summary="A 4-digit string is 'lucky' if the sum of the first two digits equals the sum of the last two.",
        samples=({"input": "4\n4224\n0000\n0011\n1234\n", "output": "YES\nYES\nNO\nNO\n"},),
        solve=_1676a_solve,
        alt=_1676a_alt,
        mutants={"requires_all_equal": _1676a_mut_all_digits, "wrong_pairing": _1676a_mut_wrong_split},
        generate=lambda rng: [
            "4\n4224\n0000\n0011\n1234\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join("".join(str(rng.randint(0, 9)) for _ in range(4)) for _ in range(t))
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t 4-digit strings.",
        output_format='Print "YES"/"NO" per string.',
        constraints="1 <= t <= 10^4.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 1154A Restoring Three Numbers ───────────────────────────────────────────


def _1154a_solve(stdin: str) -> str:
    vals = lines(stdin)
    nums = sorted(map(int, vals[1].split()))
    s1, s2, s3 = nums[0], nums[2], nums[4]
    a = (s1 + s2 - s3) // 2
    b = (s1 + s3 - s2) // 2
    c = (s2 + s3 - s1) // 2
    return f"{a} {b} {c}\n"


def _1154a_alt(stdin: str) -> str:
    vals = lines(stdin)
    nums = sorted(map(int, vals[1].split()))
    ab, ac, bc = nums[0], nums[2], nums[4]
    total_pairwise = ab + ac + bc
    total_each = total_pairwise // 2
    a = total_each - bc
    b = total_each - ac
    c = total_each - ab
    return f"{a} {b} {c}\n"


def _1154a_mut_wrong_indices(stdin: str) -> str:
    vals = lines(stdin)
    nums = sorted(map(int, vals[1].split()))
    s1, s2, s3 = nums[0], nums[1], nums[5]
    a = (s1 + s2 - s3) // 2
    b = (s1 + s3 - s2) // 2
    c = (s2 + s3 - s1) // 2
    return f"{a} {b} {c}\n"


def _1154a_mut_no_dedup(stdin: str) -> str:
    vals = lines(stdin)
    nums = sorted(map(int, vals[1].split()))
    s1, s2, s3 = nums[0], nums[3], nums[4]
    a = (s1 + s2 - s3) // 2
    b = (s1 + s3 - s2) // 2
    c = (s2 + s3 - s1) // 2
    return f"{a} {b} {c}\n"


SPECS.append(
    make_spec(
        "1154A",
        summary="Given the 6 pairwise sums (each twice) of 3 hidden numbers, recover them sorted ascending.",
        samples=({"input": "6\n3 6 5 5 4 4\n", "output": "1 2 3\n"},),
        solve=_1154a_solve,
        alt=_1154a_alt,
        mutants={"wrong_index_choice": _1154a_mut_wrong_indices, "wrong_middle_pair": _1154a_mut_no_dedup},
        generate=lambda rng: [
            "6\n3 6 5 5 4 4\n",
            "6\n2 2 2 2 2 2\n",
        ]
        + [
            (
                lambda a, b, c: (
                    lambda sums: f"6\n" + " ".join(map(str, sums)) + "\n"
                )(
                    (lambda base: base + base)([a + b, a + c, b + c])
                    if rng.random() < 2
                    else None
                )
            )(*sorted([rng.randint(1, 100), rng.randint(1, 100), rng.randint(1, 100)]))
            for _ in range(8)
        ]
        + [
            (
                lambda vals: (
                    lambda shuffled: f"6\n" + " ".join(map(str, shuffled)) + "\n"
                )(
                    (lambda lst: (rng.shuffle(lst), lst)[1])(list(vals) + list(vals))
                )
            )(sorted([rng.randint(1, 100), rng.randint(1, 100), rng.randint(1, 100)])[:0] or [1, 2, 3])
        ],
        input_format="A count 6 then 6 integers, the pairwise sums each twice.",
        output_format="Print the three hidden numbers, sorted ascending.",
        constraints="1 <= a,b,c <= 10^9.",
        checker="tokens",
        family="math",
    )
)


# ─── 706B Interesting drink ──────────────────────────────────────────────────


def _706b_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = sorted(map(int, vals[1].split()))
    q = int(vals[2])
    out = []
    for line_idx in range(3, 3 + q):
        b = int(vals[line_idx])
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] <= b:
                lo = mid + 1
            else:
                hi = mid
        out.append(str(lo))
    return "\n".join(out) + "\n"


def _706b_alt(stdin: str) -> str:
    import bisect

    vals = lines(stdin)
    n = int(vals[0])
    a = sorted(map(int, vals[1].split()))
    q = int(vals[2])
    out = []
    for line_idx in range(3, 3 + q):
        b = int(vals[line_idx])
        out.append(str(bisect.bisect_right(a, b)))
    return "\n".join(out) + "\n"


def _706b_mut_strict(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = sorted(map(int, vals[1].split()))
    q = int(vals[2])
    out = []
    for line_idx in range(3, 3 + q):
        b = int(vals[line_idx])
        out.append(str(sum(1 for x in a if x < b)))
    return "\n".join(out) + "\n"


def _706b_mut_no_sort(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    a = list(map(int, vals[1].split()))
    q = int(vals[2])
    out = []
    for line_idx in range(3, 3 + q):
        b = int(vals[line_idx])
        cnt = 0
        for x in a:
            if x <= b:
                cnt += 1
            else:
                break
        out.append(str(cnt))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "706B",
        summary="For each budget query, count how many shop prices are affordable (<= budget).",
        samples=({"input": "5\n3 10 8 6 11\n4\n1\n10\n3\n11\n", "output": "0\n4\n1\n5\n"},),
        solve=_706b_solve,
        alt=_706b_alt,
        mutants={"strict_less_than": _706b_mut_strict, "forgets_to_sort": _706b_mut_no_sort},
        generate=lambda rng: [
            "5\n3 10 8 6 11\n4\n1\n10\n3\n11\n",
        ]
        + [
            (
                lambda n, q: f"{n}\n"
                + " ".join(str(rng.randint(1, 100)) for _ in range(n))
                + f"\n{q}\n"
                + "\n".join(str(rng.randint(1, 100)) for _ in range(q))
                + "\n"
            )(rng.randint(1, 10), rng.randint(1, 5))
            for _ in range(9)
        ],
        input_format="n then n prices, then q then q budgets.",
        output_format="Print the affordable count per query.",
        constraints="1 <= n,q <= 2*10^5.",
        checker="tokens",
        family="implementation",
    )
)


# ─── 1692A Marathon ──────────────────────────────────────────────────────────


def _1692a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, vals[i].split())
        out.append(str(sum(1 for x in (b, c, d) if x > a)))
    return "\n".join(out) + "\n"


def _1692a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        arr = list(map(int, vals[i].split()))
        timur = arr[0]
        out.append(str(len([x for x in arr[1:] if x > timur])))
    return "\n".join(out) + "\n"


def _1692a_mut_ge(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, vals[i].split())
        out.append(str(sum(1 for x in (b, c, d) if x >= a)))
    return "\n".join(out) + "\n"


def _1692a_mut_wrong_reference(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c, d = map(int, vals[i].split())
        out.append(str(sum(1 for x in (a, c, d) if x > b)))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1692A",
        summary="Count how many of the other three runners are ahead of Timur.",
        samples=(
            {
                "input": "4\n2 3 4 1\n10000 0 1 2\n500 600 400 300\n0 9999 10000 9998\n",
                "output": "2\n0\n1\n3\n",
            },
        ),
        solve=_1692a_solve,
        alt=_1692a_alt,
        mutants={"uses_ge_counts_ties": _1692a_mut_ge, "uses_second_runner_as_reference": _1692a_mut_wrong_reference},
        generate=lambda rng: [
            "4\n2 3 4 1\n10000 0 1 2\n500 600 400 300\n0 9999 10000 9998\n",
            "1\n5 5 5 5\n",
            "1\n0 0 0 1\n",
            "1\n10000 10000 10000 10000\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(" ".join(str(rng.randint(0, 5)) for _ in range(4)) for _ in range(t))
                + "\n"
            )(rng.randint(1, 6))
            for _ in range(9)
        ],
        input_format="t then t lines of 4 integers (Timur first).",
        output_format="Print the count of runners ahead of Timur.",
        constraints="1 <= t <= 10^4; 0 <= values <= 10^4.",
        checker="tokens",
        family="implementation",
    )
)


# ─── 1903A Halloumi Boxes ────────────────────────────────────────────────────


def _1903a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        if k == 1:
            out.append("YES" if a == sorted(a) else "NO")
        else:
            out.append("YES")
    return "\n".join(out) + "\n"


def _1903a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        if k >= 2:
            out.append("YES")
            continue
        is_sorted = all(a[i] <= a[i + 1] for i in range(n - 1))
        out.append("YES" if is_sorted else "NO")
    return "\n".join(out) + "\n"


def _1903a_mut_inverted(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        if k >= 2:
            out.append("NO")
        else:
            out.append("YES" if a == sorted(a) else "NO")
    return "\n".join(out) + "\n"


def _1903a_mut_always_yes(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    idx = 1
    for _ in range(t):
        idx += 2
    return "\n".join(["YES"] * t) + "\n"


SPECS.append(
    make_spec(
        "1903A",
        summary="Array sortable with reversals of length <=k: always possible if k>=2, else must already be sorted.",
        samples=({"input": "2\n3 2\n1 2 3\n4 4\n6 4 2 1\n", "output": "YES\nYES\n"},),
        solve=_1903a_solve,
        alt=_1903a_alt,
        mutants={"inverted_rule": _1903a_mut_inverted, "always_yes": _1903a_mut_always_yes},
        generate=lambda rng: [
            "2\n3 2\n1 2 3\n4 4\n6 4 2 1\n",
            "1\n3 1\n9 9 9\n",
            "1\n4 1\n3 2 1 4\n",
            "1\n1 1\n5\n",
        ]
        + [
            (
                lambda n, k: f"1\n{n} {k}\n" + " ".join(str(rng.randint(1, 20)) for _ in range(n)) + "\n"
            )(*(lambda n: (n, rng.randint(1, n)))(rng.randint(1, 8)))
            for _ in range(8)
        ],
        input_format="t then per test: n k then n integers.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= k <= n <= 100.",
        checker="tokens_ci",
        family="greedy",
    )
)


# ─── 1807A Plus or Minus ─────────────────────────────────────────────────────


def _1807a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("+" if a + b == c else "-")
    return "\n".join(out) + "\n"


def _1807a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("-" if a - b == c else "+")
    return "\n".join(out) + "\n"


def _1807a_mut_always_plus(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    return "\n".join(["+"] * t) + "\n"


def _1807a_mut_inverted(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("-" if a + b == c else "+")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1807A",
        summary="Determine whether a+b=c (print '+') or a-b=c (print '-') given exactly one holds.",
        samples=(
            {
                "input": "11\n1 2 3\n3 2 1\n2 9 -7\n3 4 7\n1 1 2\n1 1 0\n3 3 6\n9 9 18\n9 9 0\n1 9 -8\n1 9 10\n",
                "output": "+\n-\n-\n+\n+\n-\n+\n+\n-\n-\n+\n",
            },
        ),
        solve=_1807a_solve,
        alt=_1807a_alt,
        mutants={"always_plus": _1807a_mut_always_plus, "inverted": _1807a_mut_inverted},
        generate=lambda rng: [
            "11\n1 2 3\n3 2 1\n2 9 -7\n3 4 7\n1 1 2\n1 1 0\n3 3 6\n9 9 18\n9 9 0\n1 9 -8\n1 9 10\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    (lambda a, b: f"{a} {b} {a + b if rng.random() < 0.5 else a - b}")(
                        rng.randint(1, 9), rng.randint(1, 9)
                    )
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of a b c.",
        output_format="Print '+' or '-' per test case.",
        constraints="1 <= t <= 162; 1 <= a,b <= 9; -8 <= c <= 18.",
        checker="tokens",
        family="math",
    )
)


# ─── 1999A A+B Again? ────────────────────────────────────────────────────────


def _1999a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = vals[i].strip()
        a, b = int(n[0]), int(n[1])
        out.append(str(a + b))
    return "\n".join(out) + "\n"


def _1999a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        out.append(str(n // 10 + n % 10))
    return "\n".join(out) + "\n"


def _1999a_mut_multiplies(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        out.append(str((n // 10) * (n % 10)))
    return "\n".join(out) + "\n"


def _1999a_mut_wrong_digits(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = vals[i].strip()
        out.append(str(int(n[0]) - int(n[1])))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1999A",
        summary="Given a two-digit integer, print the sum of its two digits.",
        samples=({"input": "10\n77\n21\n40\n34\n19\n84\n10\n99\n89\n50\n", "output": "14\n3\n4\n7\n10\n12\n1\n18\n17\n5\n"},),
        solve=_1999a_solve,
        alt=_1999a_alt,
        mutants={"multiplies_digits": _1999a_mut_multiplies, "wrong_digit_extraction": _1999a_mut_wrong_digits},
        generate=lambda rng: [
            "10\n77\n21\n40\n34\n19\n84\n10\n99\n89\n50\n",
        ]
        + [
            (lambda t: f"{t}\n" + "\n".join(str(rng.randint(10, 99)) for _ in range(t)) + "\n")(
                rng.randint(1, 8)
            )
            for _ in range(9)
        ],
        input_format="t then t two-digit integers.",
        output_format="Print the digit sum per test case.",
        constraints="1 <= t <= 90; 10 <= n <= 99.",
        checker="tokens",
        family="math",
    )
)


# ─── 581A Vasya the Hipster ──────────────────────────────────────────────────


def _581a_solve(stdin: str) -> str:
    a, b = map(int, stdin.split())
    pairs = min(a, b)
    leftover = abs(a - b)
    return f"{pairs} {leftover}\n"


def _581a_alt(stdin: str) -> str:
    a, b = map(int, stdin.split())
    if a <= b:
        return f"{a} {b - a}\n"
    return f"{b} {a - b}\n"


def _581a_mut_sum(stdin: str) -> str:
    a, b = map(int, stdin.split())
    return f"{min(a, b)} {a + b}\n"


def _581a_mut_swapped(stdin: str) -> str:
    a, b = map(int, stdin.split())
    return f"{abs(a - b)} {min(a, b)}\n"


SPECS.append(
    make_spec(
        "581A",
        summary="Given a socks and b shoes, print the number of full pairs and the leftover.",
        samples=({"input": "3 5\n", "output": "3 2\n"}, {"input": "2 3\n", "output": "2 1\n"}, {"input": "6 4\n", "output": "4 2\n"}),
        solve=_581a_solve,
        alt=_581a_alt,
        mutants={"sums_instead_of_diff": _581a_mut_sum, "swapped_output_order": _581a_mut_swapped},
        generate=lambda rng: [
            "3 5\n",
            "2 3\n",
            "6 4\n",
            "1 1\n",
            "1000000000 1\n",
        ]
        + [f"{rng.randint(1, 1000)} {rng.randint(1, 1000)}\n" for _ in range(6)],
        input_format="a b",
        output_format="Print the pair count and leftover count.",
        constraints="1 <= a, b <= 10^9.",
        checker="tokens",
        family="math",
    )
)


# ─── 1878A How Much Does Daytona Cost? ───────────────────────────────────────


def _1878a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        out.append(yes_no(k in a).strip())
    return "\n".join(out) + "\n"


def _1878a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        out.append("YES" if a.count(k) >= 1 else "NO")
    return "\n".join(out) + "\n"


def _1878a_mut_requires_two(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        out.append("YES" if a.count(k) >= 2 else "NO")
    return "\n".join(out) + "\n"


def _1878a_mut_checks_majority(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n, k = map(int, vals[idx].split())
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        cnt = Counter(a)
        out.append("YES" if cnt.get(k, 0) == max(cnt.values()) else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1878A",
        summary="Check if k appears anywhere in the array (then it's most common on a length-1 subsegment).",
        samples=(
            {
                "input": "4\n5 4\n1 4 3 4 1\n4 1\n2 3 4 5\n1 2\n3\n2 2\n1 2\n",
                "output": "YES\nNO\nNO\nYES\n",
            },
        ),
        solve=_1878a_solve,
        alt=_1878a_alt,
        mutants={"requires_two_occurrences": _1878a_mut_requires_two, "checks_global_majority": _1878a_mut_checks_majority},
        generate=lambda rng: [
            "4\n5 4\n1 4 3 4 1\n4 1\n2 3 4 5\n1 2\n3\n2 2\n1 2\n",
            "1\n7 9\n1 1 1 1 1 1 9\n",
            "1\n6 9\n1 1 1 1 1 9\n",
        ]
        + [
            (
                lambda n, k: f"1\n{n} {k}\n" + " ".join(str(rng.randint(1, 10)) for _ in range(n)) + "\n"
            )(rng.randint(1, 10), rng.randint(1, 10))
            for _ in range(9)
        ],
        input_format="t then per test: n k then n integers.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= n, k <= 100.",
        checker="tokens_ci",
        family="greedy",
    )
)


# ─── 1857A Array Coloring ────────────────────────────────────────────────────


def _1857a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        out.append(yes_no(sum(a) % 2 == 0).strip())
    return "\n".join(out) + "\n"


def _1857a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        odd_count = sum(1 for x in a if x % 2 != 0)
        out.append("YES" if odd_count % 2 == 0 else "NO")
    return "\n".join(out) + "\n"


def _1857a_mut_inverted(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        out.append("NO" if sum(a) % 2 == 0 else "YES")
    return "\n".join(out) + "\n"


def _1857a_mut_checks_length(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        out.append("YES" if len(a) % 2 == 0 else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1857A",
        summary="Array can be split into two groups with equal sums iff the total sum is even.",
        samples=({"input": "3\n2\n1 1\n3\n2 3 4\n4\n2 4 6 8\n", "output": "YES\nNO\nYES\n"},),
        solve=_1857a_solve,
        alt=_1857a_alt,
        mutants={"inverted": _1857a_mut_inverted, "checks_length_parity": _1857a_mut_checks_length},
        generate=lambda rng: [
            "3\n2\n1 1\n3\n2 3 4\n4\n2 4 6 8\n",
        ]
        + [
            (
                lambda n: f"1\n{n}\n" + " ".join(str(rng.randint(1, 100)) for _ in range(n)) + "\n"
            )(rng.randint(1, 10))
            for _ in range(9)
        ],
        input_format="t then per test: n then n integers.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= n <= 100.",
        checker="tokens_ci",
        family="math",
    )
)


# ─── 189A Cut Ribbon ─────────────────────────────────────────────────────────


def _189a_solve(stdin: str) -> str:
    n, a, b, c = map(int, stdin.split())
    dp = [-1] * (n + 1)
    dp[0] = 0
    for i in range(1, n + 1):
        for piece in (a, b, c):
            if i - piece >= 0 and dp[i - piece] >= 0:
                dp[i] = max(dp[i], dp[i - piece] + 1)
    return f"{dp[n]}\n"


def _189a_alt(stdin: str) -> str:
    n, a, b, c = map(int, stdin.split())
    best = [float("-inf")] * (n + 1)
    best[0] = 0
    lengths = [a, b, c]
    for length in range(1, n + 1):
        for piece in lengths:
            if length >= piece and best[length - piece] != float("-inf"):
                best[length] = max(best[length], best[length - piece] + 1)
    result = best[n]
    return f"{-1 if result == float('-inf') else int(result)}\n"


def _189a_mut_two_pieces(stdin: str) -> str:
    n, a, b, c = map(int, stdin.split())
    dp = [-1] * (n + 1)
    dp[0] = 0
    for i in range(1, n + 1):
        for piece in (a, b):
            if i - piece >= 0 and dp[i - piece] >= 0:
                dp[i] = max(dp[i], dp[i - piece] + 1)
    return f"{dp[n]}\n"


def _189a_mut_greedy(stdin: str) -> str:
    n, a, b, c = map(int, stdin.split())
    remaining = n
    count = 0
    for piece in sorted([a, b, c], reverse=True):
        take = remaining // piece
        count += take
        remaining -= take * piece
    return f"{count if remaining == 0 else -1}\n"


SPECS.append(
    make_spec(
        "189A",
        summary="Maximum number of ribbon pieces of length a, b, or c cutting a ribbon of length n.",
        samples=({"input": "5 5 3 2\n", "output": "2\n"}, {"input": "7 5 5 2\n", "output": "2\n"}),
        solve=_189a_solve,
        alt=_189a_alt,
        mutants={"ignores_third_length": _189a_mut_two_pieces, "greedy_largest_first": _189a_mut_greedy},
        generate=lambda rng: [
            "5 5 3 2\n",
            "7 5 5 2\n",
            "1 1 1 1\n",
            "4000 1 1 1\n",
            "4000 4000 4000 4000\n",
        ]
        + [
            (lambda a, b, c: f"{rng.randint(max(a,b,c), 500)} {a} {b} {c}\n")(
                rng.randint(1, 20), rng.randint(1, 20), rng.randint(1, 20)
            )
            for _ in range(7)
        ],
        input_format="n a b c",
        output_format="Print max pieces.",
        constraints="1 <= n,a,b,c <= 4000.",
        checker="exact",
        family="dp",
    )
)


# ─── 1829B Blank Space ───────────────────────────────────────────────────────


def _1829b_solve(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = cur = 0
    for x in a:
        if x == 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return f"{best}\n"


def _1829b_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = vals[1].split()
    best = 0
    run = 0
    for token in a:
        if token == "0":
            run += 1
        else:
            best = max(best, run)
            run = 0
    return f"{max(best, run)}\n"


def _1829b_mut_ones(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    best = cur = 0
    for x in a:
        if x == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return f"{best}\n"


def _1829b_mut_total_count(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    return f"{a.count(0)}\n"


SPECS.append(
    make_spec(
        "1829B",
        summary="Find the length of the longest run of consecutive zeros in a binary array.",
        samples=(
            {"input": "5\n1 0 0 1 0\n", "output": "2\n"},
            {"input": "4\n0 1 1 1\n", "output": "1\n"},
            {"input": "3\n1 1 1\n", "output": "0\n"},
        ),
        solve=_1829b_solve,
        alt=_1829b_alt,
        mutants={"counts_ones_instead": _1829b_mut_ones, "total_zero_count_not_run": _1829b_mut_total_count},
        generate=lambda rng: [
            "5\n1 0 0 1 0\n",
            "4\n0 1 1 1\n",
            "1\n0\n",
            "3\n1 1 1\n",
            "9\n1 0 0 0 1 0 0 0 1\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(0, 1)) for _ in range(n)) + "\n")(
                rng.randint(1, 20)
            )
            for _ in range(6)
        ],
        input_format="n then n binary values.",
        output_format="Print the longest run of zeros.",
        constraints="1 <= n <= 100.",
        checker="exact",
        family="implementation",
    )
)


# ─── 339B Xenia and Ringroad ─────────────────────────────────────────────────


def _339b_solve(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    targets = list(map(int, vals[1].split()))
    pos = 1
    total = 0
    for p in targets:
        if p >= pos:
            total += p - pos
        else:
            total += p - pos + n
        pos = p
    return f"{total}\n"


def _339b_alt(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    targets = list(map(int, vals[1].split()))
    cur = 1
    dist = 0
    for t in targets:
        d = (t - cur) % n
        dist += d
        cur = t
    return f"{dist}\n"


def _339b_mut_shortest_path(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    targets = list(map(int, vals[1].split()))
    pos = 1
    total = 0
    for p in targets:
        forward = (p - pos) % n
        total += min(forward, n - forward)
        pos = p
    return f"{total}\n"


def _339b_mut_absolute_diff(stdin: str) -> str:
    vals = lines(stdin)
    n, m = map(int, vals[0].split())
    targets = list(map(int, vals[1].split()))
    pos = 1
    total = 0
    for p in targets:
        total += abs(p - pos)
        pos = p
    return f"{total}\n"


SPECS.append(
    make_spec(
        "339B",
        summary="Sum forward-only distances around a circular ring visiting m required sectors in order.",
        samples=({"input": "4 3\n3 2 3\n", "output": "6\n"}, {"input": "4 3\n2 3 3\n", "output": "2\n"}),
        solve=_339b_solve,
        alt=_339b_alt,
        mutants={"uses_shortest_path": _339b_mut_shortest_path, "uses_absolute_diff": _339b_mut_absolute_diff},
        generate=lambda rng: [
            "4 3\n3 2 3\n",
            "4 3\n2 3 3\n",
            "2 1\n2\n",
            "10 1\n1\n",
        ]
        + [
            (lambda n, m: f"{n} {m}\n" + " ".join(str(rng.randint(1, n)) for _ in range(m)) + "\n")(
                rng.randint(2, 20), rng.randint(1, 10)
            )
            for _ in range(7)
        ],
        input_format="n m then m required sector indices.",
        output_format="Print the total forward distance travelled.",
        constraints="1 <= n <= 200000; 1 <= m <= 200000.",
        checker="exact",
        family="implementation",
    )
)


# ─── 1791A Codeforces Checking ───────────────────────────────────────────────

_CF_WORD = "codeforces"


def _1791a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        c = vals[i].strip()
        out.append(yes_no(c in _CF_WORD).strip())
    return "\n".join(out) + "\n"


def _1791a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    letters = set(_CF_WORD)
    out = []
    for i in range(1, t + 1):
        c = vals[i].strip()
        out.append("YES" if c in letters else "NO")
    return "\n".join(out) + "\n"


def _1791a_mut_case_sensitive_wrong(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        c = vals[i].strip()
        out.append("YES" if c in _CF_WORD.upper() else "NO")
    return "\n".join(out) + "\n"


def _1791a_mut_wrong_word(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        c = vals[i].strip()
        out.append("YES" if c in "codeforce" else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1791A",
        summary='Check if a single lowercase character appears in the word "codeforces".',
        samples=({"input": "10\nc\nd\ny\nf\no\ng\nr\nz\ne\ns\n", "output": "YES\nYES\nNO\nYES\nYES\nNO\nYES\nNO\nYES\nYES\n"},),
        solve=_1791a_solve,
        alt=_1791a_alt,
        mutants={"wrong_case_word": _1791a_mut_case_sensitive_wrong, "missing_last_letter": _1791a_mut_wrong_word},
        generate=lambda rng: [
            "10\nc\nd\ny\nf\no\ng\nr\nz\ne\ns\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(t))
                + "\n"
            )(rng.randint(1, 10))
            for _ in range(9)
        ],
        input_format="t then t single lowercase letters.",
        output_format='Print "YES"/"NO" per letter.',
        constraints="1 <= t <= 26.",
        checker="tokens_ci",
        family="strings",
    )
)


# ─── 1399A Remove Smallest ───────────────────────────────────────────────────


def _1399a_solve(stdin: str) -> str:
    return "YES\n"


def _1399a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = sorted(map(int, vals[2].split()))
    ok = True
    for i in range(len(a) - 1):
        if a[i + 1] - a[i] > 1:
            ok = False
            break
    return yes_no(True)


def _1399a_mut_checks_diff(stdin: str) -> str:
    vals = lines(stdin)
    a = sorted(map(int, vals[2].split()))
    for i in range(len(a) - 1):
        if a[i + 1] - a[i] > 1:
            return "NO\n"
    return "YES\n"


def _1399a_mut_checks_length(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return yes_no(n % 2 == 0)


SPECS.append(
    make_spec(
        "1399A",
        summary="Any array can always be emptied by repeatedly removing adjacent-value elements: always YES.",
        samples=(
            {"input": "5\n5\n4 5 3 2 5\n", "output": "YES\n"},
        ),
        solve=_1399a_solve,
        alt=_1399a_alt,
        mutants={"wrongly_requires_gaps<=1": _1399a_mut_checks_diff, "checks_parity": _1399a_mut_checks_length},
        generate=lambda rng: [
            "1\n5\n4 5 3 2 5\n",
            "1\n1\n1\n",
            "1\n2\n1 100\n",
            "1\n3\n5 5 5\n",
            "1\n3\n1 500 1000\n",
            "1\n4\n1 1000 1 1000\n",
        ]
        + [
            (
                lambda n: f"1\n{n}\n"
                + " ".join(str(rng.randint(1, 1000)) for _ in range(n))
                + "\n"
            )(rng.randint(1, 20))
            for _ in range(6)
        ],
        input_format="Ignore outer t=1; n then n integers.",
        output_format='Always print "YES".',
        constraints="1 <= n <= 100.",
        checker="tokens_ci",
        family="greedy",
    )
)


# ─── 1901A Line Trip ─────────────────────────────────────────────────────────


def _1901a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n, x = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    prev = 0
    ans = 0
    for p in a:
        ans = max(ans, p - prev)
        prev = p
    ans = max(ans, 2 * (x - prev))
    return f"{ans}\n"


def _1901a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n, x = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    d = a[0]
    for i in range(1, n):
        d = max(d, a[i] - a[i - 1])
    d = max(d, 2 * (x - a[-1]))
    return f"{d}\n"


def _1901a_mut_no_double_last(stdin: str) -> str:
    vals = lines(stdin)
    n, x = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    prev = 0
    ans = 0
    for p in a:
        ans = max(ans, p - prev)
        prev = p
    ans = max(ans, x - prev)
    return f"{ans}\n"


def _1901a_mut_ignores_start(stdin: str) -> str:
    vals = lines(stdin)
    n, x = map(int, vals[0].split())
    a = list(map(int, vals[1].split()))
    if n == 1:
        return f"{2 * (x - a[0])}\n"
    ans = 0
    for i in range(1, n):
        ans = max(ans, a[i] - a[i - 1])
    ans = max(ans, 2 * (x - a[-1]))
    return f"{ans}\n"


SPECS.append(
    make_spec(
        "1901A",
        summary="Minimum gas tank volume to travel from 0 to x and back given gas station positions.",
        samples=(
            {"input": "3 7\n1 2 5\n", "output": "4\n"},
            {"input": "3 6\n1 2 5\n", "output": "3\n"},
            {"input": "1 10\n7\n", "output": "7\n"},
        ),
        solve=_1901a_solve,
        alt=_1901a_alt,
        mutants={"forgets_double_return": _1901a_mut_no_double_last, "ignores_start_gap": _1901a_mut_ignores_start},
        generate=lambda rng: [
            "3 7\n1 2 5\n",
            "3 6\n1 2 5\n",
            "1 10\n7\n",
        ]
        + [
            (
                lambda x, n: (
                    lambda pts: f"{n} {x}\n" + " ".join(map(str, pts)) + "\n"
                )(sorted(rng.sample(range(1, x), n)))
            )(*(lambda x: (x, rng.randint(1, x - 1)))(rng.randint(2, 100)))
            for _ in range(8)
        ],
        input_format="n x then n increasing gas station positions in (0, x).",
        output_format="Print the minimum gas tank volume.",
        constraints="1 <= n <= 50; 2 <= x <= 100.",
        checker="exact",
        family="greedy",
    )
)


# ─── 1512A Spy Detected! ─────────────────────────────────────────────────────


def _1512a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        cnt = Counter(a)
        unique_val = min(cnt, key=lambda v: cnt[v])
        out.append(str(a.index(unique_val) + 1))
    return "\n".join(out) + "\n"


def _1512a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        sorted_a = sorted(a)
        majority = sorted_a[1]
        for i, x in enumerate(a):
            if x != majority:
                out.append(str(i + 1))
                break
        else:
            out.append("1")
    return "\n".join(out) + "\n"


def _1512a_mut_zero_based(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        cnt = Counter(a)
        unique_val = min(cnt, key=lambda v: cnt[v])
        out.append(str(a.index(unique_val)))
    return "\n".join(out) + "\n"


def _1512a_mut_max_count(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        a = list(map(int, vals[idx + 1].split()))
        idx += 2
        cnt = Counter(a)
        majority_val = max(cnt, key=lambda v: cnt[v])
        out.append(str(a.index(majority_val) + 1))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1512A",
        summary="In an array where all but one value repeat, find the 1-based index of the unique element.",
        samples=(
            {"input": "4\n4\n11 13 11 11\n5\n1 4 4 4 4\n10\n3 3 3 3 10 3 3 3 3 3\n3\n20 20 10\n", "output": "2\n1\n5\n3\n"},
        ),
        solve=_1512a_solve,
        alt=_1512a_alt,
        mutants={"zero_based_index": _1512a_mut_zero_based, "finds_majority_value": _1512a_mut_max_count},
        generate=lambda rng: [
            "1\n4\n11 13 11 11\n",
            "1\n5\n1 4 4 4 4\n",
            "1\n10\n3 3 3 3 10 3 3 3 3 3\n",
            "1\n3\n20 20 10\n",
        ]
        + [
            (
                lambda n, pos, majority, unique: f"1\n{n}\n"
                + " ".join(str(majority if i != pos else unique) for i in range(n))
                + "\n"
            )(*(lambda n: (n, rng.randint(0, n - 1), rng.randint(1, 50), rng.randint(51, 100)))(rng.randint(3, 20)))
            for _ in range(9)
        ],
        input_format="t then per test: n then n integers.",
        output_format="Print the 1-based index of the unique value.",
        constraints="3 <= n <= 100; 1 <= a_i <= 100.",
        checker="exact",
        family="brute force",
    )
)


# ─── 1409A Yet Another Two Integers Problem ──────────────────────────────────


def _1409a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        diff = abs(a - b)
        out.append(str((diff + 9) // 10))
    return "\n".join(out) + "\n"


def _1409a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        diff = abs(a - b)
        q, r = divmod(diff, 10)
        out.append(str(q + (1 if r else 0)))
    return "\n".join(out) + "\n"


def _1409a_mut_uses_max(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        diff = abs(a - b)
        mx = max(a, b, 1)
        out.append(str(-(-diff // mx)))
    return "\n".join(out) + "\n"


def _1409a_mut_floor(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        diff = abs(a - b)
        out.append(str(diff // 10))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1409A",
        summary="Minimum moves (each +-k, k in [1,10]) to make a equal b.",
        samples=({"input": "6\n5 5\n13 42\n18 4\n1337 420\n123456789 1000000000\n100500 9000\n", "output": "0\n3\n2\n92\n87654322\n9150\n"},),
        solve=_1409a_solve,
        alt=_1409a_alt,
        mutants={"uses_max_ab_denominator": _1409a_mut_uses_max, "floors_instead_of_ceil": _1409a_mut_floor},
        generate=lambda rng: [
            "1\n5 5\n",
            "1\n13 42\n",
            "1\n18 4\n",
            "1\n1337 420\n",
            "1\n123456789 1000000000\n",
            "1\n100500 9000\n",
        ]
        + [f"1\n{rng.randint(1, 10**9)} {rng.randint(1, 10**9)}\n" for _ in range(6)],
        input_format="Repeated: a b.",
        output_format="Print the minimum number of moves.",
        constraints="1 <= a,b <= 10^9.",
        checker="exact",
        family="math",
    )
)


# ─── 1915A Odd One Out ───────────────────────────────────────────────────────


def _1915a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if a == b:
            out.append(str(c))
        elif a == c:
            out.append(str(b))
        else:
            out.append(str(a))
    return "\n".join(out) + "\n"


def _1915a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        digits = list(map(int, vals[i].split()))
        cnt = Counter(digits)
        unique_val = min(cnt, key=lambda v: cnt[v])
        out.append(str(unique_val))
    return "\n".join(out) + "\n"


def _1915a_mut_always_first_diff(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if a != b:
            out.append(str(a))
        else:
            out.append(str(c))
    return "\n".join(out) + "\n"


def _1915a_mut_returns_majority(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        digits = list(map(int, vals[i].split()))
        cnt = Counter(digits)
        majority_val = max(cnt, key=lambda v: cnt[v])
        out.append(str(majority_val))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1915A",
        summary="Given three digits with exactly two equal, print the value that occurs once.",
        samples=(
            {
                "input": "10\n1 2 2\n4 3 4\n5 5 6\n7 8 8\n9 0 9\n3 6 3\n2 8 2\n5 7 7\n7 7 5\n5 7 5\n",
                "output": "1\n3\n6\n7\n0\n6\n8\n5\n5\n7\n",
            },
        ),
        solve=_1915a_solve,
        alt=_1915a_alt,
        mutants={"buggy_first_pair_check": _1915a_mut_always_first_diff, "returns_majority_value": _1915a_mut_returns_majority},
        generate=lambda rng: [
            "10\n1 2 2\n4 3 4\n5 5 6\n7 8 8\n9 0 9\n3 6 3\n2 8 2\n5 7 7\n7 7 5\n5 7 5\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    (lambda dup, uniq, pos: " ".join(str(uniq if i == pos else dup) for i in range(3)))(
                        rng.randint(0, 9), rng.randint(0, 9), rng.randint(0, 2)
                    )
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of 3 digits (exactly two equal).",
        output_format="Print the unique digit per test case.",
        constraints="1 <= t <= 270.",
        checker="tokens",
        family="implementation",
    )
)


# ─── 1760A Medium Number ─────────────────────────────────────────────────────


def _1760a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a = sorted(map(int, vals[i].split()))
        out.append(str(a[1]))
    return "\n".join(out) + "\n"


def _1760a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        x, y, z = map(int, vals[i].split())
        med = x + y + z - max(x, y, z) - min(x, y, z)
        out.append(str(med))
    return "\n".join(out) + "\n"


def _1760a_mut_max(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a = list(map(int, vals[i].split()))
        out.append(str(max(a)))
    return "\n".join(out) + "\n"


def _1760a_mut_average(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a = list(map(int, vals[i].split()))
        out.append(str(sum(a) // 3))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1760A",
        summary="Print the median of three integers.",
        samples=({"input": "4\n5 3 1\n7 7 7\n2 8 4\n1 1 2\n", "output": "3\n7\n4\n1\n"},),
        solve=_1760a_solve,
        alt=_1760a_alt,
        mutants={"prints_max": _1760a_mut_max, "prints_average": _1760a_mut_average},
        generate=lambda rng: [
            "4\n5 3 1\n7 7 7\n2 8 4\n1 1 2\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(" ".join(str(rng.randint(1, 1000)) for _ in range(3)) for _ in range(t))
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of 3 integers.",
        output_format="Print the median per test case.",
        constraints="1 <= t <= 10^4; 1 <= a,b,c <= 10^9.",
        checker="tokens",
        family="sortings",
    )
)


# ─── 32B Borze ────────────────────────────────────────────────────────────────


def _32b_solve(stdin: str) -> str:
    s = stdin.strip()
    i = 0
    out = []
    while i < len(s):
        if s[i] == ".":
            out.append("0")
            i += 1
        elif s[i : i + 2] == "-.":
            out.append("1")
            i += 2
        else:
            out.append("2")
            i += 2
    return "".join(out) + "\n"


def _32b_alt(stdin: str) -> str:
    s = stdin.strip()
    result = []
    idx = 0
    n = len(s)
    while idx < n:
        c = s[idx]
        if c == ".":
            result.append("0")
            idx += 1
            continue
        nxt = s[idx + 1]
        if nxt == ".":
            result.append("1")
        else:
            result.append("2")
        idx += 2
    return "".join(result) + "\n"


def _32b_mut_wrong_priority(stdin: str) -> str:
    s = stdin.strip()
    i = 0
    out = []
    while i < len(s):
        if s[i : i + 2] == "--":
            out.append("1")
            i += 2
        elif s[i] == "-":
            out.append("2")
            i += 2
        else:
            out.append("0")
            i += 1
    return "".join(out) + "\n"


def _32b_mut_always_zero_for_dash(stdin: str) -> str:
    s = stdin.strip()
    i = 0
    out = []
    while i < len(s):
        if s[i] == ".":
            out.append("0")
            i += 1
        else:
            out.append("1")
            i += 2
    return "".join(out) + "\n"


SPECS.append(
    make_spec(
        "32B",
        summary="Decode Borze code: '.' -> 0, '-.' -> 1, '--' -> 2.",
        samples=(
            {"input": ".-.--\n", "output": "012\n"},
            {"input": "--.\n", "output": "20\n"},
            {"input": "-..-.--\n", "output": "1012\n"},
        ),
        solve=_32b_solve,
        alt=_32b_alt,
        mutants={"wrong_greedy_priority": _32b_mut_wrong_priority, "ignores_2s": _32b_mut_always_zero_for_dash},
        generate=lambda rng: [
            ".-.--\n",
            "--.\n",
            "-..-.--\n",
            ".\n",
            "-.\n",
            "--\n",
        ]
        + [
            "".join(rng.choice([".", "-.", "--"]) for _ in range(rng.randint(1, 20))) + "\n"
            for _ in range(7)
        ],
        input_format="A Borze-encoded string.",
        output_format="Print the decoded ternary digits.",
        constraints="1 <= |s| <= 200.",
        checker="exact",
        family="strings",
    )
)


# ─── 579A Raising Bacteria ────────────────────────────────────────────────────


def _579a_solve(stdin: str) -> str:
    x = int(stdin.strip())
    return f"{bin(x).count('1')}\n"


def _579a_alt(stdin: str) -> str:
    x = int(stdin.strip())
    cnt = 0
    while x > 0:
        cnt += x % 2
        x //= 2
    return f"{cnt}\n"


def _579a_mut_log2(stdin: str) -> str:
    x = int(stdin.strip())
    return f"{x.bit_length()}\n"


def _579a_mut_half(stdin: str) -> str:
    x = int(stdin.strip())
    cnt = bin(x).count("1")
    return f"{max(1, cnt // 2)}\n"


SPECS.append(
    make_spec(
        "579A",
        summary="Minimum bacteria to add so doubling each night eventually yields exactly x: popcount(x).",
        samples=({"input": "5\n", "output": "2\n"}, {"input": "8\n", "output": "1\n"}),
        solve=_579a_solve,
        alt=_579a_alt,
        mutants={"uses_bit_length": _579a_mut_log2, "halves_popcount": _579a_mut_half},
        generate=lambda rng: [
            "5\n",
            "8\n",
            "1\n",
            "1000000000\n",
            "999999999\n",
            "2\n",
        ]
        + [f"{rng.randint(1, 10**9)}\n" for _ in range(6)],
        input_format="One integer x.",
        output_format="Print the minimum bacteria count.",
        constraints="1 <= x <= 10^9.",
        checker="exact",
        family="math",
    )
)


# ─── 1791C Prepend and Append ────────────────────────────────────────────────


def _1791c_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        l, r = 0, n - 1
        ans = n
        while l < r and s[l] != s[r]:
            l += 1
            r -= 1
            ans -= 2
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _1791c_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        i, j = 0, n - 1
        length = n
        while i < j:
            if s[i] == s[j]:
                break
            i += 1
            j -= 1
            length -= 2
        out.append(str(length))
    return "\n".join(out) + "\n"


def _1791c_mut_no_stop(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        l, r = 0, n - 1
        ans = n
        while l < r:
            l += 1
            r -= 1
            ans -= 2
        out.append(str(max(ans, 0)))
    return "\n".join(out) + "\n"


def _1791c_mut_off_by_two(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        l, r = 0, n - 1
        ans = n
        while l < r and s[l] != s[r]:
            l += 1
            r -= 1
            ans -= 2
        out.append(str(ans + 2))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1791C",
        summary="Trim matching outer 0/1 pairs from a string to find the shortest possible original length.",
        samples=(
            {
                "input": "5\n3\n100\n4\n0111\n5\n10101\n6\n101010\n7\n1010110\n",
                "output": "1\n2\n5\n0\n3\n",
            },
        ),
        solve=_1791c_solve,
        alt=_1791c_alt,
        mutants={"trims_unconditionally": _1791c_mut_no_stop, "off_by_two": _1791c_mut_off_by_two},
        generate=lambda rng: [
            "5\n3\n100\n4\n0111\n5\n10101\n6\n101010\n7\n1010110\n",
            "4\n1\n1\n2\n10\n2\n11\n10\n1101011010\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    (lambda s: f"{len(s)}\n{s}")(
                        "".join(rng.choice("01") for _ in range(rng.randint(1, 15)))
                    )
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 6))
            for _ in range(9)
        ],
        input_format="t then per test: n then a binary string.",
        output_format="Print the shortest original length per test case.",
        constraints="1 <= n <= 2000.",
        checker="tokens",
        family="strings",
    )
)


# ─── 466A Cheap Travel ────────────────────────────────────────────────────────


def _466a_solve(stdin: str) -> str:
    n, m, a, b = map(int, stdin.split())
    if m * a <= b:
        return f"{n * a}\n"
    full = n // m
    rem = n % m
    cost = full * b + rem * a
    if rem > 0:
        cost = min(cost, (full + 1) * b)
    return f"{cost}\n"


def _466a_alt(stdin: str) -> str:
    n, m, a, b = map(int, stdin.split())
    if m * a <= b:
        return f"{n * a}\n"
    packs = n // m
    remainder = n % m
    if remainder == 0:
        return f"{packs * b}\n"
    option1 = (packs + 1) * b
    option2 = packs * b + remainder * a
    return f"{min(option1, option2)}\n"


def _466a_mut_no_extra_pack(stdin: str) -> str:
    n, m, a, b = map(int, stdin.split())
    full = n // m
    rem = n % m
    return f"{full * b + rem * a}\n"


def _466a_mut_ignores_singles(stdin: str) -> str:
    n, m, a, b = map(int, stdin.split())
    import math as _m

    packs = _m.ceil(n / m)
    return f"{packs * b}\n"


SPECS.append(
    make_spec(
        "466A",
        summary="Minimum cost for n rides given single-ride price a and m-ride pack price b.",
        samples=({"input": "6 2 1 2\n", "output": "6\n"}, {"input": "5 2 2 3\n", "output": "8\n"}),
        solve=_466a_solve,
        alt=_466a_alt,
        mutants={"never_buys_extra_pack": _466a_mut_no_extra_pack, "always_rounds_up_packs": _466a_mut_ignores_singles},
        generate=lambda rng: [
            "6 2 1 2\n",
            "5 2 2 3\n",
            "1 1 1 1\n",
            "1000 1 5 5\n",
            "1000 1000 1 1000\n",
        ]
        + [
            f"{rng.randint(1, 1000)} {rng.randint(1, 1000)} {rng.randint(1, 1000)} {rng.randint(1, 1000)}\n"
            for _ in range(7)
        ],
        input_format="n m a b",
        output_format="Print the minimum total cost.",
        constraints="1 <= n, m, a, b <= 1000.",
        checker="exact",
        family="math",
    )
)


# ─── 451A Game With Sticks ───────────────────────────────────────────────────


def _451a_solve(stdin: str) -> str:
    n, m = map(int, stdin.split())
    return "Akshat\n" if min(n, m) % 2 == 1 else "Malvika\n"


def _451a_alt(stdin: str) -> str:
    n, m = map(int, stdin.split())
    moves = min(n, m)
    return "Akshat\n" if moves & 1 else "Malvika\n"


def _451a_mut_inverted(stdin: str) -> str:
    n, m = map(int, stdin.split())
    return "Malvika\n" if min(n, m) % 2 == 1 else "Akshat\n"


def _451a_mut_uses_max(stdin: str) -> str:
    n, m = map(int, stdin.split())
    return "Akshat\n" if max(n, m) % 2 == 1 else "Malvika\n"


SPECS.append(
    make_spec(
        "451A",
        summary="Sticks game winner determined by the parity of min(n, m).",
        samples=({"input": "2 2\n", "output": "Malvika\n"}, {"input": "2 3\n", "output": "Malvika\n"}, {"input": "3 3\n", "output": "Akshat\n"}),
        solve=_451a_solve,
        alt=_451a_alt,
        mutants={"inverted_winner": _451a_mut_inverted, "uses_max_instead_of_min": _451a_mut_uses_max},
        generate=lambda rng: [
            "2 2\n",
            "2 3\n",
            "3 3\n",
            "1 1\n",
            "100 100\n",
            "1 100\n",
        ]
        + [f"{rng.randint(1, 100)} {rng.randint(1, 100)}\n" for _ in range(6)],
        input_format="n m",
        output_format='Print "Akshat" or "Malvika".',
        constraints="1 <= n, m <= 100.",
        checker="tokens",
        family="math",
    )
)


# ─── 758A Holiday Of Equality ─────────────────────────────────────────────────


def _758a_solve(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    m = max(a)
    return f"{sum(m - x for x in a)}\n"


def _758a_alt(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    total = 0
    mx = max(a)
    for x in a:
        total += mx - x
    return f"{total}\n"


def _758a_mut_uses_avg(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    avg = sum(a) // len(a)
    return f"{sum(max(0, avg - x) for x in a)}\n"


def _758a_mut_off_by_one_max(stdin: str) -> str:
    vals = lines(stdin)
    a = list(map(int, vals[1].split()))
    m = max(a) + 1
    return f"{sum(m - x for x in a)}\n"


SPECS.append(
    make_spec(
        "758A",
        summary="Minimum burles to raise every citizen's welfare to the current maximum.",
        samples=(
            {"input": "5\n0 1 2 3 4\n", "output": "10\n"},
            {"input": "5\n1 1 0 1 1\n", "output": "1\n"},
            {"input": "3\n1 3 1\n", "output": "4\n"},
            {"input": "1\n12\n", "output": "0\n"},
        ),
        solve=_758a_solve,
        alt=_758a_alt,
        mutants={"uses_average_target": _758a_mut_uses_avg, "off_by_one_target": _758a_mut_off_by_one_max},
        generate=lambda rng: [
            "5\n0 1 2 3 4\n",
            "5\n1 1 0 1 1\n",
            "3\n1 3 1\n",
            "1\n12\n",
        ]
        + [
            (lambda n: f"{n}\n" + " ".join(str(rng.randint(0, 1000)) for _ in range(n)) + "\n")(
                rng.randint(1, 15)
            )
            for _ in range(6)
        ],
        input_format="n then n welfare values.",
        output_format="Print the minimum total gift.",
        constraints="1 <= n <= 100; 0 <= a_i <= 10^6.",
        checker="exact",
        family="implementation",
    )
)


# ─── 1850A To My Critics ─────────────────────────────────────────────────────


def _1850a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append(yes_no(a + b + c - min(a, b, c) >= 10).strip())
    return "\n".join(out) + "\n"


def _1850a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        digits = sorted(map(int, vals[i].split()))
        out.append("YES" if digits[1] + digits[2] >= 10 else "NO")
    return "\n".join(out) + "\n"


def _1850a_mut_checks_max_pair_only(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("YES" if a + b >= 10 else "NO")
    return "\n".join(out) + "\n"


def _1850a_mut_wrong_threshold(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("YES" if a + b + c - min(a, b, c) > 10 else "NO")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1850A",
        summary="Check if some pair of the three digits sums to at least 10.",
        samples=({"input": "5\n8 1 2\n4 4 5\n9 9 0\n0 0 0\n8 5 3\n", "output": "YES\nNO\nYES\nNO\nYES\n"},),
        solve=_1850a_solve,
        alt=_1850a_alt,
        mutants={"checks_only_first_pair": _1850a_mut_checks_max_pair_only, "wrong_threshold_strict": _1850a_mut_wrong_threshold},
        generate=lambda rng: [
            "5\n8 1 2\n4 4 5\n9 9 0\n0 0 0\n8 5 3\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(" ".join(str(rng.randint(0, 9)) for _ in range(3)) for _ in range(t))
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of 3 digits.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= t <= 1000; 0 <= a,b,c <= 9.",
        checker="tokens_ci",
        family="implementation",
    )
)


# ─── 1374B Multiply by 2, divide by 6 ────────────────────────────────────────


def _factor_counts(n: int) -> tuple[int, int, int]:
    c2 = 0
    while n % 2 == 0:
        n //= 2
        c2 += 1
    c3 = 0
    while n % 3 == 0:
        n //= 3
        c3 += 1
    return n, c2, c3


def _1374b_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        rem, c2, c3 = _factor_counts(n)
        if rem == 1 and c2 <= c3:
            out.append(str(2 * c3 - c2))
        else:
            out.append("-1")
    return "\n".join(out) + "\n"


def _1374b_alt(stdin: str) -> str:
    def strip(n, base):
        cnt = 0
        while n % base == 0:
            n //= base
            cnt += 1
        return n, cnt

    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        rem, twos = strip(n, 2)
        rem, threes = strip(rem, 3)
        if rem != 1 or twos > threes:
            out.append("-1")
            continue
        divides = threes
        multiplies = threes - twos
        out.append(str(divides + multiplies))
    return "\n".join(out) + "\n"


def _1374b_mut_ignores_leftover(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        rem, c2, c3 = _factor_counts(n)
        if c2 <= c3:
            out.append(str(2 * c3 - c2))
        else:
            out.append("-1")
    return "\n".join(out) + "\n"


def _1374b_mut_wrong_formula(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n = int(vals[i])
        rem, c2, c3 = _factor_counts(n)
        if rem == 1 and c2 <= c3:
            out.append(str(c3 + c2))
        else:
            out.append("-1")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1374B",
        summary="Minimum ops (x*2 or x/6) needed to reduce n to 1, or -1 if impossible.",
        samples=(
            {
                "input": "7\n1\n2\n3\n12\n12345\n15116544\n387420489\n",
                "output": "0\n-1\n2\n-1\n-1\n12\n36\n",
            },
        ),
        solve=_1374b_solve,
        alt=_1374b_alt,
        mutants={"ignores_leftover_factors": _1374b_mut_ignores_leftover, "wrong_move_formula": _1374b_mut_wrong_formula},
        generate=lambda rng: [
            "7\n1\n2\n3\n12\n12345\n15116544\n387420489\n",
        ]
        + [
            f"1\n{n}\n"
            for n in [
                6,
                36,
                6 ** rng.randint(1, 9),
                (6 ** rng.randint(1, 5)) * (2 ** rng.randint(0, 3)),
                rng.randint(1, 10**9),
                rng.randint(1, 10**9),
                rng.randint(1, 10**9),
                rng.randint(1, 10**9),
                10,
            ]
        ],
        input_format="t then t values of n.",
        output_format="Print the min number of operations or -1.",
        constraints="1 <= t <= 2*10^4; 1 <= n <= 10^9.",
        checker="tokens",
        family="math",
    )
)


# ─── 1873C Target Practice ───────────────────────────────────────────────────

_TARGET_BOARD = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
    [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


def _1873c_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        score = 0
        for r in range(10):
            row = vals[idx]
            idx += 1
            for c in range(10):
                if row[c] == "X":
                    score += _TARGET_BOARD[r][c]
        out.append(str(score))
    return "\n".join(out) + "\n"


def _1873c_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        total = 0
        grid = vals[idx : idx + 10]
        idx += 10
        for r in range(10):
            for c in range(10):
                if grid[r][c] == "X":
                    total += _TARGET_BOARD[r][c]
        out.append(str(total))
    return "\n".join(out) + "\n"


def _1873c_mut_counts_arrows(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        cnt = 0
        for r in range(10):
            row = vals[idx]
            idx += 1
            cnt += row.count("X")
        out.append(str(cnt))
    return "\n".join(out) + "\n"


def _1873c_mut_wrong_board(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        score = 0
        for r in range(10):
            row = vals[idx]
            idx += 1
            for c in range(10):
                if row[c] == "X":
                    score += 5 - min(r, c, 9 - r, 9 - c)
        out.append(str(score))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1873C",
        summary="Sum the ring-based point values of all 'X' arrow positions on a 10x10 target.",
        samples=(
            {
                "input": (
                    "4\n"
                    "X.........\n"
                    "..........\n"
                    ".......X..\n"
                    ".....X....\n"
                    "......X...\n"
                    "..........\n"
                    ".........X\n"
                    "..X.......\n"
                    "..........\n"
                    ".........X\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "....X.....\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "..........\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                    "XXXXXXXXXX\n"
                ),
                "output": "17\n0\n5\n220\n",
            },
        ),
        solve=_1873c_solve,
        alt=_1873c_alt,
        mutants={"counts_arrows_not_points": _1873c_mut_counts_arrows, "wrong_ring_formula": _1873c_mut_wrong_board},
        generate=lambda rng: [
            (
                "4\n"
                "X.........\n"
                "..........\n"
                ".......X..\n"
                ".....X....\n"
                "......X...\n"
                "..........\n"
                ".........X\n"
                "..X.......\n"
                "..........\n"
                ".........X\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "....X.....\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "..........\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
                "XXXXXXXXXX\n"
            ),
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "".join(
                    "".join(rng.choice("X" if rng.random() < 0.15 else ".") for _ in range(10)) + "\n"
                    for _ in range(10 * t)
                )
            )(rng.randint(1, 3))
            for _ in range(9)
        ],
        input_format="t then per test case 10 lines of 10 characters (X or .).",
        output_format="Print the total score per test case.",
        constraints="1 <= t <= 1000.",
        checker="tokens",
        family="implementation",
    )
)


# ─── 2009A Minimize! ─────────────────────────────────────────────────────────


def _2009a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        out.append(str(b - a))
    return "\n".join(out) + "\n"


def _2009a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        best = min((c - a) + (b - c) for c in range(a, b + 1))
        out.append(str(best))
    return "\n".join(out) + "\n"


def _2009a_mut_zero(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    return "\n".join(["0"] * t) + "\n"


def _2009a_mut_double(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = map(int, vals[i].split())
        out.append(str(2 * (b - a)))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "2009A",
        summary="Minimum of (c-a)+(b-c) over integer c in [a,b] is always b-a.",
        samples=({"input": "3\n1 2\n3 10\n5 5\n", "output": "1\n7\n0\n"},),
        solve=_2009a_solve,
        alt=_2009a_alt,
        mutants={"always_zero": _2009a_mut_zero, "doubles_difference": _2009a_mut_double},
        generate=lambda rng: [
            "3\n1 2\n3 10\n5 5\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    " ".join(map(str, sorted([rng.randint(1, 10), rng.randint(1, 10)])))
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of a b (a<=b).",
        output_format="Print b-a per test case.",
        constraints="1 <= t <= 55; 1 <= a <= b <= 10.",
        checker="tokens",
        family="brute force",
    )
)


# ─── 1560A Dislike of Threes ─────────────────────────────────────────────────


def _1560a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        k = int(vals[i])
        num = 0
        cnt = 0
        while cnt < k:
            num += 1
            if num % 3 == 0 or num % 10 == 3:
                continue
            cnt += 1
        out.append(str(num))
    return "\n".join(out) + "\n"


def _1560a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        k = int(vals[i])
        i2 = 0
        num = 0
        while True:
            num += 1
            if num % 3 != 0 and num % 10 != 3:
                i2 += 1
                if i2 == k:
                    break
        out.append(str(num))
    return "\n".join(out) + "\n"


def _1560a_mut_only_div3(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        k = int(vals[i])
        num = 0
        cnt = 0
        while cnt < k:
            num += 1
            if num % 3 == 0:
                continue
            cnt += 1
        out.append(str(num))
    return "\n".join(out) + "\n"


def _1560a_mut_only_ends3(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        k = int(vals[i])
        num = 0
        cnt = 0
        while cnt < k:
            num += 1
            if num % 10 == 3:
                continue
            cnt += 1
        out.append(str(num))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1560A",
        summary="Find the k-th positive integer not divisible by 3 and not ending in digit 3.",
        samples=({"input": "10\n1\n2\n3\n4\n5\n6\n7\n8\n9\n1000\n", "output": "1\n2\n4\n5\n7\n8\n10\n11\n14\n1666\n"},),
        solve=_1560a_solve,
        alt=_1560a_alt,
        mutants={"ignores_ends_in_3": _1560a_mut_only_div3, "ignores_div_by_3": _1560a_mut_only_ends3},
        generate=lambda rng: [
            "10\n1\n2\n3\n4\n5\n6\n7\n8\n9\n1000\n",
        ]
        + [
            (lambda t: f"{t}\n" + "\n".join(str(rng.randint(1, 1000)) for _ in range(t)) + "\n")(
                rng.randint(1, 8)
            )
            for _ in range(9)
        ],
        input_format="t then t values of k.",
        output_format="Print the k-th liked number per test case.",
        constraints="1 <= t <= 100; 1 <= k <= 1000.",
        checker="tokens",
        family="math",
    )
)


# ─── 1985A Creating Words ────────────────────────────────────────────────────


def _1985a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = vals[i].split()
        new_a = b[0] + a[1:]
        new_b = a[0] + b[1:]
        out.append(f"{new_a} {new_b}")
    return "\n".join(out) + "\n"


def _1985a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        parts = vals[i].split()
        a, b = list(parts[0]), list(parts[1])
        a[0], b[0] = b[0], a[0]
        out.append("".join(a) + " " + "".join(b))
    return "\n".join(out) + "\n"


def _1985a_mut_swaps_last(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b = vals[i].split()
        new_a = a[:-1] + b[-1]
        new_b = b[:-1] + a[-1]
        out.append(f"{new_a} {new_b}")
    return "\n".join(out) + "\n"


def _1985a_mut_no_swap(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        out.append(vals[i])
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1985A",
        summary="Swap the first characters of two length-3 words.",
        samples=(
            {
                "input": "6\nbit set\ncat dog\nhot dog\nuwu owo\ncat cat\nzzz zzz\n",
                "output": "sit bet\ndat cog\ndot hog\nowu uwo\ncat cat\nzzz zzz\n",
            },
        ),
        solve=_1985a_solve,
        alt=_1985a_alt,
        mutants={"swaps_last_char_instead": _1985a_mut_swaps_last, "no_swap_at_all": _1985a_mut_no_swap},
        generate=lambda rng: [
            "6\nbit set\ncat dog\nhot dog\nuwu owo\ncat cat\nzzz zzz\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    " ".join(
                        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(3))
                        for _ in range(2)
                    )
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of two 3-letter words.",
        output_format="Print both words after swapping first letters.",
        constraints="1 <= t <= 100.",
        checker="tokens",
        family="strings",
    )
)


# ─── 514A Chewbacca and Number ───────────────────────────────────────────────


def _514a_solve(stdin: str) -> str:
    s = stdin.strip()
    digits = list(s)
    for i, ch in enumerate(digits):
        d = int(ch)
        if d > 4:
            if i == 0 and d == 9:
                continue
            digits[i] = str(9 - d)
    return "".join(digits) + "\n"


def _514a_alt(stdin: str) -> str:
    s = stdin.strip()
    out = []
    for i, ch in enumerate(s):
        d = int(ch)
        inverted = 9 - d
        if inverted < d and not (i == 0 and inverted == 0):
            out.append(str(inverted))
        else:
            out.append(str(d))
    return "".join(out) + "\n"


def _514a_mut_ignores_leading_exception(stdin: str) -> str:
    s = stdin.strip()
    digits = list(s)
    for i, ch in enumerate(digits):
        d = int(ch)
        if d > 4:
            digits[i] = str(9 - d)
    return "".join(digits) + "\n"


def _514a_mut_threshold5(stdin: str) -> str:
    s = stdin.strip()
    digits = list(s)
    for i, ch in enumerate(digits):
        d = int(ch)
        if d >= 5 and not (i == 0 and d == 9):
            digits[i] = str(9 - d)
        elif d == 4:
            digits[i] = "5"
    return "".join(digits) + "\n"


SPECS.append(
    make_spec(
        "514A",
        summary="Invert digits >4 (replace t with 9-t) except a leading 9, to minimize the number.",
        samples=({"input": "27\n", "output": "22\n"}, {"input": "4545\n", "output": "4444\n"}, {"input": "9\n", "output": "9\n"}),
        solve=_514a_solve,
        alt=_514a_alt,
        mutants={"ignores_leading_9_exception": _514a_mut_ignores_leading_exception, "wrong_threshold": _514a_mut_threshold5},
        generate=lambda rng: [
            "27\n",
            "4545\n",
            "9\n",
            "1\n",
            "99999\n",
            "90000\n",
            "100000000000000000\n",
        ]
        + [str(rng.randint(1, 10**17)) + "\n" for _ in range(6)],
        input_format="One integer x (1 <= x <= 10^18).",
        output_format="Print the minimized number.",
        constraints="1 <= x <= 10^18.",
        checker="exact",
        family="greedy",
    )
)


# ─── 1873A Short Sort ────────────────────────────────────────────────────────


def _1873a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        diff = sum(1 for i2, ch in enumerate(s) if ch != "abc"[i2])
        out.append("YES" if diff <= 2 else "NO")
    return "\n".join(out) + "\n"


def _1873a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    bad = {"bca", "cab"}
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        out.append("NO" if s in bad else "YES")
    return "\n".join(out) + "\n"


def _1873a_mut_strict_one_diff(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        diff = sum(1 for i2, ch in enumerate(s) if ch != "abc"[i2])
        out.append("YES" if diff <= 1 else "NO")
    return "\n".join(out) + "\n"


def _1873a_mut_always_yes(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    return "\n".join(["YES"] * t) + "\n"


SPECS.append(
    make_spec(
        "1873A",
        summary="Check if 'abc' is reachable from a permutation of a,b,c with at most one swap.",
        samples=({"input": "6\nabc\nacb\nbac\ncab\nbca\nabc\n", "output": "YES\nYES\nYES\nNO\nNO\nYES\n"},),
        solve=_1873a_solve,
        alt=_1873a_alt,
        mutants={"requires_at_most_one_diff": _1873a_mut_strict_one_diff, "always_yes": _1873a_mut_always_yes},
        generate=lambda rng: [
            "6\nabc\nacb\nbac\ncab\nbca\nabc\n",
        ]
        + [
            f"6\n" + "\n".join("".join(p) for p in [
                "abc", "acb", "bac", "cab", "bca", "cba",
            ]) + "\n"
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    "".join(rng.sample(["a", "b", "c"], 3)) for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 6))
            for _ in range(8)
        ],
        input_format="t then t permutations of 'abc'.",
        output_format='Print "YES"/"NO" per test case.',
        constraints="1 <= t <= 6.",
        checker="tokens_ci",
        family="brute force",
    )
)


# ─── 1352C K-th Not Divisible by n ────────────────────────────────────────────


def _1352c_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, vals[i].split())
        out.append(str(k + (k - 1) // (n - 1)))
    return "\n".join(out) + "\n"


def _1352c_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, vals[i].split())
        lo, hi = k, k * 2
        while lo < hi:
            mid = (lo + hi) // 2
            not_div = mid - mid // n
            if not_div >= k:
                hi = mid
            else:
                lo = mid + 1
        out.append(str(lo))
    return "\n".join(out) + "\n"


def _1352c_mut_wrong_denominator(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, vals[i].split())
        out.append(str(k + (k - 1) // n))
    return "\n".join(out) + "\n"


def _1352c_mut_no_add(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        n, k = map(int, vals[i].split())
        out.append(str(k))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1352C",
        summary="Find the k-th positive integer not divisible by n.",
        samples=(
            {
                "input": "6\n3 7\n4 12\n2 1000000000\n7 97\n1000000000 1000000000\n2 1\n",
                "output": "10\n15\n1999999999\n113\n1000000001\n1\n",
            },
        ),
        solve=_1352c_solve,
        alt=_1352c_alt,
        mutants={"wrong_denominator": _1352c_mut_wrong_denominator, "forgets_offset": _1352c_mut_no_add},
        generate=lambda rng: [
            "6\n3 7\n4 12\n2 1000000000\n7 97\n1000000000 1000000000\n2 1\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(f"{rng.randint(2, 1000)} {rng.randint(1, 1000)}" for _ in range(t))
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of n k.",
        output_format="Print the k-th non-multiple of n per test case.",
        constraints="1 <= t <= 1000; 2 <= n <= 10^9; 1 <= k <= 10^9.",
        checker="tokens",
        family="math",
    )
)


# ─── 1829A Love Story ────────────────────────────────────────────────────────

_CODEFORCES_WORD = "codeforces"


def _1829a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        out.append(str(sum(1 for a, b in zip(s, _CODEFORCES_WORD) if a != b)))
    return "\n".join(out) + "\n"


def _1829a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        diff = 0
        for idx in range(10):
            if s[idx] != _CODEFORCES_WORD[idx]:
                diff += 1
        out.append(str(diff))
    return "\n".join(out) + "\n"


def _1829a_mut_counts_matches(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        out.append(str(sum(1 for a, b in zip(s, _CODEFORCES_WORD) if a == b)))
    return "\n".join(out) + "\n"


def _1829a_mut_set_diff(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        s = vals[i]
        out.append(str(len(set(s) - set(_CODEFORCES_WORD))))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1829A",
        summary='Count the number of index positions where a 10-letter string differs from "codeforces".',
        samples=(
            {
                "input": "5\ncoolforsez\ncadafurcie\ncodeforces\npaiuforces\nforcescode\n",
                "output": "4\n5\n0\n4\n9\n",
            },
        ),
        solve=_1829a_solve,
        alt=_1829a_alt,
        mutants={"counts_matches_instead": _1829a_mut_counts_matches, "uses_set_difference": _1829a_mut_set_diff},
        generate=lambda rng: [
            "5\ncoolforsez\ncadafurcie\ncodeforces\npaiuforces\nforcescode\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(10))
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t 10-letter lowercase strings.",
        output_format="Print the Hamming distance to 'codeforces' per test case.",
        constraints="1 <= t <= 1000.",
        checker="tokens",
        family="strings",
    )
)


# ─── 9A Die Roll ──────────────────────────────────────────────────────────────


def _9a_solve(stdin: str) -> str:
    y, w = map(int, stdin.split())
    mx = max(y, w)
    favorable = 6 - mx + 1
    g = math.gcd(favorable, 6)
    return f"{favorable // g}/{6 // g}\n"


def _9a_alt(stdin: str) -> str:
    y, w = map(int, stdin.split())
    mx = max(y, w)
    num, den = 6 - mx + 1, 6
    while True:
        g = math.gcd(num, den)
        if g == 1:
            break
        num //= g
        den //= g
    return f"{num}/{den}\n"


def _9a_mut_uses_min(stdin: str) -> str:
    y, w = map(int, stdin.split())
    mn = min(y, w)
    favorable = 6 - mn + 1
    g = math.gcd(favorable, 6)
    return f"{favorable // g}/{6 // g}\n"


def _9a_mut_off_by_one(stdin: str) -> str:
    y, w = map(int, stdin.split())
    mx = max(y, w)
    favorable = 6 - mx
    if favorable == 0:
        return "0/1\n"
    g = math.gcd(favorable, 6)
    return f"{favorable // g}/{6 // g}\n"


SPECS.append(
    make_spec(
        "9A",
        summary="Probability Dot rolls strictly higher than max(Y, W), as an irreducible fraction (ties favor Dot).",
        samples=({"input": "4 2\n", "output": "1/2\n"}, {"input": "1 1\n", "output": "1/1\n"}, {"input": "6 6\n", "output": "1/6\n"}),
        solve=_9a_solve,
        alt=_9a_alt,
        mutants={"uses_min_instead_of_max": _9a_mut_uses_min, "off_by_one_favorable": _9a_mut_off_by_one},
        generate=lambda rng: [
            "4 2\n",
            "1 1\n",
            "6 6\n",
            "1 6\n",
            "5 5\n",
            "2 1\n",
        ]
        + [f"{rng.randint(1, 6)} {rng.randint(1, 6)}\n" for _ in range(6)],
        input_format="Y W",
        output_format='Print the probability as "A/B".',
        constraints="1 <= Y, W <= 6.",
        checker="tokens",
        family="math",
    )
)


# ─── 1858A Buttons ────────────────────────────────────────────────────────────


def _1858a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if c % 2 == 0:
            out.append("First" if a > b else "Second")
        else:
            out.append("First" if a >= b else "Second")
    return "\n".join(out) + "\n"


def _1858a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if a > b:
            out.append("First")
        elif a < b:
            out.append("Second")
        else:
            out.append("First" if (a + b + c) % 2 == 1 else "Second")
    return "\n".join(out) + "\n"


def _1858a_mut_ignores_c_parity(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        out.append("First" if a >= b else "Second")
    return "\n".join(out) + "\n"


def _1858a_mut_inverted_parity(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if c % 2 == 1:
            out.append("First" if a > b else "Second")
        else:
            out.append("First" if a >= b else "Second")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1858A",
        summary="Two-player button game; winner depends on a vs b and parity of shared buttons c.",
        samples=({"input": "5\n1 1 1\n9 3 3\n1 2 3\n6 6 9\n2 2 8\n", "output": "First\nFirst\nSecond\nFirst\nSecond\n"},),
        solve=_1858a_solve,
        alt=_1858a_alt,
        mutants={"ignores_c_parity": _1858a_mut_ignores_c_parity, "inverted_parity_rule": _1858a_mut_inverted_parity},
        generate=lambda rng: [
            "5\n1 1 1\n9 3 3\n1 2 3\n6 6 9\n2 2 8\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    f"{rng.randint(1, 20)} {rng.randint(1, 20)} {rng.randint(1, 20)}" for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of a b c.",
        output_format='Print "First"/"Second" per test case.',
        constraints="1 <= t <= 10^4; 1 <= a,b,c <= 10^9.",
        checker="tokens",
        family="games",
    )
)


# ─── 43A Football ─────────────────────────────────────────────────────────────


def _43a_solve(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    teams = vals[1 : 1 + n]
    cnt = Counter(teams)
    winner = max(cnt, key=lambda team: cnt[team])
    return f"{winner}\n"


def _43a_alt(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    goals = vals[1 : 1 + n]
    tally: dict[str, int] = {}
    for g in goals:
        tally[g] = tally.get(g, 0) + 1
    best_team = None
    best_count = -1
    for team, count in tally.items():
        if count > best_count:
            best_count = count
            best_team = team
    return f"{best_team}\n"


def _43a_mut_first_team(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return f"{vals[1]}\n"


def _43a_mut_last_team(stdin: str) -> str:
    vals = lines(stdin)
    n = int(vals[0])
    return f"{vals[n]}\n"


SPECS.append(
    make_spec(
        "43A",
        summary="Given a list of goal-scoring teams, print the team with the most goals.",
        samples=({"input": "1\nABC\n", "output": "ABC\n"}, {"input": "5\nA\nABA\nABA\nAA\nA\n"[0:0] or "6\nA\nB\nA\nA\nB\nA\n", "output": "A\n"}),
        solve=_43a_solve,
        alt=_43a_alt,
        mutants={"always_first_scorer": _43a_mut_first_team, "always_last_scorer": _43a_mut_last_team},
        generate=lambda rng: [
            "1\nABC\n",
            "6\nA\nB\nA\nA\nB\nA\n",
            "2\nXX\nYY\n",
        ]
        + [
            (
                lambda n, a_count: f"{n}\n"
                + "\n".join(["TEAMA"] * a_count + ["TEAMB"] * (n - a_count))
                + "\n"
            )(*(lambda n: (n, rng.choice([i for i in range(1, n) if i != n - i])))(rng.randint(3, 20)))
            for _ in range(7)
        ],
        input_format="n then n team names (goal scorers).",
        output_format="Print the name of the winning team.",
        constraints="1 <= n <= 100; at most 2 distinct team names.",
        checker="exact",
        family="strings",
    )
)


# ─── 1950A Stair, Peak, or Neither? ──────────────────────────────────────────


def _1950a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if a < b < c:
            out.append("STAIR")
        elif a < b and b > c:
            out.append("PEAK")
        else:
            out.append("NONE")
    return "\n".join(out) + "\n"


def _1950a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        digits = list(map(int, vals[i].split()))
        rising1 = digits[0] < digits[1]
        rising2 = digits[1] < digits[2]
        if rising1 and rising2:
            out.append("STAIR")
        elif rising1 and not rising2 and digits[1] > digits[2]:
            out.append("PEAK")
        else:
            out.append("NONE")
    return "\n".join(out) + "\n"


def _1950a_mut_allows_equal(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if a <= b <= c:
            out.append("STAIR")
        elif a <= b and b >= c:
            out.append("PEAK")
        else:
            out.append("NONE")
    return "\n".join(out) + "\n"


def _1950a_mut_swaps_stair_peak(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    for i in range(1, t + 1):
        a, b, c = map(int, vals[i].split())
        if a < b < c:
            out.append("PEAK")
        elif a < b and b > c:
            out.append("STAIR")
        else:
            out.append("NONE")
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1950A",
        summary="Classify three digits as STAIR (a<b<c), PEAK (a<b>c), or NONE.",
        samples=(
            {
                "input": "7\n1 2 3\n3 2 1\n1 5 3\n3 4 1\n0 0 0\n4 1 7\n4 5 7\n",
                "output": "STAIR\nNONE\nPEAK\nPEAK\nNONE\nNONE\nSTAIR\n",
            },
        ),
        solve=_1950a_solve,
        alt=_1950a_alt,
        mutants={"allows_equal_values": _1950a_mut_allows_equal, "swaps_stair_and_peak": _1950a_mut_swaps_stair_peak},
        generate=lambda rng: [
            "7\n1 2 3\n3 2 1\n1 5 3\n3 4 1\n0 0 0\n4 1 7\n4 5 7\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(" ".join(str(rng.randint(0, 9)) for _ in range(3)) for _ in range(t))
                + "\n"
            )(rng.randint(1, 8))
            for _ in range(9)
        ],
        input_format="t then t lines of 3 digits.",
        output_format='Print "STAIR", "PEAK", or "NONE" per test case.',
        constraints="1 <= t <= 1000; 0 <= a,b,c <= 9.",
        checker="tokens_ci",
        family="implementation",
    )
)


# ─── 1900A Cover in Water ─────────────────────────────────────────────────────


def _1900a_solve(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        if "..." in s:
            out.append("2")
        else:
            out.append(str(s.count(".")))
    return "\n".join(out) + "\n"


def _1900a_alt(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        run = 0
        has_triple = False
        for ch in s:
            if ch == ".":
                run += 1
                if run >= 3:
                    has_triple = True
            else:
                run = 0
        out.append("2" if has_triple else str(s.count(".")))
    return "\n".join(out) + "\n"


def _1900a_mut_threshold2(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        if ".." in s:
            out.append("2")
        else:
            out.append(str(s.count(".")))
    return "\n".join(out) + "\n"


def _1900a_mut_always_count(stdin: str) -> str:
    vals = lines(stdin)
    t = int(vals[0])
    out = []
    idx = 1
    for _ in range(t):
        n = int(vals[idx])
        s = vals[idx + 1]
        idx += 2
        out.append(str(s.count(".")))
    return "\n".join(out) + "\n"


SPECS.append(
    make_spec(
        "1900A",
        summary="Min action-1 uses to fill all empty cells: 2 if there are 3 consecutive empties, else count of empties.",
        samples=(
            {
                "input": "5\n3\n...\n7\n##....#\n7\n..#.#..\n4\n####\n10\n#...#..#.#\n",
                "output": "2\n2\n5\n0\n2\n",
            },
        ),
        solve=_1900a_solve,
        alt=_1900a_alt,
        mutants={"threshold_two_not_three": _1900a_mut_threshold2, "ignores_propagation": _1900a_mut_always_count},
        generate=lambda rng: [
            "5\n3\n...\n7\n##....#\n7\n..#.#..\n4\n####\n10\n#...#..#.#\n",
        ]
        + [
            (
                lambda t: f"{t}\n"
                + "\n".join(
                    (lambda s: f"{len(s)}\n{s}")(
                        "".join(rng.choice(".#") for _ in range(rng.randint(1, 15)))
                    )
                    for _ in range(t)
                )
                + "\n"
            )(rng.randint(1, 6))
            for _ in range(9)
        ],
        input_format="t then per test: n then a string of '.' and '#'.",
        output_format="Print the minimum action-1 count per test case.",
        constraints="1 <= n <= 100.",
        checker="tokens",
        family="constructive algorithms",
    )
)

_KEEP = ['630A', '155A', '381A', '492B', '1669A', '1475A', '732A', '1676A', '1154A', '706B', '1692A', '1903A', '1807A', '1999A', '581A', '1878A', '1857A', '189A', '1829B', '339B', '1791A', '1399A', '1901A', '1512A', '1409A', '1915A', '1760A', '32B', '579A', '1791C', '466A', '451A', '758A', '1850A', '1374B', '1873C', '2009A', '1560A', '1985A', '514A', '1873A', '1352C', '1829A', '9A', '1858A', '43A', '1950A', '1900A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
