# Execution Phase Status

Last updated: 2026-04-14

This document captures the current execution/go-live status so work can resume quickly later without reconstructing context from chat history.

## Current Phase

We are past the core same-chain multi-pair detection work and into the live-execution hardening phase.

Current focus:
- Arbitrum-first live rollout
- V3-only live execution path
- accurate execution PnL and launch-readiness visibility

Not in scope right now:
- Optimism live rollout
- Velodrome live execution
- bridge-based cross-chain execution

## What Is Done

### 1. Same-chain multi-pair detection path

Implemented:
- pair-aware `OnChainMarket`
- pair-aware `ArbitrageStrategy`
- discovered pair metadata preserved through on-chain scanning
- canonical pair lists used in:
  - `src/run_event_driven.py`
  - `src/run_live_with_dashboard.py`
  - `src/event_listener.py`
- event-driven flow is pair-aware structurally

### 2. Metadata and ops persistence

Implemented:
- persisted discovered pairs
- DB-backed monitored pool bootstrap
- warm-start metadata from DB
- ops dashboard + `/operations`
- startup checkpoints for discovery, monitored pools, and live readiness

### 3. Live execution stack wiring

Implemented:
- `run_event_driven` now wires:
  - simulator
  - submitter
  - verifier
- current live executor supports only:
  - `uniswap_v3`
  - `sushi_v3`
  - `pancakeswap_v3`
- unsupported live venues are rejected explicitly

### 4. Arbitrum-first live hardening

Implemented:
- `config/arbitrum_live_execution_config.json`
- live rollout summary:
  - executable chains
  - executable venues
  - rollout target
- launch readiness assessment:
  - `launch_ready`
  - `launch_blockers`
  - `launch_chain`
  - executor key/contract/rpc flags
- startup fail-safe:
  - runner forces simulation mode if launch is not ready
- runtime fail-safe:
  - `POST /execution` refuses live enablement unless launch readiness is green
- direct readiness endpoint:
  - `GET /launch-readiness`

### 5. Execution PnL cleanup

Implemented:
- verifier now returns structured execution result fields
- trade results persist:
  - `realized_profit_quote`
  - `gas_cost_base`
  - `profit_currency`
  - `actual_net_profit`
- execution detail page now shows:
  - tx hash
  - inclusion/revert
  - realized quote profit
  - gas cost in base
  - net base profit
- ops dashboard now shows:
  - realized quote profit
  - gas cost (base)
  - net profit (base)

## What Is Still Blocked / Not Done

### 1. Not live-ready on all configs

`config/multichain_onchain_config.json` is still not a clean live-launch config because it includes:
- off-target chains
- unsupported live venues
- venues that are detection-only today

Use `config/arbitrum_live_execution_config.json` for the supported live path.

### 2. Velodrome / Optimism execution is still not supported

Detection may work better now that RPC keys were updated, but live execution is still not ready because:
- executor/contract path is V3-router-shaped
- Velodrome uses a different execution model
- deploy/execution support for Optimism is not the chosen launch path yet

### ~~3. Full fork-style dry execution pass not done yet~~ DONE (2026-04-15)

Completed via `scripts/fork_rehearsal.py --auto-anvil`:
- forks Arbitrum mainnet via anvil
- builds tx against deployed contract
- simulates via eth_call
- signs, submits, waits for receipt
- verifies via OnChainVerifier
- all 7 checks passed (revert expected — no real arb at forked block)

### ~~4. Startup/runbook summary still missing~~ DONE (2026-04-15)

Completed via `scripts/check_readiness.py`:
- CLI readiness check for any config
- API-based readiness check for running instances
- shows: target chain, blockers, executable DEXes, financial params

### 5. Contract deployed on Arbitrum (2026-04-15)

- FlashArbExecutor: `0x95AFF47C4E58F4e4d2A0586bbBEDdbd926198115`
- Aave Pool: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- Owner: `0xcfF46971b1BA42d74C4c51ec850c7F33f903EAeB`
- Launch readiness: GREEN (all checks pass)

## Flash Loan Behavior

The flash loan is part of execution itself.

Current behavior:
- Python calls `executeArbitrage(...)`
- contract requests flash loan from Aave V3
- Aave calls back into the contract
- contract performs both swaps, repays principal + premium, and sends profit to owner

Important property:
- this is one atomic transaction
- if profit is below `minProfit`, or a swap fails, the whole transaction reverts
- principal is not lost
- in a revert case, the practical loss is gas only

Current control points:
- config:
  - `flash_loan_fee_bps`
  - `flash_loan_provider`
- executor:
  - chain-specific `AAVE_V3_POOL`
- deployment:
  - contract constructor gets the chain’s Aave pool
- live toggle:
  - `POST /execution`
- launch safety gate:
  - launch readiness must be true

## Most Relevant Files

Core live path:
- `src/run_event_driven.py`
- `src/chain_executor.py`
- `src/pipeline/lifecycle.py`
- `src/pipeline/verifier.py`

Persistence / API / dashboard:
- `src/persistence/db.py`
- `src/persistence/repository.py`
- `src/api/app.py`
- `src/api/dashboard.py`

Configs:
- `config/arbitrum_live_execution_config.json`
- `config/multichain_onchain_config.json`

Contract:
- `contracts/FlashArbExecutor.sol`
- `contracts/deploy.sh`

## Latest Verified Test Slices

Execution verifier / pipeline / persistence:
```bash
/usr/local/bin/python3.11 -m pytest tests/test_verifier.py tests/test_pipeline.py tests/test_persistence.py
```

Result:
- `77 passed`

API / dashboard:
```bash
/usr/local/bin/python3.11 -m pytest tests/test_api.py tests/test_dashboard.py
```

Result:
- `44 passed`

Launch-readiness / API / dashboard:
```bash
/usr/local/bin/python3.11 -m pytest tests/test_event_driven.py tests/test_api.py tests/test_dashboard.py
```

Result at last run:
- `67 passed`

## What Was Completed This Session (2026-04-15)

1. Contract deployed on Arbitrum mainnet
2. `check_readiness.py` CLI — launch readiness passes
3. Fork rehearsal (`fork_rehearsal.py`) — full execution path verified
4. Dashboard upgraded:
   - all columns sortable (click to sort, arrows show direction)
   - default sort: approved first, then by profit desc
   - Expected Profit only shown for approved statuses
   - new Realized PnL column
   - executed transactions shown first with expandable detail rows
   - click executed row to see: tx hash, inclusion, gas, realized profit, net PnL
   - async wallet balance cards (fetched from on-chain RPC)
   - wallet link to Arbiscan
5. `/wallet/balance` API endpoint added
6. `/opportunities` API now includes execution + trade_result data in one query

## Recommended Next Steps

### Next step 1

Enable live execution and monitor the first few trades.

```
curl -u admin:$DASHBOARD_PASS -X POST \
  http://localhost:8000/execution \
  -H 'Content-Type: application/json' \
  -d '{"enabled": true}'
```

### Next step 2

Monitor PnL and gas costs on the dashboard. Tune `min_profit_base` if spreads are too thin after gas.

### Next step 3

Consider deploying on Base (already funded, 0.011 ETH) for multi-chain execution.

## Resume Prompt

If resuming later, a good starting prompt is:

> The bot is live-ready on Arbitrum. Contract deployed, fork rehearsal passed, dashboard upgraded. Check `docs/execution_phase_status.md` for current state.
