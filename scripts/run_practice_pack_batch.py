#!/usr/bin/env python3
"""Enqueue + process practice pack activation batches."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enqueue-limit", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--max-batches", type=int, default=40)
    parser.add_argument("--activate-all", action="store_true", help="Directly activate all registry packs")
    args = parser.parse_args()

    from contestiq_api import duels
    from contestiq_api.practice_packs.batch import enqueue_registry_candidates, run_batch
    from contestiq_api.practice_packs.pipeline import activate_oracle_packs, coverage_snapshot

    duels.seed_builtin_duel_problem_packs()

    if args.activate_all:
        result = activate_oracle_packs()
        print(json.dumps({"activation": result, "coverage": coverage_snapshot()}, indent=2))
        return 0 if not result["failed"] else 0  # fail-closed failures are expected for bad specs

    enq = enqueue_registry_candidates(limit=args.enqueue_limit)
    batches = []
    for i in range(args.max_batches):
        batch = run_batch(limit=args.batch_size, worker_id=f"cli-batch-{i}")
        batches.append(
            {
                "claimed": batch["claimed"],
                "activated": batch["activated"],
                "review_required": batch["review_required"],
                "rejected": batch["rejected"],
            }
        )
        if batch["claimed"] == 0:
            break

    print(
        json.dumps(
            {
                "enqueue": enq,
                "batches": batches,
                "coverage": coverage_snapshot(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
