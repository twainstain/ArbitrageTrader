"""Tests for the risk policy engine."""

import sys
from decimal import Decimal
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models import Opportunity
from risk.policy import RiskPolicy, RiskVerdict

D = Decimal


def _make_opp(**overrides) -> Opportunity:
    defaults = dict(
        pair="WETH/USDC", buy_dex="A", sell_dex="B",
        trade_size=D("1"), cost_to_buy_quote=D("3001"),
        proceeds_from_sell_quote=D("3079"), gross_profit_quote=D("78"),
        net_profit_quote=D("50"), net_profit_base=D("0.005"),
        gas_cost_base=D("0.001"), liquidity_score=0.8,
        warning_flags=(),
    )
    defaults.update(overrides)
    return Opportunity(**defaults)


class KillSwitchTests(unittest.TestCase):
    def test_execution_disabled_rejects_everything(self) -> None:
        policy = RiskPolicy(execution_enabled=False)
        verdict = policy.evaluate(_make_opp())
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "execution_disabled")

    def test_execution_enabled_allows(self) -> None:
        policy = RiskPolicy(execution_enabled=True)
        verdict = policy.evaluate(_make_opp())
        self.assertTrue(verdict.approved)


class MinProfitTests(unittest.TestCase):
    def test_below_min_rejected(self) -> None:
        policy = RiskPolicy(execution_enabled=True, min_net_profit=D("0.01"))
        verdict = policy.evaluate(_make_opp(net_profit_base=D("0.005")))
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "below_min_profit")

    def test_above_min_approved(self) -> None:
        policy = RiskPolicy(execution_enabled=True, min_net_profit=D("0.001"))
        verdict = policy.evaluate(_make_opp(net_profit_base=D("0.005")))
        self.assertTrue(verdict.approved)


class WarningFlagTests(unittest.TestCase):
    def test_too_many_flags_rejected(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_warning_flags=0)
        opp = _make_opp(warning_flags=("low_liquidity",))
        verdict = policy.evaluate(opp)
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "too_many_flags")

    def test_within_flag_limit_approved(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_warning_flags=2)
        opp = _make_opp(warning_flags=("low_liquidity", "thin_market"))
        verdict = policy.evaluate(opp)
        self.assertTrue(verdict.approved)


class LiquidityScoreTests(unittest.TestCase):
    def test_low_score_rejected(self) -> None:
        policy = RiskPolicy(execution_enabled=True, min_liquidity_score=0.5)
        verdict = policy.evaluate(_make_opp(liquidity_score=0.2))
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "low_liquidity_score")


class GasProfitRatioTests(unittest.TestCase):
    def test_gas_too_expensive_rejected(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_gas_profit_ratio=D("0.3"))
        # gas 0.002 / profit 0.003 = 0.67 > 0.3
        opp = _make_opp(net_profit_base=D("0.003"), gas_cost_base=D("0.002"))
        verdict = policy.evaluate(opp)
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "gas_too_expensive")

    def test_reasonable_gas_approved(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_gas_profit_ratio=D("0.5"))
        # gas 0.001 / profit 0.005 = 0.2 < 0.5
        verdict = policy.evaluate(_make_opp())
        self.assertTrue(verdict.approved)


class RateLimitTests(unittest.TestCase):
    def test_rate_limit_exceeded(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_trades_per_hour=10)
        verdict = policy.evaluate(_make_opp(), current_hour_trades=10)
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "rate_limit_exceeded")

    def test_below_rate_limit(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_trades_per_hour=10)
        verdict = policy.evaluate(_make_opp(), current_hour_trades=5)
        self.assertTrue(verdict.approved)


class ExposureLimitTests(unittest.TestCase):
    def test_over_exposure_rejected(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_exposure_per_pair=D("5"))
        verdict = policy.evaluate(
            _make_opp(trade_size=D("3")),
            current_pair_exposure=D("4"),
        )
        self.assertFalse(verdict.approved)
        self.assertEqual(verdict.reason, "exposure_limit")

    def test_within_exposure_approved(self) -> None:
        policy = RiskPolicy(execution_enabled=True, max_exposure_per_pair=D("10"))
        verdict = policy.evaluate(
            _make_opp(trade_size=D("1")),
            current_pair_exposure=D("2"),
        )
        self.assertTrue(verdict.approved)


class ToDictTests(unittest.TestCase):
    def test_serializes_all_fields(self) -> None:
        policy = RiskPolicy()
        d = policy.to_dict()
        self.assertIn("min_net_profit", d)
        self.assertIn("execution_enabled", d)
        self.assertIn("max_trades_per_hour", d)
        self.assertEqual(d["execution_enabled"], False)


if __name__ == "__main__":
    unittest.main()
