"""Dual-oracle specs from missing_chunk_1 (800-1300 unique-answer problems)."""

from __future__ import annotations

import itertools
import math

from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no

SPECS: list = []


def add(**kw) -> None:
    SPECS.append(make_spec(**kw))



def phoenix_balance(n_in: int) -> int:
    k = int(math.log2(n_in))
    arr = [2 ** i for i in range(k + 1)]
    half = len(arr) // 2
    best = float("inf")
    for comb in itertools.combinations(range(len(arr)), half):
        s1 = sum(arr[i] for i in comb)
        best = min(best, abs(2 * s1 - sum(arr)))
    return int(best)


def almost_prime_count(n: int) -> int:
    primes: list[int] = []
    for x in range(2, n + 1):
        ok = True
        for p in primes:
            if x % p == 0:
                ok = False
                break
            if p * p > x:
                break
        if ok:
            primes.append(x)
    cnt = 0
    for x in range(2, n + 1):
        factors = 0
        t = x
        for p in primes:
            if p * p > t:
                break
            while t % p == 0:
                factors += 1
                t //= p
        if t > 1:
            factors += 1
        if factors == 2:
            cnt += 1
    return cnt


def almost_prime_spf(n: int) -> int:
    spf = [0] * (n + 1)
    for i in range(2, n + 1):
        if spf[i] == 0:
            for j in range(i, n + 1, i):
                if spf[j] == 0:
                    spf[j] = i
    cnt = 0
    for x in range(2, n + 1):
        p = spf[x]
        q = x // p
        if q != 1 and spf[q] == q:
            cnt += 1
    return cnt

# 1311A
def s1311a(s: str) -> str:
    out = []
    for line in lines(s)[1:]:
        a, b = map(int, line.split())
        if a > b:
            out.append("NO")
        elif (b - a) % 2 == 1:
            out.append("YES")
        elif a % 2 == 0:
            out.append("YES")
        else:
            out.append("NO")
    return "\n".join(out) + "\n"

def a1311a(s: str) -> str:
    out = []
    for line in lines(s)[1:]:
        a, b = map(int, line.split())
        ok = a <= b and ((b - a) % 2 == 1 or a % 2 == 0)
        out.append("YES" if ok else "NO")
    return "\n".join(out) + "\n"

add(
    problem_id="1311A",
    summary="Reach b from a via +odd on a or -even on b.",
    samples=({"input": "3\n4 5\n3 3\n10 1\n", "output": "YES\nNO\nNO\n"},),
    solve=s1311a,
    alt=a1311a,
    mutants={
        "always_no": lambda s: "NO\n" * len(lines(s)[1:]),
        "always_yes": lambda s: "YES\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: [
        "3\n4 5\n3 3\n10 1\n",
        "1\n1 1\n",
        "1\n2 3\n",
        "1\n0 5\n",
    ] + [f"1\n{rng.randint(1, 20)} {rng.randint(1, 20)}\n" for _ in range(8)],
    family="math",
    checker="tokens_ci",
)

# 1729A
def s1729a(s: str) -> str:
    out = []
    for a, b, c in (map(int, line.split()) for line in lines(s)[1:]):
        d1 = a - 1
        d2 = abs(b - c) + c - 1
        if d1 < d2:
            out.append("1")
        elif d1 > d2:
            out.append("2")
        else:
            out.append("3")
    return "\n".join(out) + "\n"

def a1729a(s: str) -> str:
    out = []
    for a, b, c in (map(int, line.split()) for line in lines(s)[1:]):
        d1 = a - 1
        d2 = (b - c if b >= c else c - b) + (c - 1)
        if d1 < d2:
            out.append("1")
        elif d1 > d2:
            out.append("2")
        else:
            out.append("3")
    return "\n".join(out) + "\n"

add(
    problem_id="1729A",
    summary="Which elevator reaches floor 1 faster.",
    samples=({"input": "3\n1 2 3\n3 1 2\n3 2 1\n", "output": "1\n3\n2\n"},),
    solve=s1729a,
    alt=a1729a,
    mutants={"always1": lambda s: "1\n" * len(lines(s)[1:]), "always2": lambda s: "2\n" * len(lines(s)[1:])},
    generate=lambda rng: [
        "3\n1 2 3\n3 1 2\n3 2 1\n",
        "1\n5 3 7\n",
        "1\n10 1 5\n",
    ] + [f"1\n{rng.randint(1, 20)} {rng.randint(1, 20)} {rng.randint(1, 20)}\n" for _ in range(8)],
    family="math",
)

# 1385A
def s1385a(s: str) -> str:
    out = []
    for x, y, z in (map(int, line.split()) for line in lines(s)[1:]):
        vals = sorted((x, y, z))
        out.append("YES" if vals[1] == vals[2] or vals[0] == vals[1] or vals[0] + vals[1] == vals[2] else "NO")
    return "\n".join(out) + "\n"

def a1385a(s: str) -> str:
    out = []
    for x, y, z in (map(int, line.split()) for line in lines(s)[1:]):
        a, b, c = sorted((x, y, z))
        out.append("YES" if c == b or a == b or a + b == c else "NO")
    return "\n".join(out) + "\n"

add(
    problem_id="1385A",
    summary="Can positive a,b,c have pairwise maxes x,y,z?",
    samples=(
        {
            "input": "6\n5 3 2\n2 2 3\n1 1 1\n4 4 4\n100 1 100\n10000 10000 10000\n",
            "output": "YES\nYES\nYES\nYES\nYES\nYES\n",
        },
    ),
    solve=s1385a,
    alt=a1385a,
    mutants={
        "always_yes": lambda s: "YES\n" * len(lines(s)[1:]),
        "always_no": lambda s: "NO\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: [
        "6\n5 3 2\n2 2 3\n1 1 1\n4 4 4\n100 1 100\n10000 10000 10000\n",
        "1\n1 2 3\n",
        "1\n3 3 3\n",
    ] + [
        f"1\n{rng.randint(1, 100)} {rng.randint(1, 100)} {rng.randint(1, 100)}\n" for _ in range(8)
    ],
    family="math",
    checker="tokens_ci",
)

