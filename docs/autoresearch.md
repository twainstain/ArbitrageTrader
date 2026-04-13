# AutoResearch Notes For My Own Experiments

Inspired by:

- Video: [The only AutoResearch tutorial you’ll ever need](https://www.youtube.com/watch?v=uBWuKh1nZ2Y&t=683s)
- Official repo: [karpathy/autoresearch](https://github.com/karpathy/autoresearch)

Date: April 12, 2026

## What AutoResearch Actually Is

AutoResearch is a very simple but powerful pattern:

1. give an agent a clear goal
2. limit what files it can change
3. define one measurable score
4. let it run short experiments
5. keep only the changes that improve the score
6. discard the rest
7. repeat many times

From the official repo, the core structure is intentionally tiny:

- `prepare.py`: fixed setup and utilities
- `train.py`: the one file the agent edits
- `program.md`: the instructions that tell the agent how to behave

The key idea is not "AI magic". The key idea is a **ratchet loop**:

- propose a change
- run an experiment
- measure the result
- keep the change only if it wins

## Why This Matters For Arbitrage Experiments

This maps very well to trading-system research, because arbitrage strategy work is also an iterative optimization problem.

Instead of optimizing `val_bpb` on a model, I would optimize a trading score such as:

- net PnL
- Sharpe ratio
- win rate after fees
- drawdown-adjusted return
- opportunity capture rate
- false-positive rate

So the AutoResearch pattern for me becomes:

- the agent edits strategy logic
- the system runs a backtest or simulation
- the results are scored
- only better changes are kept

## The Best Way To Apply This To ArbitrageTrader

### Goal

Build a repeatable research loop for testing many strategy variants safely.

### Human Role

My job is not to manually tweak every experiment.

My job is to define:

- the objective
- the constraints
- the metric
- the files the agent may change
- the rules for when a change is accepted

### Agent Role

The agent should:

- read the experiment instructions
- make one small strategy change
- run the evaluation
- compare against the current baseline
- keep the change only if the score improves
- record what happened

## Recommended Structure For My Repo

If I want an AutoResearch-style setup for arbitrage experiments, I should keep the repo small and controlled.

Suggested structure:

```text
program.md
prepare.py
run_experiment.py
src/
  arbitrage_bot/
    strategy.py
    market.py
    executor.py
    bot.py
experiments/
  results.csv
  logs/
  accepted/
  rejected/
```

### File Responsibilities

`program.md`

- the research instructions for the agent
- success metric
- constraints
- allowed files
- forbidden changes

`prepare.py`

- fixed dataset generation
- scenario setup
- seed control
- utility functions

`run_experiment.py`

- runs one simulation or backtest
- writes one comparable score
- saves experiment metadata

`strategy.py`

- the primary file the agent is allowed to change

## Best First Constraint

One of the smartest ideas in AutoResearch is limiting edit scope.

For my arbitrage experiments, I should **start by allowing edits to only one file**:

- `src/arbitrage_bot/strategy.py`

Why:

- changes stay reviewable
- results are easier to interpret
- the agent does not destroy the whole codebase
- I can understand which logic change caused the improvement

Only after the loop works well should I allow edits to additional files.

## What Metric Should I Optimize

This is the most important design decision.

For arbitrage research, I should not optimize raw profit alone.

Better metrics:

- `score = net_pnl - penalty_for_drawdown - penalty_for_reverts`
- Sharpe ratio with minimum trade count
- net profit after fees and gas with stability constraints

For early experiments, a strong simple score would be:

```text
score =
  total_net_profit
  - 2.0 * max_drawdown
  - 0.5 * failed_trade_count
  - 0.1 * volatility_of_returns
```

This is an engineering recommendation, not something stated directly in the video.

## What To Test First

The agent needs a search space that is small but meaningful.

Good first experiment knobs for arbitrage:

- minimum spread threshold
- minimum profit threshold
- gas buffer multiplier
- slippage buffer
- trade-size cap
- cooldown between trades
- pair-selection filters
- liquidity threshold

Good first derived signals:

- spread persistence across multiple ticks
- quote freshness
- route confidence score
- opportunity quality ranking

## What Not To Let The Agent Change At First

Do not start by letting the agent change:

- execution wallet logic
- RPC endpoints
- secret handling
- deployment scripts
- live trading code
- position sizing without hard caps
- anything that sends real transactions

Keep the first loop fully offline.

## Safe Experiment Progression

### Phase 1: Pure Simulation

Use only simulated quotes or historical snapshots.

Optimize:

- trade filtering
- threshold tuning
- opportunity ranking

### Phase 2: Historical Replay

Replay stored market conditions and compare:

- expected vs realized simulated outcomes
- false positives
- missed opportunities

### Phase 3: Paper Trading

Use live data, but no real execution.

Track:

- signal quality
- execution assumptions
- latency effects

### Phase 4: Tiny Live Tests

Only after the above:

- strict size caps
- strict kill switch
- strict max daily loss

## Example `program.md` For Arbitrage Research

```md
# Research Goal

Improve the arbitrage strategy in `src/arbitrage_bot/strategy.py`.

# Metric

Maximize `score` reported by `python run_experiment.py`.

# Allowed Changes

- You may only edit `src/arbitrage_bot/strategy.py`.

# Forbidden Changes

- Do not edit config loading.
- Do not edit execution code.
- Do not edit tests unless required to fix a real bug introduced by your change.
- Do not remove risk checks.
- Do not add live trading behavior.

# Process

1. Read the current strategy.
2. Make one focused change.
3. Run `python run_experiment.py`.
4. Compare the result to baseline.
5. Keep the change only if the score improves.
6. Record a short note about what changed and why.

# Research Heuristics

- Prefer simple changes over complex ones.
- Avoid overfitting to one scenario.
- Prefer robustness over raw profit.
- If performance is tied, prefer the simpler logic.
```

## Example Experiment Ideas For ArbitrageTrader

### Experiment 1: Better Trade Filter

Test whether requiring spread confirmation across 2 or 3 consecutive ticks reduces bad trades.

### Experiment 2: Dynamic Gas Buffer

Test whether a volatility-aware gas/slippage buffer improves net score.

### Experiment 3: Liquidity Gate

Skip trades when simulated liquidity is below a threshold.

### Experiment 4: Opportunity Ranking

Compare:

- raw spread ranking
- expected net profit ranking
- risk-adjusted ranking

### Experiment 5: Position Cap

Test whether smaller trade sizes produce better risk-adjusted performance than always using max size.

## Logging Requirements

The research loop is much better if each run logs:

- experiment id
- timestamp
- git commit hash
- strategy description
- score
- total profit
- drawdown
- trade count
- failed trade count
- notes

This lets me inspect the evolution later instead of just keeping the final winner.

## What Success Looks Like

A good AutoResearch-style setup for this repo would give me:

- one command to run one experiment
- one score that is stable and comparable
- one strategy file the agent can improve
- one experiment log that shows accepted and rejected ideas

That is enough to create a real research loop.

## Best Next Step For This Repo

The highest-value next implementation step would be:

1. create `run_experiment.py`
2. create a fixed scoring function
3. create `program.md`
4. allow the agent to edit only `src/arbitrage_bot/strategy.py`
5. log every experiment result to `experiments/results.csv`

## Bottom Line

The main lesson from AutoResearch is not just "let AI run experiments."

The real lesson is:

- keep the system tiny
- define one metric
- tightly constrain edits
- accept only measured improvements

That pattern is a very good fit for building my own arbitrage trader testing and research workflow.

## Sources

- YouTube metadata for [The only AutoResearch tutorial you’ll ever need](https://www.youtube.com/watch?v=uBWuKh1nZ2Y&t=683s)
- Official repo README for [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
- Additional background and setup details from [DataCamp’s guide](https://www.datacamp.com/tutorial/guide-to-autoresearch)
