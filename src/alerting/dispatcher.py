"""Alert dispatcher — routes structured alert events to all configured backends.

Alert events:
  - opportunity_found
  - trade_executed
  - trade_reverted
  - trade_not_included
  - simulation_failed
  - system_error
  - daily_summary

Each backend receives the same (event_type, message, details) and decides
how to format and deliver it. Backends that fail are logged but don't
crash the bot.
"""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class AlertBackend(Protocol):
    """Protocol that all alert backends must satisfy."""

    @property
    def name(self) -> str: ...

    def send(self, event_type: str, message: str, details: dict | None = None) -> bool:
        """Send an alert. Returns True if delivered successfully."""
        ...


class AlertDispatcher:
    """Fan-out alerts to all registered backends.

    Failures in one backend don't block others or crash the bot.
    """

    def __init__(self, backends: list[AlertBackend] | None = None) -> None:
        self._backends: list[AlertBackend] = list(backends) if backends else []

    def add_backend(self, backend: AlertBackend) -> None:
        self._backends.append(backend)

    @property
    def backend_count(self) -> int:
        return len(self._backends)

    def alert(
        self,
        event_type: str,
        message: str,
        details: dict | None = None,
    ) -> int:
        """Send alert to all backends. Returns count of successful deliveries."""
        delivered = 0
        for backend in self._backends:
            try:
                ok = backend.send(event_type, message, details)
                if ok:
                    delivered += 1
                else:
                    logger.warning("Alert backend '%s' returned failure for %s",
                                   backend.name, event_type)
            except Exception as exc:
                logger.error("Alert backend '%s' error for %s: %s",
                             backend.name, event_type, exc)
        return delivered

    def opportunity_found(self, pair: str, buy_dex: str, sell_dex: str,
                          spread_pct: float, net_profit: float) -> int:
        msg = (f"Opportunity: {pair}\n"
               f"Buy: {buy_dex} → Sell: {sell_dex}\n"
               f"Spread: {spread_pct:.4f}%\n"
               f"Net profit: {net_profit:.6f}")
        return self.alert("opportunity_found", msg, {
            "pair": pair, "buy_dex": buy_dex, "sell_dex": sell_dex,
            "spread_pct": spread_pct, "net_profit": net_profit,
        })

    def trade_executed(self, pair: str, tx_hash: str, profit: float) -> int:
        msg = (f"Trade Executed: {pair}\n"
               f"TX: {tx_hash}\n"
               f"Profit: {profit:.6f}")
        return self.alert("trade_executed", msg, {
            "pair": pair, "tx_hash": tx_hash, "profit": profit,
        })

    def trade_reverted(self, pair: str, tx_hash: str, reason: str) -> int:
        msg = (f"Trade REVERTED: {pair}\n"
               f"TX: {tx_hash}\n"
               f"Reason: {reason}")
        return self.alert("trade_reverted", msg, {
            "pair": pair, "tx_hash": tx_hash, "reason": reason,
        })

    def system_error(self, component: str, error: str) -> int:
        msg = f"System Error in {component}:\n{error}"
        return self.alert("system_error", msg, {
            "component": component, "error": error,
        })

    def daily_summary(self, scans: int, opportunities: int, executed: int,
                      total_profit: float, reverts: int) -> int:
        msg = (f"Daily Summary\n"
               f"Scans: {scans}\n"
               f"Opportunities: {opportunities}\n"
               f"Executed: {executed}\n"
               f"Reverts: {reverts}\n"
               f"Total Profit: {total_profit:.6f}")
        return self.alert("daily_summary", msg, {
            "scans": scans, "opportunities": opportunities,
            "executed": executed, "total_profit": total_profit, "reverts": reverts,
        })
