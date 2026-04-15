# API Reference

The arbitrage bot exposes a REST API via FastAPI for monitoring, control, and
analytics. All endpoints return JSON unless noted otherwise.

**Base URL:** `http://<host>:8000`

**Authentication:** HTTP Basic Auth (`DASHBOARD_USER` / `DASHBOARD_PASS` from
`.env`). Disabled in tests via `require_auth=False`.

**Auto-generated docs:** FastAPI provides interactive docs at `/docs` (Swagger)
and `/redoc` (ReDoc).

---

## Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/execution` | Execution status (per-chain) |
| POST | `/execution` | Enable/disable execution |
| GET | `/launch-readiness` | Pre-launch checklist |
| GET | `/pause` | Soft pause status |
| POST | `/pause` | Toggle soft pause |
| GET | `/scanner` | Scanner running status |
| POST | `/scanner/start` | Start scanner |
| POST | `/scanner/stop` | Stop scanner |
| GET | `/risk/policy` | Current risk thresholds |
| GET | `/opportunities` | List opportunities (filterable) |
| GET | `/opportunities/{id}` | Single opportunity |
| GET | `/opportunities/{id}/full` | Full lifecycle data |
| GET | `/opportunities/{id}/pricing` | Pricing breakdown |
| GET | `/opportunities/{id}/risk` | Risk decision |
| GET | `/opportunities/{id}/simulation` | Simulation result |
| POST | `/opportunities/{id}/replay` | Re-evaluate with current policy |
| GET | `/pnl` | All-time PnL summary |
| GET | `/funnel` | Opportunity funnel counts |
| GET | `/metrics` | In-memory runtime metrics |
| GET | `/operations` | System operational state |
| GET | `/diagnostics/quotes` | Per-DEX quote health |
| GET | `/wallet/balance` | On-chain wallet balances |
| GET | `/dashboard/window/{key}` | Windowed stats (15m, 1h, 24h...) |
| GET | `/dashboard/range` | Custom time range stats |
| GET | `/dashboard/windows` | All windows at once |
| GET | `/dashboard/chains` | Per-chain summary |
| GET | `/dashboard/distinct-chains` | List of active chains |
| GET | `/dashboard/hourly-bars` | Hourly win/loss chart data |
| GET | `/scan-history` | Recent scan records |
| GET | `/scan-history/summary` | Scan analytics summary |
| GET | `/pnl/analytics` | PnL breakdown by pair/venue |
| GET | `/dashboard` | Main dashboard (HTML) |
| GET | `/ops` | Ops dashboard (HTML) |
| GET | `/analytics` | Analytics dashboard (HTML) |
| GET | `/opportunity/{id}` | Opportunity detail page (HTML) |

---

## System Control

### `GET /health`

Health check. Always returns 200 if the API is running.

```json
{
  "status": "ok",
  "execution_enabled": false
}
```

---

### `GET /execution`

Current execution state including per-chain mode and router readiness.

```json
{
  "execution_enabled": false,
  "chain_execution_mode": {"arbitrum": "live", "base": "live"},
  "chains": {
    "arbitrum": {
      "mode": "live",
      "has_routers": true,
      "has_aave": true,
      "executable": true
    },
    "ethereum": {
      "mode": "simulated",
      "has_routers": true,
      "has_aave": true,
      "executable": true
    }
  }
}
```

---

### `POST /execution`

Enable or disable execution. Requires `launch_ready=true` to enable.

**Global toggle:**
```json
// Request
{"enabled": true}

// Response (success)
{"execution_enabled": true, "chain_execution_mode": {}, "message": "updated"}

// Response (not ready — 409)
{"detail": {"message": "launch_not_ready", "launch_ready": false, "launch_blockers": [...]}}
```

**Per-chain mode:**
```json
// Request
{"chain": "arbitrum", "mode": "live"}

// Response
{"chain": "arbitrum", "mode": "live", "chain_execution_mode": {"arbitrum": "live"}}
```

Valid modes: `"live"`, `"simulated"`, `"disabled"`.

---

### `GET /launch-readiness`

Pre-launch checklist. All fields must be true/empty to enable live execution.

```json
{
  "launch_chain": "arbitrum",
  "launch_ready": true,
  "launch_blockers": [],
  "executor_key_configured": true,
  "executor_contract_configured": true,
  "rpc_configured": true
}
```

---

### `GET /pause` / `POST /pause`

Soft pause — stops new scans but lets in-flight trades complete. Separate from
the execution kill switch.

```json
// GET
{"paused": false}

// POST {"paused": true}
{"paused": true}
```

---

