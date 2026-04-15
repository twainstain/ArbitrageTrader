# Architecture & Decision Logic

> A human-readable guide to how the arbitrage bot detects, evaluates, and
> executes trades.  Every threshold, formula, and decision gate is documented
> here so an engineer can reason about the system without reading every source
> file.

---

## 1. System Overview

### High-level architecture

```mermaid
graph LR
    subgraph Data Layer
        RPC[RPC Nodes<br/>Alchemy / Infura]
        DB[(PostgreSQL<br/>or SQLite)]
    end

    subgraph Core Engine
        OM[OnChainMarket<br/>quote fetching]
        SC[OpportunityScanner<br/>detect & rank]
        Q[CandidateQueue<br/>priority queue]
        PL[CandidatePipeline<br/>6-stage lifecycle]
    end

    subgraph Safety
        RP[RiskPolicy<br/>8-rule gate]
        CB[CircuitBreaker<br/>auto-pause]
    end

    subgraph Execution
        CE[ChainExecutor<br/>tx build & send]
        VR[OnChainVerifier<br/>PnL reconcile]
    end

    subgraph Outputs
        DASH[Dashboard<br/>FastAPI + HTML]
        ALERT[Alerting<br/>Email / Telegram]
    end

    RPC --> OM --> SC --> Q --> PL
    PL --> RP
    PL --> CB
    PL --> CE --> VR
    PL --> DB
    DB --> DASH
    PL --> ALERT
```

### Threading model

```mermaid
graph TD
    MAIN["Main Thread<br/><b>EventDrivenScanner</b><br/>polls blocks, fetches quotes,<br/>pushes to queue"]
    PIPE["Consumer Thread<br/><b>PipelineConsumer</b><br/>pops queue, runs 6-stage pipeline"]
    HOUR["Daemon Thread<br/><b>SmartAlerter</b><br/>hourly + daily email reports"]
    DIAG["Daemon Thread<br/><b>QuoteDiagnostics</b><br/>flush health to DB every 5 min"]
    API["Daemon Thread<br/><b>FastAPI / Uvicorn</b><br/>dashboard + API endpoints"]

    MAIN -->|"CandidateQueue<br/>(thread-safe)"| PIPE
    PIPE -->|"maybe_send_hourly()"| HOUR
    MAIN -.->|"signal handlers<br/>SIGINT / SIGTERM"| MAIN
```

### Data flow

```mermaid
flowchart TD
    A[Poll RPC for swap events] --> B[Fetch fresh DEX quotes]
    B --> C[Scanner: filter & rank]
    C --> D{Queue full?}
    D -->|No| E[Push to queue]
    D -->|Yes, score > lowest| F[Evict lowest, push new]
    D -->|Yes, score < lowest| G[Drop candidate]
    E --> H[Pipeline consumer pops]
    F --> H
    H --> I[Detect: persist to DB]
    I --> J[Price: cost waterfall]
    J --> K[Risk: 8-rule evaluation]
    K -->|Rejected| L[Log reason, stop]
    K -->|Sim-approved| M[Log as dry-run, stop]
    K -->|Approved| N[Simulate: eth_call]
    N -->|Revert| L
    N -->|Pass| O[Submit: sign & send tx]
    O --> P[Verify: check receipt]
    P --> Q[Reconcile PnL]
```

---

## 2. Opportunity Detection (`scanner.py`)

### What it does

For every scan cycle the scanner fetches fresh quotes from all configured DEXes
and chains, then evaluates **every cross-DEX pair** looking for price
discrepancies that survive the cost model.

### Scanner workflow

