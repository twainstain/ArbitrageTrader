#!/bin/bash
# Run the arbitrage trader locally with .env.test credentials.
#
# Usage:
#   ./scripts/run_local.sh              # default: --live (DeFi Llama)
#   ./scripts/run_local.sh --onchain    # on-chain RPC quotes
#
# Dashboard: http://localhost:8000/dashboard  (admin / adminTest)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Load .env.test instead of .env
if [ ! -f .env.test ]; then
    echo "Error: .env.test not found"
    exit 1
fi
set -a
source .env.test
set +a

MODE_FLAG=""
MODE_LABEL="live"
EXTRA_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --onchain)
            MODE_FLAG="--onchain"
            MODE_LABEL="onchain"
            ;;
        *)
            EXTRA_ARGS+=("$arg")
            ;;
    esac
done

echo "Starting local dashboard..."
echo "  Mode: $MODE_LABEL"
echo "  Env:  .env.test"
echo "  URL:  http://localhost:8000/dashboard"
echo "  Auth: admin / adminTest"
echo ""

PYTHONPATH=src python -m run_live_with_dashboard \
    $MODE_FLAG \
    --iterations 10 \
    --sleep 15 \
    "${EXTRA_ARGS[@]}"
