#!/usr/bin/env python3
"""Activate oracle-backed SolveX practice packs that pass quality gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


def main() -> int:
    from contestiq_api import duels
    from contestiq_api.practice_packs.pipeline import (
        activate_oracle_packs,
        coverage_snapshot,
    )

    duels.seed_builtin_duel_problem_packs()
    result = activate_oracle_packs()
    print(json.dumps({"activation": result, "coverage": coverage_snapshot()}, indent=2))
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
