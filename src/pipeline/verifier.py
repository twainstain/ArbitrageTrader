"""On-chain result verifier — extracts structured realized PnL from receipts.

Implements the ResultVerifier protocol from lifecycle.py.
Verifies that a submitted transaction was included, checks for reverts,
extracts gas used, and calculates actual profit from on-chain state.

Usage::

    verifier = OnChainVerifier(w3, contract_address, quote_decimals=6)
    result = verifier.verify(tx_hash)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from web3 import Web3

from core.models import Opportunity

D = Decimal
logger = logging.getLogger(__name__)

# ERC-20 Transfer event signature: Transfer(address,address,uint256)
TRANSFER_EVENT_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()
PROFIT_REALIZED_EVENT_TOPIC = Web3.keccak(
    text="ProfitRealized(address,uint256,uint256)"
).hex()


@dataclass(frozen=True)
class VerificationResult:
    included: bool
    reverted: bool
    gas_used: int
    realized_profit_quote: Decimal = D("0")
    gas_cost_base: Decimal = D("0")
    actual_profit_base: Decimal = D("0")
    block_number: int = 0
    profit_currency: str = ""


class OnChainVerifier:
    """Verify on-chain transaction results and extract realized PnL fields.

    Checks tx receipt for inclusion/revert, calculates gas cost,
    extracts realized quote-token profit, and only computes base-unit
    net profit when an opportunity context makes that conversion safe.
    """

    def __init__(
        self,
        w3: Web3,
        contract_address: str,
        quote_decimals: int = 6,
        timeout: int = 120,
    ) -> None:
        self.w3 = w3
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.quote_decimals = quote_decimals
        self.timeout = timeout

    def verify(
        self,
        tx_hash: str,
        opportunity: Opportunity | None = None,
    ) -> VerificationResult:
        """Verify a transaction and return structured realized-PnL fields.

        - included: True if the tx was mined in a block
        - reverted: True if the tx reverted (status=0)
        - gas_used: actual gas consumed
        - realized_profit_quote: raw realized profit in the quote token
        - gas_cost_base: gas cost in the chain's base gas asset
        - actual_profit_base: realized net profit in base units only when
          opportunity context is provided and conversion is safe
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        except Exception as exc:
            logger.warning("Could not fetch receipt for %s: %s", tx_hash, exc)
            return VerificationResult(False, False, 0)

        if receipt is None:
            return VerificationResult(False, False, 0)

        included = receipt["blockNumber"] > 0
        reverted = receipt["status"] == 0
        gas_used = receipt["gasUsed"]
        block_number = int(receipt.get("blockNumber") or 0)

        if reverted or not included:
            return VerificationResult(
                included=included,
                reverted=reverted,
                gas_used=gas_used,
                block_number=block_number,
            )

        profit_quote = self._extract_profit(receipt)
        gas_cost_base = self._calculate_gas_cost(receipt)
        profit_currency = ""
        actual_profit_base = D("0")
        if opportunity is not None and opportunity.trade_size > D("0"):
            quote_per_base = opportunity.cost_to_buy_quote / opportunity.trade_size
            if quote_per_base > D("0"):
                actual_profit_base = (profit_quote / quote_per_base) - gas_cost_base
            pair_parts = opportunity.pair.split("/", 1)
            if len(pair_parts) == 2:
                profit_currency = pair_parts[1]

        logger.info(
            "Verified %s: included=%s gas=%d profit_quote=%s gas_cost_base=%s actual_base=%s",
            tx_hash, included, gas_used, profit_quote, gas_cost_base, actual_profit_base,
        )
        return VerificationResult(
            included=included,
            reverted=reverted,
            gas_used=gas_used,
            realized_profit_quote=profit_quote,
            gas_cost_base=gas_cost_base,
            actual_profit_base=actual_profit_base,
            block_number=block_number,
            profit_currency=profit_currency,
        )

    def _extract_profit(self, receipt: dict) -> Decimal:
        """Extract profit from ProfitRealized or legacy ERC-20 Transfer events.

        Prefers the explicit ProfitRealized event emitted by the executor
        contract. Falls back to legacy Transfer logs for backward
        compatibility with already-deployed contracts.
        """
        for log_entry in receipt.get("logs", []):
            topics = log_entry.get("topics", [])
            if not topics:
                continue
            topic_hex = topics[0].hex() if isinstance(topics[0], bytes) else topics[0]
            if topic_hex != PROFIT_REALIZED_EVENT_TOPIC:
                continue
            data_hex = log_entry["data"].hex() if isinstance(log_entry["data"], bytes) else log_entry["data"].replace("0x", "")
            if len(data_hex) >= 128:
                # Event data packs: profit, totalOwed
                profit_raw = int(data_hex[:64], 16)
                return D(profit_raw) / D(10 ** self.quote_decimals)

        profit = D("0")
        contract_lower = self.contract_address.lower()

        for log_entry in receipt.get("logs", []):
            topics = log_entry.get("topics", [])
            if not topics:
                continue

            # Check if this is a Transfer event.
            topic_hex = topics[0].hex() if isinstance(topics[0], bytes) else topics[0]
            if topic_hex != TRANSFER_EVENT_TOPIC:
                continue

            if len(topics) < 3:
                continue

            from_addr = "0x" + (topics[1].hex() if isinstance(topics[1], bytes) else topics[1])[-40:]
            if from_addr.lower() == contract_lower:
                # Legacy fallback: outgoing transfer from contract, which is a
                # closer proxy for realized payout than incoming loan/swap flows.
                raw_amount = int(log_entry["data"].hex() if isinstance(log_entry["data"], bytes) else log_entry["data"], 16)
                profit += D(raw_amount) / D(10 ** self.quote_decimals)

        return profit

    def _calculate_gas_cost(self, receipt: dict) -> Decimal:
        """Calculate gas cost in ETH from the receipt."""
        gas_used = receipt["gasUsed"]
        effective_gas_price = receipt.get("effectiveGasPrice", 0)
        gas_cost_wei = gas_used * effective_gas_price
        return D(gas_cost_wei) / D(10 ** 18)