```mermaid
flowchart TD
    START[New scan cycle] --> FETCH[Fetch quotes from all DEXes]
    FETCH --> GROUP[Group quotes by pair]
    GROUP --> MEDIAN[Compute per-chain price medians]
    MEDIAN --> PAIRS[Generate all cross-DEX pairs]
    PAIRS --> F1{Same DEX?}
    F1 -->|Yes| DROP1[Skip]
    F1 -->|No| F2{Cross-chain?}
    F2 -->|Yes| DROP2[Skip]
    F2 -->|No| F3{Negative spread?}
    F3 -->|Yes| DROP3[Skip]
    F3 -->|No| F4{Liquidity < $1M?}
    F4 -->|Yes| DROP4[Skip]
    F4 -->|No| F5{Price > 2% from median?}
    F5 -->|Yes| DROP5[Skip]
    F5 -->|No| COST[Run cost model]
    COST --> SCORE[Composite scoring]
    SCORE --> RANK[Rank by score descending]
    RANK --> ALERT_FILTER{Net profit > min?<br/>Flags <= max?}
    ALERT_FILTER -->|No| DROP6[Skip]
    ALERT_FILTER -->|Yes| QUEUE[Push to CandidateQueue]
```

### Filtering pipeline (applied in order)

| Filter | Rule | Why |
|--------|------|-----|
| Same-DEX | Skip if `buy_dex == sell_dex` | No arbitrage possible |
| Cross-chain | Skip if buy and sell are on different chains | Cannot execute atomically |
| Negative spread | Skip if `sell_price <= buy_price` after fees | Unprofitable |
| Low liquidity | Skip if `min(buy_liq, sell_liq) < $1M` | Execution risk too high |
| Price outlier | Skip if price deviates > 2% from chain median | Likely stale/bad quote |

### Composite scoring

Every surviving opportunity gets a **composite score** (0.0 - 1.0):

```
score = 0.50 * profit_score     profit / 1.0 WETH, capped at 1.0
      + 0.25 * liquidity_score  log10(min_liq) / 7.0, capped at 1.0
      + 0.15 * flag_score       1.0 - (warning_count * 0.25), min 0
      + 0.10 * spread_score     spread_pct / 5.0, capped at 1.0
```

**Why these weights:** Profit is most important but a thin pool with a fat
spread is a trap.  Liquidity and warning flags prevent the bot from chasing
mirages.

### Warning flags

| Flag | Condition | Meaning |
|------|-----------|---------|
| `low_liquidity` | `min_liquidity < $100K` | Pool too thin, likely slippage |
| `thin_market` | `min_volume < $50K` | Low trading activity |
| `stale_quote` | `quote_age > 60s` | Price may have moved |
| `high_fee_ratio` | `(fees + flash + slippage) / gross_spread > 80%` | Costs eat most of the profit |

---

## 3. Cost Model & Net Profit (`strategy.py`)

Every opportunity goes through a full cost waterfall before profit is
calculated.  **All intermediate math uses `Decimal` — never `float`.**

### Cost waterfall diagram

```mermaid
flowchart TD
    A["<b>Gross Spread</b><br/>sell_price - buy_price"] --> B["- DEX Fees<br/>(buy fee + sell fee)"]
    B --> C["- Slippage<br/>dynamic: scales with trade_size/liquidity"]
    C --> D["- Flash Loan Fee<br/>Aave: 9 bps, Balancer: 0 bps"]
    D --> E["= Net Profit (quote)<br/>in USDC"]
    E --> F["/ mid_price<br/>convert to base asset"]
    F --> G["- Gas Cost (base)<br/>estimated from chain"]
    G --> H["= <b>Net Profit (base)</b><br/>in WETH"]

    style A fill:#00a87e,color:#fff
    style H fill:#00a87e,color:#fff
    style B fill:#e23b4a,color:#fff
    style C fill:#e23b4a,color:#fff
    style D fill:#e23b4a,color:#fff
    style G fill:#e23b4a,color:#fff
```

### Formula

```
buy_cost      = trade_size * buy_price / (1 - fee_bps/10000)   [if fees not pre-included]
sell_proceeds = trade_size * sell_price * (1 - fee_bps/10000)   [if fees not pre-included]

slippage_cost = buy_cost * base_slippage * (1 + trade_size / liquidity)
flash_fee     = buy_cost * flash_loan_fee_bps / 10000

net_profit_quote = sell_proceeds - buy_cost - slippage_cost - flash_fee
net_profit_base  = (net_profit_quote / mid_price) - gas_cost_base
```

