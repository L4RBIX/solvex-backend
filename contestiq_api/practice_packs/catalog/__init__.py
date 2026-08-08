"""Catalog loader for bulk dual-oracle practice pack specs."""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contestiq_api.practice_packs.oracles import ProblemOracleSpec

logger = logging.getLogger(__name__)

_BULK_MODULES = tuple(f"contestiq_api.practice_packs.catalog.bulk_{i:02d}" for i in range(0, 16))


def load_catalog_specs() -> list["ProblemOracleSpec"]:
    """Import all available bulk_* modules and collect SPECS (dedupe by problem_id)."""
    specs: list[ProblemOracleSpec] = []
    seen: set[str] = set()
    for modname in _BULK_MODULES:
        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError:
            continue
        except Exception as exc:  # noqa: BLE001
            logger.warning("catalog module %s failed to import: %s", modname, exc)
            continue
        for spec in getattr(mod, "SPECS", []) or []:
            pid = getattr(spec, "problem_id", None)
            if not pid or pid in seen:
                continue
            seen.add(pid)
            specs.append(spec)
    return specs
