"""Smart alerting rules — Telegram for big wins, hourly email summary.

Rules:
  - Spread > 5%: Immediate Telegram alert
  - Every hour: Email aggregate report with dashboard link
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from threading import Thread

from alerting.dispatcher import AlertDispatcher
from alerting.telegram import TelegramAlert
from alerting.gmail import GmailAlert
from persistence.repository import Repository

logger = logging.getLogger(__name__)

D = Decimal
BIG_WIN_THRESHOLD_PCT = D("5")


class SmartAlerter:
    """Applies alerting rules on top of the dispatcher.

    - Telegram: immediate alert for spreads > 5%
    - Gmail: hourly aggregate report
    """

    def __init__(
        self,
        repo: Repository,
        telegram: TelegramAlert | None = None,
        gmail: GmailAlert | None = None,
        dashboard_url: str = "http://localhost:8000/dashboard",
        email_interval_seconds: float = 3600.0,
    ) -> None:
        self.repo = repo
        self.telegram = telegram or TelegramAlert()
        self.gmail = gmail or GmailAlert()
        self.dashboard_url = dashboard_url
        self.email_interval = email_interval_seconds
        self._last_email_at: float = time.time()
        self._hourly_thread: Thread | None = None
        self._running = False

    def check_opportunity(self, spread_pct: Decimal, pair: str,
                          buy_dex: str, sell_dex: str, chain: str,
                          net_profit: float) -> None:
        """Check if an opportunity warrants an immediate Telegram alert."""
        if spread_pct >= BIG_WIN_THRESHOLD_PCT and self.telegram.configured:
            self.telegram.send(
                "opportunity_found",
                f"BIG SPREAD: {pair}\n"
                f"Chain: {chain}\n"
                f"Buy: {buy_dex} -> Sell: {sell_dex}\n"
                f"Spread: {float(spread_pct):.2f}%\n"
                f"Net profit: {net_profit:.6f}\n"
                f"\nDashboard: {self.dashboard_url}",
            )
            logger.info("Telegram alert sent for %.2f%% spread on %s", float(spread_pct), pair)

    def send_hourly_report(self) -> None:
        """Send an hourly aggregate email report."""
        if not self.gmail.configured:
            return

        from datetime import datetime, timedelta, timezone
        since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        total = self.repo.count_opportunities_since(since)
        approved = self.repo.count_opportunities_since(since, status="approved")
        rejected = self.repo.count_opportunities_since(since, status="rejected")
        dry_run = self.repo.count_opportunities_since(since, status="dry_run")
        included = self.repo.count_opportunities_since(since, status="included")

        funnel = self.repo.get_opportunity_funnel()
        pnl = self.repo.get_pnl_summary()

        msg = (
            f"Hourly Arbitrage Report\n"
            f"{'='*40}\n\n"
            f"Last Hour:\n"
            f"  Opportunities: {total}\n"
            f"  Approved: {approved}\n"
            f"  Rejected: {rejected}\n"
            f"  Dry-run: {dry_run}\n"
            f"  Included: {included}\n\n"
            f"All Time:\n"
            f"  Funnel: {funnel}\n"
            f"  Total PnL: {pnl.get('total_profit', 0)}\n"
            f"  Successful: {pnl.get('successful', 0)}\n"
            f"  Reverted: {pnl.get('reverted', 0)}\n\n"
            f"Dashboard: {self.dashboard_url}\n"
        )

        details = {
            "last_hour_total": total,
            "last_hour_approved": approved,
            "last_hour_rejected": rejected,
            "all_time_profit": str(pnl.get("total_profit", 0)),
            "dashboard": self.dashboard_url,
        }

        self.gmail.send("daily_summary", msg, details)
        self._last_email_at = time.time()
        logger.info("Hourly email report sent")

    def maybe_send_hourly(self) -> None:
        """Check if it's time to send the hourly email."""
        if time.time() - self._last_email_at >= self.email_interval:
            self.send_hourly_report()

    def start_background_hourly(self) -> None:
        """Start a background thread that sends hourly emails."""
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                time.sleep(60)  # check every minute
                self.maybe_send_hourly()

        self._hourly_thread = Thread(target=_loop, daemon=True)
        self._hourly_thread.start()
        logger.info("Hourly email reporter started")

    def stop(self) -> None:
        self._running = False
