"""Practice pack support classification."""

from __future__ import annotations

from typing import Any

AUTO_PACK_POSSIBLE = "AUTO_PACK_POSSIBLE"
REVIEW_PACK_POSSIBLE = "REVIEW_PACK_POSSIBLE"
UNSUPPORTED = "UNSUPPORTED"


def classify_problem(
    *,
    is_interactive: bool = False,
    io_mode: str | None = None,
    availability_status: str | None = None,
    has_oracle: bool = False,
    display_ready: bool = False,
) -> str:
    if is_interactive:
        return UNSUPPORTED
    if (io_mode or "stdio") == "file":
        return UNSUPPORTED
    if availability_status in {"asset_required"}:
        return UNSUPPORTED
    if has_oracle and display_ready:
        return AUTO_PACK_POSSIBLE
    if display_ready and (io_mode in {None, "stdio"}):
        return REVIEW_PACK_POSSIBLE
    return UNSUPPORTED


def classify_from_statement_row(row: dict[str, Any] | None, *, has_oracle: bool) -> str:
    if row is None:
        return UNSUPPORTED
    return classify_problem(
        is_interactive=bool(row.get("is_interactive")),
        io_mode=row.get("io_mode"),
        availability_status=row.get("availability_status"),
        has_oracle=has_oracle,
        display_ready=bool(row.get("display_ready")),
    )
