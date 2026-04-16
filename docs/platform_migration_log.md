# Trading Platform Migration Log

Tracks completed phases, what changed, how other bots (SolanaTrader, PolymarketTrader) use the same patterns.

---

## Phase 1: Circuit Breaker + Retry (completed)

### What Changed

| Item | Before | After |
|------|--------|-------|
| `src/risk/circuit_breaker.py` | 170-line local implementation | **Deleted** — uses `trading_platform.risk.circuit_breaker` via adapter |
| `src/risk/retry.py` | 80-line local implementation | **Deleted** — uses `trading_platform.risk.retry` via adapter |
| `src/platform_adapters.py` | Did not exist | **Created** — thin wrappers mapping AT domain terms to TP generic API |

### Adapter Pattern

The platform uses **generic names** that work across all products. Each product creates an adapter layer mapping its domain language:

```
trading_platform (generic)     ArbitrageTrader (EVM arb)
─────────────────────────────  ──────────────────────────
record_failure()           →   record_revert()
record_error()             →   record_rpc_error()
record_success()           →   record_execution_success()
record_fresh_data()        →   record_fresh_quote()
record_event(seq)          →   record_trade_at_block(block)
should_block()             →   allows_execution() → (bool, reason)
is_still_valid             →   is_still_profitable
"repeated_failures"        →   "repeated_reverts"
"external_errors"          →   "rpc_degradation"
```

### How Other Bots Use This

**SolanaTrader** would create its own `platform_adapters.py`:

```python
from trading_platform.risk.circuit_breaker import CircuitBreaker as _PlatformBreaker

class CircuitBreaker:
    """Solana-flavored circuit breaker."""

    _REASON_MAP = {
        "repeated_failures": "repeated_tx_drops",
        "external_errors": "rpc_degradation",
    }

    def record_tx_drop(self) -> None:
        """Solana tx dropped from block (equivalent of EVM revert)."""
        self._breaker.record_failure()

    def record_rpc_error(self) -> None:
        """Solana RPC node error."""
        self._breaker.record_error()

    def record_slot_confirmation(self) -> None:
        """Tx confirmed in a slot."""
        self._breaker.record_success()
```

**PolymarketTrader** would create its own:

```python
class CircuitBreaker:
    """Polymarket-flavored circuit breaker."""

    _REASON_MAP = {
        "repeated_failures": "repeated_order_rejects",
        "external_errors": "api_degradation",
    }

    def record_order_rejected(self) -> None:
        self._breaker.record_failure()

    def record_api_error(self) -> None:
        self._breaker.record_error()

    def record_order_filled(self) -> None:
        self._breaker.record_success()
```

