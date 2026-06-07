"""Fixed-window, in-memory rate limiter (Task 4-D).

Per-IP request counting. In-memory only -- a distributed deployment would back this with
Redis, but the interface (`allow`) would stay the same.
"""
from __future__ import annotations

from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str, now: float) -> bool:
        """Record a hit for `key` at time `now`; return False if over the limit."""
        window_start = now - self.window_seconds
        hits = [t for t in self._hits[key] if t > window_start]
        if len(hits) >= self.max_requests:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True
