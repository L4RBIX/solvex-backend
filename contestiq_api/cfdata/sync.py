"""Codeforces sync service.

- First sync for a handle is full; later syncs are incremental using the
  max_submission_id cursor on cf_users (Codeforces returns submissions
  newest-first, so paging stops at the first already-seen submission id).
- One sync at a time per handle (in-process lock + active cf_sync_jobs check).
- The problemset is synced globally with a TTL, never per user.
- All writes are upserts: re-running a sync never duplicates rows.
"""

from __future__ import annotations

import threading
from typing import Any

from contestiq_api.cfdata import store
from contestiq_api.cfdata.client import CodeforcesClient
from contestiq_api.settings import get_settings

PAGE_SIZE = 2000

_locks_guard = threading.Lock()
_handle_locks: dict[str, threading.Lock] = {}


class SyncInProgressError(RuntimeError):
    def __init__(self, job: dict[str, Any] | None = None) -> None:
        super().__init__("A sync is already running for this handle.")
        self.job = job


def _handle_lock(handle: str) -> threading.Lock:
    with _locks_guard:
        return _handle_locks.setdefault(handle, threading.Lock())


def _fetch_all_submissions(
    client: CodeforcesClient, handle: str, since_id: int | None, page_size: int | None = None
) -> tuple[list[dict[str, Any]], bool, int]:
    """Page through user.status newest-first; stop at since_id for incremental syncs."""
    page_size = page_size or PAGE_SIZE
    collected: list[dict[str, Any]] = []
    any_stale = False
    pages = 0
    from_index = 1
    while True:
        result = client.get_user_status(handle, from_index=from_index, count=page_size)
        pages += 1
        any_stale = any_stale or result.stale
        batch = list(result.data or [])
        if since_id is not None:
            fresh = [row for row in batch if row.get("id", 0) > since_id]
            collected.extend(fresh)
            if len(fresh) < len(batch):
                break  # reached already-synced territory
        else:
            collected.extend(batch)
        if len(batch) < page_size:
            break
        from_index += page_size
    return collected, any_stale, pages


def sync_handle(handle: str, force_full: bool = False, client: CodeforcesClient | None = None) -> dict[str, Any]:
    """Run a full or incremental sync for one handle. Returns the finished sync job."""
    canonical = store.canonical_handle(handle)
    lock = _handle_lock(canonical)
    if not lock.acquire(blocking=False):
        raise SyncInProgressError(store.find_active_sync_job(canonical))
    try:
        active = store.find_active_sync_job(canonical)
        if active is not None:
            return active

        client = client or CodeforcesClient()
        prior = store.get_user(canonical)
        since_id = None if force_full or prior is None else prior.get("max_submission_id")
        sync_type = "incremental" if since_id is not None else "full"
        job = store.create_sync_job(sync_type, canonical)
        store.mark_sync_running(job["id"])

        try:
            user_result = client.get_user_info(handle)
            rating_result = client.get_user_rating(handle)
            submissions, subs_stale, pages = _fetch_all_submissions(client, canonical, since_id)

            store.upsert_user(user_result.data)
            rating_count = store.upsert_rating_history(canonical, list(rating_result.data or []))
            sub_stats = store.upsert_submissions(canonical, submissions)
            max_id = max((row.get("id", 0) for row in submissions), default=None)
            store.update_user_sync_cursor(canonical, max_id)

            any_stale = user_result.stale or rating_result.stale or subs_stale
            stats = {
                "sync_type": sync_type,
                "pages_fetched": pages,
                "submissions_fetched": sub_stats["fetched"],
                "submissions_new": sub_stats["new"],
                "rating_history_rows": rating_count,
                "used_stale_cache": any_stale,
            }
            store.finish_sync_job(job["id"], "stale_cache_used" if any_stale else "success", stats=stats)
        except Exception as exc:
            store.finish_sync_job(job["id"], "failed", error_message=str(exc))
            raise
        finished = store.get_sync_job(job["id"])
        assert finished is not None
        return finished
    finally:
        lock.release()


def sync_problemset(force: bool = False, client: CodeforcesClient | None = None) -> dict[str, Any]:
    """Global problemset sync, skipped while the latest snapshot is within the TTL."""
    snapshot = store.latest_problemset_snapshot()
    ttl_hours = get_settings().codeforces_problemset_ttl_hours
    if snapshot is not None and not force and not _snapshot_expired(snapshot["fetched_at"], ttl_hours):
        return {
            "status": "fresh",
            "fetched_at": snapshot["fetched_at"],
            "problem_count": snapshot["problem_count"],
            "refetched": False,
        }

    active = store.find_active_sync_job(None, sync_type="problemset")
    if active is not None:
        return {**active, "refetched": False}

    client = client or CodeforcesClient()
    job = store.create_sync_job("problemset", None)
    store.mark_sync_running(job["id"])
    try:
        result = client.get_problemset()
        counts = store.save_problemset_snapshot(result.data or {})
        stats = {**counts, "used_stale_cache": result.stale}
        store.finish_sync_job(job["id"], "stale_cache_used" if result.stale else "success", stats=stats)
    except Exception as exc:
        store.finish_sync_job(job["id"], "failed", error_message=str(exc))
        raise
    finished = store.get_sync_job(job["id"])
    assert finished is not None
    return {**finished, "refetched": True}


def _snapshot_expired(fetched_at: str, ttl_hours: int) -> bool:
    from datetime import datetime, timedelta, timezone

    try:
        fetched = datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - fetched > timedelta(hours=ttl_hours)


def sync_status(handle: str) -> dict[str, Any]:
    """Visibility payload for a handle's sync state."""
    canonical = store.canonical_handle(handle)
    user = store.get_user(canonical)
    counts = store.submission_counts(canonical)
    jobs = store.list_sync_jobs(canonical)
    return {
        "handle": canonical,
        "synced": user is not None,
        "user": {
            "display_handle": user["display_handle"],
            "rating": user["rating"],
            "max_rating": user["max_rating"],
            "rank": user["rank"],
            "first_synced_at": user["first_synced_at"],
            "last_synced_at": user["last_synced_at"],
            "max_submission_id": user["max_submission_id"],
            "submission_count": user["submission_count"],
        }
        if user
        else None,
        "submissions": counts,
        "recent_jobs": jobs,
        "problemset": store.latest_problemset_snapshot(),
    }
