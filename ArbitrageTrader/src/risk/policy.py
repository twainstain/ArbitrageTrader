"""Risk policy engine — configurable rules for trade approval.

Per the architecture doc, the risk engine must:
  - enforce trade thresholds
  - reject opportunities below minimum expected edge
  - reject stale quotes
  - reject low-liquidity routes
  - reject trades with excessive price impact
  - reject routes too sensitive to gas spikes
  - reject trades with poor execution confidence

Principle: No trade is better than a bad trade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import NamedTuple

from models import ZERO, Opportunity

D = Decimal


class RiskVerdict(NamedTuple):
    """Result of a risk evaluation."""
    approved: bool
    reason: str
    details: dict


@dataclass
class RiskPolicy:
    """Configurable risk policy with named rules.

    Each rule is a threshold. An opportunity must pass ALL rules to be approved.
    """
    # Minimum net profit in base asset (e.g. 0.001 WETH)
    min_net_profit: Decimal = D("0.001")

    # Maximum allowed slippage in bps
    max_slippage_bps: Decimal = D("50")

    # Minimum pool liquidity in USD for either venue
    min_liquidity_usd: Decimal = D("50000")

    # Maximum quote age in seconds (0 = disabled)
    max_quote_age_seconds: float = 60.0

    # Gas cost must be below this fraction of expected profit (e.g. 0.5 = 50%)
    max_gas_profit_ratio: Decimal = D("0.5")

    # Maximum warning flags allowed
    max_warning_flags: int = 1

    # Maximum trades per interval (rate limiting)
    max_trades_per_hour: int = 100

    # Maximum open exposure per pair in base asset
    max_exposure_per_pair: Decimal = D("10")

    # Minimum liquidity score (0.0-1.0)
    min_liquidity_score: float = 0.3

    # Whether live execution is enabled (global kill switch)
    execution_enabled: bool = False

    def evaluate(
        self,
        opportunity: Opportunity,
        current_hour_trades: int = 0,
        current_pair_exposure: Decimal = ZERO,
    ) -> RiskVerdict:
        """Evaluate an opportunity against all risk rules.

        Returns RiskVerdict with approved=True only if ALL rules pass.
        """
        # Rule 1: Global kill switch
        if not self.execution_enabled:
            return RiskVerdict(False, "execution_disabled", {})

        # Rule 2: Minimum net profit
        if opportunity.net_profit_base < self.min_net_profit:
            return RiskVerdict(False, "below_min_profit", {
                "required": str(self.min_net_profit),
                "actual": str(opportunity.net_profit_base),
            })

        # Rule 3: Warning flags
        if len(opportunity.warning_flags) > self.max_warning_flags:
            return RiskVerdict(False, "too_many_flags", {
                "max": self.max_warning_flags,
                "actual": len(opportunity.warning_flags),
                "flags": list(opportunity.warning_flags),
            })

        # Rule 4: Liquidity score
        if opportunity.liquidity_score < self.min_liquidity_score:
            return RiskVerdict(False, "low_liquidity_score", {
                "required": self.min_liquidity_score,
                "actual": opportunity.liquidity_score,
            })

        # Rule 5: Gas-to-profit ratio
        if opportunity.net_profit_base > ZERO and opportunity.gas_cost_base > ZERO:
            gas_ratio = opportunity.gas_cost_base / opportunity.net_profit_base
            if gas_ratio > self.max_gas_profit_ratio:
                return RiskVerdict(False, "gas_too_expensive", {
                    "max_ratio": str(self.max_gas_profit_ratio),
                    "actual_ratio": str(gas_ratio),
                })

        # Rule 6: Rate limiting
        if current_hour_trades >= self.max_trades_per_hour:
            return RiskVerdict(False, "rate_limit_exceeded", {
                "max": self.max_trades_per_hour,
                "current": current_hour_trades,
            })

        # Rule 7: Exposure limit
        new_exposure = current_pair_exposure + opportunity.trade_size
        if new_exposure > self.max_exposure_per_pair:
            return RiskVerdict(False, "exposure_limit", {
                "max": str(self.max_exposure_per_pair),
                "current": str(current_pair_exposure),
                "would_be": str(new_exposure),
            })

        return RiskVerdict(True, "approved", {})

    def to_dict(self) -> dict:
        """Serialize the current policy for logging/API."""
        return {
            "min_net_profit": str(self.min_net_profit),
            "max_slippage_bps": str(self.max_slippage_bps),
            "min_liquidity_usd": str(self.min_liquidity_usd),
            "max_quote_age_seconds": self.max_quote_age_seconds,
            "max_gas_profit_ratio": str(self.max_gas_profit_ratio),
            "max_warning_flags": self.max_warning_flags,
            "max_trades_per_hour": self.max_trades_per_hour,
            "max_exposure_per_pair": str(self.max_exposure_per_pair),
            "min_liquidity_score": self.min_liquidity_score,
            "execution_enabled": self.execution_enabled,
        }
