"""Paper (simulated) trade executor.

Executor hierarchy
------------------
The bot uses a simple **Executor protocol**: any object with an
``execute(opportunity: Opportunity) -> ExecutionResult`` method can serve as
the executor.  Two concrete implementations exist:

* **PaperExecutor** (this module) -- Simulated execution that never touches
  the chain.  It validates that expected profit is positive and returns an
  ``ExecutionResult`` as if the trade succeeded.  This is the **default** and
  the safe choice for development, backtesting, and dry-run scanning.

* **ChainExecutor** (``chain_executor.py``) -- Real on-chain execution via
  the ``FlashArbExecutor`` Solidity contract.  Requires a funded wallet
  (``EXECUTOR_PRIVATE_KEY``) and a deployed contract address
  (``EXECUTOR_CONTRACT``) in ``.env``.  Must be explicitly opted into with the
  ``--execute`` CLI flag; it is **never** activated automatically.

Why PaperExecutor exists
~~~~~~~~~~~~~~~~~~~~~~~~
1. **Safety** -- The default mode should never risk capital.  PaperExecutor
   lets the full pipeline (detect -> price -> risk -> execute -> observe) run
   end-to-end without sending any transactions.
2. **Testing** -- Unit and integration tests exercise the execution path
   without needing an RPC connection or funded wallet.
3. **Backtesting** -- Historical replay mode pairs naturally with paper
   execution to evaluate strategy performance on past data.

When to use which
~~~~~~~~~~~~~~~~~
* Development / CI / tests: PaperExecutor (default -- no flag needed).
* Live monitoring / dry-run dashboards: PaperExecutor (explicit ``--dry-run``).
* Real trading on mainnet: ChainExecutor (``--execute`` flag + confirmation).
"""

from __future__ import annotations

from decimal import Decimal

from core.config import BotConfig
from core.models import ZERO, ExecutionResult, Opportunity


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