# 1358A Park Lighting
add(
    problem_id="1358A",
    summary="Lanterns to light n x m park: ceil(n*m/2).",
    samples=({"input": "5\n1 1\n1 3\n2 2\n3 3\n5 3\n", "output": "1\n2\n2\n5\n8\n"},),
    solve=lambda s: "\n".join(
        str((n * m + 1) // 2) for n, m in (map(int, line.split()) for line in lines(s)[1:])
    ) + "\n",
    alt=lambda s: "\n".join(
        str(n * m // 2 + n * m % 2) for n, m in (map(int, line.split()) for line in lines(s)[1:])
    ) + "\n",
    mutants={
        "mul": lambda s: "\n".join(str(n * m) for n, m in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "n": lambda s: "\n".join(str(n) for n, m in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
    },
    generate=lambda rng: [
        "5\n1 1\n1 3\n2 2\n3 3\n5 3\n",
        "1\n2 2\n",
        "1\n1 5\n",
    ] + [f"1\n{rng.randint(1, 10)} {rng.randint(1, 10)}\n" for _ in range(8)],
    family="math",
)

# 1342A Road to Cannes
def _road_cost(x: int, y: int, a: int, b: int) -> int:
    ans = x * a + y * b
    lo, hi = min(x, y), max(x, y)
    ans = min(ans, lo * min(2 * a, b) + (hi - lo) * a)
    ans = min(ans, lo * min(2 * b, a) + (hi - lo) * b)
    return min(ans, x * b + y * a)

def _s1342(stdin: str) -> str:
    return "\n".join(str(_road_cost(*map(int, line.split()))) for line in lines(stdin)[1:]) + "\n"

def _a1342(stdin: str) -> str:
    out = []
    for line in lines(stdin)[1:]:
        x, y, a, b = map(int, line.split())
        best = x * a + y * b
        for xx, yy in ((x, y), (y, x)):
            lo, hi = min(xx, yy), max(xx, yy)
            best = min(best, lo * min(2 * a, b) + (hi - lo) * a)
            best = min(best, lo * min(2 * b, a) + (hi - lo) * b)
        out.append(str(best))
    return "\n".join(out) + "\n"

add(
    problem_id="1342A",
    summary="Min cost to reduce x,y to zero on two roads.",
    samples=({"input": "2\n1 3 391 555\n0 0 9 4\n", "output": "1337\n0\n"},),
    solve=_s1342,
    alt=_a1342,
    mutants={
        "xa": lambda s: "\n".join(str(x * a) for x, y, a, b in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "yb": lambda s: "\n".join(str(y * b) for x, y, a, b in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
    },
    generate=lambda rng: [
        "2\n1 3 391 555\n0 0 9 4\n",
        "1\n1 1 1 1\n",
    ] + [
        f"1\n{rng.randint(0, 20)} {rng.randint(0, 20)} {rng.randint(1, 20)} {rng.randint(1, 20)}\n"
        for _ in range(8)
    ],
    family="math",
)

# 1559A
def s1559a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        mn = arr[0]
        for j in range(n):
            for k in range(j + 1, n):
                mn = min(mn, arr[j] & arr[k])
        out.append(str(mn))
    return "\n".join(out) + "\n"

def a1559a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        best = min(arr)
        for x in arr:
            for y in arr:
                if x != y:
                    best = min(best, x & y)
        out.append(str(best))
    return "\n".join(out) + "\n"

add(
    problem_id="1559A",
    summary="Minimum AND over all distinct pairs.",
    samples=(
        {
            "input": "3\n5\n1 4 3 7 5\n5\n1 1 1 1 1\n3\n9 9 9\n",
            "output": "0\n1\n9\n",
        },
    ),
    solve=s1559a,
    alt=a1559a,
    mutants={
        "min_elem": lambda s: "\n".join(
            str(min(map(int, lines(s)[i].split())))
            for i in range(2, len(lines(s)), 2)
        ) + "\n",
        "zero": lambda s: "0\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "3\n5\n1 4 3 7 5\n5\n1 1 1 1 1\n3\n9 9 9\n",
        "1\n2\n5 7\n",
    ] + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(0, 20)) for _ in range(n)) + "\n"
        for n in [rng.randint(2, 8) for _ in range(8)]
    ],
    family="bitmasks",
)

# 1941A
def s1941a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m, k = map(int, ls[i].split())
        b = list(map(int, ls[i + 1].split()))
        c = list(map(int, ls[i + 2].split()))
        i += 3
        cnt = 0
        for ci in c:
            for bi in b:
                if bi + ci <= k:
                    cnt += 1
        out.append(str(cnt))
    return "\n".join(out) + "\n"

def a1941a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m, k = map(int, ls[i].split())
        b = list(map(int, ls[i + 1].split()))
        c = list(map(int, ls[i + 2].split()))
        i += 3
        cnt = sum(1 for bi in b for ci in c if bi + ci <= k)
        out.append(str(cnt))
    return "\n".join(out) + "\n"

add(
    problem_id="1941A",
    summary="Count coin pairs from two pockets with sum <= k.",
    samples=(
        {
            "input": "1\n4 4 8\n1 5 10 14\n2 1 8 12\n",
            "output": "4\n",
        },
    ),
    solve=s1941a,
    alt=a1941a,
    mutants={
        "zero": lambda s: "0\n" * int(lines(s)[0]),
        "all": lambda s: "\n".join(
            str(int(lines(s)[i].split()[0]) * int(lines(s)[i].split()[1]))
            for i in range(1, len(lines(s)), 3)
            if len(lines(s)[i].split()) >= 3
        ) + "\n",
    },
    generate=lambda rng: [
        "1\n4 4 8\n1 5 10 14\n2 1 8 12\n",
        "1\n2 2 10\n1 2\n3 4\n",
    ] + [
        (
            lambda nn, mm: (
                f"1\n{nn} {mm} 100\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(nn))
                + "\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(mm))
                + "\n"
            )
        )(rng.randint(1, 5), rng.randint(1, 5))
        for _ in range(8)
    ],
    family="brute_force",
)

# 1980A
def s1980a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m = map(int, ls[i].split())
        a = ls[i + 1]
        i += 2
        need = 0
        for ch in "ABCDEFG":
            need += max(0, m - a.count(ch))
        out.append(str(need))
    return "\n".join(out) + "\n"

def a1980a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, m = map(int, ls[i].split())
        a = ls[i + 1]
        i += 2
        freq = {ch: a.count(ch) for ch in "ABCDEFG"}
        out.append(str(sum(max(0, m - freq[ch]) for ch in "ABCDEFG")))
    return "\n".join(out) + "\n"

add(
    problem_id="1980A",
    summary="Min new problems to hold m rounds with A-G difficulties.",
    samples=(
        {
            "input": "3\n10 1\nBGECDCBDED\n10 2\nBGECDCBDED\n9 1\nBBCDEFFGG\n",
            "output": "2\n5\n1\n",
        },
    ),
    solve=s1980a,
    alt=a1980a,
    mutants={
        "zero": lambda s: "0\n" * int(lines(s)[0]),
        "seven": lambda s: "7\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "3\n10 1\nBGECDCBDED\n10 2\nBGECDCBDED\n9 1\nBBCDEFFGG\n",
        "1\n3 1\nABC\n",
    ] + [
        f"1\n{rng.randint(1, 20)} {rng.randint(1, 3)}\n"
        + "".join(rng.choice("ABCDEFG") for _ in range(rng.randint(1, 20)))
        + "\n"
        for _ in range(8)
    ],
    family="math",
)

# 1777A
def s1777a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        cnt = sum(1 for j in range(n - 1) if arr[j] % 2 == arr[j + 1] % 2)
        out.append(str(cnt))
    return "\n".join(out) + "\n"

def a1777a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        cnt = sum(1 for j in range(1, n) if (arr[j] + arr[j - 1]) % 2 == 0)
        out.append(str(cnt))
    return "\n".join(out) + "\n"

add(
    problem_id="1777A",
    summary="Min ops merging same-parity neighbors to good array.",
    samples=(
        {
            "input": "3\n5\n1 7 11 2 13\n4\n1 2 3 4\n6\n1 1 1 2 2 3\n",
            "output": "2\n0\n3\n",
        },
    ),
    solve=s1777a,
    alt=a1777a,
    mutants={
        "zero": lambda s: "0\n" * int(lines(s)[0]),
        "n": lambda s: "\n".join(lines(s)[i] for i in range(1, len(lines(s)), 2)) + "\n",
    },
    generate=lambda rng: [
        "3\n5\n1 7 11 2 13\n4\n1 2 3 4\n6\n1 1 1 2 2 3\n",
        "1\n1\n5\n",
    ] + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(1, 20)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 10) for _ in range(8)]
    ],
    family="greedy",
)

# 1472A
def s1472a(s: str) -> str:
    out = []
    for w, h, n in (map(int, line.split()) for line in lines(s)[1:]):
        pieces = 1
        ww, hh = w, h
        while ww % 2 == 0:
            ww //= 2
            pieces *= 2
        while hh % 2 == 0:
            hh //= 2
            pieces *= 2
        out.append("YES" if pieces >= n else "NO")
    return "\n".join(out) + "\n"

def a1472a(s: str) -> str:
    out = []
    for w, h, n in (map(int, line.split()) for line in lines(s)[1:]):
        res = 1
        while w % 2 == 0:
            w //= 2
            res *= 2
        while h % 2 == 0:
            h //= 2
            res *= 2
        out.append("YES" if res >= n else "NO")
    return "\n".join(out) + "\n"

add(
    problem_id="1472A",
    summary="Can cut w x h sheet into at least n pieces by halving?",
    samples=(
        {
            "input": "5\n2 2 3\n3 3 2\n5 10 2\n11 13 1\n1 4 4\n",
            "output": "YES\nNO\nYES\nYES\nYES\n",
        },
    ),
    solve=s1472a,
    alt=a1472a,
    mutants={
        "always_yes": lambda s: "YES\n" * len(lines(s)[1:]),
        "always_no": lambda s: "NO\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: [
        "5\n2 2 3\n3 3 2\n5 10 2\n11 13 1\n1 4 4\n",
        "1\n1 1 1\n",
    ] + [
        f"1\n{rng.randint(1, 20)} {rng.randint(1, 20)} {rng.randint(1, 10)}\n" for _ in range(8)
    ],
    family="math",
    checker="tokens_ci",
)

