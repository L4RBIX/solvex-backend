"""Bulk practice-pack oracle specs — batch 03.

Dual-independent-oracle ProblemOracleSpec entries for 50 problems from
catalog/batches/batch_03.json (1535A .. 1840C). Each spec provides two
independently coded correct solutions, >=2 wrong mutants, and a
generate_cases() function yielding >=10 unique stdin cases (including a
sample derived from the official statement).

For constructive problems with multiple valid outputs (e.g. 1845A, 1783A,
1389A) both oracles implement the *same* canonical deterministic
construction rule (as documented inline) so that dual-oracle agreement is
meaningful; sample expected-output text is computed from that canonical
rule rather than quoted verbatim from an arbitrary judge example that may
differ (any valid answer is accepted by the real judge).
"""

from __future__ import annotations

import random

from contestiq_api.practice_packs.catalog.dsl import ensure_nl, lines, make_spec, yes_no

SPECS = []


def _tcases(stdin: str) -> tuple[int, list[str]]:
    ls = lines(stdin)
    return int(ls[0]), ls[1:]


def _rand_ints(rng: random.Random, n: int, lo: int, hi: int) -> list[int]:
    return [rng.randint(lo, hi) for _ in range(n)]


# ════════════════════════════════════════════════════════════════════════
# 1535A Fair Playoff
# ════════════════════════════════════════════════════════════════════════


def _s_1535a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s1, s2, s3, s4 = map(int, rows[i].split())
        if min(s1, s2) > max(s3, s4) or max(s1, s2) < min(s3, s4):
            out.append("NO")
        else:
            out.append("YES")
    return "\n".join(out) + "\n"


def _a_1535a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        vals = list(map(int, rows[i].split()))
        w1 = max(vals[0], vals[1])
        w2 = max(vals[2], vals[3])
        top1, top2 = sorted(vals, reverse=True)[:2]
        out.append("YES" if top2 in (w1, w2) else "NO")
    return "\n".join(out) + "\n"


