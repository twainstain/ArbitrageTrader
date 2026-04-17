# Postgres Migration + S3 Backup Plan

**Applies to**: `ArbitrageTrader` (EVM bot) and `solana-trader` (Solana bot).
Both persist trading data and benefit from the same migration: off Neon, onto a self-hosted Postgres with S3 backups.

---

## 1. Goal

Move persistence off Neon onto a self-hosted Postgres container so we can:

- Retain unbounded history without paying Neon storage fees
- Run arbitrary analytical SQL against accumulated scan/trade data
- Own the backup/restore lifecycle end-to-end

S3 is the durability layer. The Docker volume is the hot data; S3 is the
cold copy that survives host loss.

---

## 2. Per-bot parameters

Both bots share the same pattern. Substitute these values when copying the scripts:

| Variable             | ArbitrageTrader (EVM)         | solana-trader               |
|----------------------|-------------------------------|------------------------------|
| Container name       | `arb-postgres`                | `solana-postgres`            |
| DB name              | `arbitrage`                   | `solana_arb`                 |
| DB user              | `arb`                         | `solana`                     |
| Docker volume        | `pg-data`                     | `pg-data`                    |
| Compose file         | `docker-compose.yml`          | `docker-compose.yml`         |
| Backup dir (host)    | `/opt/arb-trader/backups`     | `/opt/solana-trader/backups` |
| S3 prefix            | `s3://arb-trader-data/postgres/evm/` | `s3://arb-trader-data/postgres/solana/` |
| Code change needed   | No — `src/persistence/db.py` already handles `postgresql://` | Confirm same abstraction exists in solana-trader; if it uses SQLite only, add a `DATABASE_URL` branch |

> **Note**: S3 bucket names cannot contain underscores. Using `arb-trader-data` (shared across both bots, separated by prefix).

---

## 3. Architecture decision

Two viable shapes. **Recommendation: Option B** unless trade volume is high enough that >1h of lost `trade_results` rows would be material.

### Option B — Postgres in Docker on the same host, hourly S3 backup

```
┌──────────────────── EC2 (spot) ─────────────────────┐
│                                                      │
│   bot container  ──writes──▶  postgres container    │
│                                      │              │
│                                      ▼              │
│                               pg-data volume        │
│                                      │              │
│                                      ▼              │
│                             pg_dump → /backups ───────▶ S3 (hourly)
└──────────────────────────────────────────────────────┘
```

- **Pros**: zero new infra; ~$0.50/mo S3 cost; restore is `aws s3 cp + pg_restore`.
- **Cons**: spot eviction between backups → up to 1h data loss window.
- **Loss tolerance**: `scan_history` regenerates on next scan. `trade_results` / `execution_attempts` are the rows that hurt to lose; at current cadence, this is <1 row per hour worst case.

### Option C — Postgres on a separate on-demand instance

```
┌──── EC2 spot ────┐         ┌──── EC2 on-demand (t4g.nano) ────┐
│   bot container  │ ───────▶│   postgres container              │
└──────────────────┘         │   pg-data volume                  │
                             │          │                        │
                             │          ▼                        │
                             │   pg_dump → /backups ────▶ S3    │
                             └───────────────────────────────────┘
```

- **Pros**: spot eviction doesn't touch the DB; no data loss window beyond the backup cadence.
- **Cons**: +$3–5/mo for t4g.nano + EBS; two hosts to monitor; VPC security group + inter-host networking; more surface area to secure.
- **When this wins**: trade frequency is high enough that even 1h of lost executions is unacceptable, or you want the DB to outlive any bot-host decisions.

**Pick B unless there's a stated reason to pick C.** Everything below assumes B; deltas for C are noted inline.

---

## 4. Code changes required

### ArbitrageTrader (EVM)

- **None.** `src/persistence/db.py:314-317` already routes `DATABASE_URL` starting with `postgres://` or `postgresql://` to the psycopg2 backend. Just change the env var.

### solana-trader

- **Verify** the persistence layer supports a Postgres URL. If it's SQLite-only:
  - Add a `DATABASE_URL` branch in the connection factory mirroring `src/persistence/db.py:304-346` from this repo.
  - Adapt schema creation for Postgres syntax (`SERIAL` vs `INTEGER PRIMARY KEY AUTOINCREMENT`, etc.) — see `_TABLES_POSTGRES` at `src/persistence/db.py:215-217` for the minimal diff approach (string replace).
  - Replicate the placeholder adapter (`?` → `%s`) from `DbConnection._adapt_sql` at `src/persistence/db.py:233-247`.

