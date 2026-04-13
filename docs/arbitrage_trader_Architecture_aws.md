# Arbitrage Trader Architecture (Full)

## Vercel + Low-Cost AWS + Neon / Supabase Option

Full production architecture for DEX arbitrage trading system.

---

## Overview

- Vercel → Dashboard + Control Plane
- EC2 → Trading Engine (scanner + execution)
- Neon → Primary database (cheap, serverless)
- Optional Supabase → if backend features needed

---

## Runtime Schedule

- Start: Saturday 10 PM
- Stop: Friday 1 PM

---

## Core Flow

detect → simulate → risk → build → private submit → verify → store → alert

---

## Key Principles

- Execution > detection
- Always simulate before execution
- Never use public mempool
- Deterministic logic only
- Keep costs minimal early

---

## Components

### Scanner
- Detect spreads
- Rank opportunities

### Execution
- Simulate trades
- Apply risk filters
- Submit via private relays

### Persistence
- Opportunities
- Trades
- PnL
- Checkpoints

### Observability
- Logs
- Metrics
- Alerts (Telegram, Discord, Gmail)

---

## Infrastructure

### EC2
- t3.small or t3.medium
- runs bot + scheduler + API

### Database
- Neon (recommended — serverless Postgres, free tier)
- Supabase (optional — adds auth, storage, edge functions)
- RDS (future — if scale demands it)

### Alerts
- Telegram Bot (real-time trade alerts, kill switch commands)
- Discord Webhook (team notifications, channel-based)
- Gmail SMTP (daily summaries, failure reports)

---

## Alerting Architecture

### Event Types

| Event | Telegram | Discord | Gmail |
|---|---|---|---|
| opportunity_found | Real-time push | Channel embed | — |
| trade_executed | Real-time push | Channel embed | — |
| trade_reverted | Real-time push | Channel embed | Immediate email |
| simulation_failed | Real-time push | Channel embed | — |
| system_error | Real-time push | Channel embed | Immediate email |
| daily_summary | Daily digest | Daily embed | Daily email |

### Environment Variables

```bash
# Telegram (real-time alerts)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321

# Discord (team notifications)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Gmail (daily summaries + critical errors)
GMAIL_ADDRESS=bot@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_RECIPIENT=you@gmail.com
```

### Setup Notes

- **Telegram**: Message @BotFather → create bot → get token. Start chat with bot → GET /getUpdates → find chat_id.
- **Discord**: Channel Settings → Integrations → Webhooks → copy URL.
- **Gmail**: Enable 2FA → myaccount.google.com → Security → App passwords → generate for "Mail".

### Dispatcher Model

All three backends are behind an `AlertDispatcher` that:
- fans out each event to all configured backends
- skips unconfigured backends gracefully (no crash)
- logs failures but never blocks the trading loop

---

## Dashboard (Vercel)

- PnL tracking
- Execution quality
- Opportunity funnel
- Failure analysis
- Consumes FastAPI endpoints: /pnl, /funnel, /opportunities, /health

---

## API Control Plane (FastAPI on EC2)

| Endpoint | Method | Purpose |
|---|---|---|
| /health | GET | System status + kill switch state |
| /execution | GET | Current execution mode |
| /execution | POST | Enable/disable live trading (kill switch) |
| /risk/policy | GET | Current risk thresholds |
| /opportunities | GET | Recent candidates |
| /opportunities/{id} | GET | Single opportunity detail |
| /opportunities/{id}/pricing | GET | Pricing breakdown |
| /opportunities/{id}/risk | GET | Risk decision |
| /opportunities/{id}/simulation | GET | Simulation result |
| /pnl | GET | Aggregate trade results |
| /funnel | GET | Opportunity status distribution |

---

## Safety

- Kill switch required (POST /execution)
- Simulation required before execution
- Gas + slippage always included in profitability
- No blind retries
- Alerts on every revert and system error
- Pause on repeated failures

---

## Database Schema

SQLite for development, Neon (Postgres) for production.
Same schema, swap connection string only.

Core tables:
- opportunities (lifecycle tracking)
- pricing_results (cost breakdown per candidate)
- risk_decisions (approval/rejection with reason)
- simulations (pre-execution validation)
- execution_attempts (tx hashes, bundles, target blocks)
- trade_results (actual vs expected PnL)
- system_checkpoints (restart-safe state)

---

## Deployment

### EC2 Setup

```bash
# Install
sudo apt update && sudo apt install python3.11 python3-pip
pip install -r requirements.txt

# Run bot
PYTHONPATH=src python -m main --config config/uniswap_pancake_config.json --onchain --dry-run

# Run API
PYTHONPATH=src uvicorn api.app:app --host 0.0.0.0 --port 8000

# Scheduler (cron)
# Start Saturday 10 PM, stop Friday 1 PM
0 22 * * 6 cd /opt/arbitrage && ./start.sh
0 13 * * 5 cd /opt/arbitrage && ./stop.sh
```

### Environment File (.env)

```bash
# RPC (use Alchemy/Infura for production)
RPC_ETHEREUM=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
RPC_ARBITRUM=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY

# Execution (only for live trading)
EXECUTOR_PRIVATE_KEY=0x...
EXECUTOR_CONTRACT=0x...

# Database
DATABASE_URL=postgres://user:pass@your-neon-host/arbitrage

# Alerting
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DISCORD_WEBHOOK_URL=...
GMAIL_ADDRESS=...
GMAIL_APP_PASSWORD=...
GMAIL_RECIPIENT=...
```

---

## Final Goal

Build a safe, observable, restartable, cost-efficient arbitrage trading system with real-time alerting and full audit trail.
