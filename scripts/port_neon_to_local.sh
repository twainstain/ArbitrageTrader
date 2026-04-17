#!/usr/bin/env bash
# One-shot migration from Neon Postgres to the local docker-compose `postgres`
# service. Safe to re-run — pg_restore with --clean --if-exists drops and
# recreates objects. Stop the bot before running to avoid writes during copy.
#
# Runs pg_dump *inside* the postgres container so the host needs no
# postgresql-client install — the container has pg_dump and outbound
# internet access to Neon.
#
# Usage:
#   ./scripts/port_neon_to_local.sh "postgresql://user:pass@ep-xxx.neon.tech/arbitrage"
set -euo pipefail

NEON_URL="${1:?Usage: $0 <neon-connection-url>}"
CONTAINER="${POSTGRES_CONTAINER:-arb-postgres}"
LOCAL_DB="${POSTGRES_DB:-arbitrage}"
LOCAL_USER="${POSTGRES_USER:-arb}"

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "ERROR: container '$CONTAINER' not running. Start with: docker compose up -d postgres" >&2
  exit 1
fi

echo "==> Source row counts (Neon):"
docker exec -i "$CONTAINER" psql "$NEON_URL" -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables ORDER BY tablename;
"

echo "==> Dumping Neon → container:/tmp/import.dump"
docker exec "$CONTAINER" bash -lc "pg_dump --format=custom --no-owner --no-privileges -f /tmp/import.dump '$NEON_URL'"

echo "==> Restoring into $CONTAINER:$LOCAL_DB"
docker exec "$CONTAINER" pg_restore \
  --clean --if-exists --no-owner --no-privileges \
  -U "$LOCAL_USER" -d "$LOCAL_DB" /tmp/import.dump

echo "==> Post-restore row counts (local):"
docker exec "$CONTAINER" psql -U "$LOCAL_USER" -d "$LOCAL_DB" -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables ORDER BY tablename;
"

docker exec "$CONTAINER" rm -f /tmp/import.dump

echo
echo "==> Done. Verify row counts above match before flipping DATABASE_URL to local."