If solana-trader currently uses Neon Postgres already, no code change is needed either — just swap the URL.

---

## 5. Implementation steps

All paths below are for ArbitrageTrader. For solana-trader, swap the parameters from §2.

### Step 1 — Add Postgres service to `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: arb-postgres           # solana-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg-data:/var/lib/postgresql/data
    # No host port binding by default — access via SSH tunnel.
    # Uncomment only if you've locked down the EC2 security group to your IP.
    # ports:
    #   - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - arb-net

  bot:
    # ...existing config...
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pg-data:
```

**Important**: never run `docker compose down -v` — the `-v` flag destroys named volumes.

### Step 2 — Add env vars to `.env` (and document in `.env.example`)

```bash
# --- Postgres (local, self-hosted) ---
POSTGRES_DB=arbitrage
POSTGRES_USER=arb
POSTGRES_PASSWORD=<generate with: openssl rand -base64 32>
DATABASE_URL=postgresql://arb:${POSTGRES_PASSWORD}@postgres:5432/arbitrage

# --- S3 backup ---
S3_BACKUP_BUCKET=arb-trader-data
S3_BACKUP_PREFIX=postgres/evm/            # solana bot: postgres/solana/
AWS_REGION=us-east-1                       # match the EC2 region
# AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY — prefer IAM role on EC2 over env vars
```

### Step 3 — One-time migration from Neon: `scripts/port_neon_to_local.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

NEON_URL="${1:?Usage: $0 <neon-connection-url>}"
CONTAINER="${POSTGRES_CONTAINER:-arb-postgres}"
LOCAL_DB="${POSTGRES_DB:-arbitrage}"
LOCAL_USER="${POSTGRES_USER:-arb}"

DUMP_FILE="/tmp/neon-export-$(date +%s).dump"

echo "==> Dumping from Neon..."
pg_dump --format=custom --no-owner --no-privileges \
        --file="$DUMP_FILE" "$NEON_URL"

echo "==> Pre-restore row counts (local):"
docker exec "$CONTAINER" psql -U "$LOCAL_USER" -d "$LOCAL_DB" -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables ORDER BY tablename;
" || true

echo "==> Restoring into $CONTAINER:$LOCAL_DB..."
docker cp "$DUMP_FILE" "$CONTAINER:/tmp/import.dump"
docker exec "$CONTAINER" pg_restore \
  --clean --if-exists --no-owner --no-privileges \
  -U "$LOCAL_USER" -d "$LOCAL_DB" /tmp/import.dump

echo "==> Post-restore row counts:"
docker exec "$CONTAINER" psql -U "$LOCAL_USER" -d "$LOCAL_DB" -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables ORDER BY tablename;
"

docker exec "$CONTAINER" rm /tmp/import.dump
rm "$DUMP_FILE"
echo "==> Done. Verify row counts match Neon source."
```

Run as: `./scripts/port_neon_to_local.sh "postgresql://user:pass@ep-xxx.neon.tech/arbitrage"`

**Downtime window**: stop the bot first (`docker compose stop bot`), run the port, restart (`docker compose start bot`). Expect ~2–5 minutes for a 0.5 GB database.

### Step 4 — Scheduled backup: `scripts/backup_postgres.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${POSTGRES_CONTAINER:-arb-postgres}"
DB="${POSTGRES_DB:-arbitrage}"
USER="${POSTGRES_USER:-arb}"
BUCKET="${S3_BACKUP_BUCKET:?set S3_BACKUP_BUCKET}"
PREFIX="${S3_BACKUP_PREFIX:-postgres/evm/}"
BACKUP_DIR="${BACKUP_DIR:-/opt/arb-trader/backups}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$BACKUP_DIR/${DB}-${STAMP}.dump"

docker exec "$CONTAINER" pg_dump --format=custom -U "$USER" "$DB" > "$FILE"

# Fail loudly if the dump is suspiciously small (<1 KB usually means broken).
if [ "$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE")" -lt 1024 ]; then
  echo "ERROR: backup file is <1KB — aborting upload" >&2
  exit 1
fi

aws s3 cp "$FILE" "s3://${BUCKET}/${PREFIX}${DB}-${STAMP}.dump" \
  --storage-class STANDARD_IA

# Local retention: keep last 3 dumps on disk
ls -1t "$BACKUP_DIR"/${DB}-*.dump | tail -n +4 | xargs -r rm

