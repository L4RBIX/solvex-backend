"""Practice pack pipeline: build → validate → activate."""

from __future__ import annotations

import json
import logging
from typing import Any

from contestiq_api import duels
from contestiq_api.cfdata import store
from contestiq_api.practice_packs.oracles import (
    ORACLE_REGISTRY,
    build_candidate_pack,
    list_oracle_problem_ids,
)

logger = logging.getLogger(__name__)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def upsert_practice_pack(pack: dict[str, Any], *, activate: bool = True) -> bool:
    """Persist a versioned pack with quality metadata. Never mutates an existing pack_id row's tests."""
    required_text = (
        "pack_id",
        "problem_id",
        "statement_summary",
        "input_format",
        "output_format",
        "constraints_text",
    )
    if any(not isinstance(pack.get(key), str) or not pack[key].strip() for key in required_text):
        return False
    tests = duels._normalize_judge_tests(pack.get("judge_tests"))
    if not tests:
        return False
    samples = duels._normalize_sample_tests(pack.get("sample_tests"))
    version = int(pack.get("version") or 0)
    if version < 1:
        return False

    review_state = str(pack.get("review_state") or "review_required")
    checker_type = str(pack.get("checker_type") or "exact")
    active = 1 if activate and review_state in {"reviewed", "active"} else 0
    if active:
        review_state = "active"

    with store.connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM problems WHERE problem_key = ?", (pack["problem_id"],)
        ).fetchone()
        if exists is None:
            return False
        if active:
            conn.execute(
                "UPDATE duel_problem_packs SET active = 0 WHERE problem_id = ? AND pack_id != ?",
                (pack["problem_id"], pack["pack_id"]),
            )
        conn.execute(
            """
            INSERT OR IGNORE INTO duel_problem_packs (
                pack_id, problem_id, version, statement_summary, input_format, output_format,
                constraints_text, sample_tests, judge_tests, active, created_at,
                review_state, checker_type, oracle_strategy, provenance, quality_report,
                mutation_score, test_count, activated_at, quality_score, oracle_family
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pack["pack_id"],
                pack["problem_id"],
                version,
                pack["statement_summary"],
                pack["input_format"],
                pack["output_format"],
                pack["constraints_text"],
                _canonical_json(samples),
                _canonical_json(tests),
                active,
                store._now(),
                review_state,
                checker_type,
                pack.get("oracle_strategy"),
                _canonical_json(pack.get("provenance") or {}),
                _canonical_json(pack.get("quality_report") or {}),
                pack.get("mutation_score"),
                pack.get("test_count") or len(tests),
                store._now() if active else None,
                pack.get("quality_score"),
                pack.get("oracle_family"),
            ),
        )
        # If pack_id already existed (INSERT OR IGNORE), refresh metadata/active only —
        # do not rewrite judge_tests in place.
        if active:
            conn.execute(
                """
                UPDATE duel_problem_packs
                SET active = 1,
                    review_state = ?,
                    checker_type = ?,
                    oracle_strategy = ?,
                    provenance = ?,
                    quality_report = ?,
                    mutation_score = ?,
                    test_count = ?,
                    quality_score = ?,
                    oracle_family = ?,
                    activated_at = COALESCE(activated_at, ?)
                WHERE pack_id = ?
                """,
                (
                    review_state,
                    checker_type,
                    pack.get("oracle_strategy"),
                    _canonical_json(pack.get("provenance") or {}),
                    _canonical_json(pack.get("quality_report") or {}),
                    pack.get("mutation_score"),
                    pack.get("test_count") or len(tests),
                    pack.get("quality_score"),
                    pack.get("oracle_family"),
                    store._now(),
                    pack["pack_id"],
                ),
            )
    return True


def activate_oracle_packs(*, problem_ids: list[str] | None = None) -> dict[str, Any]:
    """Build and activate registry packs that pass quality gates + auto-activate score."""
    ids = problem_ids or list_oracle_problem_ids()
    activated: list[str] = []
    failed: list[dict[str, str]] = []
    skipped: list[str] = []
    review_required: list[str] = []
    for problem_id in ids:
        if problem_id not in ORACLE_REGISTRY:
            failed.append({"problem_id": problem_id, "error": "no oracle registry entry"})
            continue
        try:
            pack = build_candidate_pack(problem_id)
        except Exception as exc:  # noqa: BLE001
            failed.append({"problem_id": problem_id, "error": str(exc)})
            continue
        quality = pack.get("quality_report") or {}
        recommendation = quality.get("recommendation")
        if pack.get("review_state") == "review_required" or recommendation == "review_required":
            pack["review_state"] = "review_required"
            upsert_practice_pack(pack, activate=False)
            review_required.append(problem_id)
            continue
        if not quality.get("passed") or recommendation == "reject":
            failed.append(
                {
                    "problem_id": problem_id,
                    "error": "quality gate failed: "
                    + ",".join(quality.get("failures") or [recommendation or "reject"]),
                }
            )
            continue
        with store.connect() as conn:
            active = conn.execute(
                """
                SELECT pack_id, version FROM duel_problem_packs
                WHERE problem_id = ? AND active = 1
                ORDER BY version DESC LIMIT 1
                """,
                (problem_id,),
            ).fetchone()
        if active is not None and int(active["version"]) >= int(pack["version"]):
            # Keep existing active pack unless we introduce a higher version.
            skipped.append(problem_id)
            continue
        pack["review_state"] = "reviewed"
        if upsert_practice_pack(pack, activate=True):
            activated.append(problem_id)
            logger.info(
                "practice_pack_activated problem_id=%s pack_id=%s tests=%s mutation=%.3f score=%s",
                problem_id,
                pack["pack_id"],
                pack.get("test_count"),
                float(pack.get("mutation_score") or 0),
                pack.get("quality_score"),
            )
        else:
            failed.append({"problem_id": problem_id, "error": "upsert failed"})
    return {
        "activated": activated,
        "failed": failed,
        "skipped": skipped,
        "review_required": review_required,
        "registry_size": len(ORACLE_REGISTRY),
    }


def seed_auto_practice_packs() -> int:
    """Seed/activate oracle packs when problems exist and no higher pack is active."""
    result = activate_oracle_packs()
    return len(result["activated"])


_auto_packs_seeded = False


def ensure_auto_packs_seeded() -> None:
    """Idempotent process-local seed of oracle-backed packs."""
    global _auto_packs_seeded
    if _auto_packs_seeded:
        return
    try:
        seed_auto_practice_packs()
    finally:
        _auto_packs_seeded = True


def problem_has_active_pack(problem_id: str) -> bool:
    duels.seed_builtin_duel_problem_packs()
    ensure_auto_packs_seeded()
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT pack_id, judge_tests, statement_summary, input_format, output_format, constraints_text
            FROM duel_problem_packs
            WHERE problem_id = ? AND active = 1
            ORDER BY version DESC
            LIMIT 1
            """,
            (problem_id,),
        ).fetchone()
    if row is None:
        return False
    pack = dict(row)
    tests = duels._normalize_judge_tests(pack.get("judge_tests"))
    return bool(tests) and duels._pack_has_complete_content(pack)


