"""v1 endpoints for problem episodes and the skill taxonomy."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from contestiq_api import auth
from contestiq_api.cfdata import episodes as cf_episodes
from contestiq_api.cfdata import taxonomy as cf_taxonomy
from contestiq_api.errors import APIError
from contestiq_api.service import validate_handle
from contestiq_api.versions import TAXONOMY_VERSION

router = APIRouter(prefix="/api/v1")


@router.post("/episodes/{handle}/rebuild")
def rebuild_episodes(handle: str):
    cleaned = validate_handle(handle)
    result = cf_episodes.rebuild_episodes(cleaned)
    if result["from_submissions"] == 0:
        result["warning"] = (
            "No normalized submissions found for this handle. "
            "Run POST /api/v1/sync/codeforces/{handle} first."
        )
    return result


@router.get("/episodes/{handle}")
def list_episodes(handle: str, limit: int = Query(default=100, ge=1, le=1000)):
    cleaned = validate_handle(handle)
    rows = cf_episodes.list_episodes(cleaned, limit=limit)
    return {"handle": cleaned.lower(), "count": len(rows), "episodes": rows}


@router.get("/taxonomy")
def taxonomy(version: str = TAXONOMY_VERSION):
    data = cf_taxonomy.get_taxonomy(version)
    if data["version"] is None:
        raise APIError("TAXONOMY_NOT_SEEDED", f"Taxonomy version {version} is not seeded yet.", 404)
    return data


@router.post("/taxonomy/seed")
def seed_taxonomy(_admin: dict[str, Any] = Depends(auth.require_admin)):
    return cf_taxonomy.seed_taxonomy()


@router.post("/skill-map/rebuild")
def rebuild_skill_map(_admin: dict[str, Any] = Depends(auth.require_admin)):
    return cf_taxonomy.build_problem_skill_map()


@router.get("/skill-map/{problem_id}")
def problem_skills(problem_id: str):
    mappings = cf_taxonomy.get_problem_skills(problem_id)
    return {"problem_id": problem_id, "taxonomy_version": TAXONOMY_VERSION, "skills": mappings}
