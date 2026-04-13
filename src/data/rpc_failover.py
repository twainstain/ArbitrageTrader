"""RPC failover — multi-endpoint provider with automatic failover.

Each chain can have multiple RPC URLs. If the primary fails, the provider
rotates to the next one. Tracks error counts per endpoint.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from web3 import Web3

logger = logging.getLogger(__name__)


@dataclass
class _EndpointState:
    url: str
    error_count: int = 0
    last_error_at: float = 0
    disabled_until: float = 0  # Unix timestamp — skip until this time


class RpcProvider:
    """Multi-endpoint RPC provider with automatic failover.

    Usage::

        provider = RpcProvider("ethereum", [
            "https://eth-mainnet.g.alchemy.com/v2/KEY",
            "https://eth.llamarpc.com",
            "https://rpc.ankr.com/eth",
        ])
        w3 = provider.get_web3()  # returns connected Web3 instance
    """

    def __init__(
        self,
        chain: str,
        urls: list[str],
        backoff_seconds: float = 30.0,
        max_errors_before_disable: int = 3,
    ) -> None:
        if not urls:
            raise ValueError(f"At least one RPC URL required for chain '{chain}'")
        self.chain = chain
        self.backoff_seconds = backoff_seconds
        self.max_errors_before_disable = max_errors_before_disable
        self._endpoints = [_EndpointState(url=u) for u in urls]
        self._current_index = 0

    @property
    def endpoint_count(self) -> int:
        return len(self._endpoints)

    @property
    def current_url(self) -> str:
        return self._endpoints[self._current_index].url

    def get_web3(self) -> Web3:
        """Return a Web3 instance connected to the best available endpoint."""
        url = self._select_endpoint()
        return Web3(Web3.HTTPProvider(url))

    def record_success(self) -> None:
        """Record a successful RPC call on the current endpoint."""
        ep = self._endpoints[self._current_index]
        ep.error_count = 0

    def record_error(self) -> None:
        """Record a failed RPC call and potentially rotate to next endpoint."""
        now = time.time()
        ep = self._endpoints[self._current_index]
        ep.error_count += 1
        ep.last_error_at = now

        if ep.error_count >= self.max_errors_before_disable:
            ep.disabled_until = now + self.backoff_seconds
            logger.warning(
                "RPC endpoint disabled for %ds: %s (chain=%s, errors=%d)",
                self.backoff_seconds, ep.url[:60], self.chain, ep.error_count,
            )
            self._rotate()

    def _select_endpoint(self) -> str:
        """Select the best available endpoint, rotating past disabled ones."""
        now = time.time()
        tried = 0
        while tried < len(self._endpoints):
            ep = self._endpoints[self._current_index]
            if ep.disabled_until <= now:
                return ep.url
            self._rotate()
            tried += 1

        # All disabled — re-enable the least-recently-errored one.
        best = min(self._endpoints, key=lambda e: e.last_error_at)
        best.disabled_until = 0
        best.error_count = 0
        logger.warning("All RPC endpoints disabled — re-enabling %s", best.url[:60])
        return best.url

    def _rotate(self) -> None:
        """Move to the next endpoint in the list."""
        self._current_index = (self._current_index + 1) % len(self._endpoints)

    def to_dict(self) -> dict:
        now = time.time()
        return {
            "chain": self.chain,
            "current_url": self.current_url[:60] + "...",
            "endpoints": [
                {
                    "url": ep.url[:60] + ("..." if len(ep.url) > 60 else ""),
                    "error_count": ep.error_count,
                    "disabled": ep.disabled_until > now,
                }
                for ep in self._endpoints
            ],
        }