### `GET /scanner`

Scanner thread status.

```json
{
  "status": "running",
  "running": true,
  "paused": false,
  "execution_enabled": false
}
```

Status values: `"running"`, `"stopped"`, `"not_configured"`.

### `POST /scanner/start` / `POST /scanner/stop`

Start or stop the scanner. Returns 400 if scanner is not configured.

```json
{"status": "started"}
{"status": "stopping"}
```

---

### `GET /risk/policy`

Current risk policy thresholds. Reflects runtime values including per-chain
spread overrides.

```json
{
  "min_net_profit": "0.005",
  "min_spread_pct_default": "0.40",
  "chain_min_spread_pct": {
    "ethereum": "0.40",
    "arbitrum": "0.20",
    "base": "0.15",
    "optimism": "0.15"
  },
  "max_slippage_bps": "50",
  "min_liquidity_usd": "50000",
  "max_quote_age_seconds": 60.0,
  "max_gas_profit_ratio": "0.5",
  "max_warning_flags": 1,
  "max_trades_per_hour": 100,
  "max_exposure_per_pair": "10",
  "min_liquidity_score": 0.3,
  "execution_enabled": false
}
```

---

## Opportunities

### `GET /opportunities`

List recent opportunities with pricing and execution data. Supports filtering.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Max rows returned |
| `window` | string | — | Predefined window: `5m`, `15m`, `1h`, `4h`, `8h`, `24h`, `3d`, `1w`, `1m` |
| `start` | string | — | ISO timestamp (UTC) — show opportunities >= start |
| `end` | string | — | ISO timestamp (UTC) — show opportunities <= end |
| `chain` | string | — | Filter by chain name |

`start`/`end` take precedence over `window` when both provided.

**Response:** Array of opportunities with joined pricing and execution data.

```json
[
  {
    "opportunity_id": "opp_8a71966cfed3",
    "pair": "WETH/USDC",
    "chain": "optimism",
    "buy_dex": "Uniswap-Optimism",
    "sell_dex": "Sushi-Optimism",
    "spread_bps": "25",
    "status": "simulation_approved",
    "detected_at": "2026-04-15T18:51:08.388754+00:00",
    "updated_at": "2026-04-15T18:51:08.388772+00:00",
    "expected_net_profit": "0.008",
    "fee_cost": "5",
    "slippage_cost": "2",
    "gas_estimate": "0.003",
    "tx_hash": null,
    "submission_type": null,
    "exec_included": null,
    "exec_reverted": null,
    "exec_gas_used": null,
    "realized_profit_quote": null,
    "exec_gas_cost_base": null,
    "actual_net_profit": null,
    "profit_currency": null
  }
]
```

**Status values:** `detected`, `priced`, `approved`, `rejected`,
`simulation_approved`, `submitted`, `included`, `reverted`, `not_included`,
`dry_run`.

---

### `GET /opportunities/{opp_id}`

Single opportunity by ID.

```json
{
  "opportunity_id": "opp_8a71966cfed3",
  "pair": "WETH/USDC",
  "chain": "arbitrum",
  "buy_dex": "Uniswap-Arbitrum",
  "sell_dex": "Sushi-Arbitrum",
  "spread_bps": "42",
  "status": "approved",
  "detected_at": "2026-04-15T14:37:04+00:00",
  "updated_at": "2026-04-15T14:37:04+00:00"
}
```

Returns 404 if not found.

---

### `GET /opportunities/{opp_id}/full`

Complete lifecycle data for one opportunity: pricing, risk decision, simulation,
execution attempt, and trade result — all in one call.

```json
{
  "opportunity": { "...": "..." },
  "pricing": {
    "input_amount": "2200",
    "estimated_output": "2215",
    "fee_cost": "5",
    "slippage_cost": "2",
    "gas_estimate": "0.003",
    "expected_net_profit": "0.008"
  },
  "risk_decision": {
    "approved": 1,
    "reason_code": "passed",
    "threshold_snapshot": "{...}"
  },
  "simulation": {
    "success": 1,
    "revert_reason": "",
    "expected_net_profit": "0.008"
  },
  "execution_attempt": {
    "tx_hash": "0xabcdef1234...",
    "submission_type": "flashbots",
    "target_block": 19000001
  },
  "trade_result": {
    "included": 1,
    "reverted": 0,
    "gas_used": 250000,
    "realized_profit_quote": "12.5",
    "gas_cost_base": "0.002",
    "actual_net_profit": "0.006",
    "profit_currency": "USDC"
  }
}
```

Fields are `null` for stages not yet reached.

---

