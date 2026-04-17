"""Cache for low-liquidity DEX/chain pairs.

Pairs that return zero quotes or have insufficient liquidity are cached
so we don't waste RPC calls checking them every scan cycle. The cache
auto-expires after a configurable TTL (default 3 hours).

Usage::

    cache = LiquidityCache(ttl_seconds=3 * 3600)
    cache.mark_skip("Sushi-Polygon", "polygon", "zero quotes")

    if cache.should_skip("Sushi-Polygon", "polygon"):
        # Skip this DEX — it's in the cache
        pass
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_TTL = 3 * 3600  # 3 hours


@dataclass
class CacheEntry:
    """A single cached skip entry."""
    dex: str
    chain: str
    reason: str
    cached_at: float
    ttl: float
    skip_count: int = 0

    @property
    def expired(self) -> bool:
        return time.monotonic() - self.cached_at >= self.ttl


class LiquidityCache:
    """Thread-safe cache for DEX/chain pairs that should be skipped.

    When a DEX on a chain returns zero quotes or has low liquidity,
    call ``mark_skip()`` to cache it. Subsequent ``should_skip()``
    calls return True until the TTL expires.

    After expiry, the next scan will re-check the DEX. If it still
    returns zero, it gets re-cached.
    """

    # When a (dex, chain) fails this many times in a row, escalate its
    # cache TTL so we don't keep re-checking a known-broken endpoint every
    # 15 minutes. Mostly affects local dev (where public RPCs reject the
    # quoter call) and chains with degraded paid endpoints — saves the
    # ~timeout × N cost per scan that would otherwise repeat indefinitely.
    _FAILURE_ESCALATION_THRESHOLD = 5
    _ESCALATED_TTL = 60 * 60  # 1 hour

    def __init__(self, ttl_seconds: float = DEFAULT_TTL) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}
        self._consecutive_failures: dict[str, int] = {}
        self._lock = threading.Lock()
        self._total_skips = 0

    @staticmethod
    def _key(dex: str, chain: str) -> str:
        return f"{dex}:{chain}".lower()

    def should_skip(self, dex: str, chain: str) -> bool:
        """Check if a DEX/chain pair should be skipped."""
        key = self._key(dex, chain)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.expired:
                del self._cache[key]
                logger.info("Cache expired for %s on %s — will re-check", dex, chain)
                return False
            entry.skip_count += 1
            self._total_skips += 1
            return True

    def mark_skip(self, dex: str, chain: str, reason: str, ttl_override: float | None = None) -> None:
        """Cache a DEX/chain pair as low-liquidity / zero-quote.

        Args:
            ttl_override: Custom TTL in seconds. If None, uses the default.
                          Use shorter TTL for transient errors (timeout, rate limit).

        After ``_FAILURE_ESCALATION_THRESHOLD`` consecutive failures (with no
        intervening success) the TTL is escalated to ``_ESCALATED_TTL`` to
        avoid re-checking known-broken quoters every 15min.
        """
        key = self._key(dex, chain)
        with self._lock:
            self._consecutive_failures[key] = self._consecutive_failures.get(key, 0) + 1
            failures = self._consecutive_failures[key]
            if ttl_override is not None:
                entry_ttl = ttl_override
            elif failures >= self._FAILURE_ESCALATION_THRESHOLD:
                entry_ttl = self._ESCALATED_TTL
            else:
                entry_ttl = self._ttl
            existing = self._cache.get(key)
            if existing and not existing.expired:
                return  # Already cached
            self._cache[key] = CacheEntry(
                dex=dex, chain=chain, reason=reason,
                cached_at=time.monotonic(), ttl=entry_ttl,
            )
        if failures >= self._FAILURE_ESCALATION_THRESHOLD:
            logger.warning("Cached skip (ESCALATED): %s on %s (%s) — TTL %.0fm "
                           "after %d consecutive failures",
                           dex, chain, reason, entry_ttl / 60, failures)
        else:
            logger.info("Cached skip: %s on %s (%s) — TTL %.0fm",
                         dex, chain, reason, entry_ttl / 60)

    def mark_success(self, dex: str, chain: str) -> None:
        """Reset the consecutive-failure counter for a (dex, chain).

        Call from the quoter success path so a quoter that recovers from
        a transient outage isn't permanently demoted to the escalated TTL.
        """
        key = self._key(dex, chain)
        with self._lock:
            if key in self._consecutive_failures:
                self._consecutive_failures[key] = 0

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        """Number of active (non-expired) entries."""
        with self._lock:
            self._purge_expired()
            return len(self._cache)

    @property
    def total_skips(self) -> int:
        """Total number of skip hits since creation."""
        return self._total_skips

    def get_cached(self) -> list[dict]:
        """Return all active cache entries as dicts (for API/dashboard)."""
        with self._lock:
            self._purge_expired()
            return [
                {
                    "dex": e.dex,
                    "chain": e.chain,
                    "reason": e.reason,
                    "age_minutes": round((time.monotonic() - e.cached_at) / 60, 1),
                    "ttl_minutes": round(self._ttl / 60, 1),
                    "skip_count": e.skip_count,
                }
                for e in self._cache.values()
            ]

    def stats(self) -> dict:
        """Cache statistics."""
        with self._lock:
            self._purge_expired()
            return {
                "cached_pairs": len(self._cache),
                "total_skips": self._total_skips,
                "ttl_minutes": round(self._ttl / 60, 1),
                "entries": [f"{e.dex}:{e.chain}" for e in self._cache.values()],
            }

    def _purge_expired(self) -> None:
        """Remove expired entries (call while holding lock)."""
        expired = [k for k, v in self._cache.items() if v.expired]
        for k in expired:
            del self._cache[k]
