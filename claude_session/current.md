# Current State

## Session: 2026-04-14

### Summary

Production bot deployed on AWS EC2 with 22 DEX quoters implemented, dynamic pair discovery, thin pool detection. 571 tests. Currently debugging RPC call hangs.

### Deployed

- **EC2**: 18.215.6.141 (spot t3.small)
- **Dashboard**: https://arb-trader.yeda-ai.com/dashboard
- **DB**: Neon Postgres
- **Alerting**: Discord + Gmail

### What Works

| Feature | Status |
|---------|--------|
| Pipeline (detect → price → risk) | Working, ~30ms |
| Thin pool filter (5% global median) | Working |
| Liquidity cache (3h/15min TTL) | Working |
| Auto pair discovery (DexScreener hourly) | Working, finds 7+ pairs |
| Dynamic token registry | Working, auto-registers from DexScreener |
| Dashboard profit reports (per time window) | Working |
| Cross-chain filter | Working |

### What Needs Fixing

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **Scans hang on first cycle** | SushiSwap/PancakeSwap quoters hang on eth_call despite 8s HTTP timeout | Need `eth_call` level timeout or move to WebSocket RPCs |
| Niche DEXes (Velodrome, Camelot, Aerodrome) | Contract calls hang | Debug ABI/contract interaction separately |
| BSC WETH decimal mismatch | Returns $2.3 quadrillion | Need WBNB/USDT pair instead |
| CI/CD test failure | Unknown — tests pass locally | Check GitHub Actions logs |

### DEX Coverage (implemented in code)

| DEX | Type | Chains | Status |
|-----|------|--------|--------|
| Uniswap V3 | V3 Quoter | ETH, ARB, BASE, OPT | Working |
| SushiSwap V3 | V3 Quoter | ETH, ARB, BASE, OPT | Hanging on some chains |
| PancakeSwap V3 | V3 Quoter | ETH, ARB, BASE | Hanging |
| QuickSwap | Algebra | Polygon | Zero quotes |
| Camelot V3 | Algebra | Arbitrum | Implemented, disabled (hangs) |
| Velodrome V2 | Solidly Router | Optimism | Implemented, disabled (zero) |
| Aerodrome | Solidly Router | Base | Implemented, disabled (hangs) |

### Test Count: 571
