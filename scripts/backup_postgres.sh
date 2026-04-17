#!/usr/bin/env bash
# Hourly Postgres → S3 backup. Fails loudly on suspicious (tiny) dumps to
# avoid silently uploading garbage.
#
# Env: POSTGRES_CONTAINER, POSTGRES_DB, POSTGRES_USER, S3_BACKUP_BUCKET,
#      S3_BACKUP_PREFIX, BACKUP_DIR (optional).
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

SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE")
if [ "$SIZE" -lt 1024 ]; then
  echo "ERROR: backup file $FILE is ${SIZE} bytes — aborting upload" >&2
  exit 1
fi

aws s3 cp "$FILE" "s3://${BUCKET}/${PREFIX}${DB}-${STAMP}.dump" \
  --storage-class STANDARD_IA

# Local retention: keep last 3 dumps on disk (S3 is the archive).
ls -1t "$BACKUP_DIR"/${DB}-*.dump 2>/dev/null | tail -n +4 | xargs -r rm

echo "OK: s3://${BUCKET}/${PREFIX}${DB}-${STAMP}.dump (${SIZE} bytes)"