class PnLReconciler:
    """Compare actual on-chain profit with expected off-chain estimates.

    Flags significant deviations for alerting and analysis.
    """

    def __init__(self, deviation_threshold_pct: float = 20.0) -> None:
        self.deviation_threshold_pct = deviation_threshold_pct
        self._reconciliations: list[dict] = []

    def reconcile(
        self,
        opp_id: str,
        expected_profit: Decimal,
        actual_profit: Decimal,
        gas_used: int,
        estimated_gas: Decimal,
    ) -> dict:
        """Compare expected vs actual profit. Returns reconciliation report."""
        deviation = D("0")
        deviation_pct = 0.0
        if expected_profit > D("0"):
            deviation = actual_profit - expected_profit
            deviation_pct = float(deviation / expected_profit * D("100"))

        gas_deviation = 0.0
        if estimated_gas > D("0"):
            gas_deviation = float((D(gas_used) - estimated_gas) / estimated_gas * D("100"))

        is_significant = abs(deviation_pct) > self.deviation_threshold_pct

        report = {
            "opp_id": opp_id,
            "expected_profit": str(expected_profit),
            "actual_profit": str(actual_profit),
            "deviation": str(deviation),
            "deviation_pct": round(deviation_pct, 2),
            "gas_used": gas_used,
            "estimated_gas": str(estimated_gas),
            "gas_deviation_pct": round(gas_deviation, 2),
            "significant_deviation": is_significant,
        }

        self._reconciliations.append(report)

        if is_significant:
            logger.warning(
                "PnL deviation for %s: expected=%s actual=%s (%.1f%%)",
                opp_id, expected_profit, actual_profit, deviation_pct,
            )

        return report

    @property
    def recent_reconciliations(self) -> list[dict]:
        """Return the last 100 reconciliation reports."""
        return self._reconciliations[-100:]

    @property
    def summary(self) -> dict:
        """Aggregate reconciliation stats."""
        if not self._reconciliations:
            return {"total": 0}

        deviations = [r["deviation_pct"] for r in self._reconciliations]
        significant = [r for r in self._reconciliations if r["significant_deviation"]]
        return {
            "total": len(self._reconciliations),
            "significant_deviations": len(significant),
            "avg_deviation_pct": round(sum(deviations) / len(deviations), 2),
            "max_deviation_pct": round(max(deviations, key=abs), 2),
        }
