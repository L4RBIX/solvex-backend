"""In-process metrics registry (Phase 09).

Stdlib-only counters and latency histograms, rendered Prometheus-style at
GET /api/v1/metrics (admin-gated). Covers the golden signals: traffic
(http_requests_total by status class), latency (p50/p95/p99 per group),
errors (error counters), saturation (queue depths where known).
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from typing import Any

_LOCK = threading.Lock()
_COUNTERS: dict[str, float] = defaultdict(float)
_DURATIONS: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=1000))


def inc(name: str, value: float = 1.0) -> None:
    with _LOCK:
        _COUNTERS[name] += value


def observe(name: str, value_ms: float) -> None:
    with _LOCK:
        _DURATIONS[name].append(value_ms)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(pct / 100.0 * (len(ordered) - 1))))
    return ordered[index]


def snapshot() -> dict[str, Any]:
    with _LOCK:
        counters = dict(_COUNTERS)
        durations = {name: list(values) for name, values in _DURATIONS.items()}
    latencies = {}
    for name, values in durations.items():
        latencies[name] = {
            "count": len(values),
            "p50_ms": round(_percentile(values, 50), 2),
            "p95_ms": round(_percentile(values, 95), 2),
            "p99_ms": round(_percentile(values, 99), 2),
        }
    return {"counters": counters, "latencies": latencies}


def render_text() -> str:
    data = snapshot()
    lines = []
    for name in sorted(data["counters"]):
        lines.append(f"{name} {data['counters'][name]:g}")
    for name in sorted(data["latencies"]):
        stats = data["latencies"][name]
        for key in ("p50_ms", "p95_ms", "p99_ms"):
            lines.append(f"{name}_{key} {stats[key]}")
        lines.append(f"{name}_count {stats['count']}")
    return "\n".join(lines) + "\n"


def reset() -> None:
    """Test hook."""
    with _LOCK:
        _COUNTERS.clear()
        _DURATIONS.clear()


def path_group(path: str) -> str:
    """Normalize a request path into a low-cardinality metric label."""
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "root"
    if parts[0] == "api" and len(parts) >= 2:
        if parts[1] == "v1" and len(parts) >= 3:
            return f"api_v1_{parts[2]}"
        return f"api_{parts[1]}"
    return parts[0]
