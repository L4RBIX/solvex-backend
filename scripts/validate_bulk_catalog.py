"""Standalone validator for bulk_*.py oracle specs (no pytest dependency)."""
import importlib
import random
import sys

sys.path.insert(0, ".")

from contestiq_api.practice_packs.checkers import outputs_match
from contestiq_api.practice_packs.mutation import score_mutations


def validate_module(modname: str) -> int:
    mod = importlib.import_module(modname)
    specs = mod.SPECS
    print(f"=== {modname}: {len(specs)} specs ===")
    failures = []
    for spec in specs:
        pid = spec.problem_id
        try:
            rng = random.Random(12345)
            raw = spec.generate_cases(rng)
            seen = set()
            inputs = []
            for item in raw:
                if item not in seen:
                    seen.add(item)
                    inputs.append(item)
            if len(inputs) < 10:
                failures.append((pid, f"only {len(inputs)} unique generated cases (<10)"))

            primary, secondary = spec.oracles
            tests = []
            disagreements = 0
            for stdin in inputs:
                try:
                    out_a = primary(stdin)
                    out_b = secondary(stdin)
                except Exception as exc:  # noqa: BLE001
                    failures.append((pid, f"oracle crashed on input {stdin!r}: {exc!r}"))
                    continue
                if not outputs_match(out_a, out_b, checker_type=spec.checker_type):
                    disagreements += 1
                    failures.append(
                        (pid, f"oracle disagreement on input {stdin!r}: {out_a!r} vs {out_b!r}")
                    )
                    continue
                tests.append({"input": stdin, "expected_output": out_a})

            if len(tests) < 8:
                failures.append((pid, f"only {len(tests)} agreed tests (<8)"))

            # sample check
            has_sample = False
            for sample in spec.sample_tests:
                sin = sample["input"]
                sout = sample["output"]
                try:
                    actual = primary(sin)
                except Exception as exc:  # noqa: BLE001
                    failures.append((pid, f"solve crashed on sample: {exc!r}"))
                    continue
                if not outputs_match(actual, sout, checker_type=spec.checker_type):
                    failures.append(
                        (pid, f"sample mismatch: solve({sin!r})={actual!r} expected {sout!r}")
                    )
                else:
                    has_sample = True
                try:
                    actual2 = secondary(sin)
                    if not outputs_match(actual2, sout, checker_type=spec.checker_type):
                        failures.append(
                            (pid, f"alt disagrees with sample: alt({sin!r})={actual2!r} expected {sout!r}")
                        )
                except Exception as exc:  # noqa: BLE001
                    failures.append((pid, f"alt crashed on sample: {exc!r}"))

            if not has_sample:
                failures.append((pid, "no sample matched"))

            if len(spec.mutants) < 2:
                failures.append((pid, f"only {len(spec.mutants)} mutants (<2)"))

            if tests:
                checker = lambda a, e: outputs_match(a, e, checker_type=spec.checker_type)
                try:
                    mutation = score_mutations(
                        tests, correct=primary, mutants=spec.mutants, checker=checker
                    )
                    if mutation.mutation_score < 0.75:
                        failures.append(
                            (
                                pid,
                                f"mutation_score {mutation.mutation_score:.2f} < 0.75, "
                                f"surviving={mutation.surviving}",
                            )
                        )
                except Exception as exc:  # noqa: BLE001
                    failures.append((pid, f"mutation scoring crashed: {exc!r}"))
        except Exception as exc:  # noqa: BLE001
            failures.append((pid, f"unexpected error: {exc!r}"))

    if failures:
        print(f"--- {len(failures)} issues ---")
        for pid, msg in failures:
            print(f"[{pid}] {msg}")
    else:
        print("All specs passed validation.")
    return len(failures)


if __name__ == "__main__":
    total = 0
    for m in sys.argv[1:]:
        total += validate_module(m)
    sys.exit(1 if total else 0)