### Key parameters

| Parameter | Typical value | Source |
|-----------|--------------|--------|
| `trade_size` | 1-3 WETH | Config |
| `fee_bps` | 30 (standard V3 pool) | Pool-specific |
| `slippage_bps` | 10-15 | Config |
| `flash_loan_fee_bps` | 9 (Aave V3), 0 (Balancer) | Config |
| `gas_cost_base` | ~0.003 ETH (Arbitrum), ~0.01 ETH (Ethereum) | Estimated at runtime |

### Fee-included vs. calculated

On-chain quoters (Uniswap V3 `quoteExactInputSingle`) return amounts with
fees already deducted.  When `fee_included=True` the cost model skips the
fee adjustment to avoid double-counting.

### Liquidity score

```python
score = min(1.0, log10(min_liquidity_usd) / 7.0)
```

- `$10M+ TVL` -> 1.0 (saturated)
- `$1M TVL` -> 0.86
- `$100K TVL` -> 0.71
- `$10K TVL` -> 0.57

---

## 4. Risk Policy (`risk/policy.py`)

Once an opportunity is priced, the risk policy runs **eight sequential
checks**.  A failure at any step is a **hard veto** — the opportunity is
rejected immediately.

### Risk evaluation flowchart

```mermaid
flowchart TD
    IN[Opportunity priced] --> R1{Execution mode?}
    R1 -->|disabled| REJ[REJECTED]
    R1 -->|live or simulated| R2{Spread >= chain min?}
    R2 -->|No| REJ
    R2 -->|Yes| R3{Net profit >= 0.005 WETH?}
    R3 -->|No| REJ
    R3 -->|Yes| R4{Warning flags <= 1?}
    R4 -->|No| REJ
    R4 -->|Yes| R5{Liquidity score >= 0.3?}
    R5 -->|No| REJ
    R5 -->|Yes| R6{Gas/profit ratio <= 50%?}
    R6 -->|No| REJ
    R6 -->|Yes| R7{Trades this hour < 100?}
    R7 -->|No| REJ
    R7 -->|Yes| R8{Pair exposure < 10 WETH?}
    R8 -->|No| REJ
    R8 -->|Yes| MODE{Execution enabled<br/>for this chain?}
    MODE -->|Yes| APP[APPROVED<br/>proceed to simulate]
    MODE -->|No| SIM[SIMULATION_APPROVED<br/>log as dry-run]

    style REJ fill:#e23b4a,color:#fff
    style APP fill:#00a87e,color:#fff
    style SIM fill:#ec7e00,color:#fff
```

### Evaluation order

| # | Rule | Threshold (default) | Why |
|---|------|---------------------|-----|
| 1 | **Execution mode** | Per-chain: `live` / `simulated` / `disabled` | Prevents accidental trades on wrong chains |
| 2 | **Minimum spread** | Ethereum: 0.40%, Arbitrum: 0.20%, Base/Optimism: 0.15% | Must exceed chain-specific gas + fee floor |
| 3 | **Minimum net profit** | 0.005 WETH (~$12) | Below this, gas variance can flip trade negative |
| 4 | **Warning flags** | max 1 flag allowed | Multiple flags = compounding risk |
| 5 | **Liquidity score** | min 0.3 | Pools below this risk slippage blow-up |
| 6 | **Gas-to-profit ratio** | max 50% | If gas eats >50% of profit, variance is too high |
| 7 | **Rate limiting** | max 100 trades/hour | Prevents execution clustering |
| 8 | **Exposure limit** | max 10 WETH per pair | Prevents concentration in one pair |

### Per-chain spread thresholds

These are calibrated to each chain's gas cost:

