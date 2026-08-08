"""Auto-expanded unique-answer oracle catalog (bulk_09)."""
from __future__ import annotations
from contestiq_api.practice_packs.catalog.dsl import lines, make_spec, yes_no

SPECS = []

def add(**kw):
    SPECS.append(make_spec(**kw))


def _solve_1433a(s: str) -> str:
    ls=lines(s); out=[]
    for x in ls[1:]:
     d=int(x[0]); L=len(x); out.append(str((d-1)*10 + L*(L+1)//2))
    return "\n".join(out)+"\n"

def _alt_1433a(s: str) -> str:
    ls=lines(s); out=[]
    for x in ls[1:]:
     total=0
     for dig in range(1,10):
      cur=""
      for _ in range(4):
       cur+=str(dig); total+=len(cur)
       if cur==x:
        out.append(str(total)); break
      else:
       continue
      break
    return "\n".join(out)+"\n"

def _m1_1433a(s: str) -> str:
    return "\n".join(str(len(x)) for x in lines(s)[1:])+"\n"

def _m2_1433a(s: str) -> str:
    return "\n".join(x[0] for x in lines(s)[1:])+"\n"

add(
    problem_id="1433A",
    summary="Keypresses for boring apartments",
    samples=({"input": "4\n22\n1\n777\n9999\n", "output": "13\n1\n24\n46\n"},),
    solve=_solve_1433a,
    alt=_alt_1433a,
    mutants={"m1": _m1_1433a, "m2": _m2_1433a},
    generate=lambda rng: ["4\n22\n1\n777\n9999\n","1\n2\n","1\n22\n","1\n222\n","1\n2222\n","1\n5\n","1\n55\n","1\n555\n","1\n5555\n","1\n9\n","1\n99\n"],
    family="math",
    checker="exact",
)

def _solve_1619a(s: str) -> str:
    ls=lines(s);t=int(ls[0]);out=[]
    for x in ls[1:1+t]:
     out.append("YES" if len(x)%2==0 and x[:len(x)//2]==x[len(x)//2:] else "NO")
    return "\n".join(out)+"\n"

def _alt_1619a(s: str) -> str:
    ls=lines(s);out=[]
    for x in ls[1:1+int(ls[0])]:
     n=len(x); out.append("YES" if n%2==0 and all(x[i]==x[i+n//2] for i in range(n//2)) else "NO")
    return "\n".join(out)+"\n"

def _m1_1619a(s: str) -> str:
    return "\n".join("YES" if len(x)%2==0 else "NO" for x in lines(s)[1:])+"\n"

def _m2_1619a(s: str) -> str:
    return "YES\n"*int(lines(s)[0])

add(
    problem_id="1619A",
    summary="Is string a square tt?",
    samples=({"input": "5\naa\nab\nabab\naaaa\nabc\n", "output": "YES\nNO\nYES\nYES\nNO\n"},),
    solve=_solve_1619a,
    alt=_alt_1619a,
    mutants={"m1": _m1_1619a, "m2": _m2_1619a},
    generate=lambda rng: ["5\naa\nab\nabab\naaaa\nabc\n","1\nabab\n","1\nabba\n","1\na\n","1\nab\n","1\nabcabc\n","1\nxxxx\n","1\nxyxy\n","1\naba\n","1\nzzzzzz\n"],
    family="strings",
    checker="tokens_ci",
)

def _solve_1374a(s: str) -> str:
    ls=lines(s);out=[]
    for line in ls[1:1+int(ls[0])]:
     x,y,n=map(int,line.split()); out.append(str(n-(n-y)%x))
    return "\n".join(out)+"\n"

def _alt_1374a(s: str) -> str:
    ls=lines(s);out=[]
    for line in ls[1:1+int(ls[0])]:
     x,y,n=map(int,line.split()); k=n//x*x+y
     if k>n: k-=x
     out.append(str(k))
    return "\n".join(out)+"\n"

def _m1_1374a(s: str) -> str:
    return "\n".join(line.split()[-1] for line in lines(s)[1:])+"\n"

def _m2_1374a(s: str) -> str:
    return "\n".join(line.split()[1] for line in lines(s)[1:])+"\n"

add(
    problem_id="1374A",
    summary="Largest k<=n with k%x==y",
    samples=({"input": "5\n7 5 12345\n5 0 4\n10 5 15\n17 8 54321\n499999999 999999998 1000000000\n", "output": "12339\n0\n15\n54306\n999999998\n"},),
    solve=_solve_1374a,
    alt=_alt_1374a,
    mutants={"m1": _m1_1374a, "m2": _m2_1374a},
    generate=lambda rng: ["5\n7 5 12345\n5 0 4\n10 5 15\n17 8 54321\n499999999 999999998 1000000000\n","1\n3 1 10\n","1\n2 0 1\n","1\n4 2 100\n","1\n9 0 9\n","1\n6 3 20\n","1\n5 4 4\n","1\n8 1 100\n","1\n11 5 50\n","1\n100 50 1000\n"],
    family="math",
    checker="exact",
)

def _solve_492a(s: str) -> str:
    n=int(s.strip());h=0;used=0
    while True:
     h+=1; need=h*(h+1)//2
     if used+need>n: return f"{h-1}\n"
     used+=need

def _alt_492a(s: str) -> str:
    n=int(s.strip());h=0;total=0
    while total+(h+1)*(h+2)//2<=n:
     h+=1; total+=h*(h+1)//2
    return f"{h}\n"

def _m1_492a(s: str) -> str:
    return f"{int(int(s.strip())**0.5)}\n"

def _m2_492a(s: str) -> str:
    return f"{int(s.strip())//2}\n"

add(
    problem_id="492A",
    summary="Max pyramid height with n cubes",
    samples=({"input": "10\n", "output": "3\n"},),
    solve=_solve_492a,
    alt=_alt_492a,
    mutants={"m1": _m1_492a, "m2": _m2_492a},
    generate=lambda rng: [f"{n}\n" for n in [1,2,3,4,10,15,20,25,100,500,10000]],
    family="math",
    checker="exact",
)

def _solve_1283a(s: str) -> str:
    ls=lines(s);out=[]
    for line in ls[1:1+int(ls[0])]:
     h,m=map(int,line.split()); out.append(str(24*60-h*60-m))
    return "\n".join(out)+"\n"

def _alt_1283a(s: str) -> str:
    ls=lines(s);out=[]
    for line in ls[1:1+int(ls[0])]:
     h,m=map(int,line.split()); out.append(str((23-h)*60+(60-m)))
    return "\n".join(out)+"\n"

def _m1_1283a(s: str) -> str:
    return "\n".join(str(24-int(x.split()[0])) for x in lines(s)[1:])+"\n"

def _m2_1283a(s: str) -> str:
    return "\n".join(str(60-int(x.split()[1])) for x in lines(s)[1:])+"\n"

add(
    problem_id="1283A",
    summary="Minutes until New Year",
    samples=({"input": "5\n23 55\n23 0\n0 1\n4 20\n23 59\n", "output": "5\n60\n1439\n1180\n1\n"},),
    solve=_solve_1283a,
    alt=_alt_1283a,
    mutants={"m1": _m1_1283a, "m2": _m2_1283a},
    generate=lambda rng: ["5\n23 55\n23 0\n0 1\n4 20\n23 59\n","1\n0 0\n","1\n12 0\n"]+[f"1\n{h} {m}\n" for h,m in [(0,0),(23,59),(12,30),(1,1),(10,10),(5,5),(20,0),(0,59)]],
    family="math",
    checker="exact",
)

_KEEP = ['492A', '1283A']
SPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]
