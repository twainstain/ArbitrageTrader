# RPC Provider Reference

Quick reference for adding or updating chain RPCs. Set in `.env` as `RPC_<CHAIN>=<url>`.

## Current Setup (2026-04-15)

| Chain | Provider | Env Var | Status |
|-------|----------|---------|--------|
| Ethereum | Alchemy | `RPC_ETHEREUM` | Working |
| Arbitrum | Alchemy | `RPC_ARBITRUM` | Working |
| Base | Alchemy | `RPC_BASE` | Working |
| Optimism | Llamanodes | `RPC_OPTIMISM` | Working (was Infura, 429'd) |

## Free-Tier Providers (no signup required)

These work immediately with no API key. Good for testing or low-frequency scanning.

| Provider | URL Pattern | Rate Limit | Notes |
|----------|-------------|------------|-------|
| **Llamanodes** | `https://{chain}.llamarpc.com` | Very generous | Best free option. Supports: ethereum, optimism, arbitrum, base, polygon |
| **1RPC** | `https://1rpc.io/{chain_id}` | Unlimited | Privacy relay. `eth`, `op`, `arb`, `base` |
| **Ankr** | `https://rpc.ankr.com/{chain}` | 30 req/s | `ethereum`, `optimism`, `arbitrum`, `base`, `polygon`, `bsc`, `avalanche` |
| **PublicNode** | `https://{chain}-rpc.publicnode.com` | Moderate | `ethereum`, `optimism`, `arbitrum`, `base`, `polygon` |
| **Chain-native** | See below | Varies | Official RPCs, often rate-limited |

### Chain-Native Public RPCs

| Chain | URL | Notes |
|-------|-----|-------|
| Ethereum | `https://eth.llamarpc.com` | Llamanodes preferred over eth mainnet RPC |
| Arbitrum | `https://arb1.arbitrum.io/rpc` | Official, rate-limited |
| Base | `https://mainnet.base.org` | Official |
| Optimism | `https://mainnet.optimism.io` | Official |
| Polygon | `https://polygon-rpc.com` | Official |
| BSC | `https://bsc-dataseed.binance.org` | Official |
| Avalanche | `https://api.avax.network/ext/bc/C/rpc` | Official |
| Fantom | `https://rpcapi.fantom.network` | Official |
| Gnosis | `https://rpc.gnosischain.com` | Official |
| Linea | `https://rpc.linea.build` | Official |
| Scroll | `https://rpc.scroll.io` | Official |
| zkSync | `https://mainnet.era.zksync.io` | Official |

## Paid Providers (API key required)

| Provider | Free Tier | Chains | Signup |
|----------|-----------|--------|--------|
| **Alchemy** | 300M compute/month, 5 apps | All major | alchemy.com |
| **Infura** | 100K req/day | All major | infura.io — caution: aggressive rate limiting |
| **QuickNode** | 10M API credits/month | 20+ chains | quicknode.com |
| **Tenderly** | 25M compute/month | All major | tenderly.co |
| **Chainstack** | 3M req/month | 25+ chains | chainstack.com |
| **Blast** | 40 req/s | 20+ chains | blastapi.io |
| **dRPC** | 50M compute/month | 50+ chains | drpc.org |

## Recommended Setup Per Chain

For production scanning (8-10s intervals, 4 fee-tier calls per DEX):

| Chain | Primary | Fallback |
|-------|---------|----------|
| Ethereum | Alchemy | `eth.llamarpc.com` |
| Arbitrum | Alchemy | `arb1.arbitrum.io/rpc` |
| Base | Alchemy | `mainnet.base.org` |
| Optimism | Llamanodes | `mainnet.optimism.io` |
| Polygon | Llamanodes | `polygon-rpc.com` |
| BSC | Ankr | `bsc-dataseed.binance.org` |

## Adding a New Chain

1. Add `RPC_<CHAIN>` to `.env`
2. Add public fallback to `src/contracts.py` → `PUBLIC_RPC_URLS`
3. Add token addresses to `src/tokens.py` → `CHAIN_TOKENS`
4. Add quoter addresses to `src/contracts.py` (Uniswap V3 QuoterV2, Sushi, etc.)
5. Add swap router to `src/chain_executor.py` → `SWAP_ROUTERS`
6. If Aave V3 exists on that chain, add to `AAVE_V3_POOL`
7. If Velodrome/Aerodrome fork exists, add to `VELO_FACTORIES` and `SWAP_ROUTERS`
8. Test: `PYTHONPATH=src python -c "from onchain_market import OnChainMarket; ..."`

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `429 Too Many Requests` | Rate limit hit | Switch provider or use Llamanodes |
| Quotes return zero | Wrong quoter address or RPC timeout | Check `contracts.py` addresses, increase timeout |
| `eth_call` hangs | Infura free tier under load | Use Alchemy or Llamanodes |
| Connection refused | RPC down or wrong URL | Check URL, try fallback |
| Stale prices | Public RPC caching | Use paid provider with no caching |
