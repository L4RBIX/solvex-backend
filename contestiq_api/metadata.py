"""Shared response metadata for every analysis-related v1 endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from contestiq_api.versions import ANALYSIS_VERSION, PROBLEM_CATALOG_VERSION, TAXONOMY_VERSION

METADATA_FIELDS = (
    "analysis_version",
    "taxonomy_version",
    "problem_catalog_version",
    "generated_at",
    "data_cutoff_time",
    "source",
    "warnings",
)


def response_metadata(
    source: str,
    warnings: list[str] | None = None,
    data_cutoff_time: str | None = None,
) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "problem_catalog_version": PROBLEM_CATALOG_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_cutoff_time": data_cutoff_time,
        "source": source,
        "warnings": warnings or [],
    }
