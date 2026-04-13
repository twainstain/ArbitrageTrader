"""Alerting module — Telegram, Discord, Gmail backends with a unified dispatcher."""

from alerting.dispatcher import AlertDispatcher
from alerting.telegram import TelegramAlert
from alerting.discord import DiscordAlert
from alerting.gmail import GmailAlert

__all__ = ["AlertDispatcher", "TelegramAlert", "DiscordAlert", "GmailAlert"]
