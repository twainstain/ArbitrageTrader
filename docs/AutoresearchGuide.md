# Autoresearch: How It Works & How to Apply It to Any Experiment

> Based on [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) — an autonomous AI research framework.

---

## Table of Contents

1. [What Is Autoresearch?](#what-is-autoresearch)
2. [How It Works (Deep Dive)](#how-it-works-deep-dive)
3. [The Three-File Architecture](#the-three-file-architecture)
4. [The Experiment Loop](#the-experiment-loop)
5. [Applying to Other Domains](#applying-to-other-domains)
6. [Example: Arbitrage Trader Autoresearch](#example-arbitrage-trader-autoresearch)
7. [Example: Polymarket Bot Autoresearch](#example-polymarket-bot-autoresearch)
8. [Template: Build Your Own Autoresearch](#template-build-your-own-autoresearch)
9. [Tips & Lessons](#tips--lessons)

---

## What Is Autoresearch?

Autoresearch is Karpathy's framework for **autonomous AI-driven experimentation**. The core idea:

> Give an AI agent a real experiment setup and let it run autonomously overnight. It modifies the code, runs for a fixed time, checks if the result improved, keeps or discards the change, and repeats. You wake up in the morning to a log of experiments and (hopefully) better results.

**You don't write Python. You write `program.md` — a Markdown file that programs the AI agent.**

The agent does the actual coding, running, measuring, and iterating. It's a paradigm shift: instead of being the researcher, you become the **research director** who defines the problem, constraints, and evaluation metric, then lets the AI execute.

---

## How It Works (Deep Dive)

### The Original Setup (LLM Training)

In Karpathy's version, the experiment is training a small language model:

```
Goal:           Minimize val_bpb (validation bits per byte)
Time budget:    5 minutes per experiment (wall clock)
What changes:   train.py (model architecture, optimizer, hyperparameters)
What's fixed:   prepare.py (data, tokenizer, evaluation metric)
Who runs it:    An AI agent (Claude/Codex) in a loop
```

The agent runs ~12 experiments/hour, ~100 while you sleep. Each experiment:

1. **Edits** `train.py` with a new idea (change architecture, hyperparameters, optimizer, etc.)
2. **Commits** the change to git
3. **Runs** the training for exactly 5 minutes
4. **Measures** the result (val_bpb)
5. **Keeps** if improved (advance the branch) or **discards** (git reset)
6. **Logs** the result to `results.tsv`
7. **Repeats** forever until manually stopped

### Why It Works

| Design Choice | Why |
|--------------|-----|
| **Fixed time budget** | Makes every experiment directly comparable regardless of what changed |
| **Single file to modify** | Keeps scope manageable, diffs reviewable |
| **Single metric** | Clear, unambiguous "did it improve?" signal |
| **Git-based versioning** | Every experiment is a commit; easy to rewind |
| **TSV logging** | Human-readable experiment history |
| **Never stop** | Agent runs indefinitely — no "should I continue?" pauses |
| **Simplicity criterion** | Equal results + simpler code = keep (prevents complexity bloat) |

---

## The Three-File Architecture

This is the core pattern that makes autoresearch portable to any domain:

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTORESEARCH PATTERN                       │
│                                                              │
│  ┌──────────────┐   Human writes/edits this.                │
│  │  program.md   │   Instructions for the AI agent.          │
│  │  (the "brain")│   Defines goals, constraints, rules.      │
│  └──────────────┘                                            │
│                                                              │
│  ┌──────────────┐   AI agent edits this.                    │
│  │  train.py     │   The single experiment file.             │
│  │  (the target) │   All changes happen here.                │
│  └──────────────┘                                            │
│                                                              │
│  ┌──────────────┐   Nobody touches this.                    │
│  │  prepare.py   │   Fixed infrastructure: data loading,     │
│  │  (the ground  │   evaluation metric, constants.           │
│  │   truth)      │   The agent CANNOT modify this.           │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

### Mapping to Any Domain

| Original (LLM) | Generic Name | Your Experiment |
|----------------|-------------|-----------------|
| `prepare.py` | **Infrastructure** | Data loading, evaluation harness, fixed constants |
| `train.py` | **Experiment** | The single file the agent modifies |
| `program.md` | **Agent Instructions** | Rules, goals, constraints for the AI |
| `val_bpb` | **Metric** | The single number to optimize |
| 5 minutes | **Time Budget** | Fixed wall-clock per experiment |
| `results.tsv` | **Experiment Log** | Tab-separated results history |

---

## The Experiment Loop

This is the exact loop from `program.md` — portable to any domain:

```
LOOP FOREVER:

1. Look at current git state (branch/commit)
2. Edit the experiment file with a new idea
3. Git commit the change
4. Run the experiment: `command > run.log 2>&1`
5. Read out results: `grep "^metric:" run.log`
6. If grep empty → crash. Read `tail -n 50 run.log`, attempt fix or skip
7. Log results to results.tsv
8. If metric improved → KEEP (advance branch)
9. If metric equal or worse → DISCARD (git reset)
10. GOTO 1
```

### Key Rules

- **NEVER STOP** — the agent runs until manually interrupted
- **Crashes**: Fix trivial bugs (typos, imports), skip fundamentally broken ideas
- **Timeout**: Kill runs exceeding 2x the time budget
- **Simplicity**: Equal results + simpler code = keep
- **No new dependencies**: Only use what's already installed

---

## Applying to Other Domains

### Step-by-Step: Port Autoresearch to Your Problem

#### 1. Define Your Metric

The most critical decision. Must be:
- **Single number** — the agent needs an unambiguous "better or worse" signal
- **Computed automatically** — no human judgment needed
- **Deterministic or low-variance** — results should be reproducible
- **Direction-clear** — lower is better OR higher is better, not both

Examples:

| Domain | Metric | Direction |
|--------|--------|-----------|
| LLM training | val_bpb | Lower is better |
| Arbitrage bot | net_profit_pct | Higher is better |
| Polymarket bot | win_rate | Higher is better |
| Image classifier | validation_accuracy | Higher is better |
| Trading strategy | sharpe_ratio | Higher is better |
| Compiler optimization | execution_time_ms | Lower is better |
| API server | p99_latency_ms | Lower is better |

#### 2. Fix Your Time Budget

Every experiment must run for the **same wall-clock duration**. This makes results comparable even when the agent changes fundamental things (model size, batch size, strategy complexity).

Guidelines:
- **Too short** → noisy results, can't tell signal from noise
- **Too long** → fewer experiments per night, slower iteration
- **Sweet spot** → enough to get a reliable metric, short enough for ~10+ experiments/hour

| Domain | Suggested Budget |
|--------|-----------------|
| ML training | 5 minutes |
| Trading backtest | 2-5 minutes |
| Strategy simulation | 1-3 minutes |
| Unit test suite | 30 seconds |
| Benchmark | 1 minute |

#### 3. Build Your Infrastructure File (prepare.py equivalent)

This file is **read-only for the agent**. It contains:

```python
# Constants
TIME_BUDGET = 300          # seconds per experiment
EVAL_DATASET = "..."       # fixed test data

# Data loading
def load_data():
    """Load and return the fixed dataset."""
    ...

# Evaluation (THE ground truth metric)
def evaluate(strategy, data):
    """
    Run the strategy against the fixed dataset.
    Returns a single number (the metric).
    THIS FUNCTION CANNOT BE MODIFIED BY THE AGENT.
    """
    ...

# Output format (agent parses this)
def print_results(metric, extra_info):
    print(f"metric: {metric:.6f}")
    print(f"extra: {extra_info}")
```

#### 4. Create Your Experiment File (train.py equivalent)

This is the **single file the agent modifies**. It should:

- Import from the infrastructure file
- Contain all the "tuneable" logic
- Print results in a parseable format
- Run end-to-end as a script

#### 5. Write Your program.md

Adapt Karpathy's template:

```markdown
# My Autoresearch Experiment

## Setup
1. Agree on a run tag (e.g., `apr12`)
2. Create branch: `git checkout -b autoresearch/<tag>`
3. Read all files for context
4. Run baseline experiment first

## Experimentation

Each experiment runs for a fixed time budget of N minutes.

**What you CAN do:**
- Modify `experiment.py` — everything is fair game

**What you CANNOT do:**
- Modify `infrastructure.py`
- Install new packages
- Modify the evaluation function

**The goal: get the [highest/lowest] [metric_name].**

## Output format
The script prints:
```
metric: 0.123456
```

## The experiment loop
[Copy the loop from above]

## NEVER STOP
[Copy the autonomy instructions from above]
```

#### 6. Set Up results.tsv

```
commit	metric	status	description
```

---

## Example: Arbitrage Trader Autoresearch

Here's how to apply autoresearch to optimize a **crypto arbitrage trading strategy** using backtesting.

### File Structure

```
arbitrage-autoresearch/
├── prepare.py          # Fixed: historical data, backtesting engine, evaluation
├── strategy.py         # Agent modifies: trading strategy, parameters, logic
├── program.md          # Human writes: agent instructions
├── results.tsv         # Experiment log
├── pyproject.toml      # Dependencies
└── data/
    └── price_history/  # Historical price data (fixed)
```

### prepare.py — Infrastructure (DO NOT MODIFY)

```python
"""
Fixed infrastructure for arbitrage strategy backtesting.
DO NOT MODIFY — this is the evaluation ground truth.
"""

import os
import time
import json
import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

TIME_BUDGET = 180            # 3 minutes per experiment
BACKTEST_DAYS = 30           # 30 days of historical data
INITIAL_CAPITAL = 10000.0    # $10,000 starting capital
TRADING_FEE_PCT = 0.003      # 0.3% per trade (Uniswap-like)
SLIPPAGE_PCT = 0.001         # 0.1% slippage estimate
GAS_COST_USD = 5.0           # $5 per transaction
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Data Types
# ---------------------------------------------------------------------------

@dataclass
class PriceSnapshot:
    timestamp: float
    exchange_a_price: float   # e.g., Uniswap
    exchange_b_price: float   # e.g., Sushiswap
    volume_a: float
    volume_b: float

@dataclass
class Trade:
    timestamp: float
    buy_exchange: str
    sell_exchange: str
    amount_usd: float
    buy_price: float
    sell_price: float
    profit_usd: float
    fees_usd: float
    net_profit_usd: float

@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_usd: float
    total_fees_usd: float
    net_profit_usd: float
    net_profit_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    avg_profit_per_trade: float
    capital_final: float

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_price_data():
    """Load historical price snapshots from disk."""
    filepath = os.path.join(DATA_DIR, "price_snapshots.json")
    with open(filepath) as f:
        raw = json.load(f)
    return [PriceSnapshot(**s) for s in raw]

# ---------------------------------------------------------------------------
# Backtesting Engine (DO NOT CHANGE — fixed evaluation)
# ---------------------------------------------------------------------------

def run_backtest(strategy_fn, price_data, time_budget=TIME_BUDGET):
    """
    Run a strategy against historical price data.

    Args:
        strategy_fn: callable(snapshot, state) -> list[Trade] or None
                     The strategy receives each price snapshot and its own
                     mutable state dict. Returns trades to execute or None.
        price_data: list[PriceSnapshot]
        time_budget: max wall-clock seconds

    Returns:
        BacktestResult with all metrics
    """
    capital = INITIAL_CAPITAL
    trades = []
    state = {"capital": capital, "position": None, "history": []}
    peak_capital = capital
    max_drawdown = 0.0
    returns = []

    t_start = time.time()

    for snapshot in price_data:
        # Time budget check
        if time.time() - t_start > time_budget:
            break

        state["capital"] = capital

        # Get strategy decision
        try:
            result = strategy_fn(snapshot, state)
        except Exception:
            continue

        if result is None:
            returns.append(0.0)
            continue

        if not isinstance(result, list):
            result = [result]

        for trade in result:
            # Apply fixed fees
            fee = trade.amount_usd * TRADING_FEE_PCT
            slippage = trade.amount_usd * SLIPPAGE_PCT
            total_cost = fee + slippage + GAS_COST_USD
            trade.fees_usd = total_cost

            # Calculate net profit
            gross = trade.profit_usd
            net = gross - total_cost
            trade.net_profit_usd = net

            capital += net
            trades.append(trade)

            # Drawdown tracking
            peak_capital = max(peak_capital, capital)
            drawdown = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

            returns.append(net / INITIAL_CAPITAL)

    # Compute metrics
    winning = [t for t in trades if t.net_profit_usd > 0]
    losing = [t for t in trades if t.net_profit_usd <= 0]
    total_profit = sum(t.profit_usd for t in trades)
    total_fees = sum(t.fees_usd for t in trades)
    net_profit = capital - INITIAL_CAPITAL

    # Sharpe ratio (annualized, assuming daily returns)
    if len(returns) > 1:
        import numpy as np
        r = np.array(returns)
        sharpe = (r.mean() / r.std()) * math.sqrt(365) if r.std() > 0 else 0.0
    else:
        sharpe = 0.0

    return BacktestResult(
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        total_profit_usd=total_profit,
        total_fees_usd=total_fees,
        net_profit_usd=net_profit,
        net_profit_pct=(net_profit / INITIAL_CAPITAL) * 100,
        max_drawdown_pct=max_drawdown * 100,
        sharpe_ratio=sharpe,
        win_rate=len(winning) / len(trades) * 100 if trades else 0,
        avg_profit_per_trade=net_profit / len(trades) if trades else 0,
        capital_final=capital,
    )

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(result: BacktestResult):
    """Print results in the parseable format the agent expects."""
    print("---")
    print(f"net_profit_pct:     {result.net_profit_pct:.6f}")
    print(f"sharpe_ratio:       {result.sharpe_ratio:.6f}")
    print(f"win_rate:           {result.win_rate:.2f}")
    print(f"total_trades:       {result.total_trades}")
    print(f"max_drawdown_pct:   {result.max_drawdown_pct:.2f}")
    print(f"avg_profit_trade:   {result.avg_profit_per_trade:.4f}")
    print(f"capital_final:      {result.capital_final:.2f}")
```

### strategy.py — Experiment File (AGENT MODIFIES THIS)

```python
"""
Arbitrage trading strategy. This is the file the AI agent modifies.
Everything is fair game: thresholds, logic, indicators, position sizing.

Usage: python strategy.py
"""

import time
from prepare import (
    load_price_data, run_backtest, print_results,
    PriceSnapshot, Trade, TIME_BUDGET
)

# ---------------------------------------------------------------------------
# Strategy Parameters (tune these)
# ---------------------------------------------------------------------------

MIN_SPREAD_PCT = 0.5        # minimum price difference to trigger trade (%)
MAX_TRADE_SIZE_PCT = 10.0   # max % of capital per trade
COOLDOWN_SECONDS = 60       # seconds between trades
MIN_VOLUME = 1000           # minimum volume on both exchanges

# Moving average for trend filter
MA_WINDOW = 20              # number of snapshots for moving average
TREND_FILTER = True         # only trade in direction of trend

# ---------------------------------------------------------------------------
# Strategy Logic
# ---------------------------------------------------------------------------

def strategy(snapshot: PriceSnapshot, state: dict):
    """
    Core arbitrage strategy. Called for each price snapshot.

    Args:
        snapshot: current prices on exchange A and B
        state: mutable dict with 'capital', 'position', 'history'

    Returns:
        Trade object if executing, None if no trade
    """
    capital = state["capital"]
    history = state["history"]
    history.append(snapshot)

    # Volume filter
    if snapshot.volume_a < MIN_VOLUME or snapshot.volume_b < MIN_VOLUME:
        return None

    # Cooldown check
    if state.get("last_trade_time"):
        if snapshot.timestamp - state["last_trade_time"] < COOLDOWN_SECONDS:
            return None

    # Calculate spread
    price_a = snapshot.exchange_a_price
    price_b = snapshot.exchange_b_price

    if price_a <= 0 or price_b <= 0:
        return None

    spread_pct = abs(price_a - price_b) / min(price_a, price_b) * 100

    # Check if spread is large enough
    if spread_pct < MIN_SPREAD_PCT:
        return None

    # Optional trend filter using moving average
    if TREND_FILTER and len(history) >= MA_WINDOW:
        recent = history[-MA_WINDOW:]
        avg_a = sum(s.exchange_a_price for s in recent) / MA_WINDOW
        avg_b = sum(s.exchange_b_price for s in recent) / MA_WINDOW
        avg_mid = (avg_a + avg_b) / 2
        current_mid = (price_a + price_b) / 2
        # Skip if price is moving against us
        if current_mid < avg_mid * 0.995:
            return None

    # Position sizing
    trade_size = capital * (MAX_TRADE_SIZE_PCT / 100)

    # Determine direction: buy cheap, sell expensive
    if price_a < price_b:
        buy_exchange = "A"
        sell_exchange = "B"
        buy_price = price_a
        sell_price = price_b
    else:
        buy_exchange = "B"
        sell_exchange = "A"
        buy_price = price_b
        sell_price = price_a

    # Calculate gross profit
    units = trade_size / buy_price
    gross_profit = units * (sell_price - buy_price)

    state["last_trade_time"] = snapshot.timestamp

    return Trade(
        timestamp=snapshot.timestamp,
        buy_exchange=buy_exchange,
        sell_exchange=sell_exchange,
        amount_usd=trade_size,
        buy_price=buy_price,
        sell_price=sell_price,
        profit_usd=gross_profit,
        fees_usd=0,              # Filled by backtester
        net_profit_usd=0,        # Filled by backtester
    )

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    t_start = time.time()
    print("Loading price data...")
    price_data = load_price_data()
    print(f"Loaded {len(price_data)} snapshots")

    print("Running backtest...")
    result = run_backtest(strategy, price_data)

    print_results(result)

    t_end = time.time()
    print(f"total_seconds:      {t_end - t_start:.1f}")
```

### program.md — Agent Instructions

```markdown
# Arbitrage Strategy Autoresearch

## Setup

1. Agree on a run tag (e.g., `apr12`)
2. Create branch: `git checkout -b autoresearch/<tag>`
3. Read all files:
   - `prepare.py` — fixed backtesting engine, data loader, evaluation (DO NOT MODIFY)
   - `strategy.py` — your file to modify (strategy logic, parameters, indicators)
4. Verify data exists in `data/price_snapshots.json`
5. Initialize `results.tsv` with header row
6. Run baseline first

## Experimentation

Each experiment runs a backtest against fixed historical price data.

**What you CAN do:**
- Modify `strategy.py` — everything is fair game:
  - Spread thresholds, position sizing, cooldown timers
  - Add technical indicators (MA, RSI, Bollinger Bands, VWAP)
  - Multi-level entry/exit logic
  - Adaptive thresholds based on volatility
  - Dynamic position sizing (Kelly criterion, etc.)
  - Multiple strategy modes for different market conditions

**What you CANNOT do:**
- Modify `prepare.py` (read-only)
- Install new packages
- Modify the evaluation/backtesting engine
- Access future data (no lookahead bias)

**The goal: maximize `net_profit_pct` while keeping `max_drawdown_pct` under 20%.**

A constraint: if max_drawdown_pct > 20%, treat the experiment as a failure
even if net_profit_pct improved.

## Output format

```
---
net_profit_pct:     12.345678
sharpe_ratio:       1.234567
win_rate:           67.50
total_trades:       42
max_drawdown_pct:   8.50
```

Extract: `grep "^net_profit_pct:\|^max_drawdown_pct:" run.log`

## Logging

TSV format:
```
commit  net_profit_pct  max_drawdown_pct  status  description
```

## The experiment loop

LOOP FOREVER:

1. Check git state
2. Edit `strategy.py` with an idea
3. Git commit
4. Run: `python strategy.py > run.log 2>&1`
5. Read: `grep "^net_profit_pct:\|^max_drawdown_pct:" run.log`
6. If empty → crash. Check `tail -n 50 run.log`
7. Log to results.tsv
8. If net_profit_pct improved AND max_drawdown_pct < 20% → KEEP
9. Else → DISCARD (git reset)
10. Repeat

## Ideas to try (starting suggestions)

- Lower/raise MIN_SPREAD_PCT
- Add RSI filter (only trade when RSI is in neutral range)
- Dynamic position sizing based on spread magnitude
- Volume-weighted spread calculation
- Time-of-day filters (crypto markets have patterns)
- Adaptive cooldown (shorter when volatility is high)
- Trail stop-loss to lock in profits
- Multi-pair strategy (ETH/DAI + WBTC/ETH + etc.)
- Bollinger Band squeeze as entry trigger
- Mean reversion vs momentum mode switching

## NEVER STOP

Once the experiment loop begins, do NOT pause to ask. Run indefinitely.
The human might be asleep. If you run out of ideas, think harder —
try combining near-misses, try radical changes, revisit discarded ideas
with modifications. The loop runs until manually interrupted.
```

---

## Example: Polymarket Bot Autoresearch

The same pattern works for optimizing a Polymarket prediction bot. Here's how
the file mapping changes:

```
polymarket-autoresearch/
├── prepare.py          # Fixed: historical Polymarket data, simulation engine
├── bot.py              # Agent modifies: signal detection, thresholds, filters
├── program.md          # Agent instructions
├── results.tsv
└── data/
    └── polymarket_history.json  # Historical market outcomes + prices
```

### Key Differences from Arbitrage

| Aspect | Arbitrage | Polymarket |
|--------|-----------|------------|
| **Metric** | `net_profit_pct` | `net_profit_pct` or `win_rate` |
| **Constraint** | max_drawdown < 20% | bet_size < $X, daily_loss < $Y |
| **What agent tunes** | Spread thresholds, indicators | Signal thresholds, edge filters, confidence scoring |
| **Data** | DEX price pairs | Market outcomes + historical odds |
| **Time budget** | 3 min (backtest) | 2 min (simulation) |

### Polymarket-Specific Ideas for the Agent

```markdown
## Ideas to try

- Adjust price_change_threshold (0.3% to 0.6%)
- Different lookback windows (15s, 30s, 60s)
- Add volatility filter (only trade in volatile periods)
- Confidence-weighted position sizing
- Multi-asset: BTC + ETH + SOL combined signals
- Time-of-day filters (avoid low-liquidity periods)
- Spread filter adjustments
- Edge decay modeling (how fast does the edge close?)
- Momentum confirmation (require 2 consecutive ticks in same direction)
- Kelly criterion for position sizing
```

---

## Template: Build Your Own Autoresearch

### Minimal Starter Template

#### 1. `prepare.py`

```python
"""
Infrastructure file — DO NOT MODIFY.
Contains: data loading, evaluation, constants.
"""
import time

# Constants
TIME_BUDGET = 180  # seconds
METRIC_NAME = "score"  # what we're optimizing

def load_data():
    """Load your fixed evaluation dataset."""
    # TODO: Load your data
    return data

def evaluate(result):
    """
    Compute the single metric we're optimizing.
    Returns a float. Higher (or lower) is better — pick one.
    """
    # TODO: Your evaluation logic
    return score

def print_results(score, extra=None):
    print("---")
    print(f"{METRIC_NAME}: {score:.6f}")
    if extra:
        for k, v in extra.items():
            print(f"{k}: {v}")
```

#### 2. `experiment.py`

```python
"""
The experiment file — AI agent modifies this.
Everything is fair game.
"""
import time
from prepare import load_data, evaluate, print_results, TIME_BUDGET

# ---------------------------------------------------------------------------
# Parameters (tune these)
# ---------------------------------------------------------------------------

PARAM_A = 0.5
PARAM_B = 100
MODE = "default"

# ---------------------------------------------------------------------------
# Your logic
# ---------------------------------------------------------------------------

def run():
    data = load_data()

    t_start = time.time()

    # TODO: Your experimental logic here
    result = do_something(data, PARAM_A, PARAM_B, MODE)

    # Respect time budget
    elapsed = time.time() - t_start
    assert elapsed < TIME_BUDGET * 2, f"Exceeded time budget: {elapsed:.0f}s"

    score = evaluate(result)
    print_results(score, {"elapsed_seconds": f"{elapsed:.1f}"})

if __name__ == "__main__":
    run()
```

#### 3. `program.md`

```markdown
# Autoresearch: [Your Domain]

## Setup
1. Agree on a run tag
2. Create branch: `git checkout -b autoresearch/<tag>`
3. Read all files for context
4. Run baseline first
5. Initialize results.tsv

## Rules
- Only modify `experiment.py`
- `prepare.py` is read-only
- No new dependencies
- Goal: [maximize/minimize] `[metric_name]`
- Constraint: [your constraints]

## Output
```
[metric_name]: 0.123456
```
Extract: `grep "^[metric_name]:" run.log`

## Experiment Loop
[Copy the standard loop]

## NEVER STOP
[Copy the autonomy instructions]
```

#### 4. `results.tsv` (header only to start)

```
commit	score	status	description
```

#### 5. Launch

```bash
# One-time setup
git checkout -b autoresearch/apr12

# Then tell your AI agent:
# "Read program.md and let's kick off a new experiment!"
```

---

## Tips & Lessons

### From Karpathy's Design

1. **One file, one metric** — resist the urge to add complexity. The agent does better with a clear, constrained problem.

2. **Fixed time budget is genius** — it makes radically different approaches (small model vs. large model, simple strategy vs. complex strategy) directly comparable.

3. **Git is your lab notebook** — every experiment is a commit. `git log --oneline` shows your complete research history.

4. **Simplicity criterion matters** — without it, the agent adds complexity on every iteration. Explicitly tell it: "simpler code at equal performance = keep."

5. **Let it crash** — the agent handles crashes gracefully (log, skip, move on). Don't over-engineer error handling.

6. **Don't hardcode the search space** — tell the agent "everything is fair game" and let it surprise you. The best improvements often come from ideas you wouldn't have tried.

### For Trading/Finance Applications

7. **Use historical data, not live markets** — autoresearch needs fast, repeatable experiments. Backtesting on fixed data is the way.

8. **Include realistic costs** — fees, slippage, gas costs. An agent that optimizes for gross profit will find strategies that fail in production.

9. **Add constraints, not just objectives** — "maximize profit" alone leads to degenerate strategies. Add: max drawdown, min trades, max position size.

10. **Watch for overfitting** — the agent might find strategies that perfectly fit historical data but fail on new data. Consider:
    - Using out-of-sample validation (split data into train/test in prepare.py)
    - Penalizing complexity (fewer parameters = better)
    - Walk-forward validation

11. **Seed with domain knowledge** — in the "Ideas to try" section, list real trading concepts (RSI, VWAP, Kelly criterion). The agent learns from these hints.

### Operational

12. **Run overnight** — start before bed, wake up to 50-100 experiments.

13. **Review results.tsv in the morning** — the TSV is your executive summary. Look at what worked and what crashed.

14. **Iterate on program.md** — after reviewing results, refine your instructions. This is the meta-game: programming the researcher.

15. **Branch per experiment session** — `autoresearch/apr12`, `autoresearch/apr13`, etc. Makes it easy to compare sessions.

---

## Resources

- [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) — original repo
- [Karpathy's tweet](https://x.com/karpathy/status/2029701092347630069) — context and motivation
- [Dummy's Guide](https://x.com/hooeem/status/2030720614752039185) — beginner-friendly explainer
- [MacOS fork](https://github.com/miolini/autoresearch-macos)
- [Windows fork](https://github.com/jsegov/autoresearch-win-rtx)
- [AMD fork](https://github.com/andyluo7/autoresearch)
