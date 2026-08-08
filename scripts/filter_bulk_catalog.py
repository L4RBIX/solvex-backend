#!/usr/bin/env python3
"""Filter bulk_* SPECS to those that pass hard quality gates (fail-closed)."""

from __future__ import annotations

import importlib
import random
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from contestiq_api.practice_packs.checkers import outputs_match
from contestiq_api.practice_packs.mutation import score_mutations
from contestiq_api.practice_packs.quality import evaluate_quality


def passes(spec) -> bool:
    try:
        inputs: list[str] = []
        seen: set[str] = set()
        for item in spec.generate_cases(random.Random(11)):
            if item not in seen:
                seen.add(item)
                inputs.append(item)
        primary, secondary = spec.oracles
        tests: list[dict[str, str]] = []
        disagreements = 0
        for stdin in inputs:
            a = primary(stdin)
            b = secondary(stdin)
            if not outputs_match(a, b, checker_type=spec.checker_type):
                disagreements += 1
                continue
            tests.append({"input": stdin, "expected_output": a})
        if disagreements:
            return False
        for sample in spec.sample_tests:
            if not outputs_match(
                primary(sample["input"]), sample["output"], checker_type=spec.checker_type
            ):
                return False
            if not outputs_match(
                secondary(sample["input"]), sample["output"], checker_type=spec.checker_type
            ):
                return False
            if not any(t["input"] == sample["input"] for t in tests):
                tests.insert(
                    0,
                    {
                        "input": sample["input"],
                        "expected_output": primary(sample["input"]),
                    },
                )
        mut = score_mutations(
            tests,
            correct=primary,
            mutants=spec.mutants,
            checker=lambda a, e: outputs_match(a, e, checker_type=spec.checker_type),
        )
        quality = evaluate_quality(
            test_count=len(tests),
            mutation_score=mut.mutation_score,
            oracle_count=len(spec.oracles),
            oracles_agree=True,
            has_sample=True,
        )
        return bool(quality["passed"])
    except Exception:
        return False


def filter_module(modname: str) -> tuple[int, int]:
    mod = importlib.import_module(modname)
    keep = [s.problem_id for s in mod.SPECS if passes(s)]
    path = Path(BACKEND) / Path(*modname.split(".")).with_suffix(".py")
    text = path.read_text()
    marker = "\n\n_KEEP = "
    if marker in text:
        text = text.split(marker)[0]
    text = text.rstrip() + f"\n\n_KEEP = {keep!r}\nSPECS = [s for s in SPECS if s.problem_id in set(_KEEP)]\n"
    path.write_text(text)
    return len(keep), len(getattr(mod, "SPECS", []))


def main() -> int:
    catalog = Path(BACKEND) / "contestiq_api/practice_packs/catalog"
    total_keep = 0
    for path in sorted(catalog.glob("bulk_*.py")):
        modname = f"contestiq_api.practice_packs.catalog.{path.stem}"
        # Drop cached module
        sys.modules.pop(modname, None)
        keep, before = filter_module(modname)
        total_keep += keep
        print(f"{path.name}: kept {keep}/{before}")
    print(f"total_kept={total_keep}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