```
Ethereum:   0.40%   (gas ~$2-5, need bigger spread to cover)
Arbitrum:   0.20%   (gas ~$0.10)
Base:       0.15%   (gas ~$0.05)
Optimism:   0.15%   (gas ~$0.05)
Polygon:    0.20%
BSC:        0.20%
Avalanche:  0.25%
```

### Simulation-approved path

If all rules pass but execution is disabled for the chain, the policy returns
`simulation_approved` instead of `approved`.  This opportunity appears in the
dashboard as "would have executed" — useful for strategy tuning without risk.

---

## 5. Circuit Breaker (`risk/circuit_breaker.py`)

An automatic safety mechanism that **pauses all execution** when the system
detects degraded conditions.

### State machine

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> OPEN : Trip condition met<br/>(reverts, RPC errors,<br/>stale data, block exposure)
    OPEN --> HALF_OPEN : Cooldown expires<br/>(300 seconds)
    HALF_OPEN --> CLOSED : Probe trade succeeds
    HALF_OPEN --> OPEN : Probe trade fails
    CLOSED --> CLOSED : Normal operation<br/>(monitor events)

    note right of CLOSED : All trades allowed
    note right of OPEN : All trades BLOCKED
    note right of HALF_OPEN : One probe trade allowed
```

### Trip conditions

| Condition | Threshold | Window | Reason |
|-----------|-----------|--------|--------|
| Repeated reverts | 3 reverts | 5 minutes | Contract/market conditions changed |
| RPC degradation | 5 errors | 60 seconds | Node is failing, quotes unreliable |
| Stale data | No fresh quote | 120 seconds | Market data too old to trust |
| Block window exposure | 3 trades | 10 blocks | Too many trades too fast |

### Recovery

After **300 seconds** (5 min) cooldown, the breaker enters `HALF_OPEN`:
- One "probe" trade is allowed through
- If it succeeds: breaker resets to `CLOSED`
- If it fails (revert): breaker goes back to `OPEN`

---

## 6. Pipeline Lifecycle (`pipeline/lifecycle.py`)

Every opportunity flows through a **six-stage pipeline**.  Each stage persists
its result to the database before proceeding.  A failure at any stage stops the
pipeline for that opportunity.

```mermaid
flowchart LR
    subgraph "Batched DB write"
        S1["1. DETECT<br/>create record"]
        S2["2. PRICE<br/>cost waterfall"]
        S3["3. RISK<br/>8-rule gate"]
    end
    subgraph "External calls"
        S4["4. SIMULATE<br/>eth_call dry-run"]
        S5["5. SUBMIT<br/>sign & broadcast"]
        S6["6. VERIFY<br/>check receipt"]
    end

    S1 --> S2 --> S3
    S3 -->|approved| S4
    S3 -->|rejected| STOP1[Stop]
    S3 -->|sim_approved| STOP2[Log dry-run]
    S4 -->|pass| S5
    S4 -->|revert| STOP3[Stop]
    S5 --> S6
    S6 --> RESULT["included / reverted / not_included"]

    style STOP1 fill:#e23b4a,color:#fff
    style STOP2 fill:#ec7e00,color:#fff
    style STOP3 fill:#e23b4a,color:#fff
    style RESULT fill:#00a87e,color:#fff
