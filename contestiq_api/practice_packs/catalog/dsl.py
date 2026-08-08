"""Compact DSL for registering dual-oracle practice pack specs."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from contestiq_api.practice_packs.oracles import ProblemOracleSpec

OracleFn = Callable[[str], str]
MutantMap = dict[str, OracleFn]
GenFn = Callable[[random.Random], list[str]]


def make_spec(
    problem_id: str,
    *,
    summary: str,
    samples: tuple[dict[str, str], ...] | list[dict[str, str]],
    solve: OracleFn,
    alt: OracleFn,
    mutants: MutantMap,
    generate: GenFn,
    input_format: str = "See Codeforces statement.",
    output_format: str = "Print the answer as specified.",
    constraints: str = "Within Codeforces statement constraints; generated tests use safe bounds.",
    checker: str = "exact",
    strategy: str = "dual_independent_oracles",
    family: str = "general",
    pack_version: int = 1,
) -> ProblemOracleSpec:
    sample_tuple = tuple(dict(s) for s in samples)
    return ProblemOracleSpec(
        problem_id=problem_id,
        checker_type=checker,
        oracle_strategy=f"{strategy}:{family}",
        statement_summary=summary,
        input_format=input_format,
        output_format=output_format,
        constraints_text=constraints,
        sample_tests=sample_tuple,
        oracles=(solve, alt),
        mutants=mutants,
        generate_cases=generate,
        pack_version=pack_version,
    )


def yes_no(flag: bool) -> str:
    return "YES\n" if flag else "NO\n"


def ensure_nl(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"


def lines(stdin: str) -> list[str]:
    return stdin.strip().splitlines()
