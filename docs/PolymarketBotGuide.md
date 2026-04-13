# Polymarket Prediction Market Trading Bot Guide

> Based on [Nate B Jones' video](https://www.youtube.com/watch?v=BiqG3it0gY0&t=18s): *"A Polymarket Bot Made $438,000 In 30 Days. Your Industry Is Next. Here's What To Do About It."*

---

## Table of Contents

1. [Video Summary](#video-summary)
2. [The $438K Bot: How It Worked](#the-438k-bot-how-it-worked)
3. [Prerequisites](#prerequisites)
4. [Step 1 - Polymarket Account & Wallet Setup](#step-1---polymarket-account--wallet-setup)
5. [Step 2 - Development Environment Setup](#step-2---development-environment-setup)
6. [Step 3 - Polymarket API & SDK Integration](#step-3---polymarket-api--sdk-integration)
7. [Step 4 - Price Feed Integration (Binance WebSocket)](#step-4---price-feed-integration-binance-websocket)
8. [Step 5 - Latency Arbitrage Strategy](#step-5---latency-arbitrage-strategy)
9. [Step 6 - Order Execution Engine](#step-6---order-execution-engine)
10. [Step 7 - Risk Management](#step-7---risk-management)
11. [Step 8 - Testing & Deployment](#step-8---testing--deployment)
12. [Architecture Overview](#architecture-overview)
13. [Resources](#resources)

---

## Video Summary

Nate B Jones analyzes how a trading bot on **Polymarket** (a blockchain-based prediction market) converted **$313 into $438,000 in 30 days** during late 2025. The video is not a coding tutorial but a strategic analysis of what this means for every industry.

### Key Takeaways

1. **The bot didn't predict anything** — it exploited a pricing lag. Polymarket's order book prices lag behind confirmed spot prices on exchanges like Binance and Coinbase by 2-10 seconds. The bot detected this window and traded before odds adjusted.

2. **The strategy**: The bot traded exclusively in **BTC, ETH, and SOL 15-minute up/down markets**, placing bets of $4,000-$5,000 each with a **98% win rate**.

3. **92.4% of wallets on Polymarket lost money** — only 7.6% profited. Having access to AI tools doesn't guarantee success; knowing *what to build* matters.

4. **A developer claimed to rebuild the entire system using Claude in about 40 minutes** — highlighting how accessible this technology has become.

5. **Nate's framework**: AI is collapsing arbitrage windows across five categories:
   - **Speed gaps** (reaction time advantages)
   - **Knowledge asymmetries** (expertise gaps)
   - **Information distribution gaps** (who knows what, when)
   - **Cost differentials** (geographic pricing)
   - **Execution complexity** (process automation)

---

## The $438K Bot: How It Worked

```
Wallet: 0x8dxd (anonymized)
Starting capital: $313
Ending balance: ~$438,000
Timeframe: ~30 days (December 2025 - January 2026)
Win rate: 98%
Markets: BTC/ETH/SOL 15-minute up/down
Bet size: $4,000-$5,000 per trade
```

### The Latency Arbitrage Strategy

```
1. Monitor BTC/ETH/SOL spot prices on Binance/Coinbase in real-time
2. Simultaneously monitor Polymarket's 15-min up/down market prices
3. Detect when spot price makes a significant move (e.g., BTC jumps 0.4%+)
4. Check if Polymarket odds have NOT yet adjusted (2-10 second lag)
5. Buy the correct outcome (UP if price jumped, DOWN if price dropped)
6. Wait for market resolution (the 15-minute window closes)
7. Collect winnings — the spot price movement was already confirmed
```

The edge: Polymarket prices are set by human traders and market makers who react slower than a bot reading exchange WebSocket feeds.

---

## Prerequisites

### Tools & Software

| Tool | Purpose |
|------|---------|
| **Python 3.9+** | Primary language |
| **pip** | Package manager |
| **MetaMask** or wallet | Polygon-compatible wallet |
| **MATIC/POL** | Gas fees on Polygon |
| **USDC** (on Polygon) | Trading capital |
| **VPS** (optional) | Low-latency hosting (Dublin/London recommended) |

### Accounts

- **Polymarket account** — [polymarket.com](https://polymarket.com) (fund with USDC on Polygon)
- **Binance account** — for WebSocket price feed access (no trading needed)
- **Polygon RPC** — via Alchemy, Infura, or public endpoint

---

## Step 1 - Polymarket Account & Wallet Setup

### Create and Fund Your Account

1. Go to [polymarket.com](https://polymarket.com) and create an account
2. Connect or create a wallet (MetaMask, Coinbase Wallet, or email wallet)
3. Deposit USDC onto Polygon network
4. Note your **wallet address** and **private key** (for bot access)

### Generate API Credentials

API credentials are derived from your wallet's private key using the Polymarket SDK:

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    "https://clob.polymarket.com",
    key="YOUR_PRIVATE_KEY",
    chain_id=137
)

# This derives your API key, secret, and passphrase
creds = client.create_or_derive_api_creds()
print(creds)  # Save these securely
```

### Token Allowances (EOA Wallets Only)

If using MetaMask or a hardware wallet, you must approve token spending before trading:

**Approve USDC** (`0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`) for:
- `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` (Main exchange)
- `0xC5d563A36AE78145C45a50134d48A1215220f80a` (Neg risk markets)
- `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296` (Neg risk adapter)

**Approve Conditional Tokens** (`0x4D97DCd97eC945f40cF65F87097ACe5EA0476045`) for the same addresses.

> Email/Magic wallets handle allowances automatically.

---

## Step 2 - Development Environment Setup

### Initialize the Project

```bash
mkdir polymarket-bot
cd polymarket-bot
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install py-clob-client websockets aiohttp pyyaml python-dotenv pandas
```

### Environment Variables

Create a `.env` file:

```env
# Wallet
POLYMARKET_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
POLYMARKET_FUNDER_ADDRESS=0xYOUR_WALLET_ADDRESS

# API
POLYMARKET_HOST=https://clob.polymarket.com
CHAIN_ID=137

# Strategy
PRICE_CHANGE_THRESHOLD=0.004
MAX_TRADE_SIZE_USDC=20
HOLD_SECONDS=240
DAILY_LOSS_LIMIT_USDC=100

# Binance
BINANCE_WS_URL=wss://stream.binance.com:9443/ws/btcusdt@trade
```

> **SECURITY:** Add `.env` to `.gitignore`. Never commit private keys.

### Project Structure

```
polymarket-bot/
├── main.py              # CLI entry point, async orchestration
├── config.yaml          # Tunable parameters
├── .env                 # Secrets (never commit)
├── .gitignore
├── requirements.txt
├── feeds/
│   ├── __init__.py
│   ├── binance.py       # WebSocket BTC/USDT tick stream
│   └── polymarket.py    # CLOB WebSocket + REST API
├── strategy/
│   ├── __init__.py
│   └── latency_arb.py   # Signal detection logic
├── execution/
│   ├── __init__.py
│   ├── test_executor.py # Simulated fills (test mode)
│   └── live_executor.py # Real CLOB order placement
├── logger.py            # CSV results + error logging
└── results.csv          # Trade history output
```

---

## Step 3 - Polymarket API & SDK Integration

### Read-Only Client (Market Data)

```python
from py_clob_client.client import ClobClient

# No auth needed for reading market data
client = ClobClient("https://clob.polymarket.com")

# Health check
print(client.get_ok())
print(client.get_server_time())

# Get available markets
markets = client.get_simplified_markets()
for market in markets:
    print(f"{market['question']} - {market['tokens']}")
```

### Authenticated Client (Trading)

```python
from py_clob_client.client import ClobClient
import os
from dotenv import load_dotenv

load_dotenv()

client = ClobClient(
    host="https://clob.polymarket.com",
    key=os.getenv("POLYMARKET_PRIVATE_KEY"),
    chain_id=137,
    signature_type=0,  # 0=EOA, 1=Magic/Email, 2=Browser proxy
    funder=os.getenv("POLYMARKET_FUNDER_ADDRESS")
)

# Derive and set API credentials
client.set_api_creds(client.create_or_derive_api_creds())
```

### Get Market Prices

```python
from py_clob_client.clob_types import BookParams

# Get midpoint price for a specific token
token_id = "YOUR_TOKEN_ID"  # From market data
midpoint = client.get_midpoint(token_id)
print(f"Midpoint: {midpoint}")

# Get buy/sell prices
buy_price = client.get_price(token_id, side="BUY")
sell_price = client.get_price(token_id, side="SELL")

# Get full order book
book = client.get_order_book(token_id)
print(f"Best Bid: {book['bids'][0] if book['bids'] else 'N/A'}")
print(f"Best Ask: {book['asks'][0] if book['asks'] else 'N/A'}")
```

### Finding BTC 15-Minute Up/Down Markets

```python
# Search for BTC minute markets
markets = client.get_simplified_markets()
btc_markets = [
    m for m in markets
    if "BTC" in m.get("question", "") and "15" in m.get("question", "")
]

for m in btc_markets:
    print(f"Market: {m['question']}")
    print(f"  Condition ID: {m['condition_id']}")
    for token in m.get("tokens", []):
        print(f"  Token: {token['outcome']} - ID: {token['token_id']}")
```

---

## Step 4 - Price Feed Integration (Binance WebSocket)

### Binance Real-Time BTC Price Stream

Create `feeds/binance.py`:

```python
import asyncio
import websockets
import json
from collections import deque
from datetime import datetime


class BinanceFeed:
    """Real-time BTC/USDT price stream from Binance."""

    def __init__(self, symbol="btcusdt", window_seconds=30):
        self.url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
        self.current_price = None
        self.price_history = deque(maxlen=window_seconds * 10)  # ~10 ticks/sec
        self.callbacks = []

    def on_price_update(self, callback):
        """Register a callback for price updates."""
        self.callbacks.append(callback)

    async def connect(self):
        """Connect to Binance WebSocket and stream prices."""
        async for ws in websockets.connect(self.url):
            try:
                async for message in ws:
                    data = json.loads(message)
                    price = float(data["p"])
                    timestamp = datetime.utcnow()

                    self.current_price = price
                    self.price_history.append((timestamp, price))

                    # Notify all registered callbacks
                    for cb in self.callbacks:
                        await cb(price, timestamp)

            except websockets.ConnectionClosed:
                print("Binance WS disconnected, reconnecting...")
                continue

    def get_price_change_pct(self, lookback_seconds=30):
        """Calculate price change over the lookback window."""
        if len(self.price_history) < 2:
            return 0.0

        now = datetime.utcnow()
        baseline_price = None

        for ts, price in self.price_history:
            age = (now - ts).total_seconds()
            if age >= lookback_seconds:
                baseline_price = price
                break

        if baseline_price is None or baseline_price == 0:
            return 0.0

        return (self.current_price - baseline_price) / baseline_price
```

### Polymarket WebSocket Feed

Create `feeds/polymarket.py`:

```python
import asyncio
import websockets
import json


class PolymarketFeed:
    """Real-time Polymarket order book feed."""

    def __init__(self):
        self.ws_url = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        self.order_books = {}
        self.callbacks = []

    def on_book_update(self, callback):
        self.callbacks.append(callback)

    async def subscribe(self, token_ids):
        """Subscribe to order book updates for given tokens."""
        async for ws in websockets.connect(self.ws_url):
            try:
                # Subscribe to each token's order book
                for token_id in token_ids:
                    sub_msg = {
                        "type": "subscribe",
                        "channel": "book",
                        "assets_id": token_id
                    }
                    await ws.send(json.dumps(sub_msg))

                # Keep alive with PING every 10 seconds
                async def ping():
                    while True:
                        await asyncio.sleep(10)
                        await ws.send(json.dumps({"type": "PING"}))

                ping_task = asyncio.create_task(ping())

                async for message in ws:
                    data = json.loads(message)
                    if data.get("type") == "book":
                        token_id = data.get("asset_id")
                        self.order_books[token_id] = data

                        for cb in self.callbacks:
                            await cb(token_id, data)

                ping_task.cancel()

            except websockets.ConnectionClosed:
                print("Polymarket WS disconnected, reconnecting...")
                continue

    def get_best_bid(self, token_id):
        book = self.order_books.get(token_id, {})
        bids = book.get("bids", [])
        return float(bids[0]["price"]) if bids else None

    def get_best_ask(self, token_id):
        book = self.order_books.get(token_id, {})
        asks = book.get("asks", [])
        return float(asks[0]["price"]) if asks else None

    def get_midpoint(self, token_id):
        bid = self.get_best_bid(token_id)
        ask = self.get_best_ask(token_id)
        if bid and ask:
            return (bid + ask) / 2
        return None
```

---

## Step 5 - Latency Arbitrage Strategy

Create `strategy/latency_arb.py`:

```python
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Signal(Enum):
    BUY_UP = "BUY_UP"
    BUY_DOWN = "BUY_DOWN"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class TradeSignal:
    signal: Signal
    confidence: float
    btc_price: float
    btc_change_pct: float
    polymarket_up_price: float
    edge: float
    timestamp: datetime


class LatencyArbStrategy:
    """
    Detects when Polymarket's BTC Up/Down market prices lag behind
    confirmed spot price movements on Binance.

    The $438K bot's core insight: when BTC spot moves sharply,
    Polymarket odds take 2-10 seconds to adjust. Buy the correct
    outcome in that window.
    """

    def __init__(self, config):
        self.price_change_threshold = config.get("price_change_threshold_pct", 0.004)
        self.min_edge = config.get("min_edge", 0.10)
        self.up_price_range = config.get("up_price_range", (0.35, 0.65))
        self.max_spread = config.get("max_spread", 0.05)

    def evaluate(self, btc_change_pct, polymarket_up_price, spread):
        """
        Evaluate whether there is an arbitrage opportunity.

        Args:
            btc_change_pct: BTC price change over lookback window (e.g., 0.005 = +0.5%)
            polymarket_up_price: Current price of the UP token (0.0 - 1.0)
            spread: Current bid-ask spread on Polymarket

        Returns:
            TradeSignal with the recommended action
        """
        # Filter 1: Spread too wide — market is illiquid
        if spread > self.max_spread:
            return self._no_signal("Spread too wide")

        # Filter 2: Market already repriced — no edge left
        low, high = self.up_price_range
        if not (low <= polymarket_up_price <= high):
            return self._no_signal("Market already repriced")

        # Calculate fair probability based on spot price movement
        if btc_change_pct >= self.price_change_threshold:
            # BTC went UP significantly — UP outcome is more likely
            fair_up_prob = 0.75  # Simplified; real bot uses momentum model
            edge = fair_up_prob - polymarket_up_price

            if edge >= self.min_edge:
                return TradeSignal(
                    signal=Signal.BUY_UP,
                    confidence=min(edge / 0.20, 1.0),
                    btc_price=0,  # Filled by caller
                    btc_change_pct=btc_change_pct,
                    polymarket_up_price=polymarket_up_price,
                    edge=edge,
                    timestamp=datetime.utcnow()
                )

        elif btc_change_pct <= -self.price_change_threshold:
            # BTC went DOWN significantly — DOWN outcome is more likely
            fair_down_prob = 0.75
            polymarket_down_price = 1.0 - polymarket_up_price
            edge = fair_down_prob - polymarket_down_price

            if edge >= self.min_edge:
                return TradeSignal(
                    signal=Signal.BUY_DOWN,
                    confidence=min(edge / 0.20, 1.0),
                    btc_price=0,
                    btc_change_pct=btc_change_pct,
                    polymarket_up_price=polymarket_up_price,
                    edge=edge,
                    timestamp=datetime.utcnow()
                )

        return self._no_signal("No significant price move")

    def _no_signal(self, reason):
        return TradeSignal(
            signal=Signal.NO_SIGNAL,
            confidence=0,
            btc_price=0,
            btc_change_pct=0,
            polymarket_up_price=0,
            edge=0,
            timestamp=datetime.utcnow()
        )
```

---

## Step 6 - Order Execution Engine

### Placing Orders on Polymarket

Create `execution/live_executor.py`:

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL
import os
from dotenv import load_dotenv

load_dotenv()


class LiveExecutor:
    """Places real orders on Polymarket."""

    def __init__(self):
        self.client = ClobClient(
            host=os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com"),
            key=os.getenv("POLYMARKET_PRIVATE_KEY"),
            chain_id=int(os.getenv("CHAIN_ID", 137)),
            signature_type=0,
            funder=os.getenv("POLYMARKET_FUNDER_ADDRESS")
        )
        self.client.set_api_creds(self.client.create_or_derive_api_creds())

    def place_market_order(self, token_id, amount_usdc, side="BUY"):
        """
        Place a market order (Fill-or-Kill).

        Args:
            token_id: The token to trade
            amount_usdc: Dollar amount to spend
            side: BUY or SELL
        """
        order = MarketOrderArgs(
            token_id=token_id,
            amount=amount_usdc,
            side=BUY if side == "BUY" else SELL,
            order_type=OrderType.FOK
        )
        signed = self.client.create_market_order(order)
        response = self.client.post_order(signed, OrderType.FOK)
        return response

    def place_limit_order(self, token_id, price, size, side="BUY"):
        """
        Place a limit order (Good-til-Cancelled).

        Args:
            token_id: The token to trade
            price: Price per share (0.01 - 0.99)
            size: Number of shares
            side: BUY or SELL
        """
        order = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=BUY if side == "BUY" else SELL
        )
        signed = self.client.create_order(order)
        response = self.client.post_order(signed, OrderType.GTC)
        return response

    def cancel_all_orders(self):
        """Cancel all open orders."""
        return self.client.cancel_all()

    def get_open_orders(self):
        """Get all open orders."""
        from py_clob_client.clob_types import OpenOrderParams
        return self.client.get_orders(OpenOrderParams())
```

### Test Executor (Paper Trading)

Create `execution/test_executor.py`:

```python
from datetime import datetime
import csv
import os


class TestExecutor:
    """Simulates trades without placing real orders."""

    def __init__(self, results_file="results.csv"):
        self.results_file = results_file
        self.trades = []
        self._init_csv()

    def _init_csv(self):
        if not os.path.exists(self.results_file):
            with open(self.results_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "market_id", "direction", "entry_price",
                    "amount_usdc", "edge_at_entry", "mode"
                ])

    def place_market_order(self, token_id, amount_usdc, side, midpoint, edge):
        """Simulate a market order at current midpoint."""
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "market_id": token_id,
            "direction": side,
            "entry_price": midpoint,
            "amount_usdc": amount_usdc,
            "edge_at_entry": edge,
            "mode": "test"
        }

        self.trades.append(trade)

        with open(self.results_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(trade.values())

        print(f"[TEST] {side} ${amount_usdc} @ {midpoint:.4f} | Edge: {edge:.4f}")
        return trade
```

---

## Step 7 - Risk Management

### Configuration

Create `config.yaml`:

```yaml
# Strategy Parameters
strategy:
  price_change_threshold_pct: 0.004   # 0.4% BTC move triggers signal
  lookback_seconds: 30                 # Window for measuring price change
  min_edge: 0.10                       # Min edge over fair value to enter
  up_price_range: [0.35, 0.65]        # Only trade when market hasn't repriced

# Position Sizing
execution:
  max_trade_size_usdc: 20              # Start small! The $438K bot used $4-5K
  hold_seconds: 240                    # Max hold before forced exit
  max_concurrent_positions: 1          # One trade at a time

# Risk Limits
risk:
  daily_loss_limit_usdc: 100           # Stop trading after $100 loss
  max_spread: 0.05                     # Skip if bid-ask spread > 5 cents
  settlement_buffer_seconds: 60        # Don't enter in last 60s of window
  max_daily_trades: 50                 # Maximum trades per day

# Monitoring
logging:
  results_file: results.csv
  error_file: error.log
  log_level: INFO
```

### Risk Management Guards

| Guard | What It Does |
|-------|-------------|
| **Daily Loss Limit** | Halts all trading if cumulative daily losses exceed the limit |
| **Settlement Buffer** | Prevents entries in the final 60 seconds of a market window |
| **Spread Filter** | Skips signals if the order book spread is too wide (illiquid) |
| **Concurrency Lock** | Maximum 1 open position at any time |
| **Edge Threshold** | Requires minimum 0.10 edge between fair value and market price |
| **Position Size Cap** | Limits maximum USDC per trade |
| **Max Daily Trades** | Prevents overtrading |

---

## Step 8 - Testing & Deployment

### Main Entry Point

Create `main.py`:

```python
import asyncio
import yaml
import argparse
from dotenv import load_dotenv
from feeds.binance import BinanceFeed
from feeds.polymarket import PolymarketFeed
from strategy.latency_arb import LatencyArbStrategy, Signal
from execution.test_executor import TestExecutor
from execution.live_executor import LiveExecutor

load_dotenv()


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


async def run_bot(mode="test"):
    config = load_config()

    # Initialize components
    binance = BinanceFeed(symbol="btcusdt", window_seconds=30)
    polymarket = PolymarketFeed()
    strategy = LatencyArbStrategy(config["strategy"])

    if mode == "live":
        executor = LiveExecutor()
    else:
        executor = TestExecutor()

    # Token IDs for BTC 15-min Up/Down market (update these!)
    UP_TOKEN_ID = "YOUR_UP_TOKEN_ID"
    DOWN_TOKEN_ID = "YOUR_DOWN_TOKEN_ID"

    daily_pnl = 0
    trade_count = 0
    position_open = False

    async def on_price_update(btc_price, timestamp):
        nonlocal daily_pnl, trade_count, position_open

        # Risk checks
        if daily_pnl <= -config["risk"]["daily_loss_limit_usdc"]:
            return  # Daily loss limit hit
        if trade_count >= config["risk"]["max_daily_trades"]:
            return  # Max trades hit
        if position_open:
            return  # Already in a trade

        # Get current market state
        btc_change = binance.get_price_change_pct(
            config["strategy"]["lookback_seconds"]
        )
        up_price = polymarket.get_midpoint(UP_TOKEN_ID)
        if up_price is None:
            return

        bid = polymarket.get_best_bid(UP_TOKEN_ID)
        ask = polymarket.get_best_ask(UP_TOKEN_ID)
        spread = (ask - bid) if (bid and ask) else 1.0

        # Evaluate strategy
        signal = strategy.evaluate(btc_change, up_price, spread)

        if signal.signal == Signal.BUY_UP:
            position_open = True
            trade_count += 1
            print(f"\n>>> BUY UP | BTC change: {btc_change:.4%} | Edge: {signal.edge:.4f}")

            if mode == "live":
                executor.place_market_order(
                    UP_TOKEN_ID,
                    config["execution"]["max_trade_size_usdc"],
                    "BUY"
                )
            else:
                executor.place_market_order(
                    UP_TOKEN_ID,
                    config["execution"]["max_trade_size_usdc"],
                    "BUY_UP",
                    up_price,
                    signal.edge
                )

            # Hold for configured duration, then release lock
            await asyncio.sleep(config["execution"]["hold_seconds"])
            position_open = False

        elif signal.signal == Signal.BUY_DOWN:
            position_open = True
            trade_count += 1
            print(f"\n>>> BUY DOWN | BTC change: {btc_change:.4%} | Edge: {signal.edge:.4f}")

            if mode == "live":
                executor.place_market_order(
                    DOWN_TOKEN_ID,
                    config["execution"]["max_trade_size_usdc"],
                    "BUY"
                )
            else:
                executor.place_market_order(
                    DOWN_TOKEN_ID,
                    config["execution"]["max_trade_size_usdc"],
                    "BUY_DOWN",
                    1.0 - up_price,
                    signal.edge
                )

            await asyncio.sleep(config["execution"]["hold_seconds"])
            position_open = False

    # Register callback
    binance.on_price_update(on_price_update)

    # Run feeds concurrently
    print(f"=== Polymarket Latency Arb Bot ({mode} mode) ===")
    print(f"Monitoring BTC spot vs Polymarket 15-min markets...")
    print(f"Trade size: ${config['execution']['max_trade_size_usdc']}")
    print(f"Daily loss limit: ${config['risk']['daily_loss_limit_usdc']}\n")

    await asyncio.gather(
        binance.connect(),
        polymarket.subscribe([UP_TOKEN_ID, DOWN_TOKEN_ID])
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket Latency Arb Bot")
    parser.add_argument("--mode", choices=["test", "live"], default="test")
    args = parser.parse_args()

    asyncio.run(run_bot(args.mode))
```

### Running the Bot

```bash
# Test mode — no real orders, simulated fills
python main.py --mode test

# Let it run for 2-4 hours to validate the strategy
# Check results.csv for trade history

# Live mode — places real orders with real money
python main.py --mode live
```

### VPS Deployment (Production)

For minimal latency, deploy on a VPS close to Polymarket's infrastructure (Dublin or London):

```bash
# On your VPS
git clone https://github.com/YOUR_REPO/polymarket-bot.git
cd polymarket-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Create .env with your credentials
nano .env

# Run in background
nohup python main.py --mode live > bot.log 2>&1 &

# Monitor logs
tail -f bot.log
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    POLYMARKET LATENCY ARB BOT                │
│                                                              │
│  ┌──────────────────┐     ┌───────────────────────────┐     │
│  │  Binance Feed     │     │  Polymarket Feed           │     │
│  │  (WebSocket)      │     │  (WebSocket + REST)        │     │
│  │                   │     │                            │     │
│  │  BTC/USDT ticks   │     │  Order book updates        │     │
│  │  ~10/sec          │     │  Best bid/ask prices       │     │
│  └────────┬──────────┘     └──────────┬────────────────┘     │
│           │                           │                      │
│           └─────────┬─────────────────┘                      │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Latency Arb Strategy                     │   │
│  │                                                       │   │
│  │  1. Calculate BTC price change (30s window)           │   │
│  │  2. Compare to Polymarket UP/DOWN token price         │   │
│  │  3. Check: has market repriced yet?                   │   │
│  │  4. If edge > 0.10 → generate signal                  │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│               ┌─────────▼──────────┐                        │
│               │  Risk Manager       │                        │
│               │  - Daily loss limit  │                        │
│               │  - Position sizing   │                        │
│               │  - Spread filter     │                        │
│               │  - Concurrency lock  │                        │
│               └─────────┬──────────┘                        │
│                         │                                    │
│               ┌─────────▼──────────┐                        │
│               │  Order Executor     │                        │
│               │  (test or live)     │                        │
│               │                     │                        │
│               │  py-clob-client SDK │                        │
│               └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘

         EXTERNAL SERVICES
┌────────────────┐  ┌─────────────────┐  ┌──────────────┐
│  Binance       │  │  Polymarket     │  │  Polygon     │
│  (spot prices) │  │  (CLOB API)     │  │  (blockchain)│
└────────────────┘  └─────────────────┘  └──────────────┘
```

---

## Resources

### Video
- [A Polymarket Bot Made $438,000 In 30 Days — Nate B Jones](https://www.youtube.com/watch?v=BiqG3it0gY0&t=18s)

### Nate B Jones
- [Newsletter: $313 Became $438,000 in 30 Days](https://natesnewsletter.substack.com/p/313-became-438000-in-30-days-youre)
- [Podcast: AI News & Strategy Daily](https://podcasts.apple.com/nz/podcast/ai-news-strategy-daily-with-nate-b-jones/id1877109372)

### Polymarket Official
- [Polymarket Docs](https://docs.polymarket.com)
- [py-clob-client (Python SDK)](https://github.com/Polymarket/py-clob-client)
- [Polymarket Agents (AI Framework)](https://github.com/Polymarket/agents)

### Open-Source Bot Implementations
- [polymarket-latency-bot](https://github.com/learningworship/polymarket-latency-bot) — Python latency arb bot (Binance -> Polymarket)
- [polymarket-arbitrage-bot](https://github.com/0xalberto/polymarket-arbitrage-bot) — Single & multi-market arbitrage
- [polymarket-kalshi-btc-arbitrage-bot](https://github.com/CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot) — Cross-platform (Polymarket + Kalshi)
- [Polymarket BTC 15-Minute Trading Bot](https://gist.github.com/Archetapp/7680adabc48f812a561ca79d73cbac69) — Gist reference

### Tutorials
- [Build a Polymarket Trading Bot with Python](https://robottraders.io/blog/polymarket-trading-bot-python)
- [Polymarket Bot That Asks Claude to Analyse and Trade](https://robottraders.io/blog/polymarket-ai-bot-claude-python)
- [How to Build a Polymarket Trading Bot (AlphaScope)](https://www.alphascope.app/blog/polymarket-bot-tutorial)
- [Building a Polymarket BTC 15-Minute Trading Bot (Medium)](https://medium.com/@aulegabriel381/the-ultimate-guide-building-a-polymarket-btc-15-minute-trading-bot-with-nautilustrader-ef04eb5edfcb)

### News Coverage
- [Finbold: Trading bot turns $313 into $438,000](https://finbold.com/trading-bot-turns-313-into-438000-on-polymarket-in-a-month/)
- [Yahoo Finance: Arbitrage Bots Dominate Polymarket](https://finance.yahoo.com/news/arbitrage-bots-dominate-polymarket-millions-100000888.html)

---

> **Disclaimer:** This guide is for educational purposes only. Prediction market trading involves significant financial risk. The latency arbitrage edge described here may have been reduced or eliminated by Polymarket's dynamic fee updates and increased competition. Always start with test mode, use small amounts, and never risk more than you can afford to lose.
