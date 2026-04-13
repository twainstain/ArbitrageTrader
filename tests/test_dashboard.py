"""Tests for the dashboard API endpoints and time-windowed aggregations."""

import sys
import tempfile
from decimal import Decimal
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from persistence.db import init_db, close_db
from persistence.repository import Repository
from risk.policy import RiskPolicy
from api.app import create_app

D = Decimal


class _DashboardTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.conn = init_db(self.tmp.name)
        self.repo = Repository(self.conn)
        self.policy = RiskPolicy(execution_enabled=False)
        app = create_app(risk_policy=self.policy, repo=self.repo, require_auth=False)
        self.client = TestClient(app)

    def tearDown(self):
        close_db()
        Path(self.tmp.name).unlink(missing_ok=True)

    def _seed_data(self):
        """Create some test opportunities for aggregation."""
        for i, chain in enumerate(["ethereum", "ethereum", "arbitrum", "base"]):
            opp_id = self.repo.create_opportunity(
                pair="WETH/USDC", chain=chain,
                buy_dex="Uni", sell_dex="Pancake", spread_bps=D("42"),
            )
            if i % 2 == 0:
                self.repo.update_opportunity_status(opp_id, "approved")
            else:
                self.repo.update_opportunity_status(opp_id, "rejected")


class DashboardHTMLTests(_DashboardTestBase):
    def test_dashboard_returns_html(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers["content-type"])
        self.assertIn("Arbitrage Trader Dashboard", resp.text)


class TimeWindowTests(_DashboardTestBase):
    def test_window_24h_empty(self):
        resp = self.client.get("/dashboard/window/24h")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["window"], "24h")
        self.assertEqual(data["chain"], "all")
        self.assertEqual(data["opportunities"]["total"], 0)

    def test_window_with_data(self):
        self._seed_data()
        resp = self.client.get("/dashboard/window/24h")
        data = resp.json()
        self.assertEqual(data["opportunities"]["total"], 4)

    def test_window_filtered_by_chain(self):
        self._seed_data()
        resp = self.client.get("/dashboard/window/24h?chain=ethereum")
        data = resp.json()
        self.assertEqual(data["chain"], "ethereum")
        self.assertEqual(data["opportunities"]["total"], 2)

    def test_all_windows(self):
        self._seed_data()
        resp = self.client.get("/dashboard/windows")
        data = resp.json()
        self.assertIn("15m", data)
        self.assertIn("1h", data)
        self.assertIn("24h", data)
        self.assertIn("1m", data)
        self.assertEqual(data["24h"]["opportunities"]["total"], 4)

    def test_invalid_window(self):
        resp = self.client.get("/dashboard/window/99h")
        data = resp.json()
        self.assertIn("error", data)


class ChainSummaryTests(_DashboardTestBase):
    def test_chains_empty(self):
        resp = self.client.get("/dashboard/chains")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_chains_with_data(self):
        self._seed_data()
        resp = self.client.get("/dashboard/chains")
        data = resp.json()
        self.assertGreater(len(data), 0)
        # Ethereum has the most (2), should be first.
        chains = [c["chain"] for c in data]
        self.assertIn("ethereum", chains)
        self.assertIn("arbitrum", chains)

    def test_chains_custom_window(self):
        self._seed_data()
        resp = self.client.get("/dashboard/chains?window=1h")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
