"""Paper (simulated) trade executor."""

from __future__ import annotations

from decimal import Decimal

from config import BotConfig
from models import ZERO, ExecutionResult, Opportunity


class PaperExecutor:
    """Simulated executor that can model simple execution failure rules."""

    def __init__(self, config: BotConfig) -> None:
        self.config = config

    def execute(self, opportunity: Opportunity) -> ExecutionResult:
        if opportunity.net_profit_base <= ZERO:
            return ExecutionResult(
                success=False,
                reason="profit turned negative before execution",
                realized_profit_base=ZERO,
                opportunity=opportunity,
            )

        return ExecutionResult(
            success=True,
            reason="executed in paper mode",
            realized_profit_base=opportunity.net_profit_base,
            opportunity=opportunity,
        )
