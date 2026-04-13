"""Simulated market with configurable random-walk price model."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import random

from config import BotConfig, DexConfig, PairConfig
from models import BPS_DIVISOR, ONE, MarketQuote

D = Decimal

# Approximate USD prices for deriving extra pair prices from the primary pair.
# If primary pair base_price is ~3000 (WETH/USDC), these ratios derive WBTC, USDT, etc.
PAIR_PRICE_RATIOS: dict[str, Decimal] = {
    "WETH/USDC": D("1"),
    "WETH/USDT": D("1"),       # USDT ~ USDC, so WETH/USDT ~ WETH/USDC
    "WBTC/USDC": D("23.5"),   # WBTC ~ 23.5x WETH
    "WBTC/USDT": D("23.5"),
}

HALF_SPREAD_FACTOR = D("0.0005")


@dataclass
class DexState:
    config: DexConfig
    current_mid_price: Decimal


@dataclass
class PairState:
    """Tracks simulated price state for one pair across all DEXs."""
    pair_name: str
    dexes: list[DexState] = field(default_factory=list)


class SimulatedMarket:
    """Simple market model that creates mild price divergence across DEXs.

    Generates quotes for the primary pair and all extra_pairs from the config.
    Extra pair prices are derived from the primary pair using PAIR_PRICE_RATIOS.
    """

    def __init__(self, config: BotConfig, seed: int = 7) -> None:
        self.config = config
        self._rng = random.Random(seed)

        # Build pair states: primary pair + extra_pairs.
        self._pairs: list[PairState] = []

        # Primary pair — uses DEX base_prices directly.
        primary = PairState(pair_name=config.pair)
        for dex in config.dexes:
            primary.dexes.append(DexState(config=dex, current_mid_price=dex.base_price))
        self._pairs.append(primary)

        # Extra pairs — derive base price from primary using ratio.
        if config.extra_pairs:
            for extra in config.extra_pairs:
                ratio = PAIR_PRICE_RATIOS.get(extra.pair, ONE)
                pair_state = PairState(pair_name=extra.pair)
                for dex in config.dexes:
                    derived_price = dex.base_price * ratio
                    # Add small per-pair randomness so pairs don't move identically.
                    jitter = D(str(self._rng.uniform(0.998, 1.002)))
                    pair_state.dexes.append(
                        DexState(config=dex, current_mid_price=derived_price * jitter)
                    )
                self._pairs.append(pair_state)

    def get_quotes(self) -> list[MarketQuote]:
        """Advance each DEX price by one random step and return bid/ask quotes for all pairs."""
        quotes: list[MarketQuote] = []
        for pair_state in self._pairs:
            for dex in pair_state.dexes:
                self._advance_price(dex)
                half_spread = dex.current_mid_price * HALF_SPREAD_FACTOR
                quotes.append(
                    MarketQuote(
                        dex=dex.config.name,
                        pair=pair_state.pair_name,
                        buy_price=dex.current_mid_price + half_spread,
                        sell_price=dex.current_mid_price - half_spread,
                        fee_bps=dex.config.fee_bps,
                    )
                )
        return quotes

    def _advance_price(self, dex: DexState) -> None:
        """Apply a single random-walk tick to the DEX mid-price."""
        move_bps = D(str(self._rng.uniform(
            float(-dex.config.volatility_bps), float(dex.config.volatility_bps),
        )))
        dex.current_mid_price *= ONE + (move_bps / BPS_DIVISOR)
