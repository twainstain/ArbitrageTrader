#!/usr/bin/env bash
# Phase A (host side) — set up .env on the bot host with Postgres + S3
# vars while preserving the existing DATABASE_URL (so the bot stays
# connected to its current DB, typically Neon, until Phase C).
#
# Idempotent: re-running is safe; setup_env.py backs up .env first.
#
# Usage (in project directory, e.g. /opt/arb-trader):
#
#   # Preserve whatever DATABASE_URL is already in .env:
#   ./scripts/phase_a_host.sh
#
#   # Explicit URL (recommended if .env might already be swapped):
#   ./scripts/phase_a_host.sh --database-url "postgresql://..."
#
#   # From a file (no shell quoting):
#   echo 'postgresql://...' > /tmp/src.txt
#   ./scripts/phase_a_host.sh --database-url-file /tmp/src.txt
set -euo pipefail

SOURCE_URL=""
URL_FILE=""
ENV_FILE=".env"
SMOKE_TEST=true
BUCKET="arb-trader-data"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --database-url) SOURCE_URL="$2"; shift 2 ;;
    --database-url-file) URL_FILE="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --bucket) BUCKET="$2"; shift 2 ;;
    --no-smoke-test) SMOKE_TEST=false; shift ;;
    -h|--help)
      sed -n '2,17p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "ERROR: unknown arg: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# If no URL passed, try to extract one from existing .env
if [ -z "$SOURCE_URL" ] && [ -z "$URL_FILE" ] && [ -f "$ENV_FILE" ]; then
  EXISTING=$(grep '^DATABASE_URL=' "$ENV_FILE" 2>/dev/null | head -1 | sed 's/^DATABASE_URL=//' || true)
  # Only keep it if it looks like a foreign (source) DB, not our local container URL
  if [ -n "$EXISTING" ] && [[ "$EXISTING" != *"@postgres:"* ]]; then
    SOURCE_URL="$EXISTING"
    echo "==> Found source DATABASE_URL in $ENV_FILE (will preserve)"
  fi
fi

if [ -z "$SOURCE_URL" ] && [ -z "$URL_FILE" ]; then
  echo "ERROR: no source DATABASE_URL. Pass --database-url or --database-url-file," >&2
  echo "       or run from a project dir whose .env still points at the source DB." >&2
  exit 2
fi

SETUP_ARGS=(--keep-password --env-file "$ENV_FILE")
TMP_URL=""
if [ -n "$URL_FILE" ]; then
  SETUP_ARGS+=(--database-url-file "$URL_FILE")
else
  TMP_URL="$(mktemp)"
  printf '%s' "$SOURCE_URL" > "$TMP_URL"
  SETUP_ARGS+=(--database-url-file "$TMP_URL")
fi

echo "==> Running setup_env.py"
python3 "$SCRIPT_DIR/setup_env.py" "${SETUP_ARGS[@]}"
[ -n "$TMP_URL" ] && rm -f "$TMP_URL"

echo "==> Verifying required keys"
MISSING=0
for k in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD DATABASE_URL \
         S3_BACKUP_BUCKET S3_BACKUP_PREFIX AWS_REGION; do
  if ! grep -q "^${k}=" "$ENV_FILE"; then
    echo "  MISSING: $k"
    MISSING=1
  fi
done
if [ "$MISSING" -eq 1 ]; then
  echo "FAIL: required keys missing from $ENV_FILE" >&2
  exit 1
fi
echo "  all 7 keys present"

if [ "$SMOKE_TEST" = true ]; then
  echo "==> S3 write smoke test (bucket=$BUCKET)"
  if ! command -v aws >/dev/null; then
    echo "  WARN: aws CLI not found on this host — skipping smoke test" >&2
  else
    KEY="smoke-test-$(date -u +%Y%m%dT%H%M%SZ).txt"
    printf 'phase-a-host OK\n' > "/tmp/$KEY"
    aws s3 cp "/tmp/$KEY" "s3://$BUCKET/$KEY" >/dev/null
    aws s3 ls "s3://$BUCKET/$KEY" | head -1
    rm -f "/tmp/$KEY"
    echo "  OK — object $KEY uploaded. Admin can clean up via:"
    echo "       aws s3 rm s3://$BUCKET/$KEY"
  fi
fi

echo
echo "DONE. Phase A host setup complete for $ENV_FILE."