```

### Timing instrumentation

Every stage is timed in milliseconds.  The `total_ms` and per-stage breakdown
are logged and stored in `logs/latency.jsonl` for performance analysis.

### Batch persistence

Stages 1-3 (detect, price, risk) are batched into a single DB transaction to
reduce round-trips.  Stages 4-6 persist independently since they involve
external calls (RPC, mempool).

---

## 7. Priority Queue (`pipeline/queue.py`)

A **bounded, thread-safe priority queue** sits between the scanner and the
pipeline consumer.

| Property | Value |
|----------|-------|
| Max size | 100 (configurable) |
| Priority | `composite_score` from scanner (0.0 - 1.0) |
| Eviction | When full, lowest-priority candidate is dropped |
| Extraction | Highest priority first |

### Back-pressure

When the queue is full and a new candidate arrives:
1. If new candidate's score < lowest in queue: **drop the new one**
2. Otherwise: **evict the lowest**, insert the new one

This ensures the pipeline always processes the best available opportunities.

---

## 8. On-Chain Execution (`chain_executor.py`)

### Execution workflow

```mermaid
flowchart TD
    OPP[Approved opportunity] --> RESOLVE[Resolve token addresses<br/>from CHAIN_TOKENS registry]
    RESOLVE --> ROUTER[Look up swap router<br/>for buy_dex and sell_dex]
    ROUTER --> TYPE{Swap type?}
    TYPE -->|Uniswap/Sushi/Pancake| V3["V3 swap<br/>exactInputSingle()"]
    TYPE -->|Velodrome/Aerodrome| VELO["Solidly swap<br/>swapExactTokensForTokens()"]
    V3 --> BUILD[Build executeArbitrage() calldata]
    VELO --> BUILD
    BUILD --> GAS[Estimate gas * 1.2x buffer]
    GAS --> SIM{Simulate via eth_call}
    SIM -->|Reverts| ABORT[Abort — no gas spent]
    SIM -->|Success| CHAIN{Which chain?}
    CHAIN -->|Ethereum| FB[Flashbots bundle<br/>target: current_block + 1]
    CHAIN -->|L2s| PUB[Public mempool]
    FB --> WAIT[Wait for receipt<br/>timeout: 120s]
    PUB --> WAIT
    WAIT --> VERIFY[Verify outcome]

    style ABORT fill:#e23b4a,color:#fff
    style FB fill:#494fdf,color:#fff
    style PUB fill:#494fdf,color:#fff
```

### Transaction building

1. Resolve token addresses from `CHAIN_TOKENS` registry
2. Look up swap router address for the DEX on this chain
3. Determine swap type: `V3` (Uniswap-style) or `VELO` (Velodrome/Aerodrome)
4. Encode `executeArbitrage(baseToken, quoteToken, buyRouter, sellRouter, feeTier, amount, minProfit, ...)`

### Swap types

| Type | ID | DEXes | Router interface |
|------|----|-------|------------------|
| V3 | 0 | Uniswap V3, Sushi V3, PancakeSwap V3 | `exactInputSingle()` |
| Velodrome | 1 | Velodrome V2, Aerodrome | `swapExactTokensForTokens()` |

### Gas estimation

```
estimate = eth_estimateGas(tx_data) * 1.2   (20% safety buffer)
fallback = 500,000 gas                       (if estimation fails)
```

Why 1.2x: accounts for ~10% variance between estimate and execution (storage
slot changes, approval state).

### Submission strategy

| Chain | Method | Why |
|-------|--------|-----|
| Ethereum mainnet | **Flashbots bundle** (private relay) | MEV protection, no failed-tx gas cost |
| All other chains | Public mempool | No Flashbots equivalent; L2 gas is cheap |

Flashbots bundles target `current_block + 1` for maximum arbitrage freshness.
If the bundle is not included in the target block, it expires harmlessly (no
gas spent).

---

## 9. Verification & PnL Reconciliation (`pipeline/verifier.py`)

After a transaction is submitted, the verifier checks the on-chain outcome.

### Verification workflow

```mermaid
flowchart TD
    TX[tx_hash from submission] --> RECEIPT[Fetch transaction receipt]
    RECEIPT --> STATUS{receipt.status?}
    STATUS -->|0| REVERTED["REVERTED<br/>record gas_used, no profit"]
    STATUS -->|No receipt| NI["NOT_INCLUDED<br/>bundle expired or dropped"]
    STATUS -->|1| LOGS[Parse event logs]
    LOGS --> PROFIT{ProfitRealized event?}
    PROFIT -->|Yes| EXTRACT1[Extract profit amount]
    PROFIT -->|No| EXTRACT2[Fallback: ERC-20 Transfer events]
    EXTRACT1 --> GASCALC["Gas cost = gas_used * gas_price / 1e18"]
    EXTRACT2 --> GASCALC
    GASCALC --> NET["Net = realized_profit - gas_cost"]
    NET --> RECONCILE["Compare vs expected profit<br/>flag if deviation > 20%"]
    RECONCILE --> PERSIST[Persist trade_result to DB]

    style REVERTED fill:#e23b4a,color:#fff
    style NI fill:#ec7e00,color:#fff
    style PERSIST fill:#00a87e,color:#fff