### `GET /opportunities/{opp_id}/pricing`

Pricing breakdown only. Returns 404 if no pricing data.

### `GET /opportunities/{opp_id}/risk`

Risk decision only. Returns 404 if no risk decision.

### `GET /opportunities/{opp_id}/simulation`

Simulation result only. Returns 404 if not simulated.

---

### `POST /opportunities/{opp_id}/replay`

Re-evaluate a historical opportunity against the **current** risk policy.
Does not re-execute — only re-prices and re-evaluates.

```json
{
  "opportunity": { "...": "..." },
  "original_pricing": { "...": "..." },
  "original_risk": { "...": "..." },
  "original_simulation": null,
  "replay_risk_verdict": {
    "approved": false,
    "reason": "below_min_spread",
    "details": { "...": "..." }
  },
  "current_policy": { "...": "..." }
}
```

---

## Aggregations & Analytics

### `GET /pnl`

All-time PnL from trade results.

```json
{
  "total_trades": 12,
  "successful": 10,
  "reverted": 1,
  "not_included": 1,
  "total_realized_profit_quote": 125.5,
  "total_gas_cost_base": 0.024,
  "total_profit": 0.048,
  "total_gas": 3000000
}
```

---

### `GET /funnel`

Opportunity counts by status (all time).

```json
{
  "detected": 4,
  "approved": 4,
  "rejected": 661,
  "simulation_approved": 759,
  "included": 4,
  "dry_run": 4
}
```

---

### `GET /metrics`

In-memory runtime metrics (reset on restart). Includes rates and percentiles.

```json
{
  "uptime_seconds": 2770.4,
  "opportunities_detected": 1500,
  "opportunities_per_minute": 12.3,
  "opportunities_rejected": 1400,
  "rejection_reasons": {"below_min_spread": 800, "gas_too_expensive": 600},
  "simulations_run": 100,
  "simulations_passed": 95,
  "simulation_success_rate_pct": 95,
  "executions_submitted": 50,
  "executions_included": 45,
  "executions_reverted": 3,
  "executions_not_included": 2,
  "inclusion_rate_pct": 90,
  "revert_rate_pct": 6,
  "total_expected_profit": 0.25,
  "total_actual_profit": 0.22,
  "total_gas_used": 12500000,
  "avg_latency_ms": 145,
  "p95_latency_ms": 320
}
```

---

### `GET /operations`

System operational state: DB backend, discovered pairs, live stack readiness,
per-chain execution config.

```json
{
  "db_backend": "sqlite",
  "discovered_pairs_count": 5,
  "enabled_pools_total": 53,
  "discovery_snapshot_source": "db_cache",
  "last_discovery_pair_count": 5,
  "last_monitored_pools_synced": 0,
  "live_stack_ready": true,
  "live_rollout_target": "arbitrum",
  "live_executable_chains": ["arbitrum", "base", "ethereum", "optimism"],
  "live_executable_dexes": ["Uniswap-Ethereum", "Sushi-Arbitrum", "..."],
  "launch_chain": "arbitrum",
  "launch_ready": true,
  "launch_blockers": [],
  "executor_key_configured": true,
  "executor_contract_configured": true,
  "rpc_configured": true
}
```

---

### `GET /diagnostics/quotes`

Per-DEX quote health: success rate, latency, last error. Grouped by DEX name.

```json
{
  "dexes": {
    "Uniswap": [
      {
        "key": "Uniswap:ethereum:WETH/USDC",
        "success_count": 450,
        "total_quotes": 500,
        "success_rate": 0.9,
        "avg_latency_ms": 120.5,
        "last_outcome": "success",
        "last_error": ""
      }
    ]
  }
}
```

---

### `GET /wallet/balance`

On-chain wallet ETH balances across chains. Fetches live via RPC (may be slow).

```json
{
  "address": "0xcfF46971b1BA42d74C4c51ec850c7F33f903EAeB",
  "balances": {
    "arbitrum": 0.010975,
    "ethereum": 0.011,
    "base": 0.000005
  }
}
```

---

### `GET /pnl/analytics`

PnL broken down by pair, venue, hourly, and rejection reasons.

```json
{
  "per_pair": [{"pair": "WETH/USDC", "profit": 0.04, "trades": 10}],
  "per_venue": [{"buy_dex": "Uniswap", "sell_dex": "Sushi", "profit": 0.03}],
  "expected_vs_realized": [{"opportunity_id": "...", "expected": 0.005, "realized": 0.004}],
  "hourly_pnl": [{"hour": "2026-04-15T14", "profit": 0.01, "trades": 3}],
  "rejection_reasons": [{"reason_code": "gas_too_expensive", "chain": "ethereum", "cnt": 500}]
}
```

