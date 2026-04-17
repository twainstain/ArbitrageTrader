#!/usr/bin/env python3
"""Write a clean Postgres + S3 block into .env.

Idempotent: strips any existing copies of the managed keys before writing.
Generates a fresh 64-char hex POSTGRES_PASSWORD and a matching DATABASE_URL
pointing at the local `postgres` docker-compose service.

Usage:
    python3 scripts/setup_env.py                   # write new block
    python3 scripts/setup_env.py --keep-password   # reuse existing POSTGRES_PASSWORD
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import secrets
import stat
import sys
from datetime import datetime, timezone

MANAGED_KEYS = (
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "S3_BACKUP_BUCKET",
    "S3_BACKUP_PREFIX",
    "AWS_REGION",
)


def read_env(path: pathlib.Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return dict(
        re.findall(r"^([A-Z_][A-Z0-9_]*)=(.*)$", path.read_text(), re.MULTILINE)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default=".env")
    ap.add_argument(
        "--keep-password",
        action="store_true",
        help="reuse existing POSTGRES_PASSWORD if one is set",
    )
    args = ap.parse_args()

    env_path = pathlib.Path(args.env_file)
    if not env_path.exists():
        print(f"{env_path} not found — creating fresh.")
        env_path.touch(mode=0o600)

    existing = read_env(env_path)
    if args.keep_password and existing.get("POSTGRES_PASSWORD"):
        pw = existing["POSTGRES_PASSWORD"]
        print("Reusing existing POSTGRES_PASSWORD.")
    else:
        pw = secrets.token_hex(32)  # 64 clean hex chars

    backup = env_path.with_name(f".env.bak.{int(datetime.now(timezone.utc).timestamp())}")
    backup.write_text(env_path.read_text())
    os.chmod(backup, 0o600)
    print(f"Backed up existing .env → {backup.name}")

    lines = env_path.read_text().splitlines()
    kept = [
        l for l in lines
        if not any(re.match(rf"^\s*{k}\s*=", l) for k in MANAGED_KEYS)
    ]

    block = f"""
# --- Self-hosted Postgres (managed by scripts/setup_env.py) ---
POSTGRES_DB=arbitrage
POSTGRES_USER=arb
POSTGRES_PASSWORD={pw}
DATABASE_URL=postgresql://arb:{pw}@postgres:5432/arbitrage

# --- S3 backup ---
S3_BACKUP_BUCKET=arb-trader-data
S3_BACKUP_PREFIX=postgres/evm/
AWS_REGION=us-east-1
""".strip()

    env_path.write_text("\n".join(kept).rstrip() + "\n\n" + block + "\n")
    os.chmod(env_path, 0o600)

    verify = read_env(env_path)
    for k in MANAGED_KEYS:
        v = verify.get(k, "")
        if not v:
            print(f"FAIL: {k} missing after write", file=sys.stderr)
            return 1
        if v != v.strip():
            print(f"FAIL: {k} has whitespace: {v!r}", file=sys.stderr)
            return 1

    print(f"Wrote clean block to {env_path} (chmod 600).")
    print()
    print("NOTE: DATABASE_URL now points at the local 'postgres' container.")
    print("      If you need Neon to stay active (Phase A on EC2), edit .env and")
    print("      revert just the DATABASE_URL line to the Neon URL until Phase C.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
