"""Smart alerting rules — Telegram/Discord for big wins, hourly email summary.

Rules:
  - Spread > 5%: Immediate Telegram + Discord alert (big wins only)
  - Every hour: Email-only aggregate report with dashboard link
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from threading import Thread

from alerting.discord import DiscordAlert
from alerting.telegram import TelegramAlert
from alerting.gmail import GmailAlert
from persistence.repository import Repository

logger = logging.getLogger(__name__)

D = Decimal
BIG_WIN_THRESHOLD_PCT = D("5")


class SmartAlerter:
    """Applies alerting rules on top of the dispatcher.

    - Telegram + Discord: immediate alert for spreads > 5%
    - Gmail + Discord: hourly aggregate report
    """

    def __init__(
        self,
        repo: Repository,
        telegram: TelegramAlert | None = None,
        discord: DiscordAlert | None = None,
        gmail: GmailAlert | None = None,
        dashboard_url: str = "http://localhost:8000/dashboard",
        email_interval_seconds: float = 3600.0,
    ) -> None:
        self.repo = repo
        self.telegram = telegram or TelegramAlert()
        self.discord = discord or DiscordAlert()
        self.gmail = gmail or GmailAlert()
        self.dashboard_url = dashboard_url
        self.email_interval = email_interval_seconds
        self._last_email_at: float = time.time()
        self._hourly_thread: Thread | None = None
        self._running = False

    def check_opportunity(self, spread_pct: Decimal, pair: str,
                          buy_dex: str, sell_dex: str, chain: str,
                          net_profit: float) -> None:
        """Check if an opportunity warrants an immediate alert."""
        if spread_pct < BIG_WIN_THRESHOLD_PCT:
            return

        msg = (
            f"BIG SPREAD: {pair}\n"
            f"Chain: {chain}\n"
            f"Buy: {buy_dex} -> Sell: {sell_dex}\n"
            f"Spread: {float(spread_pct):.2f}%\n"
            f"Net profit: {net_profit:.6f}\n"
            f"\nDashboard: {self.dashboard_url}"
        )
        details = {
            "pair": pair, "chain": chain,
            "buy_dex": buy_dex, "sell_dex": sell_dex,
            "spread_pct": f"{float(spread_pct):.2f}%",
            "net_profit": f"{net_profit:.6f}",
            "dashboard": self.dashboard_url,
        }

        if self.telegram.configured:
            self.telegram.send("opportunity_found", msg)
            logger.info("Telegram alert sent for %.2f%% spread on %s", float(spread_pct), pair)

        if self.discord.configured:
            self.discord.send("opportunity_found", msg, details)
            logger.info("Discord alert sent for %.2f%% spread on %s", float(spread_pct), pair)

    def send_hourly_report(self) -> None:
        """Send an hourly aggregate report via email only (not Discord)."""
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        since = (now - timedelta(hours=1)).isoformat()

        total = self.repo.count_opportunities_since(since)
        approved = self.repo.count_opportunities_since(since, status="approved")
        rejected = self.repo.count_opportunities_since(since, status="rejected")
        sim_approved = self.repo.count_opportunities_since(since, status="simulation_approved")
        dry_run = self.repo.count_opportunities_since(since, status="dry_run")
        included = self.repo.count_opportunities_since(since, status="included")

        funnel = self.repo.get_opportunity_funnel()
        pnl = self.repo.get_pnl_summary()

        # Format funnel as readable lines instead of raw dict.
        funnel_lines = "\n".join(
            f"  {status}: {count}" for status, count in funnel.items()
        ) if isinstance(funnel, dict) else f"  {funnel}"

        # Actionable = sim_approved + approved + included (not rejected).
        actionable_hour = sim_approved + approved + included
        actionable_pct = f" ({actionable_hour * 100 // total}%)" if total > 0 else ""

        msg = (
            f"Hourly Arbitrage Report — {now.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"{'='*50}\n\n"
            f"Last Hour:\n"
            f"  Detected:            {total}\n"
            f"  Actionable:          {actionable_hour}{actionable_pct}\n"
            f"    Sim approved:      {sim_approved}\n"
            f"    Approved (live):   {approved}\n"
            f"    Included on-chain: {included}\n"
            f"  Rejected:            {rejected}\n"
            f"  Dry-run:             {dry_run}\n\n"
            f"All Time:\n"
            f"{funnel_lines}\n\n"
            f"PnL:\n"
            f"  Total profit: {pnl.get('total_profit', 0)}\n"
            f"  Successful:   {pnl.get('successful', 'n/a')}\n"
            f"  Reverted:     {pnl.get('reverted', 'n/a')}\n\n"
            f"Dashboard: {self.dashboard_url}\n"
        )

        details = {
            "last_hour_total": total,
            "last_hour_actionable": actionable_hour,
            "last_hour_sim_approved": sim_approved,
            "last_hour_approved": approved,
            "last_hour_rejected": rejected,
            "all_time_profit": str(pnl.get("total_profit", 0)),
            "dashboard": self.dashboard_url,
        }

        if self.gmail.configured:
            self.gmail.send("daily_summary", msg, details)
            logger.info("Hourly email report sent")

        # Hourly summary goes to email only — Discord gets big-win alerts.

        self._last_email_at = time.time()

    def maybe_send_hourly(self) -> None:
        """Check if it's time to send the hourly report."""
        if time.time() - self._last_email_at >= self.email_interval:
            self.send_hourly_report()

    def start_background_hourly(self) -> None:
        """Start a background thread that sends hourly reports."""
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                time.sleep(60)  # check every minute
                self.maybe_send_hourly()

        self._hourly_thread = Thread(target=_loop, daemon=True)
        self._hourly_thread.start()
        logger.info("Hourly report thread started")

    def stop(self) -> None:
        self._running = False