---

### `GET /scan-history`

Recent scan records with filter breakdown.

### `GET /scan-history/summary`

Scan analytics: filter breakdown, near-miss analysis, spread distribution.

```json
{
  "filter_breakdown": [{"filter": "below_min_spread", "count": 800}],
  "near_misses": [{"opp_id": "...", "shortfall": 0.001}],
  "spread_distribution": [{"bucket": "0.1-0.2%", "count": 300}]
}
```

---

## Dashboard Data (Time-Windowed)

### `GET /dashboard/window/{window_key}`

Aggregated stats for a predefined time window.

**Window keys:** `5m`, `15m`, `1h`, `4h`, `8h`, `24h`, `3d`, `1w`, `1m`

**Query params:** `chain` (optional filter)

```json
{
  "window": "1h",
  "chain": "all",
  "since": "2026-04-15T18:38:09+00:00",
  "opportunities": {
    "total": 171,
    "funnel": {
      "approved": 4,
      "rejected": 19,
      "simulation_approved": 136
    }
  },
  "trades": {
    "total_trades": 0,
    "successful": 0,
    "reverted": 0,
    "total_profit": 0,
    "total_gas": 0
  },
  "profit": {
    "priced_count": 165,
    "total_expected_profit": 1.014,
    "avg_expected_profit": 0.006,
    "max_expected_profit": 0.067,
    "min_expected_profit": 0.001
  }
}
```

---

### `GET /dashboard/range`

Custom time range stats. Same response shape as windowed stats.

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | string | Yes | ISO timestamp (UTC) |
| `end` | string | No | ISO timestamp (UTC), defaults to now |
| `chain` | string | No | Chain filter |

```
GET /dashboard/range?start=2026-04-15T00:00:00&end=2026-04-15T12:00:00&chain=arbitrum
```

---

### `GET /dashboard/windows`

All predefined windows in a single call. Returns a dict keyed by window name.

```json
{
  "5m": { "window": "5m", "opportunities": {...}, "trades": {...}, "profit": {...} },
  "15m": { "...": "..." },
  "1h": { "...": "..." },
  "24h": { "...": "..." }
}
```

---

### `GET /dashboard/chains`

Per-chain opportunity breakdown for a given window.

**Query params:** `window` (default `"24h"`)

```json
[
  {
    "chain": "ethereum",
    "total": 1418,
    "funnel": {"rejected": 659, "simulation_approved": 755, "included": 2}
  },
  {
    "chain": "arbitrum",
    "total": 6,
    "funnel": {"approved": 2, "detected": 2, "simulation_approved": 2}
  }
]
```

Sorted by total (descending).

---

### `GET /dashboard/distinct-chains`

List of chain names that have at least one opportunity.

```json
["arbitrum", "base", "ethereum", "optimism"]
```

Sorted alphabetically.

---

### `GET /dashboard/hourly-bars`

Per-chain win/loss counts for the last 24 hours, grouped by hour. Used by the
bar chart on the dashboard.

```json
[
  {"chain": "ethereum", "status": "rejected", "hour": "2026-04-15T15", "cnt": 44},
  {"chain": "ethereum", "status": "simulation_approved", "hour": "2026-04-15T15", "cnt": 32}
]
```

---

## HTML Pages

| Endpoint | Description |
|----------|-------------|
| `GET /dashboard` | Main dashboard with status cards, time windows, chain breakdown, opportunities table, bar chart |
| `GET /ops` | Operations dashboard: infra status, RPC health, DEX health table, scan metrics, risk policy |
| `GET /analytics` | Analytics dashboard: PnL by pair/venue, rejection breakdown, near-miss analysis |
| `GET /opportunity/{opp_id}` | Single opportunity detail page with full lifecycle, cost breakdown, risk analysis |

All HTML pages auto-refresh every 30 seconds. Times are displayed in EST
(America/New_York). No-cache headers are set.

---

## Notes

- **Timestamps:** All stored and returned as ISO 8601 UTC. Dashboard converts
  to EST client-side.
- **Decimal precision:** Financial values (`spread_bps`, `expected_net_profit`,
  etc.) are stored as strings to preserve precision. Convert to float/Decimal
  as needed.
- **Status progression:** `detected` → `priced` → `approved`/`rejected`/`simulation_approved`
  → `submitted` → `included`/`reverted`/`not_included`
- **spread_bps:** Stored in basis points. Divide by 100 for percentage display
  (e.g., 42 bps = 0.42%).