```

### Verification steps

1. Fetch transaction receipt
2. Check `status`: 1 = success, 0 = reverted
3. If successful:
   - Extract `ProfitRealized` event from logs (or fallback to Transfer events)
   - Calculate gas cost: `gas_used * effective_gas_price / 1e18`
   - Net profit: `realized_profit - gas_cost`

### PnL reconciliation

Compares expected profit (from pricing) vs. actual realized profit:

```
deviation     = actual - expected
deviation_pct = deviation / expected * 100
```

Deviations > 20% are flagged and logged.  Consistent deviations in one
direction indicate the cost model needs recalibration.

---

## 10. Data Models (`models.py`)

### MarketQuote

```
dex, pair, buy_price, sell_price, fee_bps, fee_included
volume_usd, liquidity_usd, quote_timestamp
```

### Opportunity

```
pair, buy_dex, sell_dex, chain, trade_size
cost_to_buy_quote, proceeds_from_sell_quote
gross_profit_quote, net_profit_quote, net_profit_base
dex_fee_cost_quote, flash_loan_fee_quote, slippage_cost_quote, gas_cost_base
warning_flags, liquidity_score, is_cross_chain
```

All financial fields are `Decimal`.  Float-to-Decimal conversion goes through
`str()` to avoid IEEE-754 precision loss.

---

## 11. Configuration (`config.py`)

### Key config fields

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `pair` | str | `"WETH/USDC"` | Primary trading pair |
| `trade_size` | Decimal | `1.0` | Trade amount in base asset |
| `min_profit_base` | Decimal | `0.005` | Hard minimum profit (WETH) |
| `flash_loan_fee_bps` | int | `9` | Aave V3: 9, Balancer: 0 |
| `slippage_bps` | int | `15` | Base slippage estimate |
| `dexes` | list | 2+ required | DEX configs with chain + type |
| `chain_execution_mode` | dict | `{"arbitrum": "live"}` | Per-chain mode |

### Validation rules

- At least 2 DEXes required
- `trade_size > 0`
- `flash_loan_provider` must be `"aave_v3"` or `"balancer"`
- Fee and slippage BPS in `[0, 9999]`

---

## 12. Supported DEXes & Chains

### Chains

| Chain | Gas cost | Min spread | RPC source |
|-------|----------|------------|------------|
| Ethereum | ~$2-5 | 0.40% | Alchemy |
| Arbitrum | ~$0.10 | 0.20% | Alchemy |
| Base | ~$0.05 | 0.15% | Alchemy |
| Optimism | ~$0.05 | 0.15% | Infura/public |
| Polygon | ~$0.01 | 0.20% | Alchemy |
| BSC | ~$0.10 | 0.20% | Public |
| Avalanche | ~$0.10 | 0.25% | Alchemy |

### DEX types

| Type | Protocol | Quote method |
|------|----------|--------------|
| `uniswap_v3` | Uniswap V3 | `QuoterV2.quoteExactInputSingle()` |
| `sushi_v3` | SushiSwap V3 | Same ABI as Uniswap V3 |
| `pancakeswap_v3` | PancakeSwap V3 | Same ABI, different addresses |
| `velodrome_v2` | Velodrome (Optimism) | `Router.getAmountOut()` |
| `aerodrome` | Aerodrome (Base) | Same as Velodrome |
| `balancer_v2` | Balancer | `Vault.queryBatchSwap()` |
| `curve` | Curve | Pool-specific `get_dy()` |

---

## 13. Flash Loan Arbitrage Sequence

```mermaid
sequenceDiagram
    participant Bot as Arbitrage Bot
    participant Aave as Aave V3 Pool
    participant Contract as FlashArbExecutor
    participant BuyDEX as Buy DEX (cheaper)
    participant SellDEX as Sell DEX (expensive)

    Bot->>Contract: executeArbitrage(tokens, routers, amount, minProfit)
    Contract->>Aave: flashLoan(WETH, amount)
    Aave->>Contract: transfer WETH (borrowed)
    Contract->>BuyDEX: swap WETH → USDC (buy quote asset)
    BuyDEX-->>Contract: USDC received
    Contract->>SellDEX: swap USDC → WETH (sell quote asset)
    SellDEX-->>Contract: WETH received (more than borrowed)
    Contract->>Aave: repay WETH + 0.09% fee
    Contract->>Bot: emit ProfitRealized(profit)
    Note over Bot: Net = profit - gas cost