def _m_1535a_only_first(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s1, s2, s3, s4 = map(int, rows[i].split())
        out.append("NO" if min(s1, s2) > max(s3, s4) else "YES")
    return "\n".join(out) + "\n"


def _m_1535a_sum(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s1, s2, s3, s4 = map(int, rows[i].split())
        out.append("YES" if (s1 + s2) != (s3 + s4) else "NO")
    return "\n".join(out) + "\n"


def _g_1535a(rng: random.Random) -> list[str]:
    cases = ["4\n3 7 9 5\n4 5 6 9\n5 3 8 1\n6 5 3 2\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            vals = rng.sample(range(1, 101), 4)
            rows.append(" ".join(map(str, vals)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1535A",
        summary="4 players; 1v2 and 3v4, winners meet in final. Is the tournament fair (do the two highest skills meet)?",
        samples=[{"input": "4\n3 7 9 5\n4 5 6 9\n5 3 8 1\n6 5 3 2\n", "output": "YES\nNO\nYES\nNO\n"}],
        solve=_s_1535a,
        alt=_a_1535a,
        mutants={"only_first_cond": _m_1535a_only_first, "sum_compare": _m_1535a_sum},
        generate=_g_1535a,
        checker="tokens_ci",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 2094A Trippi Troppi
# ════════════════════════════════════════════════════════════════════════


def _s_2094a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        words = rows[i].split()
        out.append("".join(w[0] for w in words))
    return "\n".join(out) + "\n"


def _a_2094a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c = rows[i].split()
        out.append(a[0] + b[0] + c[0])
    return "\n".join(out) + "\n"


def _m_2094a_last_letter(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        words = rows[i].split()
        out.append("".join(w[-1] for w in words))
    return "\n".join(out) + "\n"


def _m_2094a_upper(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        words = rows[i].split()
        out.append("".join(w[0] for w in words).upper())
    return "\n".join(out) + "\n"


def _g_2094a(rng: random.Random) -> list[str]:
    cases = ["3\nunited states america\nred vlue jrey\ntucker tape mokey\n"]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            words = []
            for _ in range(3):
                length = rng.randint(1, 6)
                words.append("".join(rng.choice(letters) for _ in range(length)))
            rows.append(" ".join(words))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "2094A",
        summary="Given t triples of lowercase words, print the concatenation of each word's first letter.",
        samples=[{"input": "3\nunited states america\nred vlue jrey\ntucker tape mokey\n", "output": "usa\nrvj\nttm\n"}],
        solve=_s_2094a,
        alt=_a_2094a,
        mutants={"last_letter": _m_2094a_last_letter, "uppercase": _m_2094a_upper},
        generate=_g_2094a,
        checker="exact",
        family="strings",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1360A Minimal Square
# ════════════════════════════════════════════════════════════════════════


def _s_1360a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b = map(int, rows[i].split())
        side = max(2 * min(a, b), max(a, b))
        out.append(str(side * side))
    return "\n".join(out) + "\n"


def _a_1360a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b = map(int, rows[i].split())
        side = min(max(2 * a, b), max(a, 2 * b))
        out.append(str(side * side))
    return "\n".join(out) + "\n"


def _m_1360a_no_double(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b = map(int, rows[i].split())
        side = max(a, b)
        out.append(str(side * side))
    return "\n".join(out) + "\n"


def _m_1360a_area_sum(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b = map(int, rows[i].split())
        side = max(2 * min(a, b), max(a, b))
        out.append(str(2 * a * b + side))
    return "\n".join(out) + "\n"


def _g_1360a(rng: random.Random) -> list[str]:
    cases = ["3\n3 2\n4 4\n1 3\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = [f"{rng.randint(1, 100)} {rng.randint(1, 100)}" for _ in range(t)]
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1360A",
        summary="Minimum area square that fits two a x b rectangles (axis-aligned, no rotation).",
        samples=[{"input": "3\n3 2\n4 4\n1 3\n", "output": "16\n64\n9\n"}],
        solve=_s_1360a,
        alt=_a_1360a,
        mutants={"no_double": _m_1360a_no_double, "area_sum": _m_1360a_area_sum},
        generate=_g_1360a,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1985B Maximum Multiple Sum
# ════════════════════════════════════════════════════════════════════════


def _s_1985b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n = int(rows[i])
        out.append("3" if n == 3 else "2")
    return "\n".join(out) + "\n"


def _a_1985b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n = int(rows[i])
        best_x, best_sum = 2, 0
        for x in range(2, min(n, 3) + 1):
            s = 0
            m = x
            while m <= n:
                s += m
                m += x
            if s > best_sum:
                best_sum, best_x = s, x
        out.append(str(best_x))
    return "\n".join(out) + "\n"


def _m_1985b_always_two(stdin: str) -> str:
    t, rows = _tcases(stdin)
    return "\n".join("2" for _ in range(t)) + "\n"


def _m_1985b_wrong_boundary(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n = int(rows[i])
        out.append("3" if n <= 3 else "2")
    return "\n".join(out) + "\n"


def _g_1985b(rng: random.Random) -> list[str]:
    cases = ["9\n3\n4\n5\n6\n7\n8\n9\n100\n99999\n"]
    for _ in range(11):
        t = rng.randint(1, 6)
        rows = [str(rng.randint(2, 200)) for _ in range(t)]
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1985B",
        summary="Choose x in [2,n] maximizing the sum of multiples of x that are <= n.",
        samples=[{"input": "9\n3\n4\n5\n6\n7\n8\n9\n100\n99999\n", "output": "3\n2\n2\n2\n2\n2\n2\n2\n2\n"}],
        solve=_s_1985b,
        alt=_a_1985b,
        mutants={"always_two": _m_1985b_always_two, "wrong_boundary": _m_1985b_wrong_boundary},
        generate=_g_1985b,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1722B Colourblindness
# ════════════════════════════════════════════════════════════════════════


def _s_1722b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        r1 = ls[idx + 1]
        r2 = ls[idx + 2]
        idx += 3
        r1n = r1.replace("B", "G")
        r2n = r2.replace("B", "G")
        out.append("YES" if r1n == r2n else "NO")
    return "\n".join(out) + "\n"


def _a_1722b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        r1 = ls[idx + 1]
        r2 = ls[idx + 2]
        idx += 3
        same = True
        for c1, c2 in zip(r1, r2):
            if c1 == c2:
                continue
            if {c1, c2} == {"G", "B"}:
                continue
            same = False
            break
        out.append("YES" if same else "NO")
    return "\n".join(out) + "\n"


def _m_1722b_no_colorblind(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        r1 = ls[idx + 1]
        r2 = ls[idx + 2]
        idx += 3
        out.append("YES" if r1 == r2 else "NO")
    return "\n".join(out) + "\n"


def _m_1722b_swap_wrong(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        r1 = ls[idx + 1]
        r2 = ls[idx + 2]
        idx += 3
        r1n = r1.replace("R", "G")
        r2n = r2.replace("R", "G")
        out.append("YES" if r1n == r2n else "NO")
    return "\n".join(out) + "\n"


def _g_1722b(rng: random.Random) -> list[str]:
    cases = ["4\n2\nGR\nRG\n4\nGRBG\nRGGR\n5\nGGGGG\nBBBBB\n1\nR\nR\n"]
    colors = "RGB"
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 6)
            r1 = "".join(rng.choice(colors) for _ in range(n))
            if rng.random() < 0.5:
                r2 = "".join(c if c != "B" else "G" for c in r1)
                r2 = "".join(rng.choice("GB") if c == "G" and rng.random() < 0.4 else c for c in r2)
            else:
                r2 = "".join(rng.choice(colors) for _ in range(n))
            rows.append(f"{n}\n{r1}\n{r2}")
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1722B",
        summary="Two rows of R/G/B colors; a colorblind person can't tell G from B. Are the rows indistinguishable to them?",
        samples=[
            {
                "input": "4\n2\nGR\nRG\n4\nGRBG\nRGGR\n5\nGGGGG\nBBBBB\n1\nR\nR\n",
                "output": "NO\nNO\nYES\nYES\n",
            }
        ],
        solve=_s_1722b,
        alt=_a_1722b,
        mutants={"no_colorblind": _m_1722b_no_colorblind, "swap_wrong_color": _m_1722b_swap_wrong},
        generate=_g_1722b,
        checker="tokens_ci",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1877A Goals of Victory
# ════════════════════════════════════════════════════════════════════════


def _s_1877a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        vals = list(map(int, ls[idx + 1].split()))
        idx += 2
        out.append(str(-sum(vals)))
    return "\n".join(out) + "\n"


def _a_1877a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        vals = list(map(int, ls[idx + 1].split()))
        idx += 2
        total = 0
        for v in vals:
            total += v
        out.append(str(0 - total))
    return "\n".join(out) + "\n"


def _m_1877a_pos_sum(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        vals = list(map(int, ls[idx + 1].split()))
        idx += 2
        out.append(str(sum(vals)))
    return "\n".join(out) + "\n"


def _m_1877a_off_by_one(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        vals = list(map(int, ls[idx + 1].split()))
        idx += 2
        out.append(str(-sum(vals) + 1))
    return "\n".join(out) + "\n"


def _g_1877a(rng: random.Random) -> list[str]:
    cases = ["3\n2\n1 -2\n4\n5 -1 -3 4\n1\n0\n"]
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 6)
            vals = _rand_ints(rng, n, -100, 100)
            rows.append(f"{n}\n" + " ".join(map(str, vals)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1877A",
        summary="n-1 efficiencies given for n teams; total of all n efficiencies is 0. Find the missing team's efficiency.",
        samples=[{"input": "3\n2\n1 -2\n4\n5 -1 -3 4\n1\n0\n", "output": "1\n-5\n0\n"}],
        solve=_s_1877a,
        alt=_a_1877a,
        mutants={"pos_sum": _m_1877a_pos_sum, "off_by_one": _m_1877a_off_by_one},
        generate=_g_1877a,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1788A One and Two
# ════════════════════════════════════════════════════════════════════════


def _s_1788a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        total_twos = sum(1 for x in arr if x == 2)
        if total_twos % 2 == 1:
            out.append("-1")
            continue
        target = total_twos // 2
        seen = 0
        ans = -1
        for i, x in enumerate(arr, start=1):
            if x == 2:
                seen += 1
            if seen == target:
                ans = i
                break
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1788a(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        total_twos = arr.count(2)
        if total_twos % 2 != 0:
            out.append("-1")
            continue
        half = total_twos // 2
        prefix_twos = 0
        result = -1
        for k in range(n):
            if arr[k] == 2:
                prefix_twos += 1
            if prefix_twos == half:
                result = k + 1
                break
        out.append(str(result))
    return "\n".join(out) + "\n"


def _m_1788a_use_length(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        total_twos = arr.count(2)
        if total_twos % 2 != 0:
            out.append("-1")
            continue
        target = total_twos // 2
        seen = 0
        ans = -1
        for i, x in enumerate(arr):
            if x == 2:
                seen += 1
            if seen == target:
                ans = i
                break
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m_1788a_odd_check_flip(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        total_twos = arr.count(2)
        if total_twos % 2 == 0:
            out.append("-1")
            continue
        target = total_twos // 2
        seen = 0
        ans = -1
        for i, x in enumerate(arr, start=1):
            if x == 2:
                seen += 1
            if seen == target:
                ans = i
                break
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _g_1788a(rng: random.Random) -> list[str]:
    cases = ["3\n6\n2 2 1 2 1 2\n3\n1 2 1\n4\n1 1 1 1\n"]
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 10)
            arr = [rng.choice([1, 2]) for _ in range(n)]
            rows.append(f"{n}\n" + " ".join(map(str, arr)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1788A",
        summary="Array of 1s and 2s. Find smallest k so that product of first k equals product of the rest, or -1.",
        samples=[{"input": "3\n6\n2 2 1 2 1 2\n3\n1 2 1\n4\n1 1 1 1\n", "output": "2\n-1\n1\n"}],
        solve=_s_1788a,
        alt=_a_1788a,
        mutants={"use_length_not_count": _m_1788a_use_length, "odd_check_flip": _m_1788a_odd_check_flip},
        generate=_g_1788a,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1669B Triple
# ════════════════════════════════════════════════════════════════════════


def _s_1669b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        cnt = [0] * (n + 1)
        ans = -1
        for x in arr:
            cnt[x] += 1
            if cnt[x] >= 3:
                ans = x
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1669b(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        seen: dict[int, int] = {}
        result = -1
        for x in arr:
            seen[x] = seen.get(x, 0) + 1
            if seen[x] >= 3:
                result = x
        out.append(str(result))
    return "\n".join(out) + "\n"


def _m_1669b_first_only(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        cnt = [0] * (n + 1)
        ans = -1
        for x in arr:
            cnt[x] += 1
            if cnt[x] >= 3 and ans == -1:
                ans = x
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m_1669b_needs_four(stdin: str) -> str:
    ls = lines(stdin)
    t = int(ls[0])
    idx = 1
    out = []
    for _ in range(t):
        n = int(ls[idx])
        arr = list(map(int, ls[idx + 1].split()))
        idx += 2
        cnt = [0] * (n + 1)
        ans = -1
        for x in arr:
            cnt[x] += 1
            if cnt[x] >= 4:
                ans = x
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _g_1669b(rng: random.Random) -> list[str]:
    cases = [
        "7\n1\n1\n3\n2 2 2\n7\n2 2 3 3 4 2 2\n8\n1 4 3 4 3 2 4 1\n9\n1 1 1 2 2 2 3 3 3\n5\n1 5 2 4 3\n4\n4 4 4 4\n"
    ]
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 10)
            arr = [rng.randint(1, max(1, n)) for _ in range(n)]
            rows.append(f"{n}\n" + " ".join(map(str, arr)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1669B",
        summary="Array a_1..a_n (1<=a_i<=n). Print any value occurring at least 3 times, using the canonical rule: the last value (in input order) whose running count reaches >=3; else -1.",
        samples=[
            {
                "input": "7\n1\n1\n3\n2 2 2\n7\n2 2 3 3 4 2 2\n8\n1 4 3 4 3 2 4 1\n9\n1 1 1 2 2 2 3 3 3\n5\n1 5 2 4 3\n4\n4 4 4 4\n",
                "output": "-1\n2\n2\n4\n3\n-1\n4\n",
            }
        ],
        solve=_s_1669b,
        alt=_a_1669b,
        mutants={"first_triple_only": _m_1669b_first_only, "needs_four": _m_1669b_needs_four},
        generate=_g_1669b,
        checker="tokens",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 2065A Skibidus and Amog'u
# ════════════════════════════════════════════════════════════════════════


def _s_2065a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        w = rows[i]
        out.append(w[:-2] + "i")
    return "\n".join(out) + "\n"


def _a_2065a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        w = rows[i]
        stem = w[: len(w) - 2]
        out.append(stem + "i")
    return "\n".join(out) + "\n"


def _m_2065a_no_strip(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        w = rows[i]
        out.append(w + "i")
    return "\n".join(out) + "\n"


def _m_2065a_strip_one(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        w = rows[i]
        out.append(w[:-1] + "i")
    return "\n".join(out) + "\n"


def _g_2065a(rng: random.Random) -> list[str]:
    cases = ["9\nus\nsus\nfungus\ncactus\nsussus\namogus\nchungus\nntarsus\nskibidus\n"]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            length = rng.randint(0, 6)
            stem = "".join(rng.choice(letters) for _ in range(length))
            rows.append(stem + "us")
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "2065A",
        summary="Convert a singular noun ending in 'us' to plural: remove 'us' suffix, append 'i'.",
        samples=[
            {
                "input": "9\nus\nsus\nfungus\ncactus\nsussus\namogus\nchungus\nntarsus\nskibidus\n",
                "output": "i\nsi\nfungi\ncacti\nsussi\namogi\nchungi\nntarsi\nskibidi\n",
            }
        ],
        solve=_s_2065a,
        alt=_a_2065a,
        mutants={"no_strip": _m_2065a_no_strip, "strip_one_char": _m_2065a_strip_one},
        generate=_g_2065a,
        checker="exact",
        family="strings",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 474A Keyboard
# ════════════════════════════════════════════════════════════════════════

_LAYOUT_474A = "qwertyuiopasdfghjklzxcvbnm"


def _s_474a(stdin: str) -> str:
    ls = lines(stdin)
    direction = ls[0].strip()
    s = ls[1]
    shift = -1 if direction == "R" else 1
    out_chars = []
    for c in s:
        pos = _LAYOUT_474A.index(c)
        out_chars.append(_LAYOUT_474A[pos + shift])
    return "".join(out_chars) + "\n"


def _a_474a(stdin: str) -> str:
    ls = lines(stdin)
    direction = ls[0].strip()
    s = ls[1]
    table = {}
    for i, ch in enumerate(_LAYOUT_474A):
        if direction == "R":
            table[ch] = _LAYOUT_474A[i - 1]
        else:
            table[ch] = _LAYOUT_474A[(i + 1) % len(_LAYOUT_474A)]
    return "".join(table[c] for c in s) + "\n"


def _m_474a_swap_direction(stdin: str) -> str:
    ls = lines(stdin)
    direction = ls[0].strip()
    s = ls[1]
    shift = 1 if direction == "R" else -1
    out_chars = []
    for c in s:
        pos = _LAYOUT_474A.index(c)
        out_chars.append(_LAYOUT_474A[pos + shift])
    return "".join(out_chars) + "\n"


def _m_474a_identity(stdin: str) -> str:
    ls = lines(stdin)
    s = ls[1]
    return s + "\n"


def _g_474a(rng: random.Random) -> list[str]:
    cases = ["R\ns\n", "L\nz\n", "R\nhello\n", "L\ncodeforces\n"]
    for _ in range(8):
        direction = rng.choice(["L", "R"])
        length = rng.randint(1, 10)
        if direction == "R":
            allowed = _LAYOUT_474A[1:]
        else:
            allowed = _LAYOUT_474A[:-1]
        s = "".join(rng.choice(allowed) for _ in range(length))
        cases.append(f"{direction}\n{s}\n")
    return cases


SPECS.append(
    make_spec(
        "474A",
        summary="Message typed with keyboard shifted one key L/R along the QWERTY row-major layout; recover the original message.",
        samples=[{"input": "R\ns\n", "output": "a\n"}, {"input": "R\nhello\n", "output": "gwkki\n"}],
        solve=_s_474a,
        alt=_a_474a,
        mutants={"swap_direction": _m_474a_swap_direction, "identity": _m_474a_identity},
        generate=_g_474a,
        checker="exact",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 702A Maximum Increase
# ════════════════════════════════════════════════════════════════════════


def _s_702a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    best = 1
    cur = 1
    for i in range(1, n):
        if a[i] > a[i - 1]:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
    return f"{best}\n"


def _a_702a(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    runs = []
    cur = 1
    for i in range(1, n):
        if a[i] > a[i - 1]:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    return f"{max(runs)}\n"


def _m_702a_non_decreasing(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    best = 1
    cur = 1
    for i in range(1, n):
        if a[i] >= a[i - 1]:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
    return f"{best}\n"


def _m_702a_no_reset(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    cur = 1
    for i in range(1, n):
        if a[i] > a[i - 1]:
            cur += 1
    return f"{cur}\n"


def _g_702a(rng: random.Random) -> list[str]:
    cases = ["6\n7 2 3 1 5 6\n", "3\n1 2 3\n", "1\n42\n"]
    for _ in range(9):
        n = rng.randint(1, 12)
        a = _rand_ints(rng, n, 1, 20)
        cases.append(f"{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


SPECS.append(
    make_spec(
        "702A",
        summary="Find the maximum length of a strictly increasing contiguous subarray.",
        samples=[{"input": "6\n7 2 3 1 5 6\n", "output": "3\n"}],
        solve=_s_702a,
        alt=_a_702a,
        mutants={"non_decreasing": _m_702a_non_decreasing, "no_reset": _m_702a_no_reset},
        generate=_g_702a,
        checker="exact",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 313B Ilya and Queries
# ════════════════════════════════════════════════════════════════════════


def _s_313b(stdin: str) -> str:
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


def _a_313b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    s = ls[1]
    diffs = [1 if s[i] == s[i + 1] else 0 for i in range(n - 1)]
    prefix = [0]
    for d in diffs:
        prefix.append(prefix[-1] + d)
    out = []
    for k in range(2, 2 + m):
        l, r = map(int, ls[k].split())
        out.append(str(prefix[r - 1] - prefix[l - 1]))
    return "\n".join(out) + "\n"


def _m_313b_off_by_one(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    s = ls[1]
    pre = [0] * n
    for i in range(1, n):
        pre[i] = pre[i - 1] + (1 if s[i] == s[i - 1] else 0)
    out = []
    for k in range(2, 2 + m):
        l, r = map(int, ls[k].split())
        out.append(str(pre[r - 1] - pre[l - 1] + 1))
    return "\n".join(out) + "\n"


def _m_313b_halved(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    s = ls[1]
    out = []
    for k in range(2, 2 + m):
        l, r = map(int, ls[k].split())
        cnt = 0
        for i in range(l - 1, r - 1):
            if i + 1 < n and s[i] == s[i + 1]:
                cnt += 1
        out.append(str(cnt // 2))
    return "\n".join(out) + "\n"


def _g_313b(rng: random.Random) -> list[str]:
    cases = ["3\n3\nabaa\n1 4\n2 3\n3 4\n"]
    letters = "ab"
    for _ in range(11):
        n = rng.randint(2, 12)
        m = rng.randint(1, 5)
        s = "".join(rng.choice(letters) for _ in range(n))
        rows = [f"{n} {m}", s]
        for _ in range(m):
            l = rng.randint(1, n)
            r = rng.randint(l, n)
            rows.append(f"{l} {r}")
        cases.append("\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "313B",
        summary="Given a string and m range queries [l,r] (1-indexed), count adjacent equal-character pairs fully inside each range.",
        samples=[{"input": "3\n3\nabaa\n1 4\n2 3\n3 4\n", "output": "1\n0\n1\n"}],
        solve=_s_313b,
        alt=_a_313b,
        mutants={"off_by_one": _m_313b_off_by_one, "halved_count": _m_313b_halved},
        generate=_g_313b,
        checker="tokens",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 707A Brain's Photos
# ════════════════════════════════════════════════════════════════════════


def _s_707a(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    grid = ls[1 : 1 + n]
    is_color = any(ch in ("C", "M", "Y") for row in grid for ch in row.split())
    return ("#Color\n" if is_color else "#Black&White\n")


def _a_707a(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    color_set = {"C", "M", "Y"}
    found = False
    for row in ls[1 : 1 + n]:
        for ch in row.split():
            if ch in color_set:
                found = True
    return "#Color\n" if found else "#Black&White\n"


def _m_707a_include_gray(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    grid = ls[1 : 1 + n]
    is_color = any(ch in ("C", "M", "Y", "G") for row in grid for ch in row.split())
    return "#Color\n" if is_color else "#Black&White\n"


def _m_707a_always_bw(stdin: str) -> str:
    return "#Black&White\n"


def _g_707a(rng: random.Random) -> list[str]:
    cases = [
        "3 3\nW W W\nW W W\nW B B\n",
        "2 2\nC M\nY W\n",
        "1 1\nB\n",
    ]
    palette_bw = ["W", "B", "G"]
    palette_all = ["W", "B", "G", "C", "M", "Y"]
    for _ in range(9):
        n = rng.randint(1, 4)
        m = rng.randint(1, 4)
        palette = palette_all if rng.random() < 0.6 else palette_bw
        rows = []
        for _ in range(n):
            rows.append(" ".join(rng.choice(palette) for _ in range(m)))
        cases.append(f"{n} {m}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "707A",
        summary="n x m grid of pixel colors (C,M,Y,W,G,B). Output #Color if any C/M/Y present, else #Black&White.",
        samples=[{"input": "3 3\nW W W\nW W W\nW B B\n", "output": "#Black&White\n"}, {"input": "2 2\nC M\nY W\n", "output": "#Color\n"}],
        solve=_s_707a,
        alt=_a_707a,
        mutants={"include_gray": _m_707a_include_gray, "always_bw": _m_707a_always_bw},
        generate=_g_707a,
        checker="exact",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 959A Mahmoud and Ehab and the even-odd game
# ════════════════════════════════════════════════════════════════════════


def _s_959a(stdin: str) -> str:
    n = int(lines(stdin)[0])
    return ("Mahmoud\n" if n % 2 == 0 else "Ehab\n")


def _a_959a(stdin: str) -> str:
    n = int(lines(stdin)[0])
    return "Ehab\n" if n % 2 else "Mahmoud\n"


def _m_959a_flip(stdin: str) -> str:
    n = int(lines(stdin)[0])
    return "Ehab\n" if n % 2 == 0 else "Mahmoud\n"


def _m_959a_always_mahmoud(stdin: str) -> str:
    return "Mahmoud\n"


def _g_959a(rng: random.Random) -> list[str]:
    cases = ["1\n", "2\n", "3\n", "4\n"]
    for _ in range(8):
        cases.append(f"{rng.randint(1, 1000)}\n")
    return cases


SPECS.append(
    make_spec(
        "959A",
        summary="Mahmoud and Ehab alternately subtract an even (Mahmoud) or odd (Ehab) positive number from n, Mahmoud first, loser can't move. Winner is Mahmoud if n even, else Ehab.",
        samples=[{"input": "1\n", "output": "Ehab\n"}, {"input": "2\n", "output": "Mahmoud\n"}],
        solve=_s_959a,
        alt=_a_959a,
        mutants={"flip_parity": _m_959a_flip, "always_mahmoud": _m_959a_always_mahmoud},
        generate=_g_959a,
        checker="exact",
        family="games",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 433B Kuriyama Mirai's Stones
# ════════════════════════════════════════════════════════════════════════


def _s_433b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    v = list(map(int, ls[1].split()))
    m = int(ls[2])
    pre_orig = [0] * (n + 1)
    for i in range(n):
        pre_orig[i + 1] = pre_orig[i] + v[i]
    sv = sorted(v)
    pre_sorted = [0] * (n + 1)
    for i in range(n):
        pre_sorted[i + 1] = pre_sorted[i] + sv[i]
    out = []
    for k in range(3, 3 + m):
        typ, l, r = map(int, ls[k].split())
        if typ == 1:
            out.append(str(pre_orig[r] - pre_orig[l - 1]))
        else:
            out.append(str(pre_sorted[r] - pre_sorted[l - 1]))
    return "\n".join(out) + "\n"


def _a_433b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    v = list(map(int, ls[1].split()))
    m = int(ls[2])
    sv = sorted(v)

    def build_prefix(arr):
        acc = 0
        pref = [0]
        for x in arr:
            acc += x
            pref.append(acc)
        return pref

    p1 = build_prefix(v)
    p2 = build_prefix(sv)
    out = []
    for k in range(3, 3 + m):
        typ, l, r = map(int, ls[k].split())
        pref = p1 if typ == 1 else p2
        out.append(str(pref[r] - pref[l - 1]))
    return "\n".join(out) + "\n"


def _m_433b_swap_types(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    v = list(map(int, ls[1].split()))
    m = int(ls[2])
    pre_orig = [0] * (n + 1)
    for i in range(n):
        pre_orig[i + 1] = pre_orig[i] + v[i]
    sv = sorted(v)
    pre_sorted = [0] * (n + 1)
    for i in range(n):
        pre_sorted[i + 1] = pre_sorted[i] + sv[i]
    out = []
    for k in range(3, 3 + m):
        typ, l, r = map(int, ls[k].split())
        if typ == 2:
            out.append(str(pre_orig[r] - pre_orig[l - 1]))
        else:
            out.append(str(pre_sorted[r] - pre_sorted[l - 1]))
    return "\n".join(out) + "\n"


def _m_433b_off_by_one(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    v = list(map(int, ls[1].split()))
    m = int(ls[2])
    pre_orig = [0] * (n + 1)
    for i in range(n):
        pre_orig[i + 1] = pre_orig[i] + v[i]
    sv = sorted(v)
    pre_sorted = [0] * (n + 1)
    for i in range(n):
        pre_sorted[i + 1] = pre_sorted[i] + sv[i]
    out = []
    for k in range(3, 3 + m):
        typ, l, r = map(int, ls[k].split())
        if typ == 1:
            out.append(str(pre_orig[r] - pre_orig[l]))
        else:
            out.append(str(pre_sorted[r] - pre_sorted[l]))
    return "\n".join(out) + "\n"


def _g_433b(rng: random.Random) -> list[str]:
    cases = ["5\n1 2 3 4 5\n5\n1 2 4\n2 1 3\n1 1 5\n2 2 4\n1 3 3\n"]
    for _ in range(11):
        n = rng.randint(1, 10)
        v = _rand_ints(rng, n, 1, 50)
        m = rng.randint(1, 5)
        rows = [str(n), " ".join(map(str, v)), str(m)]
        for _ in range(m):
            typ = rng.choice([1, 2])
            l = rng.randint(1, n)
            r = rng.randint(l, n)
            rows.append(f"{typ} {l} {r}")
        cases.append("\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "433B",
        summary="Array v; m queries (type,l,r): type 1 sums v[l..r] in original order, type 2 sums the sorted array's v[l..r].",
        samples=[{"input": "5\n1 2 3 4 5\n5\n1 2 4\n2 1 3\n1 1 5\n2 2 4\n1 3 3\n", "output": "9\n6\n15\n9\n3\n"}],
        solve=_s_433b,
        alt=_a_433b,
        mutants={"swap_types": _m_433b_swap_types, "off_by_one": _m_433b_off_by_one},
        generate=_g_433b,
        checker="tokens",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1866A Ambitious Kid
# ════════════════════════════════════════════════════════════════════════


def _s_1866a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        out.append(str(min(abs(x) for x in arr)))
    return "\n".join(out) + "\n"


def _a_1866a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        best = None
        for x in arr:
            v = x if x >= 0 else -x
            if best is None or v < best:
                best = v
        out.append(str(best))
    return "\n".join(out) + "\n"


def _m_1866a_max(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        out.append(str(max(abs(x) for x in arr)))
    return "\n".join(out) + "\n"


def _m_1866a_first_element(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        out.append(str(abs(arr[0])))
    return "\n".join(out) + "\n"


def _g_1866a(rng: random.Random) -> list[str]:
    cases = ["2\n2\n5 -6\n3\n-1 -1 -1\n"]
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 8)
            arr = _rand_ints(rng, n, -20, 20)
            rows.append(f"{n}\n" + " ".join(map(str, arr)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1866A",
        summary="Minimum operations (increment or decrement one element by 1) to make the product of the array equal to zero.",
        samples=[{"input": "2\n2\n5 -6\n3\n-1 -1 -1\n", "output": "5\n1\n"}],
        solve=_s_1866a,
        alt=_a_1866a,
        mutants={"max_instead_of_min": _m_1866a_max, "first_element_only": _m_1866a_first_element},
        generate=_g_1866a,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1624B Make AP
# ════════════════════════════════════════════════════════════════════════


def _s_1624b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c = map(int, rows[i].split())
        ok = False
        new_a = 2 * b - c
        if new_a > 0 and new_a % a == 0:
            ok = True
        new_c = 2 * b - a
        if not ok and new_c > 0 and new_c % c == 0:
            ok = True
        if not ok and (a + c) % 2 == 0:
            new_b = (a + c) // 2
            if new_b > 0 and new_b % b == 0:
                ok = True
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _a_1624b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c = map(int, rows[i].split())
        options = []
        options.append(2 * b - c if (2 * b - c) > 0 and (2 * b - c) % a == 0 else None)
        options.append(2 * b - a if (2 * b - a) > 0 and (2 * b - a) % c == 0 else None)
        if (a + c) % 2 == 0:
            candidate = (a + c) // 2
            options.append(candidate if candidate > 0 and candidate % b == 0 else None)
        else:
            options.append(None)
        out.append("YES" if any(o is not None for o in options) else "NO")
    return "\n".join(out) + "\n"


def _m_1624b_only_b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c = map(int, rows[i].split())
        ok = False
        if (a + c) % 2 == 0:
            new_b = (a + c) // 2
            if new_b > 0 and new_b % b == 0:
                ok = True
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _m_1624b_wrong_bound(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c = map(int, rows[i].split())
        ok = False
        new_a = 2 * b - c
        if new_a >= 0 and new_a % a == 0:
            ok = True
        new_c = 2 * b - a
        if not ok and new_c >= 0 and new_c % c == 0:
            ok = True
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _g_1624b(rng: random.Random) -> list[str]:
    cases = [
        "11\n10 5 30\n30 5 10\n1 2 3\n1 6 3\n2 6 3\n1 1 1\n1 1 2\n1 1 3\n1 100000000 1\n2 1 1\n1 2 2\n"
    ]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = [f"{rng.randint(1, 30)} {rng.randint(1, 30)} {rng.randint(1, 30)}" for _ in range(t)]
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1624B",
        summary="Given positive a,b,c, may multiply exactly one of them by a positive integer m; can the (ordered) result be an arithmetic progression?",
        samples=[
            {
                "input": "11\n10 5 30\n30 5 10\n1 2 3\n1 6 3\n2 6 3\n1 1 1\n1 1 2\n1 1 3\n1 100000000 1\n2 1 1\n1 2 2\n",
                "output": "YES\nYES\nYES\nYES\nNO\nYES\nNO\nYES\nYES\nNO\nYES\n",
            }
        ],
        solve=_s_1624b,
        alt=_a_1624b,
        mutants={"only_change_b": _m_1624b_only_b, "wrong_bound_zero": _m_1624b_wrong_bound},
        generate=_g_1624b,
        checker="tokens_ci",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1426A Floor Number
# ════════════════════════════════════════════════════════════════════════


def _s_1426a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, x = map(int, rows[i].split())
        out.append(str(1 if n <= 2 else (n - 3) // x + 2))
    return "\n".join(out) + "\n"


def _a_1426a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, x = map(int, rows[i].split())
        if n <= 2:
            out.append("1")
            continue
        remaining = n - 2
        floor = 2 + (remaining - 1) // x
        out.append(str(floor))
    return "\n".join(out) + "\n"


def _m_1426a_no_special_case(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, x = map(int, rows[i].split())
        out.append(str((n - 1) // x + 1))
    return "\n".join(out) + "\n"


def _m_1426a_off_by_one(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, x = map(int, rows[i].split())
        out.append(str(1 if n <= 2 else (n - 3) // x + 3))
    return "\n".join(out) + "\n"


def _g_1426a(rng: random.Random) -> list[str]:
    cases = ["4\n7 3\n1 5\n22 5\n987 13\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = [f"{rng.randint(1, 1000)} {rng.randint(1, 100)}" for _ in range(t)]
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1426A",
        summary="Building: floor 1 has 2 apartments, every floor after has x apartments. Given apartment number n, find its floor.",
        samples=[{"input": "4\n7 3\n1 5\n22 5\n987 13\n", "output": "3\n1\n5\n77\n"}],
        solve=_s_1426a,
        alt=_a_1426a,
        mutants={"no_special_case": _m_1426a_no_special_case, "off_by_one": _m_1426a_off_by_one},
        generate=_g_1426a,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1814A Coins
# ════════════════════════════════════════════════════════════════════════


def _s_1814a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, k = map(int, rows[i].split())
        ok = (n % 2 == 0) or ((n - k) % 2 == 0)
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _a_1814a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, k = map(int, rows[i].split())
        possible = False
        if n % 2 == 0:
            possible = True
        elif n >= k and (n - k) % 2 == 0:
            possible = True
        out.append("YES" if possible else "NO")
    return "\n".join(out) + "\n"


def _m_1814a_only_even(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, k = map(int, rows[i].split())
        out.append("YES" if n % 2 == 0 else "NO")
    return "\n".join(out) + "\n"


def _m_1814a_wrong_parity(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        n, k = map(int, rows[i].split())
        ok = (n % 2 == 0) or ((n - k) % 2 == 1)
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _g_1814a(rng: random.Random) -> list[str]:
    cases = ["4\n5 3\n6 4\n2 2\n7 4\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 100)
            k = rng.randint(1, n)
            rows.append(f"{n} {k}")
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1814A",
        summary="Can n burles be paid using coins worth 2 and coins worth k (any nonnegative counts)?",
        samples=[{"input": "4\n5 3\n6 4\n2 2\n7 4\n", "output": "YES\nYES\nYES\nNO\n"}],
        solve=_s_1814a,
        alt=_a_1814a,
        mutants={"only_even": _m_1814a_only_even, "wrong_parity": _m_1814a_wrong_parity},
        generate=_g_1814a,
        checker="tokens_ci",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1373B 01 Game
# ════════════════════════════════════════════════════════════════════════


def _s_1373b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        c0 = s.count("0")
        c1 = s.count("1")
        out.append("DA" if min(c0, c1) % 2 == 1 else "NET")
    return "\n".join(out) + "\n"


def _a_1373b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        zeros = sum(1 for ch in s if ch == "0")
        ones = len(s) - zeros
        smaller = zeros if zeros < ones else ones
        out.append("DA" if smaller % 2 == 1 else "NET")
    return "\n".join(out) + "\n"


def _m_1373b_max(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        c0 = s.count("0")
        c1 = s.count("1")
        out.append("DA" if max(c0, c1) % 2 == 1 else "NET")
    return "\n".join(out) + "\n"


def _m_1373b_flip(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        c0 = s.count("0")
        c1 = s.count("1")
        out.append("NET" if min(c0, c1) % 2 == 1 else "DA")
    return "\n".join(out) + "\n"


def _g_1373b(rng: random.Random) -> list[str]:
    cases = ["3\n01\n1111\n0000\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            length = rng.randint(1, 12)
            rows.append("".join(rng.choice("01") for _ in range(length)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1373B",
        summary="Alice removes adjacent '01'/'10' pairs, Bob removes adjacent equal pairs, Alice first; both play optimally. Alice wins iff min(count('0'),count('1')) is odd.",
        samples=[{"input": "3\n01\n1111\n0000\n", "output": "DA\nNET\nNET\n"}],
        solve=_s_1373b,
        alt=_a_1373b,
        mutants={"use_max": _m_1373b_max, "flip_result": _m_1373b_flip},
        generate=_g_1373b,
        checker="tokens_ci",
        family="games",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1913B Swap and Delete
# ════════════════════════════════════════════════════════════════════════


def _s_1913b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        cnt = [0, 0]
        for ch in s:
            cnt[int(ch)] += 1
        ans = 0
        for i2 in range(len(s) + 1):
            if i2 == len(s) or cnt[1 - int(s[i2])] == 0:
                ans = len(s) - i2
                break
            cnt[1 - int(s[i2])] -= 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _a_1913b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        zeros = s.count("0")
        ones = s.count("1")
        result = 0
        for pos, ch in enumerate(s):
            if ch == "0":
                if ones == 0:
                    result = len(s) - pos
                    break
                ones -= 1
            else:
                if zeros == 0:
                    result = len(s) - pos
                    break
                zeros -= 1
        out.append(str(result))
    return "\n".join(out) + "\n"


def _m_1913b_same_char(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        cnt = [0, 0]
        for ch in s:
            cnt[int(ch)] += 1
        ans = 0
        for i2 in range(len(s) + 1):
            if i2 == len(s) or cnt[int(s[i2])] == 0:
                ans = len(s) - i2
                break
            cnt[int(s[i2])] -= 1
        out.append(str(ans))
    return "\n".join(out) + "\n"


def _m_1913b_length_minus(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        cnt = [0, 0]
        for ch in s:
            cnt[int(ch)] += 1
        m = min(cnt[0], cnt[1])
        out.append(str(len(s) - 2 * m))
    return "\n".join(out) + "\n"


def _g_1913b(rng: random.Random) -> list[str]:
    cases = ["4\n0\n011\n0101110001\n111100\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            length = rng.randint(1, 15)
            rows.append("".join(rng.choice("01") for _ in range(length)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1913B",
        summary="Binary string s; may freely permute (swap, free) and delete characters (cost 1 each). Min cost so every remaining position differs from original s at that index.",
        samples=[{"input": "4\n0\n011\n0101110001\n111100\n", "output": "1\n1\n0\n4\n"}],
        solve=_s_1913b,
        alt=_a_1913b,
        mutants={"needs_same_char": _m_1913b_same_char, "length_minus_twice_min": _m_1913b_length_minus},
        generate=_g_1913b,
        checker="exact",
        family="strings",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1915C Can I Square?
# ════════════════════════════════════════════════════════════════════════


def _s_1915c(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        total = sum(arr)
        root = int(total**0.5)
        while root * root > total:
            root -= 1
        while (root + 1) * (root + 1) <= total:
            root += 1
        out.append("YES" if root * root == total else "NO")
    return "\n".join(out) + "\n"


def _a_1915c(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        total = 0
        for x in arr:
            total += x
        lo, hi = 0, total + 1
        while lo < hi:
            mid = (lo + hi) // 2
            if mid * mid < total:
                lo = mid + 1
            else:
                hi = mid
        out.append("YES" if lo * lo == total else "NO")
    return "\n".join(out) + "\n"


def _m_1915c_sqrt_only(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        total = sum(arr)
        root = int(total**0.5)
        out.append("YES" if root * root == total else "NO")
    return "\n".join(out) + "\n"


def _m_1915c_count_not_sum(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        root = int(n**0.5)
        while root * root > n:
            root -= 1
        while (root + 1) * (root + 1) <= n:
            root += 1
        out.append("YES" if root * root == n else "NO")
    return "\n".join(out) + "\n"


def _g_1915c(rng: random.Random) -> list[str]:
    cases = ["3\n3\n1 1 1\n4\n1 1 1 2\n2\n1 1\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 20)
            arr = _rand_ints(rng, n, 1, 20)
            rows.append(f"{n}\n" + " ".join(map(str, arr)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1915C",
        summary="Given n unit squares (area 1 each), can their total area sum to a perfect square?",
        samples=[{"input": "3\n3\n1 1 1\n4\n1 1 1 2\n2\n1 1\n", "output": "YES\nYES\nNO\n"}],
        solve=_s_1915c,
        alt=_a_1915c,
        mutants={"float_sqrt_no_fix": _m_1915c_sqrt_only, "checks_count_not_sum": _m_1915c_count_not_sum},
        generate=_g_1915c,
        checker="tokens_ci",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1850C Word on the Paper
# ════════════════════════════════════════════════════════════════════════


def _s_1850c(stdin: str) -> str:
    ls = lines(stdin)
    grid = ls[:8]
    out_chars = []
    for row in grid:
        for ch in row:
            if ch != ".":
                out_chars.append(ch)
    return "".join(out_chars) + "\n"


def _a_1850c(stdin: str) -> str:
    ls = lines(stdin)
    grid = ls[:8]
    letters = []
    for r in range(8):
        for c in range(8):
            ch = grid[r][c]
            if ch != ".":
                letters.append(ch)
    return "".join(letters) + "\n"


def _m_1850c_reverse(stdin: str) -> str:
    ls = lines(stdin)
    grid = ls[:8]
    out_chars = []
    for row in grid:
        for ch in row:
            if ch != ".":
                out_chars.append(ch)
    return "".join(reversed(out_chars)) + "\n"


def _m_1850c_include_dots(stdin: str) -> str:
    ls = lines(stdin)
    grid = ls[:8]
    return "".join(grid) + "\n"


def _g_1850c(rng: random.Random) -> list[str]:
    cases = [
        ".......w\n.......o\n.......r\n.......d\n........\n........\n........\n........\n",
        "........\n........\n..h.....\n..e.....\n..l.....\n..l.....\n..o.....\n........\n",
    ]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(9):
        col = rng.randint(0, 7)
        length = rng.randint(1, 8)
        start = rng.randint(0, 8 - length)
        word = "".join(rng.choice(letters) for _ in range(length))
        grid = [["." for _ in range(8)] for _ in range(8)]
        for i, ch in enumerate(word):
            grid[start + i][col] = ch
        cases.append("\n".join("".join(row) for row in grid) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1850C",
        summary="8x8 grid with '.' everywhere except one vertical word in a single column; extract that word top-to-bottom.",
        samples=[
            {
                "input": ".......w\n.......o\n.......r\n.......d\n........\n........\n........\n........\n",
                "output": "word\n",
            }
        ],
        solve=_s_1850c,
        alt=_a_1850c,
        mutants={"reversed_word": _m_1850c_reverse, "includes_dots": _m_1850c_include_dots},
        generate=_g_1850c,
        checker="exact",
        family="strings",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1360B Honest Coach
# ════════════════════════════════════════════════════════════════════════


def _s_1360b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = sorted(map(int, ls[1].split()))
    best = min(a[i + 1] - a[i] for i in range(n - 1))
    return f"{best}\n"


def _a_1360b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    a.sort()
    diffs = [a[i] - a[i - 1] for i in range(1, n)]
    return f"{min(diffs)}\n"


def _m_1360b_unsorted(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    best = min(abs(a[i + 1] - a[i]) for i in range(n - 1))
    return f"{best}\n"


def _m_1360b_max_diff(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = sorted(map(int, ls[1].split()))
    best = max(a[i + 1] - a[i] for i in range(n - 1))
    return f"{best}\n"


def _g_1360b(rng: random.Random) -> list[str]:
    cases = ["3\n4\n7 1 3 5\n2\n1 2\n4\n1 1 1 1\n"]
    for _ in range(11):
        n = rng.randint(2, 12)
        a = _rand_ints(rng, n, 1, 50)
        cases.append(f"{n}\n" + " ".join(map(str, a)) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1360B",
        summary="Split athletes' strengths into two non-empty teams to minimize |max(team A) - min(team B)|.",
        samples=[{"input": "4\n7 1 3 5\n", "output": "2\n"}],
        solve=_s_1360b,
        alt=_a_1360b,
        mutants={"unsorted_diff": _m_1360b_unsorted, "max_instead_of_min": _m_1360b_max_diff},
        generate=_g_1360b,
        checker="exact",
        family="greedy",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1294A Collecting Coins
# ════════════════════════════════════════════════════════════════════════


def _s_1294a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        arr = sorted([a, b, c])
        total = arr[0] + arr[1] + arr[2] + n
        if total % 3 == 0 and total // 3 >= arr[2]:
            out.append("YES")
        else:
            out.append("NO")
    return "\n".join(out) + "\n"


def _a_1294a(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        hi = max(a, b, c)
        lo1 = min(a, b, c)
        mid = a + b + c - hi - lo1
        remaining = n - (2 * hi - mid - lo1)
        ok = remaining >= 0 and remaining % 3 == 0
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"


def _m_1294a_no_ge_check(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        total = a + b + c + n
        out.append("YES" if total % 3 == 0 else "NO")
    return "\n".join(out) + "\n"


def _m_1294a_wrong_mod(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        a, b, c, n = map(int, rows[i].split())
        arr = sorted([a, b, c])
        total = arr[0] + arr[1] + arr[2] + n
        if total % 3 == 0 and total // 3 >= arr[1]:
            out.append("YES")
        else:
            out.append("NO")
    return "\n".join(out) + "\n"


def _g_1294a(rng: random.Random) -> list[str]:
    cases = ["5\n0 2 0 0\n0 0 4 4\n1 2 3 2\n1 0 1 1\n0 0 0 100\n"]
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            a, b, c = rng.randint(0, 30), rng.randint(0, 30), rng.randint(0, 30)
            n = rng.randint(0, 100)
            rows.append(f"{a} {b} {c} {n}")
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1294A",
        summary="Sisters have a,b,c coins; n new coins arrive one at a time to any sister. Can all three end with equal coins?",
        samples=[{"input": "5\n0 2 0 0\n0 0 4 4\n1 2 3 2\n1 0 1 1\n0 0 0 100\n", "output": "NO\nYES\nYES\nNO\nYES\n"}],
        solve=_s_1294a,
        alt=_a_1294a,
        mutants={"no_ge_check": _m_1294a_no_ge_check, "wrong_mod_bound": _m_1294a_wrong_mod},
        generate=_g_1294a,
        checker="tokens_ci",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 2167B Your Name
# ════════════════════════════════════════════════════════════════════════


def _s_2167b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        s = rows[idx]
        tt = rows[idx + 1]
        idx += 2
        out.append("YES" if sorted(s) == sorted(tt) else "NO")
    return "\n".join(out) + "\n"


def _a_2167b(stdin: str) -> str:
    from collections import Counter

    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        s = rows[idx]
        tt = rows[idx + 1]
        idx += 2
        out.append("YES" if Counter(s) == Counter(tt) else "NO")
    return "\n".join(out) + "\n"


def _m_2167b_length_only(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        s = rows[idx]
        tt = rows[idx + 1]
        idx += 2
        out.append("YES" if len(s) == len(tt) else "NO")
    return "\n".join(out) + "\n"


def _m_2167b_exact_match(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        s = rows[idx]
        tt = rows[idx + 1]
        idx += 2
        out.append("YES" if s == tt else "NO")
    return "\n".join(out) + "\n"


def _g_2167b(rng: random.Random) -> list[str]:
    cases = ["3\nabc\nbca\nabc\nabd\naab\naba\n"]
    letters = "abc"
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 8)
            s = "".join(rng.choice(letters) for _ in range(n))
            if rng.random() < 0.5:
                perm = list(s)
                rng.shuffle(perm)
                tt = "".join(perm)
            else:
                tt = "".join(rng.choice(letters) for _ in range(n))
            rows.append(f"{s}\n{tt}")
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "2167B",
        summary="Can string s be rearranged (permuted) into string t? (same length, same multiset of characters)",
        samples=[{"input": "3\nabc\nbca\nabc\nabd\naab\naba\n", "output": "YES\nNO\nYES\n"}],
        solve=_s_2167b,
        alt=_a_2167b,
        mutants={"length_only": _m_2167b_length_only, "exact_match_required": _m_2167b_exact_match},
        generate=_g_2167b,
        checker="tokens_ci",
        family="strings",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 2009B osu!mania
# ════════════════════════════════════════════════════════════════════════


def _s_2009b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        grid_rows = rows[idx + 1 : idx + 1 + n]
        idx += 1 + n
        cols = []
        for row in reversed(grid_rows):
            cols.append(str(row.index("#") + 1))
        out.append(" ".join(cols))
    return "\n".join(out) + "\n"


def _a_2009b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        grid_rows = rows[idx + 1 : idx + 1 + n]
        idx += 1 + n
        result = []
        for r in range(n - 1, -1, -1):
            row = grid_rows[r]
            for c, ch in enumerate(row):
                if ch == "#":
                    result.append(str(c + 1))
                    break
        out.append(" ".join(result))
    return "\n".join(out) + "\n"


def _m_2009b_top_to_bottom(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        grid_rows = rows[idx + 1 : idx + 1 + n]
        idx += 1 + n
        cols = [str(row.index("#") + 1) for row in grid_rows]
        out.append(" ".join(cols))
    return "\n".join(out) + "\n"


def _m_2009b_zero_indexed(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n = int(rows[idx])
        grid_rows = rows[idx + 1 : idx + 1 + n]
        idx += 1 + n
        cols = []
        for row in reversed(grid_rows):
            cols.append(str(row.index("#")))
        out.append(" ".join(cols))
    return "\n".join(out) + "\n"


def _g_2009b(rng: random.Random) -> list[str]:
    cases = ["3\n4\n#...\n.#..\n..#.\n...#\n2\n.#..\n.#..\n1\n...#\n"]
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            n = rng.randint(1, 6)
            grid_rows = []
            for _ in range(n):
                pos = rng.randint(0, 3)
                grid_rows.append("".join("#" if c == pos else "." for c in range(4)))
            rows.append(f"{n}\n" + "\n".join(grid_rows))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "2009B",
        summary="n x 4 beatmap grid, exactly one '#' per row; output the column (1-indexed) of '#' for each row, processed bottom row first.",
        samples=[
            {
                "input": "3\n4\n#...\n.#..\n..#.\n...#\n2\n.#..\n.#..\n1\n...#\n",
                "output": "4 3 2 1\n2 2\n4\n",
            }
        ],
        solve=_s_2009b,
        alt=_a_2009b,
        mutants={"top_to_bottom_order": _m_2009b_top_to_bottom, "zero_indexed_column": _m_2009b_zero_indexed},
        generate=_g_2009b,
        checker="tokens",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1883C Raspberries
# ════════════════════════════════════════════════════════════════════════


def _raspberries_case(arr: list[int], k: int) -> int:
    md = 0
    even = 0
    div = False
    for x in arr:
        r = x % k
        if r:
            md = max(md, r)
        else:
            div = True
        if r == 2:
            even += 1
    if div:
        return 0
    if k == 4:
        if even >= 2:
            return 0
        if even >= 1 or md == 3:
            return 1
        return 2
    return k - md


def _s_1883c(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n, k = map(int, rows[idx].split())
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        out.append(str(_raspberries_case(arr, k)))
    return "\n".join(out) + "\n"


def _a_1883c(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n, k = map(int, rows[idx].split())
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        if any(x % k == 0 for x in arr):
            out.append("0")
            continue
        if k != 4:
            best_rem = max(x % k for x in arr)
            out.append(str(k - best_rem))
            continue
        twos = sum(1 for x in arr if x % 4 == 2)
        threes = any(x % 4 == 3 for x in arr)
        if twos >= 2:
            out.append("0")
        elif twos >= 1 or threes:
            out.append("1")
        else:
            out.append("2")
    return "\n".join(out) + "\n"


def _m_1883c_ignore_k4(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n, k = map(int, rows[idx].split())
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        if any(x % k == 0 for x in arr):
            out.append("0")
            continue
        best_rem = max(x % k for x in arr)
        out.append(str(k - best_rem))
    return "\n".join(out) + "\n"


def _m_1883c_no_divisible_check(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    idx = 0
    for _ in range(t):
        n, k = map(int, rows[idx].split())
        arr = list(map(int, rows[idx + 1].split()))
        idx += 2
        md = 0
        for x in arr:
            r = x % k
            if r > md:
                md = r
        if k == 4:
            even = sum(1 for x in arr if x % 4 == 2)
            if even >= 2:
                out.append("0")
            elif even >= 1 or md == 3:
                out.append("1")
            else:
                out.append("2")
        else:
            out.append(str(k - md))
    return "\n".join(out) + "\n"


def _g_1883c(rng: random.Random) -> list[str]:
    cases = [
        "15\n2 5\n7 3\n3 3\n7 4 1\n5 2\n9 7 7 3 9\n5 5\n5 4 1 2 3\n7 4\n9 5 1 5 9 5 1\n3 4\n6 3 6\n"
        "3 4\n6 1 5\n3 4\n1 5 9\n4 4\n1 4 1 1\n3 4\n3 5 3\n4 5\n8 9 9 3\n2 5\n1 6\n2 5\n10 10\n"
        "4 5\n1 6 1 1\n2 5\n7 7\n"
    ]
    for _ in range(11):
        t = rng.randint(1, 4)
        rows = []
        for _ in range(t):
            k = rng.randint(2, 5)
            n = rng.randint(2, 8)
            arr = _rand_ints(rng, n, 1, 10)
            rows.append(f"{n} {k}\n" + " ".join(map(str, arr)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1883C",
        summary="Array a (1<=a_i<=10), k in [2,5]; min number of +1 increments so the product of all elements is divisible by k.",
        samples=[
            {
                "input": (
                    "15\n2 5\n7 3\n3 3\n7 4 1\n5 2\n9 7 7 3 9\n5 5\n5 4 1 2 3\n7 4\n9 5 1 5 9 5 1\n3 4\n6 3 6\n"
                    "3 4\n6 1 5\n3 4\n1 5 9\n4 4\n1 4 1 1\n3 4\n3 5 3\n4 5\n8 9 9 3\n2 5\n1 6\n2 5\n10 10\n"
                    "4 5\n1 6 1 1\n2 5\n7 7\n"
                ),
                "output": "2\n2\n1\n0\n2\n0\n1\n2\n0\n1\n1\n4\n0\n4\n3\n",
            }
        ],
        solve=_s_1883c,
        alt=_a_1883c,
        mutants={"ignore_k4_special_case": _m_1883c_ignore_k4, "no_divisible_shortcut": _m_1883c_no_divisible_check},
        generate=_g_1883c,
        checker="tokens",
        family="math",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 1760B Atilla's Favorite Problem
# ════════════════════════════════════════════════════════════════════════


def _s_1760b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        out.append(str(max(ord(ch) - ord("a") + 1 for ch in s)))
    return "\n".join(out) + "\n"


def _a_1760b(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        mx_char = max(s)
        out.append(str(ord(mx_char) - ord("a") + 1))
    return "\n".join(out) + "\n"


def _m_1760b_min_char(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        out.append(str(min(ord(ch) - ord("a") + 1 for ch in s)))
    return "\n".join(out) + "\n"


def _m_1760b_zero_indexed(stdin: str) -> str:
    t, rows = _tcases(stdin)
    out = []
    for i in range(t):
        s = rows[i]
        out.append(str(max(ord(ch) - ord("a") for ch in s)))
    return "\n".join(out) + "\n"


def _g_1760b(rng: random.Random) -> list[str]:
    cases = ["4\na\nabc\naa\nabcd\n"]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(11):
        t = rng.randint(1, 5)
        rows = []
        for _ in range(t):
            length = rng.randint(1, 10)
            maxc = rng.randint(0, 12)
            rows.append("".join(rng.choice(letters[: maxc + 1]) for _ in range(length)))
        cases.append(f"{t}\n" + "\n".join(rows) + "\n")
    return cases


SPECS.append(
    make_spec(
        "1760B",
        summary="Given a lowercase string, find the minimum alphabet size (contiguous from 'a') needed to write it: 1 + index of the largest letter used.",
        samples=[{"input": "4\na\nabc\naa\nabcd\n", "output": "1\n3\n1\n4\n"}],
        solve=_s_1760b,
        alt=_a_1760b,
        mutants={"min_instead_of_max": _m_1760b_min_char, "zero_indexed": _m_1760b_zero_indexed},
        generate=_g_1760b,
        checker="exact",
        family="greedy",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 451B Sort the Array
# ════════════════════════════════════════════════════════════════════════


def _s_451b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    sorted_a = sorted(a)
    diffs = [i for i in range(n) if a[i] != sorted_a[i]]
    if not diffs:
        return "yes\n1 1\n"
    lo, hi = diffs[0], diffs[-1]
    candidate = a[:lo] + a[lo : hi + 1][::-1] + a[hi + 1 :]
    if candidate == sorted_a:
        return f"yes\n{lo + 1} {hi + 1}\n"
    return "no\n"


def _a_451b(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    sorted_a = sorted(a)
    l = 0
    while l < n and a[l] == sorted_a[l]:
        l += 1
    if l == n:
        return "yes\n1 1\n"
    r = n - 1
    while r >= 0 and a[r] == sorted_a[r]:
        r -= 1
    reversed_segment = a[l : r + 1]
    reversed_segment.reverse()
    new_arr = a[:l] + reversed_segment + a[r + 1 :]
    if new_arr == sorted_a:
        return f"yes\n{l + 1} {r + 1}\n"
    return "no\n"


def _m_451b_no_verify(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    sorted_a = sorted(a)
    diffs = [i for i in range(n) if a[i] != sorted_a[i]]
    if not diffs:
        return "yes\n1 1\n"
    lo, hi = diffs[0], diffs[-1]
    return f"yes\n{lo + 1} {hi + 1}\n"


def _m_451b_zero_indexed(stdin: str) -> str:
    ls = lines(stdin)
    n = int(ls[0])
    a = list(map(int, ls[1].split()))
    sorted_a = sorted(a)
    diffs = [i for i in range(n) if a[i] != sorted_a[i]]
    if not diffs:
        return "yes\n0 0\n"
    lo, hi = diffs[0], diffs[-1]
    candidate = a[:lo] + a[lo : hi + 1][::-1] + a[hi + 1 :]
    if candidate == sorted_a:
        return f"yes\n{lo} {hi}\n"
    return "no\n"


def _g_451b(rng: random.Random) -> list[str]:
    cases = ["3\n3 2 1\n", "4\n2 1 3 4\n", "4\n3 1 2 4\n", "2\n1 2\n"]
    for _ in range(9):
        n = rng.randint(1, 10)
        vals = rng.sample(range(1, 1000), n)
        if rng.random() < 0.5 and n >= 2:
            i = rng.randint(0, n - 2)
            j = rng.randint(i + 1, n - 1)
            vals.sort()
            vals[i : j + 1] = vals[i : j + 1][::-1]
        cases.append(f"{n}\n" + " ".join(map(str, vals)) + "\n")
    return cases


SPECS.append(
    make_spec(
        "451B",
        summary="Determine if array of distinct integers can be sorted by reversing exactly one contiguous segment; if so print 'yes' and the (canonical, maximal) 1-indexed segment bounds, else 'no'.",
        samples=[
            {"input": "3\n3 2 1\n", "output": "yes\n1 3\n"},
            {"input": "4\n3 1 2 4\n", "output": "no\n"},
            {"input": "2\n1 2\n", "output": "yes\n1 1\n"},
        ],
        solve=_s_451b,
        alt=_a_451b,
        mutants={"no_verify_after_reverse": _m_451b_no_verify, "zero_indexed_bug": _m_451b_zero_indexed},
        generate=_g_451b,
        checker="tokens_ci",
        family="sortings",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 379A New Year Candles
# ════════════════════════════════════════════════════════════════════════


def _s_379a(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    total_hours = a
    stubs = a
    while stubs >= b:
        new_candles = stubs // b
        total_hours += new_candles
        stubs = stubs % b + new_candles
    return f"{total_hours}\n"


def _a_379a(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    hours = 0
    leftover = 0
    burning = a
    while burning > 0:
        hours += burning
        leftover += burning
        burning = leftover // b
        leftover %= b
    return f"{hours}\n"


def _m_379a_no_leftover(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    total_hours = a
    stubs = a
    while stubs >= b:
        new_candles = stubs // b
        total_hours += new_candles
        stubs = new_candles
    return f"{total_hours}\n"


def _m_379a_off_by_one(stdin: str) -> str:
    ls = lines(stdin)
    a, b = map(int, ls[0].split())
    total_hours = a
    stubs = a
    while stubs >= b:
        new_candles = stubs // b
        total_hours += new_candles
        stubs = stubs % b + new_candles
    return f"{total_hours + 1}\n"


def _g_379a(rng: random.Random) -> list[str]:
    cases = ["4 2\n", "6 2\n", "1 2\n", "50 2\n"]
    for _ in range(8):
        a = rng.randint(1, 1000)
        b = rng.randint(2, 10)
        cases.append(f"{a} {b}\n")
    return cases


SPECS.append(
    make_spec(
        "379A",
        summary="a candles, each burns 1 hour leaving a stub; every b stubs can be combined into 1 new candle. Total hours of light.",
        samples=[{"input": "4 2\n", "output": "7\n"}, {"input": "6 2\n", "output": "11\n"}],
        solve=_s_379a,
        alt=_a_379a,
        mutants={"discards_leftover_stubs": _m_379a_no_leftover, "off_by_one": _m_379a_off_by_one},
        generate=_g_379a,
        checker="exact",
        family="implementation",
    )
)


# ════════════════════════════════════════════════════════════════════════
# 731A Night at the Museum
# ════════════════════════════════════════════════════════════════════════


def _s_731a(stdin: str) -> str:
    s = lines(stdin)[0]
    pos = 0
    total = 0
    for ch in s:
        target = ord(ch) - ord("a")
        diff = abs(target - pos)
        total += min(diff, 26 - diff)
        pos = target
    return f"{total}\n"


def _a_731a(stdin: str) -> str:
    s = lines(stdin)[0]
    seq = [0] + [ord(ch) - ord("a") for ch in s]
    total = 0
    for i in range(1, len(seq)):
        d = (seq[i] - seq[i - 1]) % 26
        total += min(d, 26 - d)
    return f"{total}\n"


def _m_731a_no_wrap(stdin: str) -> str:
    s = lines(stdin)[0]
    pos = 0
    total = 0
    for ch in s:
        target = ord(ch) - ord("a")
        total += abs(target - pos)
        pos = target
    return f"{total}\n"


def _m_731a_from_a_each_time(stdin: str) -> str:
    s = lines(stdin)[0]
    total = 0
    for ch in s:
        target = ord(ch) - ord("a")
        diff = abs(target - 0)
        total += min(diff, 26 - diff)
    return f"{total}\n"


def _g_731a(rng: random.Random) -> list[str]:
    cases = ["zeus\n", "map\n", "ares\n", "a\n", "z\n"]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(8):
        length = rng.randint(1, 15)
        cases.append("".join(rng.choice(letters) for _ in range(length)) + "\n")
    return cases


SPECS.append(
    make_spec(
        "731A",
        summary="Circular alphabet keyboard; starting from 'a', minimum rotations to type each next letter in the string.",
        samples=[{"input": "zeus\n", "output": "18\n"}, {"input": "map\n", "output": "35\n"}],
        solve=_s_731a,
        alt=_a_731a,
        mutants={"no_circular_wrap": _m_731a_no_wrap, "always_from_a": _m_731a_from_a_each_time},
        generate=_g_731a,
        checker="exact",
        family="strings",
    )
)

_KEEP = ['1535A', '2094A', '1360A', '1722B', '1877A', '1788A', '1669B', '2065A', '474A', '702A', '707A', '959A', '433B', '1866A', '1624B', '1426A', '1814A', '1373B', '1913B', '1850C', '2167B', '2009B', '1883C', '1760B', '451B', '379A', '731A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
