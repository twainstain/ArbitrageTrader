"""Tests for the alerting module — dispatcher, Telegram, Discord, Gmail backends."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alerting.dispatcher import AlertDispatcher
from alerting.telegram import TelegramAlert
from alerting.discord import DiscordAlert
from alerting.gmail import GmailAlert


# ---------------------------------------------------------------
# Dispatcher tests
# ---------------------------------------------------------------

class _FakeBackend:
    def __init__(self, name: str = "fake", should_fail: bool = False):
        self._name = name
        self._should_fail = should_fail
        self.received: list[tuple] = []

    @property
    def name(self) -> str:
        return self._name

    def send(self, event_type, message, details=None):
        if self._should_fail:
            raise RuntimeError("boom")
        self.received.append((event_type, message, details))
        return True


class DispatcherTests(unittest.TestCase):
    def test_no_backends_returns_zero(self):
        d = AlertDispatcher()
        self.assertEqual(d.alert("test", "hello"), 0)

    def test_routes_to_all_backends(self):
        b1 = _FakeBackend("b1")
        b2 = _FakeBackend("b2")
        d = AlertDispatcher([b1, b2])
        count = d.alert("trade_executed", "msg")
        self.assertEqual(count, 2)
        self.assertEqual(len(b1.received), 1)
        self.assertEqual(len(b2.received), 1)

    def test_failing_backend_doesnt_crash(self):
        good = _FakeBackend("good")
        bad = _FakeBackend("bad", should_fail=True)
        d = AlertDispatcher([bad, good])
        count = d.alert("system_error", "oops")
        self.assertEqual(count, 1)
        self.assertEqual(len(good.received), 1)

    def test_add_backend(self):
        d = AlertDispatcher()
        d.add_backend(_FakeBackend("x"))
        self.assertEqual(d.backend_count, 1)

    def test_opportunity_found_helper(self):
        b = _FakeBackend()
        d = AlertDispatcher([b])
        d.opportunity_found("WETH/USDC", "Uni", "Pancake", 0.45, 0.005)
        self.assertEqual(len(b.received), 1)
        self.assertEqual(b.received[0][0], "opportunity_found")
        self.assertIn("WETH/USDC", b.received[0][1])

    def test_trade_executed_helper(self):
        b = _FakeBackend()
        d = AlertDispatcher([b])
        d.trade_executed("WETH/USDC", "0xabc", 0.004)
        self.assertEqual(b.received[0][0], "trade_executed")

    def test_trade_reverted_helper(self):
        b = _FakeBackend()
        d = AlertDispatcher([b])
        d.trade_reverted("WETH/USDC", "0xdef", "slippage")
        self.assertEqual(b.received[0][0], "trade_reverted")

    def test_system_error_helper(self):
        b = _FakeBackend()
        d = AlertDispatcher([b])
        d.system_error("scanner", "RPC timeout")
        self.assertEqual(b.received[0][0], "system_error")

    def test_daily_summary_helper(self):
        b = _FakeBackend()
        d = AlertDispatcher([b])
        d.daily_summary(100, 5, 3, 0.015, 1)
        self.assertEqual(b.received[0][0], "daily_summary")
        self.assertIn("100", b.received[0][1])


# ---------------------------------------------------------------
# Telegram backend tests
# ---------------------------------------------------------------

class TelegramTests(unittest.TestCase):
    def test_not_configured_returns_false(self):
        t = TelegramAlert(bot_token="", chat_id="")
        self.assertFalse(t.configured)
        self.assertFalse(t.send("test", "msg"))

    def test_configured_check(self):
        t = TelegramAlert(bot_token="123:ABC", chat_id="999")
        self.assertTrue(t.configured)

    def test_name(self):
        self.assertEqual(TelegramAlert().name, "telegram")

    @patch("alerting.telegram.requests.post")
    def test_send_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        t = TelegramAlert(bot_token="123:ABC", chat_id="999")
        self.assertTrue(t.send("trade_executed", "profit!"))
        mock_post.assert_called_once()
        call_json = mock_post.call_args[1]["json"]
        self.assertEqual(call_json["chat_id"], "999")
        self.assertIn("Trade Executed", call_json["text"])

    @patch("alerting.telegram.requests.post")
    def test_send_api_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=400, text="Bad Request")
        t = TelegramAlert(bot_token="123:ABC", chat_id="999")
        self.assertFalse(t.send("test", "msg"))

    @patch("alerting.telegram.requests.post", side_effect=Exception("timeout"))
    def test_send_network_error(self, mock_post):
        t = TelegramAlert(bot_token="123:ABC", chat_id="999")
        self.assertFalse(t.send("test", "msg"))


# ---------------------------------------------------------------
# Discord backend tests
# ---------------------------------------------------------------

class DiscordTests(unittest.TestCase):
    def test_not_configured_returns_false(self):
        d = DiscordAlert(webhook_url="")
        self.assertFalse(d.configured)
        self.assertFalse(d.send("test", "msg"))

    def test_name(self):
        self.assertEqual(DiscordAlert().name, "discord")

    @patch("alerting.discord.requests.post")
    def test_send_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=204)
        d = DiscordAlert(webhook_url="https://discord.com/api/webhooks/fake")
        self.assertTrue(d.send("opportunity_found", "WETH spread", {"pair": "WETH/USDC"}))
        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["embeds"][0]["title"], "Opportunity Found")
        self.assertGreater(len(payload["embeds"][0]["fields"]), 0)

    @patch("alerting.discord.requests.post")
    def test_send_webhook_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=429, text="Rate limited")
        d = DiscordAlert(webhook_url="https://discord.com/api/webhooks/fake")
        self.assertFalse(d.send("test", "msg"))

    @patch("alerting.discord.requests.post", side_effect=Exception("network"))
    def test_send_network_error(self, mock_post):
        d = DiscordAlert(webhook_url="https://discord.com/api/webhooks/fake")
        self.assertFalse(d.send("test", "msg"))


# ---------------------------------------------------------------
# Gmail backend tests
# ---------------------------------------------------------------

class GmailTests(unittest.TestCase):
    def test_not_configured_returns_false(self):
        g = GmailAlert(address="", app_password="", recipient="")
        self.assertFalse(g.configured)
        self.assertFalse(g.send("test", "msg"))

    def test_configured_check(self):
        g = GmailAlert(address="a@g.com", app_password="pw", recipient="b@g.com")
        self.assertTrue(g.configured)

    def test_name(self):
        self.assertEqual(GmailAlert().name, "gmail")

    @patch("alerting.gmail.smtplib.SMTP")
    def test_send_success(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        g = GmailAlert(address="a@g.com", app_password="pw", recipient="b@g.com")
        self.assertTrue(g.send("daily_summary", "report", {"scans": 100}))
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("a@g.com", "pw")
        mock_server.sendmail.assert_called_once()

    @patch("alerting.gmail.smtplib.SMTP", side_effect=Exception("connection refused"))
    def test_send_smtp_error(self, mock_smtp_cls):
        g = GmailAlert(address="a@g.com", app_password="pw", recipient="b@g.com")
        self.assertFalse(g.send("test", "msg"))


# ---------------------------------------------------------------
# Integration: dispatcher + real backends (unconfigured)
# ---------------------------------------------------------------

class IntegrationTests(unittest.TestCase):
    def test_unconfigured_backends_gracefully_skip(self):
        d = AlertDispatcher([
            TelegramAlert(bot_token="", chat_id=""),
            DiscordAlert(webhook_url=""),
            GmailAlert(address="", app_password="", recipient=""),
        ])
        # All unconfigured — should return 0 successes, no crashes.
        count = d.alert("trade_executed", "test msg")
        self.assertEqual(count, 0)

    @patch("alerting.telegram.requests.post")
    @patch("alerting.discord.requests.post")
    def test_mixed_configured(self, mock_discord, mock_telegram):
        mock_telegram.return_value = MagicMock(status_code=200)
        mock_discord.return_value = MagicMock(status_code=204)

        d = AlertDispatcher([
            TelegramAlert(bot_token="123:ABC", chat_id="999"),
            DiscordAlert(webhook_url="https://discord.com/api/webhooks/fake"),
            GmailAlert(address="", app_password="", recipient=""),  # unconfigured
        ])
        count = d.alert("trade_executed", "profit!")
        self.assertEqual(count, 2)  # telegram + discord succeed, gmail skips


if __name__ == "__main__":
    unittest.main()