```

---

## 14. End-to-End Decision Flow

```mermaid
flowchart TD
    S1["1. SCAN<br/>Fetch quotes from<br/>all DEXes on all chains"]
    S2["2. FILTER<br/>Remove same-DEX, cross-chain,<br/>low-liq, outlier quotes"]
    S3["3. PRICE<br/>Full cost waterfall<br/>for each surviving pair"]
    S4["4. SCORE<br/>50% profit + 25% liquidity<br/>+ 15% safety + 10% spread"]
    S5["5. QUEUE<br/>Push to bounded priority queue<br/>(evict lowest if full)"]
    S6["6. RISK<br/>8-rule sequential check<br/>(any failure = hard reject)"]
    S7["7. CIRCUIT BREAKER<br/>Check state: OPEN = block,<br/>HALF_OPEN = probe"]
    S8["8. SIMULATE<br/>Free eth_call dry-run<br/>(catches reverts before gas)"]
    S9["9. SUBMIT<br/>Sign tx, send via Flashbots<br/>(ETH) or public mempool (L2)"]
    S10["10. VERIFY<br/>Check inclusion, extract profit,<br/>reconcile vs expected"]

    S1 --> S2 --> S3 --> S4 --> S5
    S5 --> S6
    S6 -->|pass| S7
    S6 -->|fail| R1[REJECTED]
    S7 -->|CLOSED| S8
    S7 -->|OPEN| R2[BLOCKED]
    S8 -->|pass| S9
    S8 -->|revert| R3[ABORTED]
    S9 --> S10
    S10 --> DONE["INCLUDED / REVERTED / NOT_INCLUDED"]

    style R1 fill:#e23b4a,color:#fff
    style R2 fill:#e23b4a,color:#fff
    style R3 fill:#e23b4a,color:#fff
    style DONE fill:#00a87e,color:#fff
```

At every numbered step, a negative outcome stops the pipeline for that
opportunity.  The philosophy is **capital preservation > profit** — missing a
trade is always better than losing money.

---

## 15. Database Schema (key tables)

```mermaid
erDiagram
    opportunities ||--o| pricing_results : "has pricing"
    opportunities ||--o| risk_decisions : "has risk verdict"
    opportunities ||--o| simulations : "has simulation"
    opportunities ||--o| execution_attempts : "has execution"
    execution_attempts ||--o| trade_results : "has on-chain result"
    pairs ||--o{ pools : "has pools"

    opportunities {
        string opportunity_id PK
        string pair
        string chain
        string buy_dex
        string sell_dex
        string spread_bps
        string status
        string detected_at
    }
    pricing_results {
        int pricing_id PK
        string opportunity_id FK
        string expected_net_profit
        string fee_cost
        string slippage_cost
        string gas_estimate
    }
    risk_decisions {
        int risk_id PK
        string opportunity_id FK
        bool approved
        string reason_code
        json threshold_snapshot
    }
    trade_results {
        int result_id PK
        int execution_id FK
        bool included
        bool reverted
        int gas_used
        string actual_net_profit
        string realized_profit_quote
    }
```
