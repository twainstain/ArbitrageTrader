# Arbitrage Scanner Doc

This document is based on the downloaded content of the video:

- [How to Make Money With Crypto Arbitrage (ArbitrageScanner Review)](https://www.youtube.com/watch?v=tT4iT4VByAY)

It has two goals:

- summarize what the video says an arbitrage scanner should do
- turn that into a practical spec for our own arbitrage scanner experiments

## What The Video’s Scanner Does

According to the video, ArbitrageScanner is positioned as a tool that:

- monitors spreads across multiple exchanges in real time
- scans both **CEX** and **DEX** venues
- highlights structured arbitrage setups
- helps identify funding-rate opportunities
- speeds up discovery while leaving execution under the user’s control

The video also stresses that the tool itself does not need direct access to funds. It is presented as a scanner and workflow layer, not an auto-trading wallet.

## Scanner Modes Mentioned Or Implied

### 1. Cross-Exchange Spread Scanner

Goal:

- detect the same asset priced differently across venues

Core output:

- asset
- buy venue
- sell or hedge venue
- spread percentage
- volume estimate
- timestamp

### 2. Spot-Futures Convergence Scanner

Goal:

- detect a basis or convergence setup where spot and futures are far enough apart to justify a hedged trade

Core output:

- spot venue
- futures venue
- spot price
- futures price
- basis / spread
- order book depth
- estimated exit logic

### 3. Funding Rate Scanner

Goal:

- find markets where funding payments may justify a hedged setup

Core output:

- exchange
- symbol
- funding rate
- next funding timestamp
- long/short carry direction
- liquidity checks

## What Our Own Scanner Should Include

If we build our own scanner for experiments, the minimum useful version should include the following.

## Data Inputs

### Market Data

- spot prices from target exchanges
- futures prices where available
- funding rates where available
- best bid / ask
- order book depth
- 24h volume or recent rolling volume

### Operational Data

- withdrawal/deposit availability
- estimated transfer constraints if relevant
- latency timestamp for each quote
- exchange-specific fees

## Core Scanner Modules

### 1. Venue Adapters

One adapter per exchange should normalize:

- symbol mapping
- bid/ask format
- fees
- funding rates
- market type

This is the boring but critical layer.

### 2. Opportunity Normalizer

The scanner should convert raw market feeds into comparable opportunity objects, for example:

```json
{
  "symbol": "ETH/USDT",
  "buy_exchange": "A",
  "sell_exchange": "B",
  "buy_price": 2500.0,
  "sell_price": 2512.0,
  "spread_pct": 0.48,
  "estimated_fee_pct": 0.16,
  "estimated_net_pct": 0.22,
  "liquidity_score": 0.84,
  "strategy_type": "cross_exchange"
}
```

### 3. Fee And Risk Filter

This is the piece many “scanner” demos skip.

The scanner should subtract:

- trading fees
- slippage estimate
- funding carry if relevant
- withdrawal / transfer cost if relevant
- gas cost for DEX routes

Then it should reject low-quality opportunities before surfacing them.

### 4. Ranking Layer

Rank by more than raw spread.

Better ranking fields:

- estimated net profit
- available volume
- liquidity score
- venue reliability
- quote freshness
- risk-adjusted score

### 5. Alerting Layer

The scanner should emit alerts only for actionable setups.

Alert fields should include:

- strategy type
- symbol
- venues
- spread
- estimated net edge
- required capital
- freshness timestamp
- warning flags

## Strategy Types To Support First

A good first scanner roadmap is:

1. cross-exchange spot spread scanner
2. spot-futures basis scanner
3. funding-rate scanner

That sequence matches the video reasonably well while staying implementable.

## Warning Flags The Scanner Should Generate

The video mentions several risks directly. Our scanner should mark them explicitly:

- low liquidity
- wide order book gaps
- stale quote
- transfer delay risk
- venue risk
- thin market
- spread too small after fees
- high execution complexity

This is important because the scanner should not just find “interesting spreads.” It should help reject bad ones.

## Suggested Output Format

For a first version, a simple table or JSON feed is enough:

```text
timestamp | strategy | symbol | buy_venue | sell_venue | spread_pct | net_pct | volume | risk_flags
```

If we later add a UI, the most useful views would be:

- top current spreads
- top funding-rate opportunities
- recently expired opportunities
- venue-level opportunity counts

## Recommended MVP For This Repo

For this repo specifically, I would build the scanner in stages:

### Stage 1

- simulated venues only
- normalized opportunity objects
- fee-aware ranking
- CLI output

### Stage 2

- live market adapters for a few venues
- spot spread scanning
- persistence of observations

### Stage 3

- funding-rate support
- order book depth filters
- alerting

### Stage 4

- paper-trade handoff
- experiment scoring
- historical opportunity replay

## What To Keep Separate

One useful lesson from the video is the distinction between:

- **scanner**
- **executor**

Our scanner should only:

- discover
- rank
- alert

It should not automatically manage funds by default.

That separation makes testing safer and debugging easier.

## Bottom Line

The video’s product pitch suggests that a useful arbitrage scanner is mainly about:

- coverage
- speed
- structure
- trader control

If we build our own version, the most important rule is:

- don’t optimize for “finding spreads”
- optimize for surfacing **actionable, net-positive, risk-filtered opportunities**