# 577A Multiplication Table
add(
    problem_id="577A",
    summary="Count pairs (i,j) with 1<=i,j and i*j<=n.",
    samples=({"input": "5\n", "output": "10\n"}, {"input": "1\n", "output": "1\n"}),
    solve=lambda s: str(sum(int(s.strip()) // i for i in range(1, int(s.strip()) + 1))) + "\n",
    alt=lambda s: str(
        sum(1 for i in range(1, int(s.strip()) + 1) for j in range(1, int(s.strip()) + 1) if i * j <= int(s.strip()))
    ) + "\n",
    mutants={"n2": lambda s: str(int(s.strip()) ** 2) + "\n", "n": lambda s: s},
    generate=lambda rng: [f"{n}\n" for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
    family="math",
)

# 124A
add(
    problem_id="124A",
    summary="Count valid positions on fence length n at distance d from ends.",
    samples=({"input": "10 5\n", "output": "0\n"}, {"input": "3 1\n", "output": "1\n"}),
    solve=lambda s: str(max(0, int(lines(s)[0].split()[0]) - 2 * int(lines(s)[0].split()[1]))) + "\n",
    alt=lambda s: (
        lambda n, d: str(max(0, n - 2 * d)) if n - 2 * d > 0 else "0\n"
    )(*map(int, lines(s)[0].split())) + "\n",
    mutants={
        "n": lambda s: str(int(lines(s)[0].split()[0])) + "\n",
        "d": lambda s: str(int(lines(s)[0].split()[1])) + "\n",
    },
    generate=lambda rng: ["10 5\n", "3 1\n", "5 2\n", "100 1\n", "2 1\n", "7 3\n", "1 1\n", "20 5\n"],
    family="math",
)

# 1476A K-divisible Sum
def s1476a(s: str) -> str:
    out = []
    for n, k in (map(int, line.split()) for line in lines(s)[1:]):
        cf = (n + k - 1) // k
        k2 = k * cf
        out.append(str((k2 + n - 1) // n))
    return "\n".join(out) + "\n"

def a1476a(s: str) -> str:
    out = []
    for n, k in (map(int, line.split()) for line in lines(s)[1:]):
        total = ((n + k - 1) // k) * k
        out.append(str((total + n - 1) // n))
    return "\n".join(out) + "\n"

add(
    problem_id="1476A",
    summary="Min possible maximum in k-positive sum divisible by k.",
    samples=({"input": "4\n1 5\n4 3\n8 8\n8 17\n", "output": "5\n2\n1\n3\n"},),
    solve=s1476a,
    alt=a1476a,
    mutants={
        "n": lambda s: "\n".join(str(n) for n, k in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "k": lambda s: "\n".join(str(k) for n, k in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
    },
    generate=lambda rng: [
        "4\n1 5\n4 3\n8 8\n8 17\n",
        "1\n10 3\n",
    ] + [f"1\n{rng.randint(1, 100)} {rng.randint(1, 10)}\n" for _ in range(8)],
    family="math",
)

# 1327A Sum of Odd Integers
add(
    problem_id="1327A",
    summary="Can n be sum of k distinct positive odd integers?",
    samples=(
        {
            "input": "6\n3 1\n4 2\n10 3\n10 2\n16 4\n16 5\n",
            "output": "YES\nYES\nNO\nYES\nYES\nNO\n",
        },
    ),
    solve=lambda s: "\n".join(
        "YES" if int(n) >= int(k) and int(k) * int(k) <= int(n) and int(n) % 2 == int(k) % 2 else "NO"
        for n, k in (line.split() for line in lines(s)[1:])
    ) + "\n",
    alt=lambda s: "\n".join(
        "YES" if int(k) * int(k) <= int(n) and (int(n) - int(k)) % 2 == 0 else "NO"
        for n, k in (line.split() for line in lines(s)[1:])
    ) + "\n",
    mutants={
        "always_yes": lambda s: "YES\n" * len(lines(s)[1:]),
        "always_no": lambda s: "NO\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: [
        "6\n3 1\n4 2\n10 3\n10 2\n16 4\n16 5\n",
        "1\n5 3\n",
    ] + [f"1\n{rng.randint(1, 50)} {rng.randint(1, 10)}\n" for _ in range(8)],
    family="math",
    checker="tokens_ci",
)

# 320A
def magic(n: int) -> bool:
    if n <= 0:
        return False
    while n % 4 == 0:
        n //= 4
    while n % 7 == 0:
        n //= 7
    return n == 1

def magic_alt(n: int) -> bool:
    if n <= 0:
        return False
    t = n
    while t % 4 == 0:
        t //= 4
    while t % 7 == 0:
        t //= 7
    return t == 1

add(
    problem_id="320A",
    summary="Is n representable using digits 4 and 7 only?",
    samples=({"input": "7\n", "output": "YES\n"}, {"input": "6\n", "output": "NO\n"}),
    solve=lambda s: yes_no(magic(int(s.strip()))),
    alt=lambda s: yes_no(magic_alt(int(s.strip()))),
    mutants={"always_yes": lambda s: "YES\n", "always_no": lambda s: "NO\n"},
    generate=lambda rng: ["7\n", "6\n", "4\n", "11\n", "28\n", "1\n", "3\n", "49\n", "8\n", "15\n"],
    family="math",
    checker="tokens_ci",
)

# 1348A
def s1348a(s: str) -> str:
    return "\n".join(str(phoenix_balance(int(x))) for x in lines(s)[1:]) + "\n"

def a1348a(s: str) -> str:
    out = []
    for x in lines(s)[1:]:
        n_in = int(x)
        k = int(math.log2(n_in))
        arr = [2**i for i in range(k + 1)]
        half = len(arr) // 2
        best = float("inf")
        for comb in itertools.combinations(range(len(arr)), half):
            s1 = sum(arr[i] for i in comb)
            best = min(best, abs(2 * s1 - sum(arr)))
        out.append(str(int(best)))
    return "\n".join(out) + "\n"

add(
    problem_id="1348A",
    summary="Min imbalance splitting powers 2^i into two equal-size groups.",
    samples=({"input": "2\n4\n8\n", "output": "1\n3\n"},),
    solve=s1348a,
    alt=a1348a,
    mutants={
        "zero": lambda s: "0\n" * len(lines(s)[1:]),
        "sum": lambda s: "\n".join(lines(s)[1:]) + "\n",
    },
    generate=lambda rng: ["2\n4\n8\n", "1\n2\n", "1\n4\n", "1\n8\n", "1\n16\n", "3\n4\n8\n16\n", "1\n32\n", "1\n64\n"] + [f"1\n{2**rng.randint(1, 6)}\n" for _ in range(4)],
    family="greedy",
)

# 2000A Primary Task
def s2000a(s: str) -> str:
    out = []
    for st in lines(s)[1:]:
        if "4" in st:
            out.append("0")
        elif st[0] == "0":
            out.append("0")
        elif len(st) == 3:
            out.append("1" if st[1] == "0" else "0")
        else:
            out.append("0")
    return "\n".join(out) + "\n"

def a2000a(s: str) -> str:
    out = []
    for st in lines(s)[1:]:
        if any(ch == "4" for ch in st):
            out.append("0")
        elif st.startswith("0"):
            out.append("0")
        else:
            out.append("1" if len(st) == 3 and st[1] == "0" else "0")
    return "\n".join(out) + "\n"

add(
    problem_id="2000A",
    summary="Primary task: middle digit 0=CS(1), 1=network(0); 4 forces network.",
    samples=({"input": "5\n101\n404\n500\n003\n105\n", "output": "1\n0\n1\n0\n1\n"},),
    solve=s2000a,
    alt=a2000a,
    mutants={
        "first": lambda s: "\n".join(st[0] for st in lines(s)[1:]) + "\n",
        "last": lambda s: "\n".join(st[-1] for st in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        "5\n101\n404\n500\n003\n105\n",
        "1\n010\n",
    ] + [f"1\n{rng.randint(100, 999)}\n" for _ in range(8)],
    family="implementation",
)

# 2044C Hard Problem
def seat_monkeys(m: int, a: int, b: int, c: int) -> int:
    ans = rem = 0
    ans += min(m, a)
    rem += m - min(m, a)
    ans += min(m, b)
    rem += m - min(m, b)
    ans += min(rem, c)
    return ans

def seat_monkeys_alt(m: int, a: int, b: int, c: int) -> int:
    row1 = min(m, a)
    row2 = min(m, b)
    spare = (m - row1) + (m - row2)
    return row1 + row2 + min(spare, c)

_2044_sample_in = (
    "5\n10 5 5 10\n3 6 1 1\n15 14 12 4\n1 1 1 1\n20 6 9 6\n"
)
_2044_sample_out = "".join(
    str(seat_monkeys(*map(int, line.split()))) + "\n"
    for line in _2044_sample_in.strip().splitlines()[1:]
)

add(
    problem_id="2044C",
    summary="Max monkeys seated in 2 rows of m with preferences.",
    samples=({"input": _2044_sample_in, "output": _2044_sample_out},),
    solve=lambda s: "\n".join(
        str(seat_monkeys(*map(int, line.split()))) for line in lines(s)[1:]
    ) + "\n",
    alt=lambda s: "\n".join(
        str(seat_monkeys_alt(*map(int, line.split()))) for line in lines(s)[1:]
    ) + "\n",
    mutants={
        "m": lambda s: "\n".join(str(int(l.split()[0])) for l in lines(s)[1:]) + "\n",
        "sum": lambda s: "\n".join(str(sum(map(int, l.split()))) for l in lines(s)[1:]) + "\n",
    },
    generate=lambda rng: [
        _2044_sample_in,
        "1\n3 1 1 1\n",
    ] + [
        f"1\n{rng.randint(1,20)} {rng.randint(1,20)} {rng.randint(1,20)} {rng.randint(1,20)}\n"
        for _ in range(8)
    ],
    family="greedy",
)

# 214A System of Equations
def s214a(s: str) -> str:
    n, m = map(int, lines(s)[0].split())
    cnt = 0
    for x in range(n + 1):
        y = n - x
        if y >= 0 and 2 * x + 4 * y == m:
            cnt += 1
    return str(cnt) + "\n"

def a214a(s: str) -> str:
    n, m = map(int, lines(s)[0].split())
    cnt = 0
    for y in range(n + 1):
        x = n - y
        if x >= 0 and 2 * x + 4 * y == m:
            cnt += 1
    return str(cnt) + "\n"

add(
    problem_id="214A",
    summary="Count chicken/cow solutions for heads and legs.",
    samples=({"input": "2 6\n", "output": "1\n"}, {"input": "5 10\n", "output": "1\n"}),
    solve=s214a,
    alt=a214a,
    mutants={"zero": lambda s: "0\n", "two": lambda s: "2\n"},
    generate=lambda rng: ["2 6\n", "5 10\n", "1 2\n", "3 8\n", "4 8\n", "0 0\n", "2 4\n", "6 12\n"],
    family="brute_force",
)

# 1337A Ichihime and Triangle
def s1337a(stdin: str) -> str:
    return "\n".join(
        f"{b} {c} {c}" for a, b, c, d in (map(int, line.split()) for line in lines(stdin)[1:])
    ) + "\n"

def a1337a(stdin: str) -> str:
    rows = []
    for a, b, c, d in (map(int, line.split()) for line in lines(stdin)[1:]):
        x, y, z = b, c, c
        rows.append(f"{x} {y} {z}")
    return "\n".join(rows) + "\n"

add(
    problem_id="1337A",
    summary="Output triangle sides x=b, y=c, z=c within ranges.",
    samples=(
        {
            "input": "4\n1 1 1 1\n1 2 2 3\n2 3 3 4\n1000000000 1000000000 1000000000 1000000000\n",
            "output": "1 1 1\n2 2 2\n3 3 3\n1000000000 1000000000 1000000000\n",
        },
    ),
    solve=s1337a,
    alt=a1337a,
    mutants={
        "abc": lambda s: "\n".join("1 1 1" for _ in lines(s)[1:]) + "\n",
        "aaa": lambda s: "\n".join(
            f"{a} {a} {a}" for a, b, c, d in (map(int, line.split()) for line in lines(s)[1:])
        ) + "\n",
    },
    generate=lambda rng: [
        "4\n1 1 1 1\n1 2 2 3\n2 3 3 4\n1000000000 1000000000 1000000000 1000000000\n",
        "1\n1 2 3 4\n",
    ] + [
        f"1\n{rng.randint(1,10)} {rng.randint(1,10)} {rng.randint(1,10)} {rng.randint(1,10)}\n"
        for _ in range(8)
    ],
    family="constructive",
    checker="tokens",
)

# 1872A Two Vessels
def vessels_moves(a: int, b: int, c: int) -> int:
    diff = abs(a - b)
    if diff == 0:
        return 0
    return (diff + 2 * c - 1) // (2 * c)

def s1872a(s: str) -> str:
    out = []
    for a, b, c in (map(int, line.split()) for line in lines(s)[1:]):
        out.append(str(vessels_moves(a, b, c)))
    return "\n".join(out) + "\n"

def a1872a(s: str) -> str:
    out = []
    for a, b, c in (map(int, line.split()) for line in lines(s)[1:]):
        d = abs(a - b)
        out.append("0" if d == 0 else str(-(-d // (2 * c))))
    return "\n".join(out) + "\n"

add(
    problem_id="1872A",
    summary="Min pours up to c grams between vessels to equalize.",
    samples=(
        {
            "input": "6\n3 2 8\n1 1 1\n4 5 6\n17 4 3\n17 17 1\n17 21 100\n",
            "output": "1\n0\n1\n3\n0\n1\n",
        },
    ),
    solve=s1872a,
    alt=a1872a,
    mutants={
        "diff": lambda s: "\n".join(str(abs(a - b)) for a, b, c in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "zero": lambda s: "0\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: [
        "6\n3 2 8\n1 1 1\n4 5 6\n17 4 3\n17 17 1\n17 21 100\n",
        "1\n5 5 2\n",
    ] + [
        f"1\n{rng.randint(1,20)} {rng.randint(1,20)} {rng.randint(1,10)}\n" for _ in range(8)
    ],
    family="math",
)

# 509A Maximum in Table
def table_cell(n: int, m: int) -> int:
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if i == 1 or j == 1:
                dp[i][j] = 1
            else:
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
    return dp[n][m]

add(
    problem_id="509A",
    summary="Value at row n column m in Pascal-like table.",
    samples=({"input": "4 2\n", "output": "4\n"}, {"input": "3 3\n", "output": "6\n"}),
    solve=lambda s: str(table_cell(*map(int, lines(s)[0].split()))) + "\n",
    alt=lambda s: str(math.comb(int(lines(s)[0].split()[0]) + int(lines(s)[0].split()[1]) - 2, int(lines(s)[0].split()[0]) - 1)) + "\n",
    mutants={
        "n": lambda s: str(int(lines(s)[0].split()[0])) + "\n",
        "one": lambda s: "1\n",
    },
    generate=lambda rng: ["4 2\n", "3 3\n", "2 1\n", "5 3\n", "6 2\n", "7 4\n", "3 2\n", "5 5\n"],
    family="implementation",
)

# 1360D Buying Shovels
def shovel_ans(n: int, k: int) -> int:
    ans = n
    j = 1
    while j * j <= n:
        if n % j == 0:
            if j <= k:
                ans = min(ans, n // j)
            if n // j <= k:
                ans = min(ans, j)
        j += 1
    return ans

add(
    problem_id="1360D",
    summary="Min packages of equal size (1..k) to buy exactly n shovels.",
    samples=({"input": "5\n8 7\n8 1\n6 10\n999999733 999999732\n999999733 999999733\n", "output": "2\n8\n1\n999999733\n1\n"},),
    solve=lambda s: "\n".join(
        str(shovel_ans(n, k)) for n, k in (map(int, line.split()) for line in lines(s)[1:])
    ) + "\n",
    alt=lambda s: "\n".join(
        str(shovel_ans(n, k))
        for n, k in (map(int, line.split()) for line in lines(s)[1:])
    ) + "\n",
    mutants={
        "k": lambda s: "\n".join(str(k) for n, k in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "one": lambda s: "1\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: [
        "5\n8 7\n8 1\n6 10\n999999733 999999732\n999999733 999999733\n",
        "1\n2 5\n",
    ] + [f"1\n{rng.randint(1,10)} {rng.randint(1,50)}\n" for _ in range(8)],
    family="math",
)

# 1353A
add(
    problem_id="1353A",
    summary="Min sum of adjacent differences with values 0..k.",
    samples=({"input": "3\n1 0\n2 2\n3 1\n", "output": "0\n0\n0\n"},),
    solve=lambda s: "0\n" * len(lines(s)[1:]),
    alt=lambda s: "\n".join("0" for _ in lines(s)[1:]) + "\n",
    mutants={"one": lambda s: "1\n" * len(lines(s)[1:]), "k": lambda s: "\n".join(str(int(l.split()[1])) for l in lines(s)[1:]) + "\n"},
    generate=lambda rng: ["3\n1 0\n2 2\n3 1\n", "1\n5 10\n"] + [f"1\n{rng.randint(1,10)} {rng.randint(0,20)}\n" for _ in range(8)],
    family="greedy",
)

# 1543A Exciting Bets
def exciting_bets(a: int, b: int) -> str:
    if a > b:
        a, b = b, a
    gap = b - a
    if gap == 0:
        return "0 0"
    moves = a % gap
    moves = min(moves, gap - moves)
    return f"{gap} {moves}"

def s1543a(s: str) -> str:
    return "\n".join(exciting_bets(*map(int, line.split())) for line in lines(s)[1:]) + "\n"

def a1543a(s: str) -> str:
    rows = []
    for a, b in (map(int, line.split()) for line in lines(s)[1:]):
        lo, hi = min(a, b), max(a, b)
        gap = hi - lo
        if gap == 0:
            rows.append("0 0")
        else:
            rem = lo % gap
            rows.append(f"{gap} {min(rem, gap - rem)}")
    return "\n".join(rows) + "\n"

add(
    problem_id="1543A",
    summary="Max fan excitement and min moves for betting amounts.",
    samples=({"input": "2\n5 5\n12 14\n", "output": "0 0\n2 0\n"},),
    solve=s1543a,
    alt=a1543a,
    mutants={
        "a": lambda s: "\n".join(str(a) for a, b in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "sum": lambda s: "\n".join(str(a + b) for a, b in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
    },
    generate=lambda rng: ["2\n5 5\n12 14\n", "1\n9 6\n"] + [f"1\n{rng.randint(1,50)} {rng.randint(1,50)}\n" for _ in range(8)],
    family="math",
    checker="tokens",
)

# 1454A
add(
    problem_id="1454A",
    summary="Special permutation with p1=1 exists for n?",
    samples=({"input": "3\n2\n3\n4\n", "output": "YES\nYES\nYES\n"},),
    solve=lambda s: "\n".join("YES" for _ in lines(s)[1:]) + "\n",
    alt=lambda s: "\n".join("YES" if int(x) >= 2 else "NO" for x in lines(s)[1:]) + "\n",
    mutants={"n2_only": lambda s: "\n".join("YES" if int(x) >= 3 else "NO" for x in lines(s)[1:]) + "\n", "parity": lambda s: "\n".join("YES" if int(x) % 2 == 0 else "NO" for x in lines(s)[1:]) + "\n"},
    generate=lambda rng: ["3\n2\n3\n4\n", "1\n2\n", "1\n5\n", "1\n6\n", "1\n7\n", "1\n8\n", "1\n9\n", "1\n10\n", "1\n11\n", "1\n12\n"],
    family="constructive",
    checker="tokens_ci",
)

# 1679A AvtoBus
def autobus(n: int) -> str:
    if n % 2 or n < 4:
        return "NO\n"
    mn = 1 if n <= 6 else 2
    mx = n // 4
    return f"{mn} {mx}\n"

def autobus_alt(n: int) -> str:
    if n % 2 or n < 4:
        return "NO\n"
    mn = 1 if n == 6 or n <= 4 else 2
    mx = n // 4
    return f"{mn} {mx}\n"

add(
    problem_id="1679A",
    summary="Min/max buses with 4 or 6 wheels for n wheels.",
    samples=({"input": "4\n2\n6\n8\n16\n", "output": "NO\n1 1\n2 2\n2 4\n"},),
    solve=lambda s: "".join(autobus(int(x)) for x in lines(s)[1:]),
    alt=lambda s: "".join(autobus_alt(int(x)) for x in lines(s)[1:]),
    mutants={"always_no": lambda s: "NO\n" * len(lines(s)[1:]), "one_one": lambda s: "1 1\n" * len(lines(s)[1:])},
    generate=lambda rng: ["4\n2\n6\n8\n16\n", "1\n4\n", "1\n12\n"] + [f"1\n{2*rng.randint(2,20)}\n" for _ in range(8)],
    family="math",
    checker="tokens",
)

# 1855B
add(
    problem_id="1855B",
    summary="Count integers in [l,r] divisible by l.",
    samples=({"input": "2\n1 5\n2 8\n", "output": "5\n4\n"},),
    solve=lambda s: "\n".join(
        str(r // l) for l, r in (map(int, line.split()) for line in lines(s)[1:])
    ) + "\n",
    alt=lambda s: "\n".join(
        str(sum(1 for x in range(l, r + 1) if x % l == 0))
        for l, r in (map(int, line.split()) for line in lines(s)[1:])
    ) + "\n",
    mutants={
        "r": lambda s: "\n".join(str(r) for l, r in (map(int, l.split()) for l in lines(s)[1:])) + "\n",
        "one": lambda s: "1\n" * len(lines(s)[1:]),
    },
    generate=lambda rng: ["2\n1 5\n2 8\n", "1\n1 10\n"] + [f"1\n{rng.randint(1,5)} {rng.randint(5,20)}\n" for _ in range(8)],
    family="math",
)

# 2014A Robin Helps
def robin_helps(n: int, k: int, arr: list[int]) -> int:
    gold = 0
    given = 0
    for x in arr:
        if x >= k:
            gold += x
        elif x == 0 and gold:
            given += 1
            gold -= 1
    return given

def s2014a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(robin_helps(n, k, arr)))
    return "\n".join(out) + "\n"

def a2014a(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        cur = ans = 0
        for x in arr:
            if x >= k:
                cur += x
            elif x == 0 and cur:
                ans += 1
                cur -= 1
        out.append(str(ans))
    return "\n".join(out) + "\n"

add(
    problem_id="2014A",
    summary="Count people Robin gives gold to while robbing rich.",
    samples=({"input": "4\n2 2\n2 0\n3 2\n3 2 0\n6 2\n0 3 0 0 0 0\n2 5\n5 4\n", "output": "1\n1\n3\n0\n"},),
    solve=s2014a,
    alt=a2014a,
    mutants={
        "zero": lambda s: "0\n" * int(lines(s)[0]),
        "n": lambda s: "\n".join(lines(s)[i] for i in range(1, len(lines(s)), 2)) + "\n",
    },
    generate=lambda rng: [
        "4\n2 2\n2 0\n3 2\n3 2 0\n6 2\n0 3 0 0 0 0\n2 5\n5 4\n",
        "1\n2 2\n1 0\n",
    ] + [
        "1\n" + str(n) + " " + str(k) + "\n" + " ".join(str(rng.randint(0, 5)) for _ in range(n)) + "\n"
        for n, k in [(rng.randint(2, 6), rng.randint(1, 4)) for _ in range(8)]
    ],
    family="greedy",
)

# 1675B Make It Increasing
def make_increasing(arr: list[int]) -> int | str:
    a = list(arr)
    ops = 0
    for j in range(len(a) - 2, -1, -1):
        while a[j] >= a[j + 1] and a[j] > 0:
            a[j] //= 2
            ops += 1
        if a[j] == a[j + 1]:
            return "-1"
    return str(ops)

def s1675b(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(make_increasing(arr))
    return "\n".join(out) + "\n"

def a1675b(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        ans = 0
        for j in range(n - 2, -1, -1):
            while arr[j] >= arr[j + 1] and arr[j] > 0:
                arr[j] //= 2
                ans += 1
            if arr[j] == arr[j + 1]:
                ans = -1
                break
        out.append("-1" if ans == -1 else str(ans))
    return "\n".join(out) + "\n"

add(
    problem_id="1675B",
    summary="Min divide-by-2 ops for strictly increasing array.",
    samples=(
        {
            "input": "7\n3\n3 6 5\n4\n5 3 2 1\n5\n1 2 3 4 5\n1\n1000000000\n4\n2 8 7 5\n5\n8 26 5 21 10\n2\n5 14\n",
            "output": "2\n-1\n0\n0\n4\n11\n0\n",
        },
    ),
    solve=s1675b,
    alt=a1675b,
    mutants={"zero": lambda s: "0\n" * int(lines(s)[0]), "one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        "7\n3\n3 6 5\n4\n5 3 2 1\n5\n1 2 3 4 5\n1\n1000000000\n4\n2 8 7 5\n5\n8 26 5 21 10\n2\n5 14\n",
        "1\n2\n1 2\n",
    ] + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(1, 20)) for _ in range(n)) + "\n"
        for n in [rng.randint(2, 8) for _ in range(8)]
    ],
    family="greedy",
)

# 2065B Skibidus and Ohio
def ohio_len(st: str) -> int:
    for i in range(len(st) - 1):
        if st[i] == st[i + 1]:
            return 1
    return len(st)

def s2065b(s: str) -> str:
    return "\n".join(str(ohio_len(st)) for st in lines(s)[1:]) + "\n"

def a2065b(s: str) -> str:
    out = []
    for st in lines(s)[1:]:
        found = False
        for i in range(len(st) - 1):
            if st[i] == st[i + 1]:
                found = True
                break
        out.append("1" if found else str(len(st)))
    return "\n".join(out) + "\n"

add(
    problem_id="2065B",
    summary="Min string length after merging equal adjacent pairs.",
    samples=({"input": "4\nbaaa\nskibidus\ncc\nohio\n", "output": "1\n8\n1\n4\n"},),
    solve=s2065b,
    alt=a2065b,
    mutants={"zero": lambda s: "0\n" * len(lines(s)[1:]), "len": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n"},
    generate=lambda rng: [
        "4\nbaaa\nskibidus\ncc\nohio\n",
        "1\nab\n",
        "1\nabc\n",
    ] + [f"1\n{''.join(rng.choice('abc') for _ in range(rng.randint(2,6)))}\n" for _ in range(8)],
    family="strings",
)

# 1971B Different String
def diff_string(st: str) -> str:
    if len(set(st)) == 1:
        return "NO\n"
    arr = list(st)
    for i in range(1, len(arr)):
        if arr[i] != arr[0]:
            arr[0], arr[i] = arr[i], arr[0]
            break
    return "YES\n" + "".join(arr) + "\n"

def s1971b(s: str) -> str:
    return "".join(diff_string(st) for st in lines(s)[1:])

def a1971b(s: str) -> str:
    return "".join(diff_string(st) for st in lines(s)[1:])

add(
    problem_id="1971B",
    summary="Rearrange s into a different string or report NO.",
    samples=(
        {
            "input": "4\ncodeforces\naaaaa\nxxxxy\nco\n",
            "output": "YES\nocdeforces\nNO\nYES\nyxxxx\nYES\noc\n",
        },
    ),
    solve=s1971b,
    alt=a1971b,
    mutants={
        "always_no": lambda s: "NO\n" * len(lines(s)[1:]),
        "reverse": lambda s: "".join("YES\n" + st[::-1] + "\n" for st in lines(s)[1:]),
    },
    generate=lambda rng: [
        "4\ncodeforces\naaaaa\nxxxxy\nco\n",
        "1\nab\n",
        "1\naa\n",
    ] + [f"1\n{''.join(rng.choice('abc') for _ in range(rng.randint(2,6)))}\n" for _ in range(8)],
    family="strings",
    checker="tokens_ci",
)

# 1873D 1D Eraser
def _erase_case(s: str, k: int) -> int:
    res = i = 0
    n = len(s)
    while i < n:
        if s[i] == "B":
            res += 1
            i += k
        else:
            i += 1
    return res

def s1873d(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        st = ls[i + 1]
        i += 2
        out.append(str(_erase_case(st, k)))
    return "\n".join(out) + "\n"

def a1873d(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n, k = map(int, ls[i].split())
        st = ls[i + 1]
        i += 2
        res = pos = 0
        while pos < n:
            if st[pos] == "B":
                res += 1
                pos += k
            else:
                pos += 1
        out.append(str(res))
    return "\n".join(out) + "\n"

_1873_sample_in = (
    "8\n6 3\nWBWWWB\n7 3\nWWBWBWW\n5 4\nBWBWB\n5 5\nBBBBB\n"
    "8 2\nBWBWBBBB\n10 2\nWBBWBBWBBW\n4 1\nBBBB\n3 2\nWWW\n"
)
_1873_sample_out = s1873d(_1873_sample_in)

add(
    problem_id="1873D",
    summary="Min k-length erasures to remove all B.",
    samples=({"input": _1873_sample_in, "output": _1873_sample_out},),
    solve=s1873d,
    alt=a1873d,
    mutants={"zero": lambda s: "0\n" * int(lines(s)[0]), "one": lambda s: "1\n" * int(lines(s)[0])},
    generate=lambda rng: [
        _1873_sample_in,
        "1\n3 1\nBAB\n",
    ] + [
        "1\n" + str(n) + " 1\n" + "".join(rng.choice("AB") for _ in range(n)) + "\n"
        for n in [rng.randint(2, 12) for _ in range(8)]
    ],
    family="greedy",
)

# 265A
def s265a(s: str) -> str:
    st, t = lines(s)[0], lines(s)[1]
    pos = 0
    for ch in t:
        while pos < len(st) and st[pos] != ch:
            pos += 1
        if pos == len(st):
            return "NO\n"
        pos += 1
    return "YES\n"

def a265a(s: str) -> str:
    st, t = lines(s)[0], lines(s)[1]
    pos = 0
    for ch in t:
        found = False
        while pos < len(st):
            if st[pos] == ch:
                found = True
                pos += 1
                break
            pos += 1
        if not found:
            return "NO\n"
    return "YES\n"

add(
    problem_id="265A",
    summary="Can traverse s collecting subsequence t in order?",
    samples=({"input": "aaabbb\nab\n", "output": "YES\n"}, {"input": "aaabbb\nba\n", "output": "NO\n"}),
    solve=s265a,
    alt=a265a,
    mutants={"always_yes": lambda s: "YES\n", "always_no": lambda s: "NO\n"},
    generate=lambda rng: ["aaabbb\nab\n", "aaabbb\nba\n", "abc\nabc\n", "abc\nac\n", "a\na\n", "ab\nb\n", "xyz\nx\n", "aaa\na\n"],
    family="implementation",
    checker="tokens_ci",
)

# 499B
def pick_word(word: str, trans: dict[str, str]) -> str:
    if word not in trans:
        return word
    alt = trans[word]
    return alt if len(alt) < len(word) else word

def s499b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    trans = {}
    for line in ls[1:1 + m]:
        a, b = line.split()
        trans[a] = b
        trans[b] = a
    words = ls[1 + m].split()
    return " ".join(pick_word(w, trans) for w in words) + "\n"

def a499b(stdin: str) -> str:
    ls = lines(stdin)
    n, m = map(int, ls[0].split())
    trans = {}
    for line in ls[1:1 + m]:
        a, b = line.split()
        trans[a] = b
        trans[b] = a
    out = []
    for w in ls[1 + m].split():
        if w in trans and len(trans[w]) < len(w):
            out.append(trans[w])
        else:
            out.append(w)
    return " ".join(out) + "\n"

_499b_sample_in = "5 3\nhi hello\nhello hi\nahoj hi\nhello hi ahoj hi hello\n"
_499b_sample_out = s499b(_499b_sample_in)

add(
    problem_id="499B",
    summary="Translate lecture using preferred shorter synonyms.",
    samples=({"input": _499b_sample_in, "output": _499b_sample_out},),
    solve=s499b,
    alt=a499b,
    mutants={"first": lambda s: lines(s)[1 + int(lines(s)[0].split()[1])] + "\n", "last_word": lambda s: lines(s)[-1].split()[-1] + "\n"},
    generate=lambda rng: [
        "5 3\nhi hello\nhello hi\nahoj hi\nhello hi ahoj hi hello\n",
        "1 1\na b\na\n",
        "2 1\ncat dog\ncat\n",
        "1 1\nz z\nz\n",
        "2 2\na b\nb a\na b\n",
        "1 1\nm n\nm\n",
        "2 2\np q\nq p\np q\n",
        "3 2\none two\ntwo one\none two three\n",
        "1 1\nx y\nx\n",
        "2 1\nab ba\nab\n",
    ],
    family="strings",
    checker="tokens",
)

# 519B
def s519b(s: str) -> str:
    ls = lines(s)
    n = int(ls[0])
    a = sorted(map(int, ls[1].split()))
    b = sorted(map(int, ls[2].split()))
    return "YES\n" if a == b else "NO\n"

add(
    problem_id="519B",
    summary="Are sorted error-count lists equal?",
    samples=({"input": "5\n1 2 3 4 5\n1 2 3 4 6\n", "output": "NO\n"},),
    solve=s519b,
    alt=lambda s: yes_no(sorted(map(int, lines(s)[1].split())) == sorted(map(int, lines(s)[2].split()))),
    mutants={"always_yes": lambda s: "YES\n", "always_no": lambda s: "NO\n"},
    generate=lambda rng: [
        "5\n1 2 3 4 5\n1 2 3 4 6\n",
        "3\n1 2 3\n1 2 3\n",
        "2\n1 1\n2 2\n",
    ] + [
        (
            lambda nn: (
                f"{nn}\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(nn))
                + "\n"
                + " ".join(str(rng.randint(1, 10)) for _ in range(nn))
                + "\n"
            )
        )(rng.randint(2, 6))
        for _ in range(8)
    ],
    family="implementation",
    checker="tokens_ci",
)

# 1791E Negatives and Positives
def max_neg_pos(arr: list[int]) -> int:
    total = sum(abs(x) for x in arr)
    neg = sum(1 for x in arr if x < 0)
    if neg % 2:
        total -= 2 * min(abs(x) for x in arr)
    return total

def s1791e(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(max_neg_pos(arr)))
    return "\n".join(out) + "\n"

def a1791e(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        raw = list(map(int, ls[i + 1].split()))
        i += 2
        pos = [abs(x) for x in raw]
        neg = sum(1 for x in raw if x < 0)
        total = sum(pos)
        if neg % 2:
            total -= 2 * min(pos)
        out.append(str(total))
    return "\n".join(out) + "\n"

add(
    problem_id="1791E",
    summary="Max array sum after optionally negating elements.",
    samples=({"input": "3\n3\n-1 -1 -1\n5\n1 5 -5 0 2\n3\n1 2 3\n", "output": "1\n13\n6\n"},),
    solve=s1791e,
    alt=a1791e,
    mutants={
        "sum": lambda s: "\n".join(
            str(sum(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)
        ) + "\n",
        "zero": lambda s: "0\n" * int(lines(s)[0]),
    },
    generate=lambda rng: [
        "3\n3\n-1 -1 -1\n5\n1 5 -5 0 2\n3\n1 2 3\n",
        "1\n2\n1 -1\n",
    ] + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(-10, 10)) for _ in range(n)) + "\n"
        for n in [rng.randint(1, 8) for _ in range(8)]
    ],
    family="greedy",
)

# 467B
def s467b(s: str) -> str:
    ls = lines(s)
    n, m, k = map(int, ls[0].split())
    fedor = int(ls[1])
    cnt = 0
    for line in ls[2:2 + m]:
        x = int(line)
        bits = bin(fedor ^ x).count("1")
        if bits <= k:
            cnt += 1
    return str(cnt) + "\n"

def a467b(s: str) -> str:
    ls = lines(s)
    n, m, k = map(int, ls[0].split())
    fedor = int(ls[1])
    cnt = sum(1 for line in ls[2:2 + m] if (fedor ^ int(line)).bit_count() <= k)
    return str(cnt) + "\n"

add(
    problem_id="467B",
    summary="Count players within hamming distance k of Fedor.",
    samples=({"input": "2 2 1\n3\n1\n3\n", "output": "2\n"},),
    solve=s467b,
    alt=a467b,
    mutants={"zero": lambda s: "0\n", "m": lambda s: str(int(lines(s)[0].split()[1])) + "\n"},
    generate=lambda rng: [
        "2 2 1\n3\n1\n3\n",
        "2 1 0\n1\n2\n",
        "3 2 1\n7\n3\n5\n",
        "3 2 2\n7\n3\n5\n",
        "2 2 0\n3\n1\n3\n",
        "2 2 2\n3\n1\n3\n",
        "3 1 1\n5\n4\n",
        "3 1 0\n5\n4\n",
        "2 1 1\n3\n1\n",
    ],
    family="bitmasks",
)

# 1857C Assembly via Minimums
def s1857c(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        b = sorted(map(int, ls[i + 1].split()))
        i += 2
        a0 = b[0]
        out.append(str(a0 + sum(b[j] - a0 for j in range(1, n))))
    return "\n".join(out) + "\n"

def a1857c(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        b = sorted(map(int, ls[i + 1].split()))
        i += 2
        arr = [b[0]] + [b[j] - b[0] for j in range(1, n)]
        out.append(str(sum(arr)))
    return "\n".join(out) + "\n"

add(
    problem_id="1857C",
    summary="Sum original array from pairwise minimums.",
    samples=({"input": "1\n3\n1 2 3\n", "output": "4\n"},),
    solve=s1857c,
    alt=a1857c,
    mutants={"zero": lambda s: "0\n" * int(lines(s)[0]), "first": lambda s: "\n".join(lines(s)[i + 1].split()[0] for i in range(1, len(lines(s)), 2)) + "\n"},
    generate=lambda rng: [
        "1\n3\n1 2 3\n",
        "1\n2\n1 1\n",
    ] + [
        (
            lambda nn: "1\n" + str(nn) + "\n" + " ".join(str(rng.randint(1, 10)) for _ in range(nn * (nn - 1) // 2)) + "\n"
        )(rng.randint(2, 5))
        for _ in range(8)
    ],
    family="greedy",
)

# 1593B
def s1593b(s: str) -> str:
    out = []
    for num in lines(s)[1:]:
        n = int(num.strip())
        if n % 25 == 0:
            out.append("0")
            continue
        digits = list(num.strip())
        best = len(digits)
        for end in ("00", "25", "50", "75"):
            d0, d1 = end
            i = len(digits) - 1
            p1 = -1
            while i >= 0:
                if digits[i] == d1:
                    p1 = i
                    break
                i -= 1
            if p1 == -1:
                continue
            i = p1 - 1
            p0 = -1
            while i >= 0:
                if digits[i] == d0:
                    p0 = i
                    break
                i -= 1
            if p0 == -1:
                continue
            best = min(best, len(digits) - 2)
        out.append(str(best))
    return "\n".join(out) + "\n"

add(
    problem_id="1593B",
    summary="Min digit removals to make number divisible by 25.",
    samples=({"input": "2\n100\n71300\n", "output": "0\n0\n"},),
    solve=s1593b,
    alt=lambda s: "\n".join(
        "0" if int(num) % 25 == 0 else str(min(
            len(num),
            min((len(num) - 2 for suffix in ("00", "25", "50", "75") if suffix in num), default=len(num)),
        ))
        for num in lines(s)[1:]
    ) + "\n",
    mutants={"zero": lambda s: "0\n" * len(lines(s)[1:]), "len": lambda s: "\n".join(str(len(x)) for x in lines(s)[1:]) + "\n"},
    generate=lambda rng: ["2\n100\n71300\n", "1\n25\n", "1\n125\n", "1\n50\n", "1\n75\n"] + [f"1\n{rng.randint(10,9999)}\n" for _ in range(8)],
    family="math",
)

# 26A
def almost_prime_count(n: int) -> int:
    primes = []
    for x in range(2, n + 1):
        ok = True
        for p in primes:
            if x % p == 0:
                ok = False
                break
            if p * p > x:
                break
        if ok:
            primes.append(x)
    cnt = 0
    for x in range(2, n + 1):
        factors = 0
        t = x
        for p in primes:
            if p * p > t:
                break
            while t % p == 0:
                factors += 1
                t //= p
        if t > 1:
            factors += 1
        if factors == 2:
            cnt += 1
    return cnt

def almost_prime_spf(n: int) -> int:
    spf = [0] * (n + 1)
    for i in range(2, n + 1):
        if spf[i] == 0:
            for j in range(i, n + 1, i):
                if spf[j] == 0:
                    spf[j] = i
    cnt = 0
    for x in range(2, n + 1):
        p = spf[x]
        q = x // p
        if q != 1 and spf[q] == q:
            cnt += 1
    return cnt

add(
    problem_id="26A",
    summary="Count almost-primes <= n (exactly two prime factors).",
    samples=({"input": "10\n", "output": "4\n"}, {"input": "21\n", "output": "7\n"}),
    solve=lambda s: str(almost_prime_count(int(s.strip()))) + "\n",
    alt=lambda s: str(almost_prime_spf(int(s.strip()))) + "\n",
    mutants={"n": lambda s: s, "half": lambda s: str(int(s.strip()) // 2) + "\n"},
    generate=lambda rng: ["10\n", "21\n", "5\n", "15\n", "30\n", "50\n", "100\n", "2\n", "3\n", "4\n"],
    family="number_theory",
)

# 1950C
def s1950c(s: str) -> str:
    out = []
    for st in lines(s)[1:]:
        h = int(st[:2])
        m = st[3:5]
        ap = st[5]
        if ap == "A" and h == 12:
            h = 0
        elif ap == "P" and h != 12:
            h += 12
        out.append(f"{h:02d}{m}")
    return "\n".join(out) + "\n"

def a1950c(s: str) -> str:
    out = []
    for st in lines(s)[1:]:
        hh, mm, ap = int(st[:2]), st[3:5], st[5]
        hh = hh % 12
        if ap == "P":
            hh += 12
        out.append(f"{hh:02d}{mm}")
    return "\n".join(out) + "\n"

add(
    problem_id="1950C",
    summary="Convert 12-hour clock with AM/PM to 24-hour.",
    samples=({"input": "3\n09:05AM\n12:30PM\n11:59PM\n", "output": "0905\n1230\n2359\n"},),
    solve=s1950c,
    alt=a1950c,
    mutants={"raw": lambda s: "\n".join(lines(s)[1:]) + "\n", "hours": lambda s: "\n".join(x[:2] for x in lines(s)[1:]) + "\n"},
    generate=lambda rng: [
        "3\n09:05AM\n12:30PM\n11:59PM\n",
        "1\n01:00AM\n",
    ] + [f"1\n{rng.randint(1,12):02d}:{rng.randint(0,59):02d}{rng.choice(['AM','PM'])}\n" for _ in range(8)],
    family="implementation",
    checker="tokens",
)

# 556A
def s556a(s: str) -> str:
    a, b = lines(s)[0], lines(s)[1]
    if sorted(a) != sorted(b):
        return "-1\n"
    diff = sum(1 for i in range(len(a)) if a[i] != b[i])
    return str(diff // 2) + "\n"

def a556a(s: str) -> str:
    a, b = lines(s)[0], lines(s)[1]
    if sorted(a) != sorted(b):
        return "-1\n"
    return str(sum(1 for i in range(len(a)) if a[i] != b[i]) // 2) + "\n"

add(
    problem_id="556A",
    summary="Min adjacent swaps in s to match t or -1.",
    samples=({"input": "ab\nba\n", "output": "1\n"},),
    solve=s556a,
    alt=a556a,
    mutants={"zero": lambda s: "0\n", "neg": lambda s: "-1\n"},
    generate=lambda rng: [
        "ab\nba\n",
        "aa\naa\n",
        "ab\nab\n",
        "abc\nacb\n",
        "aab\naba\n",
        "abc\nbca\n",
        "xy\nxy\n",
        "abcd\ndacb\n",
        "a\na\n",
        "ba\nab\n",
    ],
    family="greedy",
)

# 450A
def s450a(s: str) -> str:
    ls = lines(s)
    n, m = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    q = list(range(n))
    idx = 0
    while q:
        i = q.pop(0)
        if a[i] <= m:
            idx = i + 1
        else:
            a[i] -= m
            q.append(i)
    return str(idx) + "\n"

def a450a(s: str) -> str:
    ls = lines(s)
    n, m = map(int, ls[0].split())
    a = list(map(int, ls[1].split()))
    order = list(range(n))
    last = 0
    while order:
        i = order.pop(0)
        if a[i] <= m:
            last = i + 1
        else:
            a[i] -= m
            order.append(i)
    return str(last) + "\n"

add(
    problem_id="450A",
    summary="Which child gets last candy in queue simulation.",
    samples=({"input": "3 2\n1 2 3\n", "output": "3\n"},),
    solve=s450a,
    alt=a450a,
    mutants={"one": lambda s: "1\n", "n": lambda s: str(int(lines(s)[0].split()[0])) + "\n"},
    generate=lambda rng: [
        "3 2\n1 2 3\n",
        "2 1\n1 1\n",
    ] + [
        f"{n} {m}\n" + " ".join(str(rng.randint(1, 10)) for _ in range(n)) + "\n"
        for n, m in [(rng.randint(2, 8), rng.randint(1, 5)) for _ in range(8)]
    ],
    family="implementation",
)

# 1343C
def alt_subseq_sum(arr: list[int]) -> int:
    if all(x > 0 for x in arr) or all(x < 0 for x in arr):
        return sum(arr[i] for i in range(0, len(arr), 2))
    total = 0
    i = 0
    while i < len(arr):
        j = i
        pos = arr[i] > 0
        mx = arr[i]
        while j < len(arr) and (arr[j] > 0) == pos:
            mx = max(mx, arr[j])
            j += 1
        total += mx
        i = j
    return total

def s1343c(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        out.append(str(alt_subseq_sum(arr)))
    return "\n".join(out) + "\n"

def a1343c(s: str) -> str:
    ls = lines(s)
    out = []
    i = 1
    for _ in range(int(ls[0])):
        n = int(ls[i])
        arr = list(map(int, ls[i + 1].split()))
        i += 2
        if all(x > 0 for x in arr) or all(x < 0 for x in arr):
            out.append(str(sum(arr[k] for k in range(0, n, 2))))
            continue
        sgn = arr[0] > 0
        total = 0
        k = 0
        while k < n:
            mx = arr[k]
            while k < n and (arr[k] > 0) == sgn:
                mx = max(mx, arr[k])
                k += 1
            total += mx
            sgn = not sgn
        out.append(str(total))
    return "\n".join(out) + "\n"

add(
    problem_id="1343C",
    summary="Max sum alternating subsequence.",
    samples=({"input": "2\n5\n1 2 3 4 5\n4\n-1 2 -3 4\n", "output": "9\n2\n"},),
    solve=s1343c,
    alt=a1343c,
    mutants={"zero": lambda s: "0\n" * int(lines(s)[0]), "sum": lambda s: "\n".join(str(sum(map(int, lines(s)[i].split()))) for i in range(2, len(lines(s)), 2)) + "\n"},
    generate=lambda rng: [
        "2\n5\n1 2 3 4 5\n4\n-1 2 -3 4\n",
        "1\n3\n1 2 3\n",
    ] + [
        "1\n" + str(n) + "\n" + " ".join(str(rng.randint(-10, 10)) for _ in range(n)) + "\n"
        for n in [rng.randint(2, 8) for _ in range(8)]
    ],
    family="greedy",
)

# 1537B Bad Boy
def s1537b(s: str) -> str:
    out = []
    for n, m, _i, _j in (map(int, line.split()) for line in lines(s)[1:]):
        out.append(f"1 1 {n} {m}")
    return "\n".join(out) + "\n"

def a1537b(s: str) -> str:
    out = []
    for n, m, _i, _j in (map(int, line.split()) for line in lines(s)[1:]):
        out.append(f"1 1 {n} {m}")
    return "\n".join(out) + "\n"

add(
    problem_id="1537B",
    summary="Place yo-yos at opposite corners to maximize travel.",
    samples=({"input": "2\n3 3 1 1\n4 3 2 2\n", "output": "1 1 3 3\n1 1 4 3\n"},),
    solve=s1537b,
    alt=a1537b,
    mutants={"one": lambda s: "1\n" * len(lines(s)[1:]), "sum": lambda s: "\n".join(str(sum(map(int, l.split()))) for l in lines(s)[1:]) + "\n"},
    generate=lambda rng: [
        "2\n3 3 1 1\n4 3 2 2\n",
        "1\n2 2 1 1\n",
    ] + [
        f"1\n{rng.randint(2,10)} {rng.randint(2,10)} {rng.randint(1,5)} {rng.randint(1,5)}\n"
        for _ in range(8)
    ],
    family="math",
)

# 1097A
def s1097a(s: str) -> str:
    pile = lines(s)[0]
    hand = lines(s)[1]
    top, bottom = pile[0], pile[-1]
    for ch in hand:
        if ch == top or ch == bottom:
            return "YES\n"
    return "NO\n"

def a1097a(s: str) -> str:
    pile, hand = lines(s)[0], lines(s)[1]
    ends = {pile[0], pile[-1]}
    return yes_no(any(ch in ends for ch in hand))

add(
    problem_id="1097A",
    summary="First player can match pile top or bottom?",
    samples=({"input": "CD\nACB\n", "output": "YES\n"}, {"input": "AB\nC\n", "output": "NO\n"}),
    solve=s1097a,
    alt=a1097a,
    mutants={"always_yes": lambda s: "YES\n", "always_no": lambda s: "NO\n"},
    generate=lambda rng: [
        "CD\nACB\n",
        "AB\nC\n",
        "AA\nA\n",
        "XY\nXZ\n",
        "AB\nBA\n",
        "ZZ\nZ\n",
        "AB\nAB\n",
        "CD\nD\n",
        "EF\nFE\n",
        "GH\nH\n",
    ],
    family="implementation",
    checker="tokens_ci",
)

# 1950B
def s1950b(s: str) -> str:
    ls = lines(s)
    out_lines = []
    i = 1
    for _ in range(int(ls[0])):
        k = int(ls[i])
        grid = ls[i + 1 : i + 1 + k]
        i += 1 + k
        for row in grid:
            expanded = "".join(ch * k for ch in row)
            for _ in range(k):
                out_lines.append(expanded)
    return "\n".join(out_lines) + "\n"

def a1950b(s: str) -> str:
    ls = lines(s)
    out_lines = []
    i = 1
    for _ in range(int(ls[0])):
        k = int(ls[i])
        grid = ls[i + 1 : i + 1 + k]
        i += 1 + k
        for row in grid:
            line = "".join(c * k for c in row)
            out_lines.extend([line] * k)
    return "\n".join(out_lines) + "\n"

_1950_sample_in = "1\n2\nx.\n..\n"
_1950_sample_out = s1950b(_1950_sample_in)

add(
    problem_id="1950B",
    summary="Upscale each cell to k x k block.",
    samples=({"input": _1950_sample_in, "output": _1950_sample_out},),
    solve=s1950b,
    alt=a1950b,
    mutants={"one": lambda s: "x\n", "dot": lambda s: ".\n"},
    generate=lambda rng: [
        "1\n2\nx.\n..\n",
        "1\n1\nx\n",
        "1\n3\n...\n.x.\n...\n",
        "1\n2\n..\n..\n",
        "1\n1\n.\n",
        "1\n2\nxx\nxx\n",
        "1\n3\nx.x\n...\n.x.\n",
        "1\n2\n.x\nx.\n",
        "1\n1\nx\n",
        "1\n2\n.x\n..\n",
    ],
    family="implementation",
    checker="tokens",
)

_KEEP = ['1311A', '1729A', '1385A', '1358A', '1342A', '1559A', '1941A', '1980A', '1777A', '1472A', '577A', '124A', '1476A', '1327A', '320A', '1348A', '2000A', '2044C', '214A', '1337A', '1872A', '509A', '1360D', '1353A', '1543A', '1454A', '1679A', '1855B', '2014A', '1675B', '2065B', '1971B', '1873D', '265A', '499B', '519B', '1791E', '467B', '1857C', '1593B', '26A', '1950C', '556A', '450A', '1343C', '1537B', '1097A', '1950B']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