def submit_capable_problem_ids() -> set[str]:
    duels.seed_builtin_duel_problem_packs()
    ensure_auto_packs_seeded()
    with store.connect() as conn:
        rows = conn.execute(
            """
            SELECT problem_id, judge_tests, statement_summary, input_format, output_format, constraints_text
            FROM duel_problem_packs
            WHERE active = 1
            """
        ).fetchall()
    capable: set[str] = set()
    for row in rows:
        pack = dict(row)
        tests = duels._normalize_judge_tests(pack.get("judge_tests"))
        if tests and duels._pack_has_complete_content(pack):
            capable.add(pack["problem_id"])
    return capable


def coverage_snapshot() -> dict[str, Any]:
    import json

    from contestiq_api.practice_packs.classify import classify_problem
    from contestiq_api.practice_packs.jobs import job_status_counts
    from contestiq_api.practice_packs.priority import rating_band

    with store.connect() as conn:
        catalog = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        display_ready = conn.execute(
            "SELECT COUNT(*) FROM problem_statements WHERE display_ready = 1"
        ).fetchone()[0]
        solve_ready = conn.execute(
            "SELECT COUNT(*) FROM problem_statements WHERE solve_ready = 1"
        ).fetchone()[0]
        interactive = conn.execute(
            "SELECT COUNT(*) FROM problem_statements WHERE is_interactive = 1"
        ).fetchone()[0]
        file_io = conn.execute(
            "SELECT COUNT(*) FROM problem_statements WHERE io_mode = 'file'"
        ).fetchone()[0]
        asset_required = conn.execute(
            "SELECT COUNT(*) FROM problem_statements WHERE availability_status = 'asset_required'"
        ).fetchone()[0]
        pack_rows = conn.execute(
            """
            SELECT problem_id, active, review_state, mutation_score, quality_score, test_count
            FROM duel_problem_packs
            """
        ).fetchall()
        rating_rows = conn.execute(
            "SELECT problem_key, rating, tags FROM problems"
        ).fetchall()

    capable = submit_capable_problem_ids()
    rating_by_id = {r["problem_key"]: r["rating"] for r in rating_rows}
    tags_by_id: dict[str, list[str]] = {}
    for r in rating_rows:
        raw = r["tags"]
        if isinstance(raw, str):
            try:
                tags_by_id[r["problem_key"]] = json.loads(raw)
            except Exception:
                tags_by_id[r["problem_key"]] = []
        else:
            tags_by_id[r["problem_key"]] = list(raw or [])

    by_rating: dict[str, dict[str, int]] = {}
    for band in (800, 900, 1000, 1100, 1200, 1300):
        by_rating[str(band)] = {"standard": 0, "submit_capable": 0}
    for pid, rating in rating_by_id.items():
        band = rating_band(rating)
        if band is None:
            continue
        key = str(band)
        by_rating.setdefault(key, {"standard": 0, "submit_capable": 0})
        by_rating[key]["standard"] += 1
        if pid in capable:
            by_rating[key]["submit_capable"] += 1

    tag_counts: dict[str, dict[str, int]] = {}
    for pid in capable:
        for tag in tags_by_id.get(pid) or []:
            bucket = tag_counts.setdefault(str(tag), {"submit_capable": 0})
            bucket["submit_capable"] += 1

    pack_states = {
        "active": 0,
        "review_required": 0,
        "rejected": 0,
        "candidate": 0,
        "validation_failed": 0,
    }
    mutation_scores: list[float] = []
    quality_scores: list[float] = []
    for row in pack_rows:
        state = str(row["review_state"] or "")
        if int(row["active"] or 0) == 1:
            pack_states["active"] += 1
        elif state in pack_states:
            pack_states[state] += 1
        elif state:
            pack_states["candidate"] += 1
        if row["mutation_score"] is not None and int(row["active"] or 0) == 1:
            mutation_scores.append(float(row["mutation_score"]))
        qs = row["quality_score"] if "quality_score" in row.keys() else None
        if qs is not None and int(row["active"] or 0) == 1:
            quality_scores.append(float(qs))

    supportability = {
        "AUTO_HIGH_CONFIDENCE": 0,
        "AUTO_POSSIBLE": 0,
        "REVIEW_REQUIRED": 0,
        "UNSUPPORTED": 0,
    }
    for pid in ORACLE_REGISTRY:
        supportability[
            classify_problem(
                has_oracle=True,
                display_ready=True,
                io_mode="stdio",
                rating=rating_by_id.get(pid),
                tags=tags_by_id.get(pid),
            )
        ] += 1

    return {
        "catalog": catalog,
        "display_ready": display_ready,
        "solve_ready": solve_ready,
        "arena_capable_proxy_display_ready": display_ready,
        "submit_capable": len(capable),
        "submit_capable_problem_ids_sample": sorted(capable)[:50],
        "unsupported": {
            "interactive": interactive,
            "file_io": file_io,
            "asset_required": asset_required,
        },
        "oracle_registry_size": len(ORACLE_REGISTRY),
        "pack_states": pack_states,
        "job_counts": job_status_counts(),
        "coverage_by_rating": by_rating,
        "coverage_by_tag_top": dict(
            sorted(tag_counts.items(), key=lambda kv: -kv[1]["submit_capable"])[:20]
        ),
        "supportability_registry": supportability,
        "average_mutation_score": (
            round(sum(mutation_scores) / len(mutation_scores), 4) if mutation_scores else None
        ),
        "average_quality_score": (
            round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None
        ),
    }
