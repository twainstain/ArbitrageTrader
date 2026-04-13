"""Persistence layer — SQLite-backed storage for candidate lifecycle, trades, and checkpoints."""

from persistence.db import get_db, init_db
from persistence.repository import Repository

__all__ = ["get_db", "init_db", "Repository"]
