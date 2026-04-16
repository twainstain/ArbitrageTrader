# ArbitrageTrader → Trading Platform Migration Plan

## Goal

Migrate ArbitrageTrader to use `trading_platform` as its shared infrastructure layer. This reduces code duplication, makes both ArbitrageTrader and PolymarketTrader share the same battle-tested primitives, and simplifies future maintenance.

## Principle

**Incremental migration, never break production.** Each phase is independently deployable and testable. No big-bang rewrite.

---

## Current State

ArbitrageTrader has ~18 modules that overlap with trading_platform equivalents. The platform was extracted FROM ArbitrageTrader, so interfaces are similar but not identical.

### Compatibility Assessment

| Category | Modules | Migration Effort |
|----------|---------|:----------------:|
| **Drop-in** (identical APIs) | circuit_breaker, retry, time_windows, env, logging | LOW |
| **Thin wrapper** (minor API diffs) | dispatcher, db, queue | LOW-MODERATE |
| **Subclass** (extend base class) | config, repository, metrics, alerting backends, API | MODERATE |
| **Major refactor** (architectural change) | pipeline, risk_policy | HIGH |

---

## Phase 1: Drop-in Replacements (LOW risk, HIGH confidence)

**Modules:** circuit_breaker, retry, time_windows, env base, logging base

**Approach:** Import from `trading_platform` instead of local modules. Delete local copies.

### 1.1 Circuit Breaker
```
- DELETE: src/risk/circuit_breaker.py
- CHANGE: All imports from `risk.circuit_breaker` → `trading_platform.risk`
- Files affected: run_event_driven.py, tests/test_circuit_breaker.py
- Test: existing tests should pass with zero changes
```

### 1.2 Retry Policy
```
- DELETE: src/risk/retry.py
- CHANGE: imports → `from trading_platform.risk import RetryPolicy, execute_with_retry`
- RENAME: is_still_profitable → is_still_valid (1 call site)
- Files affected: run_event_driven.py, tests/test_retry.py
```

### 1.3 Time Windows
```
- DELETE: src/observability/time_windows.py
- CHANGE: imports → `from trading_platform.observability import since, window_keys`
- Files affected: api/app.py, dashboards/*.py
```

### 1.4 Environment Base
```
- KEEP: src/core/env.py (ArbitrageTrader-specific helpers: get_rpc_urls_for_chain)
- CHANGE: load_env, get_env → import from trading_platform.config.env
- DELETE: duplicate load_dotenv logic
```

### 1.5 Logging Base
```
- KEEP: src/observability/log.py (ArbitrageTrader-specific: log_scan, log_execution)
- CHANGE: setup_logging, get_logger, DecimalEncoder → from trading_platform.observability
```

**Deliverable:** 5 local modules deleted, all tests pass, zero behavior change.

---

## Phase 2: Thin Wrappers (LOW-MODERATE risk)

**Modules:** alert dispatcher, database, queue

### 2.1 Alert Dispatcher
```
- DELETE: src/alerting/dispatcher.py
- CHANGE: import AlertDispatcher from trading_platform.alerting
- KEEP: src/alerting/smart_alerts.py (ArbitrageTrader-specific convenience methods)
- Move: opp_dashboard_url(), tx_explorer_url() → smart_alerts.py
```

### 2.2 Database Layer
```
- DELETE: src/persistence/db.py
- CHANGE: DbConnection, init_db, get_db, close_db → from trading_platform.persistence
- KEEP: Schema definition in a new src/persistence/schema.py
- Pass schema to init_db(schema=ARBITRAGE_SCHEMA) instead of hardcoding in db.py
```

### 2.3 Priority Queue
```
- DELETE: src/pipeline/queue.py
- CHANGE: CandidateQueue → PriorityQueue from trading_platform.pipeline
- ADAPT: QueuedCandidate.opportunity → QueuedItem.item
        QueuedCandidate.scan_marks → QueuedItem.metadata["scan_marks"]
- Files affected: run_event_driven.py (push/pop calls)
```

**Deliverable:** 3 more modules deleted, wrapper pattern established.

---

## Phase 3: Subclass Pattern (MODERATE risk)

**Modules:** config, repository, metrics, alerting backends, API

### 3.1 Configuration
```
- CHANGE: BotConfig → ArbitrageConfig(BaseConfig)
- KEEP: DexConfig, PairConfig as-is (ArbitrageTrader-specific)
- KEEP: gas_cost_for_chain(), min_liquidity_for_chain() in subclass
- DELETE: duplicate __post_init__ Decimal coercion (use BaseConfig's)
- DELETE: duplicate from_file JSON parsing (use BaseConfig.from_file)
```

### 3.2 Repository
```
- CHANGE: Repository → ArbitrageRepository(BaseRepository)
- KEEP: All ArbitrageTrader-specific methods (create_opportunity, save_pricing, etc.)
- USE: BaseRepository._now(), _row_to_dict(), update_status(), checkpoint methods
- DELETE: duplicate _now(), _row_to_dict() helpers
```

### 3.3 Metrics
```
- DELETE: src/observability/metrics.py
- CHANGE: MetricsCollector → from trading_platform.observability
- ADAPT: record_opportunity_detected() → metrics.increment("opportunities_detected")
         record_simulation(passed) → metrics.increment("simulations", tag="passed"/"failed")
- Create thin ArbitrageMetrics wrapper if needed for backward compat
```

### 3.4 Alerting Backends
```
- DELETE: src/alerting/gmail.py, discord.py, telegram.py
- CHANGE: import from trading_platform.alerting
- ADD: `configured` property if missing in TP versions
```

