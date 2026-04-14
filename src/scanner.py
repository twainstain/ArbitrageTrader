"""Scanner module — ranking, filtering, and alerting for arbitrage opportunities.

Per the arbitrage scanner doc, a scanner should:
  1. Discover opportunities (strategy.py does this)
  2. Rank by more than raw spread (this module)
  3. Apply risk filters and warning flags (this module)
  4. Alert only for actionable setups (this module)

The scanner wraps ArbitrageStrategy and adds:
  - Multi-factor ranking (net profit, liquidity, freshness, risk flags)
  - Warning flag enrichment
  - Alert thresholds with configurable callbacks
  - Opportunity history for "recently expired" tracking

Usage::

    scanner = OpportunityScanner(config, strategy)
    ranked = scanner.scan_and_rank(quotes)
    # ranked is a list of Opportunity sorted by composite score, best first
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal

from config import BotConfig, PairConfig
from log import get_logger
from models import ZERO, MarketQuote, Opportunity

D = Decimal
from strategy import ArbitrageStrategy

logger = get_logger(__name__)

D = Decimal


@dataclass
class ScanResult:
    """Result of a full scan cycle with ranked opportunities."""
    timestamp: float
    total_quotes: int
    opportunities: list[Opportunity]    # Sorted by composite_score descending.
    rejected_count: int                 # Opportunities below threshold or flagged.
    best: Opportunity | None            # Top-ranked opportunity, or None.


class OpportunityScanner:
    """Scan, rank, filter, and alert on arbitrage opportunities.

    Wraps ArbitrageStrategy with multi-factor ranking and risk assessment.
    """

    def __init__(
        self,
        config: BotConfig,
        strategy: ArbitrageStrategy | None = None,
        pairs: list[PairConfig] | None = None,
        alert_min_net_profit: Decimal = ZERO,
        alert_max_warning_flags: int = 1,
    ) -> None:
        self.config = config
        self.strategy = strategy or ArbitrageStrategy(config, pairs=pairs)
        self.alert_min_net_profit = alert_min_net_profit
        self.alert_max_warning_flags = alert_max_warning_flags
        self._history: list[ScanResult] = []

    def scan_and_rank(self, quotes: list[MarketQuote]) -> ScanResult:
        """Evaluate all cross-DEX pairs, rank, filter, and return a ScanResult."""
        # Find ALL opportunities (not just the best one).
        opportunities = self._find_all_opportunities(quotes)

        # Rank by composite score.
        scored = [(self._composite_score(opp), opp) for opp in opportunities]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Split into actionable vs rejected.
        actionable = []
        rejected_count = 0
        for score, opp in scored:
            if self._passes_alert_filter(opp):
                actionable.append(opp)
            else:
                rejected_count += 1

        result = ScanResult(
            timestamp=time.time(),
            total_quotes=len(quotes),
            opportunities=actionable,
            rejected_count=rejected_count,
            best=actionable[0] if actionable else None,
        )

        # Emit alert for top opportunity.
        if result.best:
            self._emit_alert(result.best)

        self._history.append(result)
        return result

    @property
    def recent_history(self) -> list[ScanResult]:
        """Return the last 100 scan results for analysis."""
        return self._history[-100:]

    def _find_all_opportunities(self, quotes: list[MarketQuote]) -> list[Opportunity]:
        """Evaluate every cross-DEX pair and return all profitable opportunities.

        Filters out cross-chain pairs (can't be executed atomically) and
        opportunities from pools with very low liquidity (inflated spreads).
        """
        if len(quotes) < 2:
            return []

        # Pre-compute per-chain medians for same-chain price consistency check.
        # This catches thin pools that return stale prices indistinguishable
        # from deep pools via price-impact estimation (e.g. Camelot WETH/USDT
        # on Arbitrum returns $2276 while Uniswap returns $2340).
        _chain_medians = self._compute_chain_medians(quotes)

        results: list[Opportunity] = []
        skipped_same_dex = 0
        skipped_diff_pair = 0
        skipped_unprofitable = 0
        skipped_cross_chain = 0
        skipped_low_liq = 0
        skipped_price_deviation = 0
        evaluated = 0

        for buy_quote in quotes:
            for sell_quote in quotes:
                if buy_quote.dex == sell_quote.dex:
                    skipped_same_dex += 1
                    continue
                if buy_quote.pair != sell_quote.pair:
                    skipped_diff_pair += 1
                    continue
                evaluated += 1
                opp = self.strategy.evaluate_pair(buy_quote, sell_quote)
                if opp is None:
                    skipped_unprofitable += 1
                    continue
                # Skip cross-chain opportunities — can't atomic execute.
                if opp.is_cross_chain:
                    skipped_cross_chain += 1
                    continue
                # --- Liquidity filter (3 cases) ---
                #
                # Why $1M: a 1 WETH flash loan (~$2300) in a $50K pool has
                # ~4.6% price impact, which eats the entire spread.  $1M
                # keeps impact below ~0.1% for our trade sizes.  Derived
                # from constant-product math: impact ≈ trade_size / TVL.
                #
                # Case 1: Both sides report liquidity, but one is thin.
                #   Example: Uniswap $22M, Camelot $50K → reject.
                #
                # Case 2: One side reports liquidity, the other returns 0
                #   (estimation failed — e.g., Algebra quoter can't handle
                #   small amounts).  Asymmetric data = unreliable spread.
                #   This catches the Camelot WETH/USDT false positive where
                #   Camelot returns $0 liquidity but Uniswap returns $22M.
                #
                # Case 3: BOTH sides are 0.  We let these through because
                #   both quoters failed equally — we can't tell if the pool
                #   is thin or if the estimation just doesn't work for this
                #   DEX type.  The outlier filter and strategy warning flags
                #   provide secondary protection.
                buy_liq = buy_quote.liquidity_usd
                sell_liq = sell_quote.liquidity_usd
                min_liq = min(buy_liq, sell_liq)
                max_liq = max(buy_liq, sell_liq)
                if min_liq > ZERO and min_liq < D("1000000"):
                    skipped_low_liq += 1
                    continue
                if min_liq == ZERO and max_liq > ZERO:
                    skipped_low_liq += 1
                    continue
                # Same-chain price consistency: reject if either quote's
                # price deviates >2% from the chain median for that pair.
                # This catches thin pools that fool liquidity estimation
                # (e.g. Camelot returning stale prices with zero impact).
                if self._price_deviates_from_chain(buy_quote, _chain_medians, D("0.02")):
                    skipped_price_deviation += 1
                    logger.info(
                        "Price deviation: %s on %s deviates from chain median",
                        buy_quote.pair, buy_quote.dex,
                    )
                    continue
                if self._price_deviates_from_chain(sell_quote, _chain_medians, D("0.02")):
                    skipped_price_deviation += 1
                    logger.info(
                        "Price deviation: %s on %s deviates from chain median",
                        sell_quote.pair, sell_quote.dex,
                    )
                    continue
                results.append(opp)

        logger.info(
            "[scanner] %d quotes → %d pairs evaluated | "
            "unprofitable=%d cross_chain=%d low_liq=%d price_dev=%d | %d passed",
            len(quotes), evaluated,
            skipped_unprofitable, skipped_cross_chain, skipped_low_liq,
            skipped_price_deviation, len(results),
        )
        return results

    @staticmethod
    def _compute_chain_medians(quotes: list[MarketQuote]) -> dict[str, Decimal]:
        """Compute median mid-price per (pair, chain) for consistency checks.

        Returns a dict keyed by "pair:chain" → median mid-price.
        Chain is extracted from the DEX name suffix (e.g. "Uniswap-Arbitrum" → "arbitrum").
        """
        import statistics
        TWO = D("2")
        by_pair_chain: dict[str, list[Decimal]] = {}
        for q in quotes:
            parts = q.dex.rsplit("-", 1)
            chain = parts[1].lower() if len(parts) == 2 else ""
            if not chain:
                continue
            key = f"{q.pair}:{chain}"
            mid = (q.buy_price + q.sell_price) / TWO
            by_pair_chain.setdefault(key, []).append(mid)

        medians: dict[str, Decimal] = {}
        for key, mids in by_pair_chain.items():
            if len(mids) >= 2:
                medians[key] = statistics.median(mids)
        return medians

    @staticmethod
    def _price_deviates_from_chain(
        quote: MarketQuote,
        chain_medians: dict[str, Decimal],
        max_deviation: Decimal,
    ) -> bool:
        """Return True if a quote's price deviates from its chain median.

        Only triggers when there are 2+ quotes for the same pair on the
        same chain — ensures we have a reliable baseline to compare against.
        """
        TWO = D("2")
        parts = quote.dex.rsplit("-", 1)
        chain = parts[1].lower() if len(parts) == 2 else ""
        if not chain:
            return False
        key = f"{quote.pair}:{chain}"
        median = chain_medians.get(key)
        if median is None or median == ZERO:
            return False
        mid = (quote.buy_price + quote.sell_price) / TWO
        deviation = abs(mid - median) / median
        return deviation > max_deviation

    def _composite_score(self, opp: Opportunity) -> float:
        """Compute a multi-factor ranking score for opportunity prioritization.

        Weights were set based on initial production observations (not ML-tuned):
          - 0.50 net profit: primary signal — profit is the objective function
          - 0.25 liquidity:  guards against thin-pool false positives; pools with
            $10M+ TVL get full score, $100K gets ~0.71 (see strategy.py log10 scaling)
          - 0.15 flag safety: each warning flag (stale_quote, low_liquidity, etc.)
            reduces this component by 0.25.  4+ flags = zero.  This is aggressive
            because multiple flags compound risk in ways a weighted average can't capture.
          - 0.10 spread: tie-breaker only — wider spread = more room for execution
            slippage before the trade becomes unprofitable

        Normalization caps prevent outliers from dominating the ranking:
          - Profit capped at 1.0 WETH (~$2300): a $10K profit opportunity is
            ranked the same as $2300 — both are "very profitable", the ranking
            should prioritize execution reliability over extreme profit
          - Spread capped at 5%: above this is almost certainly a data error
            or an illiquid pool that would get filtered anyway

        These weights should be re-tuned after collecting 1000+ real trades.

        Returns float — this is a ranking metric, not a financial value.
        """
        # Convert Decimal fields to float for ranking math.
        net_profit = float(opp.net_profit_base)
        spread_pct = float(opp.gross_spread_pct)

        profit_score = min(net_profit / 1.0, 1.0) if net_profit > 0 else 0.0
        liq_score = opp.liquidity_score

        # Each warning flag reduces score by 0.25 — 4 flags = zero score.
        flag_score = max(0.0, 1.0 - len(opp.warning_flags) * 0.25)

        spread_score = min(spread_pct / 5.0, 1.0)

        return (
            0.50 * profit_score
            + 0.25 * liq_score
            + 0.15 * flag_score
            + 0.10 * spread_score
        )

    def _passes_alert_filter(self, opp: Opportunity) -> bool:
        """Return True if the opportunity should be surfaced (not rejected).

        This is a hard veto — separate from composite scoring — because multiple
        warning flags (e.g., stale + low liquidity) create compounding risk that
        a weighted score can't adequately capture. Better to reject outright.
        """
        if opp.net_profit_base < self.alert_min_net_profit:
            return False
        if len(opp.warning_flags) > self.alert_max_warning_flags:
            return False
        return True

    def _emit_alert(self, opp: Opportunity) -> None:
        """Log an alert for an actionable opportunity."""
        base_asset = opp.pair.split("/", 1)[0] if "/" in opp.pair else self.config.base_asset
        flags_str = ", ".join(opp.warning_flags) if opp.warning_flags else "none"
        logger.info(
            "ALERT: %s buy=%s sell=%s spread=%.2f%% net=%.6f %s "
            "liq_score=%.2f flags=[%s]",
            opp.pair, opp.buy_dex, opp.sell_dex,
            float(opp.gross_spread_pct), float(opp.net_profit_base),
            base_asset, opp.liquidity_score, flags_str,
        )
