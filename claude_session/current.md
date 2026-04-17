# Current State

## Session: 2026-04-17

### Summary

Migrated persistence off Neon onto self-hosted Postgres in Docker (Phase B of `docs/postgres_migration_plan.md`). Hit two issues on cutover and fixed both: (1) nginx 502s because bot container IP changed on recreate and nginx had cached the old one — fixed by `docker compose restart nginx`; (2) bot was flipped to an empty local pg *before* the Neon port ran, stranding ~1.7M scan_history + 864 opportunities on Neon. Ported via `scripts/port_neon_to_local.sh` after bumping local image from `postgres:16-alpine` → `postgres:17-alpine` (Neon runs 17, pg_dump 16 refused). Data recovered; no trade data was ever at risk (trade_results/execution_attempts were 0 on both sides).

### Deployed

- **EC2**: 18.215.6.141 (spot t3.small)
- **Dashboard**: https://arb-trader.yeda-ai.com/dashboard
- **DB**: self-hosted Postgres 17 (container `arb-postgres`, volume `arb-trader_pg-data`)
- **Alerting**: Discord + Gmail

### What Works

| Feature | Status |
|---------|--------|
| Pipeline (detect → price → risk) | Working, ~6s per scan |
| fee_included flag (no double-counting) | Working — real spreads surfacing |
| On-chain quoters return actual fee tier | Working (V3: exact bps, others: estimated) |
| Multi-pair scanning (WETH/USDC, WETH/USDT, OP/USDC) | Working |
| Dashboard cost waterfall breakdown | Working |
| Thin pool filter (5% global median) | Working (but misses ~4.8% outliers) |
| Liquidity cache (3h/15min TTL) | Working |
| Auto pair discovery (DexScreener hourly) | Working |
| scripts/run_local.sh (local dev runner) | Working |

### Latest Scan Results (onchain mode)

| Chain | Pair | Spread | Status |
|-------|------|--------|--------|
| Ethereum | WETH/USDT | ~32 bps | Real, consistent |
| Ethereum | WETH/USDC | ~19-28 bps | Real, consistent |
| Base | WETH/USDC | ~23-29 bps | Real, consistent |
| Arbitrum | WETH/USDC | ~12-13 bps | Real, consistent |
| Arbitrum | WETH/USDT | ~480 bps | FALSE POSITIVE — Sushi stale pool |

### What Needs Fixing

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **Sushi-Arbitrum WETH/USDT outlier** | Returns $2231 (stale pool), 4.8% deviation slips under 5% filter | Tighten outlier filter or cross-validate against same-DEX other pairs |
| **Optimism all DEXes returning zero** | Uniswap, Sushi, Velodrome all fail on Optimism | Debug token addresses / quoter contracts |
| **Base USDT not in token registry** | Missing USDT address for Base chain | Add to tokens.py |
| **OP/USDC only works on Optimism** | Other chains can't resolve OP token | Expected — OP is Optimism-native |
| **CI/CD deploy fails** | AWS credentials not set in GitHub secrets | Set AWS_ACCESS_KEY_ID/SECRET in repo settings |
| **Hourly S3 backup cron not installed** | Phase B left off before Step 5 | Install cron entry from `docs/postgres_migration_plan.md` §5 + rehearse `restore_from_s3.sh` |
| **Nginx DNS caching** | Static upstream `bot:8000` resolved once at startup — breaks on bot recreate | Harden with `resolver 127.0.0.11 valid=10s` + variable upstream in nginx.conf |

### Test Count: 618
