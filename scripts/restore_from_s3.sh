#!/usr/bin/env bash
# Restore a Postgres dump from S3 into the local container.
#
# Usage:
#   ./scripts/restore_from_s3.sh postgres/evm/arbitrage-20260420T030000Z.dump
#
# REHEARSE THIS on a scratch DB before you need it in anger.
set -euo pipefail

KEY="${1:?Usage: $0 <s3-key>}"
BUCKET="${S3_BACKUP_BUCKET:?set S3_BACKUP_BUCKET}"
CONTAINER="${POSTGRES_CONTAINER:-arb-postgres}"
DB="${POSTGRES_DB:-arbitrage}"
USER="${POSTGRES_USER:-arb}"

TMP="/tmp/restore-$(date +%s).dump"
echo "==> Fetching s3://${BUCKET}/${KEY}"
aws s3 cp "s3://${BUCKET}/${KEY}" "$TMP"

echo "==> Restoring into $CONTAINER:$DB (existing objects will be dropped)"
docker cp "$TMP" "$CONTAINER:/tmp/restore.dump"
docker exec "$CONTAINER" pg_restore \
  --clean --if-exists --no-owner --no-privileges \
  -U "$USER" -d "$DB" /tmp/restore.dump

docker exec "$CONTAINER" rm /tmp/restore.dump
rm "$TMP"

echo "==> Post-restore row counts:"
docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c "
  SELECT schemaname, relname AS tablename, n_live_tup
  FROM pg_stat_user_tables ORDER BY relname;
"
echo "==> Restored $KEY"
