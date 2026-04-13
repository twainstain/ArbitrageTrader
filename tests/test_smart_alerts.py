"""Tests for smart alerting rules."""

import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from persistence.db import init_db, close_db
from persistence.repository import Repository
from alerting.smart_alerts import SmartAlerter, BIG_WIN_THRESHOLD_PCT
from alerting.telegram import TelegramAlert
from alerting.gmail import GmailAlert

D = Decimal


class _AlertTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.conn = init_db(self.tmp.name)
        self.repo = Repository(self.conn)

    def tearDown(self):
        close_db()
        Path(self.tmp.name).unlink(missing_ok=True)


class BigWinTelegramTests(_AlertTestBase):
    @patch("alerting.telegram.requests.post")
    def test_sends_telegram_for_big_spread(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        tg = TelegramAlert(bot_token="123:ABC", chat_id="999")
        alerter = SmartAlerter(repo=self.repo, telegram=tg)

        alerter.check_opportunity(
            spread_pct=D("7.5"), pair="WETH/USDC",
            buy_dex="Scroll", sell_dex="Arbitrum",
            chain="scroll", net_profit=0.02,
        )
        mock_post.assert_called_once()
        call_json = mock_post.call_args[1]["json"]
        self.assertIn("BIG SPREAD", call_json["text"])
        self.assertIn("7.50%", call_json["text"])

    @patch("alerting.telegram.requests.post")
    def test_no_telegram_for_small_spread(self, mock_post):
        tg = TelegramAlert(bot_token="123:ABC", chat_id="999")
        alerter = SmartAlerter(repo=self.repo, telegram=tg)

        alerter.check_opportunity(
            spread_pct=D("1.5"), pair="WETH/USDC",
            buy_dex="A", sell_dex="B", chain="ethereum", net_profit=0.005,
        )
        mock_post.assert_not_called()

    def test_no_crash_when_telegram_unconfigured(self):
        tg = TelegramAlert(bot_token="", chat_id="")
        alerter = SmartAlerter(repo=self.repo, telegram=tg)
        # Should not crash even for big spread.
        alerter.check_opportunity(
            spread_pct=D("10"), pair="WETH/USDC",
            buy_dex="A", sell_dex="B", chain="ethereum", net_profit=0.05,
        )


class HourlyEmailTests(_AlertTestBase):
    @patch("alerting.gmail.smtplib.SMTP")
    def test_sends_hourly_email(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        gm = GmailAlert(address="a@g.com", app_password="pw", recipient="b@g.com")
        alerter = SmartAlerter(repo=self.repo, gmail=gm, dashboard_url="http://test:8000/dashboard")

        # Seed some data.
        self.repo.create_opportunity(
            pair="WETH/USDC", chain="ethereum",
            buy_dex="A", sell_dex="B", spread_bps=D("42"),
        )

        alerter.send_hourly_report()
        mock_server.sendmail.assert_called_once()
        # Check the email body contains dashboard link.
        sent_msg = mock_server.sendmail.call_args[0][2]
        self.assertIn("http://test:8000/dashboard", sent_msg)

    def test_no_crash_when_gmail_unconfigured(self):
        gm = GmailAlert(address="", app_password="", recipient="")
        alerter = SmartAlerter(repo=self.repo, gmail=gm)
        alerter.send_hourly_report()  # should not crash

    @patch("alerting.gmail.smtplib.SMTP")
    def test_maybe_send_respects_interval(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        gm = GmailAlert(address="a@g.com", app_password="pw", recipient="b@g.com")
        alerter = SmartAlerter(repo=self.repo, gmail=gm, email_interval_seconds=9999)

        alerter.maybe_send_hourly()
        # Interval not elapsed → should NOT send.
        mock_server.sendmail.assert_not_called()


class ThresholdTests(unittest.TestCase):
    def test_big_win_threshold_is_5_percent(self):
        self.assertEqual(BIG_WIN_THRESHOLD_PCT, D("5"))


if __name__ == "__main__":
    unittest.main()