### 3.5 API
```
- CHANGE: create_app() uses create_base_app() as foundation
- KEEP: All ArbitrageTrader-specific endpoints (/opportunities, /execution, etc.)
- USE: Base app's /health, /metrics, /pause endpoints
- DELETE: duplicate health/metrics endpoint code
```

**Deliverable:** ArbitrageTrader-specific code cleanly separated from infrastructure.

---

## Phase 4: Major Refactors (HIGH effort, do last)

### 4.1 Risk Policy → Rule-Based Policy

**Current:** Monolithic `RiskPolicy` with 8 hardcoded rules in `evaluate()`.

**Target:** `RuleBasedPolicy` from trading_platform with pluggable rules.

```python
# Extract each rule into its own class
class MinSpreadRule:
    name = "min_spread"
    def __init__(self, chain_thresholds): ...
    def evaluate(self, opportunity, context) -> RiskVerdict: ...

class MinProfitRule:
    name = "min_profit"
    def evaluate(self, opportunity, context) -> RiskVerdict: ...

class PoolLiquidityRule:
    name = "pool_too_thin"
    def evaluate(self, opportunity, context) -> RiskVerdict: ...

# ... 5 more rules

# Wire up
policy = RuleBasedPolicy(rules=[
    ExecutionModeRule(chain_modes),
    MinSpreadRule(chain_thresholds),
    MinProfitRule(chain_thresholds),
    PoolLiquidityRule(),
    WarningFlagRule(max_flags=1),
    GasProfitRatioRule(max_ratio=0.5),
    RateLimitRule(max_per_hour=100),
    ExposureLimitRule(max_per_pair=10),
])
```

**Benefits:** Each rule is independently testable, reorderable, toggleable.

### 4.2 Pipeline → BasePipeline Subclass

**Current:** `CandidatePipeline` with all logic inline.

**Target:** `ArbitragePipeline(BasePipeline)` with stage callbacks.

```python
class ArbitragePipeline(BasePipeline):
    def detect(self, opportunity) -> str:
        return self.repo.create_opportunity(...)
    
    def price(self, opp_id, opportunity) -> None:
        self.repo.save_pricing(...)
    
    def evaluate_risk(self, opportunity) -> RiskVerdict:
        return self.risk_policy.evaluate(opportunity, ...)
    
    def on_approved(self, opp_id, opportunity) -> None:
        self.repo.update_opportunity_status(opp_id, "approved")
    
    def on_rejected(self, opp_id, reason, opportunity) -> None:
        self.repo.update_opportunity_status(opp_id, "rejected")
    
    # Simulator/Submitter/Verifier remain as protocol implementations
```

### 4.3 RPC Provider → EndpointProvider Wrapper

```python
from trading_platform.data import EndpointProvider

class RpcProvider:
    """Web3-aware wrapper around EndpointProvider."""
    def __init__(self, chain: str, urls: list[str]):
        self._provider = EndpointProvider(chain, urls)
    
    def get_web3(self) -> Web3:
        url = self._provider.get_endpoint()
        return Web3(Web3.HTTPProvider(url))
    
    def record_success(self): self._provider.record_success()
    def record_error(self): self._provider.record_error()
```

---

## Implementation Order

```
Phase 1 (Week 1): Drop-in replacements
  1.1 circuit_breaker  → 30 min
  1.2 retry            → 30 min
  1.3 time_windows     → 30 min
  1.4 env base         → 30 min
  1.5 logging base     → 30 min
  Tests + deploy       → 1 hour
  
Phase 2 (Week 1-2): Thin wrappers
  2.1 dispatcher       → 1 hour
  2.2 database         → 2 hours (schema extraction)
  2.3 queue            → 1 hour
  Tests + deploy       → 1 hour

Phase 3 (Week 2-3): Subclass pattern
  3.1 config           → 2 hours
  3.2 repository       → 2 hours
  3.3 metrics          → 1 hour
  3.4 alerting backends → 1 hour
  3.5 API              → 2 hours
  Tests + deploy       → 2 hours

Phase 4 (Week 3-4): Major refactors
  4.1 risk policy      → 4 hours (extract 8 rules)
  4.2 pipeline         → 4 hours (abstract stages)
  4.3 rpc provider     → 1 hour
  Tests + deploy       → 2 hours
```

**Total estimated effort: ~25 hours across 4 weeks.**

---

## Dependencies

1. `trading_platform` must be installed as a package:
   ```
   pip install -e /Users/tamir.wainstain/src/trading_platform
   ```
   Or add to requirements.txt / pyproject.toml.

2. Docker image must include trading_platform in the build.

3. EC2 deployment must install the package.

---

## Testing Strategy

Each phase:
1. Run `python -m pytest tests/ -q` before AND after changes
2. Run simulation: `PYTHONPATH=src python -m main --config config/example_config.json --iterations 5`
3. Deploy to prod, verify health check + dashboard
4. Monitor DB for 1 hour to confirm no regressions

---

## Rollback Plan

Each phase is a single commit. If issues arise:
```
git revert HEAD
./scripts/deploy_prod.sh
```

No data migration needed — the database schema doesn't change.

---

## What Stays in ArbitrageTrader (NOT migrated)

- `src/core/models.py` — Opportunity, MarketQuote, ExecutionResult (domain models)
- `src/core/tokens.py` — Token address registry
- `src/core/contracts.py` — DEX quoter addresses and ABIs
- `src/strategy/` — ArbitrageStrategy, OpportunityScanner (core business logic)
- `src/execution/` — ChainExecutor, FlashArbExecutor (on-chain execution)
- `src/market/` — Market data sources (onchain, live, sim, subgraph)
- `src/registry/` — Pair discovery, pool management
- `src/dashboards/` — Dashboard UI
- `src/tools/` — CLI tools (pair_scanner, price_downloader, etc.)
- `contracts/` — Solidity contracts