**RetryPolicy** follows the same pattern — the `is_still_valid` callback maps to:
- ArbitrageTrader: `is_still_profitable` (spread still exists?)
- SolanaTrader: `is_still_profitable` (price still favorable?)
- PolymarketTrader: `is_odds_still_favorable` (market hasn't moved?)

### Tests

949/949 pass. Zero regressions.

---

## Phase 2: Alert Dispatcher + Queue (completed)

### What Changed

| Item | Before | After |
|------|--------|-------|
| `src/alerting/dispatcher.py` | 187-line standalone implementation | **Rewritten** — subclasses `trading_platform.alerting.AlertDispatcher`, keeps AT convenience methods |
| `src/pipeline/queue.py` | 168-line local `CandidateQueue` | **Deleted** — uses `trading_platform.pipeline.PriorityQueue` via adapter in `platform_adapters.py` |

### Dispatcher: Subclass Pattern

The platform provides the generic fan-out engine. Products subclass it and add domain-specific convenience methods:

```
trading_platform.AlertDispatcher (generic)
├── alert(event_type, message, details) → fan-out to all backends
├── add_backend(backend)
└── backend_count

ArbitrageTrader.AlertDispatcher (subclass)
├── inherits alert(), add_backend(), backend_count
├── opportunity_found(pair, buy_dex, sell_dex, spread, profit, ...)
├── trade_executed(pair, tx_hash, profit, ...)
├── trade_reverted(pair, tx_hash, reason, ...)
├── daily_summary(scans, opportunities, executed, profit, reverts)
└── system_error(component, error)
```

### Queue: Adapter Pattern

Platform provides a generic `PriorityQueue` with `QueuedItem(item: Any, metadata: dict)`. Products wrap it:

```
trading_platform.PriorityQueue    ArbitrageTrader.CandidateQueue
─────────────────────────────────  ──────────────────────────────
push(item, priority, metadata)  →  push(opportunity, priority, scan_marks)
pop() → QueuedItem              →  pop() → QueuedCandidate
QueuedItem.item                 →  QueuedCandidate.opportunity
QueuedItem.metadata             →  QueuedCandidate.scan_marks
```

### How Other Bots Use This

**SolanaTrader dispatcher:**

```python
from trading_platform.alerting.dispatcher import AlertDispatcher as _Base

class AlertDispatcher(_Base):
    """Solana-specific alerts."""

    def swap_executed(self, pair: str, tx_sig: str, profit: float) -> int:
        return self.alert("swap_executed", f"Swap: {pair}\nTX: {tx_sig}\nProfit: {profit:.6f}")

    def swap_failed(self, pair: str, tx_sig: str, reason: str) -> int:
        return self.alert("swap_failed", f"FAILED: {pair}\nReason: {reason}")

    def jito_bundle_landed(self, pair: str, slot: int, profit: float) -> int:
        return self.alert("bundle_landed", f"Jito bundle in slot {slot}: +{profit:.6f} SOL")
```

**PolymarketTrader dispatcher:**

```python
class AlertDispatcher(_Base):
    """Polymarket-specific alerts."""

    def position_opened(self, market: str, outcome: str, size: float, odds: float) -> int:
        return self.alert("position_opened", f"Opened: {market}\n{outcome} @ {odds:.2f}\nSize: ${size:.2f}")

    def position_closed(self, market: str, pnl: float) -> int:
        return self.alert("position_closed", f"Closed: {market}\nPnL: ${pnl:.2f}")
```

**SolanaTrader queue:**

```python
@dataclass
class QueuedSwap:
    swap: SolanaSwapOpportunity
    enqueued_at: float
    priority: float
    metadata: dict

class SwapQueue:
    def __init__(self, max_size=100):
        self._queue = PriorityQueue(max_size=max_size)

    def push(self, swap: SolanaSwapOpportunity, priority: float) -> bool:
        return self._queue.push(swap, priority=priority)

    def pop(self) -> QueuedSwap | None:
        item = self._queue.pop()
        if item is None: return None
        return QueuedSwap(swap=item.item, enqueued_at=item.enqueued_at,
                          priority=item.priority, metadata=item.metadata or {})
```

### Database Migration (Deferred)

AT's `src/persistence/db.py` has 33 CREATE TABLE/INDEX statements and 2 migration functions (`_ensure_pairs_chain_uniqueness`, `_ensure_trade_result_columns`) tightly coupled to the arbitrage schema. The platform provides a generic `DbConnection` + `init_db(schema=...)`, but extracting AT's schema is a larger refactor with lower ROI than the other Phase 2 items.

**For other bots**: Use `trading_platform.persistence.init_db(schema=YOUR_SCHEMA)` directly. Only AT has this migration debt because it predates the platform.

### Tests

949/949 pass. Zero regressions.

---

## Summary So Far

### Lines of Code

| Metric | Count |
|--------|------:|
| Lines deleted from ArbitrageTrader | ~390 |
| Lines added (adapters + rewritten dispatcher) | ~200 |
| **Net reduction** | **~190 lines** |
| Local modules replaced by TP | 4 (circuit_breaker, retry, queue, dispatcher core) |
| Tests passing | 949/949 |

### Pattern Catalog

Three patterns emerged for integrating with the platform:

1. **Adapter** (circuit_breaker, retry, queue) — Thin wrapper class in `platform_adapters.py` that maps domain terms to generic API. Used when the method signatures differ but the logic is identical.

2. **Subclass** (alert dispatcher) — Product's class extends the platform's base class, inheriting generic logic and adding domain-specific convenience methods. Used when the product needs all of the platform's behavior plus extra methods.

3. **Direct use** (future: logging, env) — Import and use the platform module directly when APIs are already compatible. Used when no domain-term mapping is needed.

### File Layout After Migration

```
src/
├── platform_adapters.py          ← NEW: domain-term adapters (CB, Retry, Queue)
├── alerting/
│   ├── dispatcher.py             ← REWRITTEN: subclasses TP AlertDispatcher
│   ├── smart_alerts.py           (unchanged — AT-specific alert rules)
│   ├── gmail.py, discord.py, telegram.py  (unchanged — migrate in Phase 3)
├── risk/
│   ├── policy.py                 (unchanged — migrate in Phase 4)
│   ├── circuit_breaker.py        ← DELETED (now in platform_adapters.py)
│   ├── retry.py                  ← DELETED (now in platform_adapters.py)
├── pipeline/
│   ├── lifecycle.py              (unchanged — migrate in Phase 4)
│   ├── queue.py                  ← DELETED (now in platform_adapters.py)
│   ├── verifier.py               (unchanged — AT-specific)
├── persistence/
│   ├── db.py                     (unchanged — deferred, tightly coupled schema)
│   ├── repository.py             (unchanged — migrate in Phase 3)
...
```

---

## Remaining Phases

### Phase 3: Subclass Pattern (config, repository, metrics, alerting backends, API)

Each module becomes a product-specific subclass of the platform's base:
- `BotConfig` → `ArbitrageConfig(BaseConfig)`
- `Repository` → `ArbitrageRepository(BaseRepository)`
- `MetricsCollector` → use TP generic `increment(name, tag=)`
- Alert backends → import from TP, add `configured` property
- API → `create_app()` extends `create_base_app()`

### Phase 4: Major Refactors (risk policy, pipeline)

- Risk policy → Extract 8 rules into pluggable `RiskRule` objects for `RuleBasedPolicy`
- Pipeline → `ArbitragePipeline(BasePipeline)` with stage callbacks
