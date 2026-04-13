"""Circuit breaker — auto-pause execution on repeated failures.

Per the architecture doc safety controls:
  - pause on repeated reverts
  - pause on stale data
  - pause on RPC degradation
  - max exposure per block window

The CircuitBreaker tracks recent events in a sliding window and trips
(pauses execution) when thresholds are breached. It auto-resets after
a cooldown period.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class BreakerState(str, Enum):
    """State machine: CLOSED → OPEN → HALF_OPEN → CLOSED.

    CLOSED:    Normal operation, all events monitored.
    OPEN:      Tripped by reverts/stale/RPC errors. Execution blocked.
    HALF_OPEN: Cooldown expired. One probe trade allowed. If it succeeds
               → CLOSED (recovered). If it fails → back to OPEN.
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Thresholds for the circuit breaker."""
    # Reverts: trip after N reverts within window_seconds
    max_reverts: int = 3
    revert_window_seconds: float = 300.0  # 5 minutes

    # Stale data: trip if no fresh quote for this many seconds
    max_stale_seconds: float = 120.0

    # RPC errors: trip after N errors within window_seconds
    max_rpc_errors: int = 5
    rpc_error_window_seconds: float = 60.0

    # Block window exposure: max trades within N blocks
    max_trades_per_block_window: int = 3
    block_window_size: int = 10

    # Cooldown: how long to stay open before allowing a probe
    cooldown_seconds: float = 300.0


class CircuitBreaker:
    """Sliding-window circuit breaker for execution safety.

    Records events (reverts, RPC errors, stale data) and trips when
    thresholds are exceeded. Once tripped, execution is paused for
    cooldown_seconds, then enters half-open state to probe.
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self._lock = Lock()
        self._state = BreakerState.CLOSED
        self._trip_reason = ""
        self._tripped_at: float = 0
        self._last_fresh_quote_at: float = time.time()

        # Sliding window event deques using deque for O(1) append/popleft.
        # Timestamps enable time-based windowing: old events are pruned automatically
        # so the breaker doesn't trip from stale history.
        self._reverts: deque[float] = deque()
        self._rpc_errors: deque[float] = deque()
        # Block trades use (block_number, timestamp) — block-based limit prevents
        # execution clustering (time-based would allow bunching during high activity).
        self._block_trades: deque[tuple[int, float]] = deque()

    @property
    def state(self) -> BreakerState:
        with self._lock:
            return self._check_state()

    @property
    def is_open(self) -> bool:
        return self.state == BreakerState.OPEN

    @property
    def trip_reason(self) -> str:
        with self._lock:
            return self._trip_reason

    def allows_execution(self) -> tuple[bool, str]:
        """Check if execution is allowed. Returns (allowed, reason)."""
        with self._lock:
            state = self._check_state()
            if state == BreakerState.OPEN:
                return False, f"circuit_open:{self._trip_reason}"
            if state == BreakerState.HALF_OPEN:
                return True, "half_open_probe"
            return True, "circuit_closed"

    # --- Event recording ---

    def record_revert(self) -> None:
        """Record a transaction revert."""
        with self._lock:
            now = time.time()
            self._reverts.append(now)
            self._prune_window(self._reverts, self.config.revert_window_seconds, now)
            if len(self._reverts) >= self.config.max_reverts:
                self._trip("repeated_reverts")

    def record_rpc_error(self) -> None:
        """Record an RPC call failure."""
        with self._lock:
            now = time.time()
            self._rpc_errors.append(now)
            self._prune_window(self._rpc_errors, self.config.rpc_error_window_seconds, now)
            if len(self._rpc_errors) >= self.config.max_rpc_errors:
                self._trip("rpc_degradation")

    def record_fresh_quote(self) -> None:
        """Record that a fresh quote was received (resets stale timer)."""
        with self._lock:
            self._last_fresh_quote_at = time.time()

    def record_trade_at_block(self, block_number: int) -> None:
        """Record a trade submission at a block number."""
        with self._lock:
            now = time.time()
            self._block_trades.append((block_number, now))
            # Prune trades outside the block window.
            min_block = block_number - self.config.block_window_size
            while self._block_trades and self._block_trades[0][0] < min_block:
                self._block_trades.popleft()
            if len(self._block_trades) >= self.config.max_trades_per_block_window:
                self._trip("block_window_exposure")

    def record_execution_success(self) -> None:
        """Record a successful execution — resets half-open to closed."""
        with self._lock:
            if self._state == BreakerState.HALF_OPEN:
                logger.info("Circuit breaker: probe succeeded, resetting to CLOSED")
                self._state = BreakerState.CLOSED
                self._trip_reason = ""

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = BreakerState.CLOSED
            self._trip_reason = ""
            self._reverts.clear()
            self._rpc_errors.clear()
            self._block_trades.clear()
            self._last_fresh_quote_at = time.time()

    def to_dict(self) -> dict:
        """Serialize current state for API/logging."""
        with self._lock:
            now = time.time()
            return {
                "state": self._check_state().value,
                "trip_reason": self._trip_reason,
                "recent_reverts": len(self._reverts),
                "recent_rpc_errors": len(self._rpc_errors),
                "seconds_since_fresh_quote": round(now - self._last_fresh_quote_at, 1),
                "trades_in_block_window": len(self._block_trades),
                "cooldown_remaining": max(0, round(
                    self.config.cooldown_seconds - (now - self._tripped_at), 1
                )) if self._state == BreakerState.OPEN else 0,
            }

    # --- Internal ---

    def _check_state(self) -> BreakerState:
        """Check and possibly transition state (must hold lock)."""
        now = time.time()

        # Stale check ALWAYS runs (even when CLOSED) because no fresh quote
        # is a hard fault — RPC may be down or market data frozen. We should
        # not trade on potentially stale prices regardless of other conditions.
        if self._state == BreakerState.CLOSED:
            stale_duration = now - self._last_fresh_quote_at
            if stale_duration > self.config.max_stale_seconds:
                self._trip("stale_data")
                return self._state

        # If open, check if cooldown has expired → half-open.
        if self._state == BreakerState.OPEN:
            if now - self._tripped_at > self.config.cooldown_seconds:
                self._state = BreakerState.HALF_OPEN
                logger.info("Circuit breaker: cooldown expired, entering HALF_OPEN")

        return self._state

    def _trip(self, reason: str) -> None:
        """Trip the breaker (must hold lock)."""
        if self._state != BreakerState.OPEN:
            logger.warning("Circuit breaker TRIPPED: %s", reason)
            self._state = BreakerState.OPEN
            self._trip_reason = reason
            self._tripped_at = time.time()

    @staticmethod
    def _prune_window(dq: deque, window_seconds: float, now: float) -> None:
        """Remove entries older than the window."""
        cutoff = now - window_seconds
        while dq and dq[0] < cutoff:
            dq.popleft()
