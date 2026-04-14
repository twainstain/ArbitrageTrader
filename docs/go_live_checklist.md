# Going Live — Execution Checklist

This document covers everything needed to move from simulation mode (detect + price + risk) to live execution (real on-chain trades). The bot is designed to run safely in simulation indefinitely — only follow this checklist when you're ready to commit capital.

---

## Prerequisites

Before enabling live execution, confirm:

- [ ] Bot has been running in simulation for 24+ hours with zero false positives
- [ ] Dashboard shows consistent opportunity detection with realistic spreads
- [ ] DEX Health panel shows 80%+ success rate on target chains
- [ ] Liquidity estimation is filtering thin pools (no $50K TVL opportunities getting through)
- [ ] Alerting is working (Discord/Telegram/Gmail notifications received)

---

## Step 1: Fund a Deployer Wallet

Create a fresh wallet for the bot. **Never use a personal wallet.**

```bash
# Generate a new wallet (or use an existing hot wallet)
cast wallet new
```

Fund it with native gas tokens on each target chain:
- **Arbitrum**: ~0.01 ETH (~$25) for deployment + early trades
- **Base**: ~0.005 ETH (~$12)
- **Ethereum**: ~0.05 ETH (~$120) — gas is expensive

Add the private key to `.env`:
```bash
EXECUTOR_PRIVATE_KEY=0x...
```

The contract transfers all profits to this wallet automatically.

---

## Step 2: Deploy FlashArbExecutor

The contract is deployed once per chain. It's immutable — redeploy only if the contract code changes.

### Install Foundry (one-time)

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Deploy

```bash
cd contracts/

# Dry-run first (simulates, costs nothing)
./deploy.sh arbitrum --dry

# Deploy for real (asks for confirmation)
./deploy.sh arbitrum
```

The script:
1. Reads RPC URLs and private key from `.env`
2. Passes the correct Aave V3 Pool address per chain
3. Asks for explicit confirmation before broadcasting
4. Prints the deployed contract address

### Save the address

```bash
# Add to .env
EXECUTOR_CONTRACT=0x<deployed_address>
```

### Supported chains

| Chain | Aave V3 Pool | Gas Cost | Notes |
|-------|-------------|----------|-------|
| Arbitrum | `0x794a...` | ~$0.10-0.50 | Start here — cheapest, deepest liquidity |
| Base | `0xA238...` | ~$0.05-0.20 | Aerodrome opportunities |
| Ethereum | `0x8787...` | ~$5-20 | Flashbots MEV protection included |

### What the contract does

1. Bot calls `executeArbitrage(params)` with token addresses, routers, amounts
2. Contract borrows from Aave V3 flash loan (9 bps fee)
3. Swaps on DEX A (buy cheap) → swaps on DEX B (sell expensive)
4. Repays flash loan + fee
5. Transfers profit to owner
6. If `profit < minProfit` → entire transaction reverts (only gas is lost, never principal)

---

## Step 3: Validate with eth_call Simulation

Before enabling real execution, the bot already simulates every trade via `eth_call` (free, no gas). Verify this is working:

```bash
# Run the bot with execution enabled but high min_profit (won't actually trade)
PYTHONPATH=src python -m run_event_driven \
    --config config/multichain_onchain_config.json
```

Check logs for `"Simulation passed"` or `"simulation_failed"` messages. If simulations pass, the contract deployment and token approvals are correct.

---

## Step 4: Enable Live Execution

**This is the point of no return for real capital.**

### Option A: Via API (runtime, no restart)

```bash
curl -u admin:$DASHBOARD_PASS -X POST \
    http://localhost:8000/execution \
    -H "Content-Type: application/json" \
    -d '{"enabled": true}'
```

### Option B: Via code (persistent)

In `src/run_event_driven.py`, line ~390:

```python
risk_policy = RiskPolicy(
    execution_enabled=True,          # was False
    min_net_profit=0.01,             # ~$25 — start conservative
)
```

### Recommended initial settings

| Parameter | Value | Why |
|-----------|-------|-----|
| `execution_enabled` | `True` | Enable real trades |
| `min_net_profit` | `0.01` (~$25) | Only execute high-confidence opportunities |
| `slippage_bps` | `15` | Conservative slippage tolerance |
| Circuit breaker `max_reverts` | `2` | Stop after 2 reverted transactions |

### What happens on the first trade

1. Bot detects an opportunity above `min_net_profit`
2. `eth_call` simulation runs (free) — if it reverts, trade is skipped
3. Transaction is signed and submitted:
   - **Ethereum**: via Flashbots private relay (invisible to public mempool)
   - **Other chains**: via public mempool
4. Bot waits up to 120s for confirmation
5. If the transaction reverts on-chain: gas is lost (~$0.10-5 depending on chain), no principal lost
6. If successful: profit is transferred to your wallet

---

## Step 5: Monitor

### Dashboard

```
https://arb-trader.yeda-ai.com/dashboard
```

Key metrics to watch:
- **Trades included** — should increase
- **Revert rate** — should be <5%
- **Expected vs Realized ratio** — should be >0.8 (realized profit close to expected)
- **DEX Health** — all green

### Alerts

The bot sends alerts via configured channels:
- **Discord**: every opportunity detected
- **Telegram**: opportunities >5% spread
- **Gmail**: hourly summary

### Circuit Breaker

The bot automatically stops execution if:
- 3+ reverts in 5 minutes
- 10+ RPC errors in 60 seconds
- No fresh quotes for 120 seconds

When tripped, the bot continues scanning but stops submitting transactions. It resumes automatically after a 5-minute cooldown.

---

## Step 6: Tune

After the first 24 hours of live execution:

1. **Lower `min_net_profit`** gradually (0.01 → 0.005 → 0.002) to capture more opportunities
2. **Review revert reasons** in the dashboard — if slippage reverts are common, increase `slippage_bps`
3. **Check gas costs** — if gas is eating profits, focus on L2 chains (Arbitrum, Base)
4. **Deploy to additional chains** if profitable on the first

---

## Rollback

To disable execution immediately:

```bash
# Via API (instant, no restart)
curl -u admin:$DASHBOARD_PASS -X POST \
    http://localhost:8000/execution \
    -d '{"enabled": false}'
```

Or send SIGTERM to the bot process — it drains the current scan and stops cleanly.

The contract remains deployed but idle. No funds are at risk when execution is disabled — the contract only acts when the bot calls it.

---

## Cost Summary

| Item | Cost | Frequency |
|------|------|-----------|
| Contract deployment (Arbitrum) | ~$0.10-0.50 | One-time |
| Contract deployment (Ethereum) | ~$5-20 | One-time |
| Failed trade (revert) | Gas only (~$0.10-5) | Per revert |
| Successful trade | Gas + 9 bps flash loan fee | Per trade |
| Bot infrastructure (EC2 t3.small) | ~$15/month | Ongoing |

No capital is locked in the contract. Flash loans provide the trading capital — you only need gas money in the wallet.