echo "OK: s3://${BUCKET}/${PREFIX}${DB}-${STAMP}.dump"
```

### Step 5 — Cron

`scripts/install-cron.sh` entry:

```
# Hourly Postgres backup → S3 (Option B)
0 * * * * cd /opt/arb-trader && ./scripts/backup_postgres.sh >> /var/log/arb-backup.log 2>&1
```

**S3 lifecycle policy** (set once on the bucket, via console or CLI):
- Transition to Glacier IR after 30 days
- Expire after 180 days

That gets the cost to pennies per month and still gives half a year of history.

### Step 6 — Restore procedure: `scripts/restore_from_s3.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

KEY="${1:?Usage: $0 <s3-key>  # e.g. postgres/evm/arbitrage-20260420T030000Z.dump}"
BUCKET="${S3_BACKUP_BUCKET:?set S3_BACKUP_BUCKET}"
CONTAINER="${POSTGRES_CONTAINER:-arb-postgres}"
DB="${POSTGRES_DB:-arbitrage}"
USER="${POSTGRES_USER:-arb}"

TMP="/tmp/restore-$(date +%s).dump"
aws s3 cp "s3://${BUCKET}/${KEY}" "$TMP"

docker cp "$TMP" "$CONTAINER:/tmp/restore.dump"
docker exec "$CONTAINER" pg_restore \
  --clean --if-exists --no-owner --no-privileges \
  -U "$USER" -d "$DB" /tmp/restore.dump

docker exec "$CONTAINER" rm /tmp/restore.dump
rm "$TMP"
echo "Restored $KEY"
```

**Rehearse this at least once** on a throwaway DB before you need it in anger.

### Step 7 — IAM for S3 access

Create an IAM role attached to the EC2 instance (preferred over static keys) with this minimum policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::arb-trader-data",
      "arn:aws:s3:::arb-trader-data/postgres/*"
    ]
  }]
}
```

---

## 6. Analytical access

To query the DB from a laptop, **don't expose port 5432 publicly**. Use one of:

- **SSH tunnel (recommended)**:
  ```
  ssh -L 5432:localhost:5432 ec2-user@<host>
  # Then connect client to localhost:5432
  ```
  Zero public exposure. Works for DataGrip, `psql`, pandas, notebooks.

- **Security-group-limited binding**: uncomment the `ports: ["5432:5432"]` line and restrict the EC2 security group to your home IP. Breaks when your IP changes.

- **Tailscale**: join EC2 to your tailnet, connect to the tailscale-internal IP. Clean but requires tailscale on every host.

Credentials stay in `.env` on the host either way.

---

## 7. Verification

After migration, before considering it done:

1. **Row counts match Neon source** — `port_neon_to_local.sh` prints them.
2. **Bot reconnects cleanly** — tail logs for DB errors after restart.
3. **One backup cycle completes** — wait for the cron fire, check S3 shows the object.
4. **Restore rehearsal on a scratch DB** — prove the restore path works before the original is gone.
5. **Analytical query runs from laptop** — confirm the SSH-tunnel workflow end-to-end.

---

## 8. Rollback

If any verification step fails:

1. `docker compose stop bot`
2. Flip `DATABASE_URL` in `.env` back to the Neon URL
3. `docker compose start bot`
4. Bot resumes against Neon. Local Postgres stays running but unused — inspect, debug, retry.

Do not drop the `pg-data` volume until the migration is confirmed green for at least 7 days.

---

## 9. Open decisions

Resolve these before implementing:

- [ ] Confirm Option B (recommended) vs Option C
- [ ] Confirm bucket name `arb-trader-data`
- [ ] Confirm exposure method (SSH tunnel recommended)
- [ ] Confirm solana-trader's current persistence layer (does it already handle `DATABASE_URL`?)
- [ ] Confirm EC2 region for S3 bucket colocation (cheapest egress)

---

## 10. Risks & mitigations

| Risk                                          | Mitigation                                                  |
|----------------------------------------------|-------------------------------------------------------------|
| Spot eviction mid-backup                     | Hourly cadence caps loss window at ~1h                      |
| Corrupt dump uploaded silently               | Size sanity check in backup script; periodic restore drill  |
| IAM role too permissive                      | Policy scoped to specific bucket/prefix, no wildcards       |
| `docker compose down -v` wipes data          | Team convention: never use `-v`; document in README         |
| Password in .env leaks                       | `.env` in `.gitignore`; rotate with `ALTER USER` + restart  |
| S3 bucket accidentally public                | Block Public Access on the bucket at account + bucket level |
