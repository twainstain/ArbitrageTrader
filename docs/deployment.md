# Deployment Guide — Arbitrage Trader

Production deployment on AWS with integrated BI dashboard on yeda-ai.com.

---

## Architecture Overview

```
           yeda-ai.com (Vercel)
          ┌────────────────────────────────────────────┐
          │  Rewrite rules:                             │
          │                                             │
          │  /apps/arb-trader/*  → trader.yeda-ai.com   │
          │  /*                  → React SPA             │
          │                                             │
          │  User visits:                               │
          │  yeda-ai.com/apps/arb-trader/dashboard      │
          └──────────────┬─────────────────────────────┘
                         │ HTTPS (Vercel proxy)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  EC2 t3.small (spot) — Ubuntu 22.04                              │
│  Security Group: 22 (SSH), 8000 (API), 3000 (Grafana)           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  docker compose                                           │    │
│  │                                                           │    │
│  │  ┌───────────┐  ┌───────────┐  ┌──────────────────────┐ │    │
│  │  │ bot       │  │ api       │  │ nginx                │ │    │
│  │  │ scan loop │  │ FastAPI   │  │ reverse proxy + TLS  │ │    │
│  │  │           │  │ :8000     │  │ :443 → 8000/3000     │ │    │
│  │  └─────┬─────┘  └─────┬─────┘  └──────────────────────┘ │    │
│  │        │              │                                   │    │
│  │  ┌─────┴──────────────┴─────────────────────────────┐    │    │
│  │  │  monitoring                                       │    │    │
│  │  │  Prometheus :9090 → scrapes /metrics              │    │    │
│  │  │  Grafana    :3000 → dashboards + alerts           │    │    │
│  │  │  Loki       :3100 → log aggregation               │    │    │
│  │  │  Promtail          → ships container logs → Loki  │    │    │
│  │  └──────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │ Neon Postgres│
                    │ (free tier)  │
                    └─────────────┘
```

---

## Cost Breakdown

| Resource | Monthly Cost |
|----------|-------------|
| EC2 t3.small spot | ~$5-7 |
| Neon Postgres (free tier, 0.5 GB) | $0 |
| ECR (Docker image, <1 GB) | ~$1 |
| Elastic IP (attached to instance) | $0 |
| Prometheus + Grafana + Loki | $0 (self-hosted) |
| Let's Encrypt SSL | $0 |
| **Total** | **~$6-8/month** |

### If you need more headroom

| Upgrade | Cost |
|---------|------|
| EC2 t3.small on-demand (no spot interruption risk) | ~$15/month |
| Neon Pro (10 GB, more compute) | $19/month |
| Dedicated Grafana Cloud (free tier: 10k metrics, 50 GB logs) | $0 |

---

## Dashboard & BI — Integration with yeda-ai.com

### Approach

The **existing FastAPI HTML dashboard** (already built in `src/api/dashboard.py`) is served
at **`https://www.yeda-ai.com/apps/arb-trader/dashboard`** via a Vercel rewrite rule.
Vercel proxies the request to the EC2 bot. No new React pages needed.

```
Browser hits: yeda-ai.com/apps/arb-trader/dashboard
                         │
                    Vercel (rewrite/proxy)
                         │ /apps/arb-trader/:path*
                         │  → https://trader.yeda-ai.com/:path*
                         ▼
              EC2 (nginx :443 → FastAPI :8000)
              ┌──────────────────────────┐
              │ /dashboard       → HTML dashboard page     │
              │ /health          → health endpoint         │
              │ /pnl             → PnL summary             │
              │ /funnel          → opportunity funnel       │
              │ /metrics         → real-time metrics        │
              │ /opportunities   → recent trades            │
              │ /opportunity/*   → detail pages             │
              └──────────────────────────┘
```

The dashboard auto-detects its base path via JavaScript:
```js
const API_BASE = window.location.pathname.split('/dashboard')[0];
// At yeda-ai.com/apps/arb-trader/dashboard → API_BASE = '/apps/arb-trader'
// At localhost:8000/dashboard              → API_BASE = ''
```

All fetch calls use `API_BASE + '/health'`, `API_BASE + '/pnl'`, etc., so the same
HTML works both locally and behind Vercel.

### What the Dashboard Shows

Already implemented in `src/api/dashboard.py`:

**Status Cards (6):** Execution status, Paused, Opportunities detected, Trades included,
Total PnL, Avg latency (P95)

**Performance Section:** 9 time windows (5m→1m), per-chain filter, opportunities/trades/profit

**Hourly Win/Loss Chart:** Per-chain green/red bars for last 24h

**Per-Chain Table:** Sortable by total, approved, rejected

**Recent Opportunities Table:** Last 50, sortable by spread/status/time, links to detail page

**Opportunity Detail Page:** Full lifecycle — pricing, risk decision, simulation result

### Vercel Configuration

One file in the yeda-ai.com repo (`vercel.json`):

```json
{
  "rewrites": [
    {
      "source": "/apps/arb-trader/:path*",
      "destination": "https://trader.yeda-ai.com/:path*"
    },
    {
      "source": "/((?!api/).*)",
      "destination": "/index.html"
    }
  ]
}
```

Vercel proxies `/apps/arb-trader/*` to the EC2 instance transparently.
No CloudFront changes needed.

### Authentication

The dashboard uses HTTP Basic auth (same creds as the bot API). When accessed
via Vercel, the browser shows the native auth prompt. Vercel forwards the
`Authorization` header to the EC2 origin automatically

---

## Prerequisites

Before deploying, these items must be ready in the ArbitrageTrader repo:

### 1. Dependencies (pyproject.toml)

Currently empty. Must declare all imports:

```toml
[project]
dependencies = [
    "web3>=6.0",
    "requests>=2.31",
    "fastapi>=0.109",
    "uvicorn[standard]>=0.27",
    "psycopg2-binary>=2.9",
    "python-dotenv>=1.0",
    "aiohttp>=3.9",
]
```

### 2. Graceful Shutdown

Add to `src/main.py`:
```python
import signal
import sys

shutdown_requested = False

def handle_signal(signum, frame):
    global shutdown_requested
    logger.info("Shutdown signal received, draining...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
```

Bot loop checks `shutdown_requested` before each iteration.

### 3. Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ src/
COPY config/ config/
COPY .env.example .env.example

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "run_live_with_dashboard", "--config", "config/live_config.json", "--live", "--dry-run"]
```

### 4. docker-compose.yml

```yaml
version: "3.8"

services:
  bot:
    build: .
    container_name: arb-bot
    restart: unless-stopped
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - prometheus
    networks:
      - arb-net

  prometheus:
    image: prom/prometheus:v2.51.2
    container_name: arb-prometheus
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - arb-net

  grafana:
    image: grafana/grafana:10.4.2
    container_name: arb-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASS:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
      - loki
    networks:
      - arb-net

  loki:
    image: grafana/loki:2.9.4
    container_name: arb-loki
    restart: unless-stopped
    volumes:
      - ./monitoring/loki.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - arb-net

  promtail:
    image: grafana/promtail:2.9.4
    container_name: arb-promtail
    restart: unless-stopped
    volumes:
      - ./monitoring/promtail.yml:/etc/promtail/config.yml
      - ./logs:/var/log/arb-bot
      - /var/run/docker.sock:/var/run/docker.sock
    command: -config.file=/etc/promtail/config.yml
    depends_on:
      - loki
    networks:
      - arb-net

  nginx:
    image: nginx:alpine
    container_name: arb-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./monitoring/nginx.conf:/etc/nginx/nginx.conf
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - bot
      - grafana
    networks:
      - arb-net

volumes:
  prometheus-data:
  grafana-data:
  loki-data:

networks:
  arb-net:
    driver: bridge
```

---

## Alerting

### Two Layers

The system has two complementary alerting layers:

**Layer 1 — Application Alerts (built into the bot)**

Events fire to Telegram, Discord, and Gmail via the `AlertDispatcher`.

```
Bot scan loop                    Pipeline lifecycle
┌──────────────────┐            ┌──────────────────────┐
│ market error     │            │ simulation_failed    │
│ opportunity_found│            │ trade_executed       │
│ trade_executed   │            │ trade_reverted       │
│ executor failure │            │ trade_not_included   │
│ daily_summary    │            └──────────┬───────────┘
└──────────┬───────┘                       │
           │                               │
           └───────────┬───────────────────┘
                       ▼
              AlertDispatcher (fan-out)
              ┌──────────────────────────┐
              │ TelegramAlert            │ ← real-time push (emoji-coded)
              │ DiscordAlert             │ ← color-coded embeds
              │ GmailAlert               │ ← HTML email
              └──────────────────────────┘
```

Plus **SmartAlerter** rules on top:
- Spread > 5% → immediate Telegram push (big win alert)
- Every hour → Gmail aggregate report with dashboard link

**Layer 2 — Infrastructure Alerts (Grafana)**

Grafana watches Prometheus metrics and fires alerts to the same Telegram/Discord channels:
- Bot down (no `/metrics` scrape for 2 min)
- High revert rate (>20% in 1h)
- Disk space >80%
- RPC failover spikes (>10 in 15m)

### Event Types

| Event | When | Telegram | Discord | Gmail |
|-------|------|----------|---------|-------|
| `opportunity_found` | Spread detected | Immediate | Embed | -- |
| `trade_executed` | TX confirmed on-chain | Immediate | Embed | -- |
| `trade_reverted` | TX reverted on-chain | Immediate | Embed | Immediate |
| `trade_not_included` | Bundle expired / not mined | Immediate | Embed | -- |
| `simulation_failed` | eth_call reverted pre-submit | Immediate | Embed | -- |
| `system_error` | Market error, RPC down, executor failure | Immediate | Embed | Immediate |
| `daily_summary` | End of bot run / scheduled | -- | Embed | Immediate |

### Smart Alert Rules

| Rule | Trigger | Channel | Purpose |
|------|---------|---------|---------|
| Big win | spread >= 5% | Telegram | Catch high-confidence opportunities in real-time |
| Hourly digest | Every 60 min | Gmail | Aggregate: opps found, approved, rejected, PnL |

### Environment Variables

```bash
# Telegram — real-time alerts
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...    # From @BotFather
TELEGRAM_CHAT_ID=987654321               # Your chat/group ID

# Discord — team notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Gmail — hourly summaries + critical errors
GMAIL_ADDRESS=bot@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx   # App password (2FA required)
GMAIL_RECIPIENT=you@gmail.com            # Where to send
```

All backends are **optional**. Unconfigured backends are skipped silently.
At least one backend should be configured for production.

### Setup Instructions

**Telegram:**
1. Message `@BotFather` on Telegram → `/newbot` → get token
2. Start a chat with your bot (or add to group)
3. `GET https://api.telegram.org/bot<TOKEN>/getUpdates` → find `chat_id`
4. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`

**Discord:**
1. Server Settings → Integrations → Webhooks → New Webhook
2. Copy webhook URL
3. Set `DISCORD_WEBHOOK_URL` in `.env`

**Gmail:**
1. Enable 2FA on your Google account
2. myaccount.google.com → Security → App passwords → generate for "Mail"
3. Set `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `GMAIL_RECIPIENT` in `.env`

### Alert Format Examples

**Telegram:**
```
🔍 opportunity_found
Opportunity: WETH/USDC
Buy: Uniswap-Arbitrum → Sell: SushiSwap-Arbitrum
Spread: 0.4521%
Net profit: 0.002341
```

**Discord:** Color-coded embeds (green=executed, red=reverted, blue=detected)

**Gmail:** HTML email with structured details table + dashboard link

### Wiring in Code

Alerting is now wired into three places:

| Location | Events fired |
|----------|-------------|
| `bot.py` — `ArbitrageBot.run()` | `opportunity_found`, `trade_executed`, `system_error` (market/executor), `daily_summary` |
| `pipeline/lifecycle.py` — `CandidatePipeline.process()` | `trade_executed`, `trade_reverted`, `trade_not_included`, `simulation_failed` |
| `run_live_with_dashboard.py` | `system_error` (market), SmartAlerter (big wins + hourly email) |

The `AlertDispatcher` accepts any number of backends and fans out to all of them.
Failures in one backend don't crash the bot or block other backends.

---

## Monitoring Config Files

### monitoring/prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "arb-bot"
    metrics_path: /metrics
    basic_auth:
      username: "${DASHBOARD_USER}"
      password: "${DASHBOARD_PASS}"
    static_configs:
      - targets: ["bot:8000"]
        labels:
          instance: "arbitrage-trader"
```

### monitoring/loki.yml

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 720h  # 30 days
```

### monitoring/promtail.yml

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: arb-bot-logs
    static_configs:
      - targets: [localhost]
        labels:
          job: arb-bot
          __path__: /var/log/arb-bot/*.log
```

### monitoring/nginx.conf

```nginx
events { worker_connections 1024; }

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # Redirect HTTP → HTTPS
    server {
        listen 80;
        server_name trader.yeda-ai.com;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl;
        server_name trader.yeda-ai.com;

        ssl_certificate     /etc/letsencrypt/live/trader.yeda-ai.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/trader.yeda-ai.com/privkey.pem;

        # CORS for yeda-ai.com frontend
        add_header Access-Control-Allow-Origin "https://www.yeda-ai.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

        # Bot API
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://bot:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Grafana
        location /grafana/ {
            proxy_pass http://grafana:3000/;
            proxy_set_header Host $host;
        }
    }
}
```

---

## Grafana Dashboards

Pre-provisioned dashboards for the bot:

### Dashboard 1: Trading Performance
- PnL over time (line chart)
- Opportunity detection rate (gauge)
- Execution success rate (gauge)
- Revert rate (gauge)
- Trades per hour (bar chart)

### Dashboard 2: System Health
- API response latency (histogram)
- RPC failover events (counter)
- Circuit breaker state changes (annotations)
- Memory / CPU usage (node exporter)

### Dashboard 3: Chain Analysis
- Per-chain opportunity count (pie chart)
- Per-chain profit breakdown (stacked bar)
- DEX pair volume heatmap

Dashboards are auto-provisioned from `monitoring/grafana/dashboards/*.json`.

Grafana alerts route to the same Telegram/Discord channels as the bot's native alerting.

---

## AWS Infrastructure

### Option A: Manual Setup (quickest)

```bash
# 1. Launch EC2 spot instance
aws ec2 run-instances \
    --image-id ami-0c7217cdde317cfec \
    --instance-type t3.small \
    --instance-market-options '{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"persistent"}}' \
    --key-name arb-trader-key \
    --security-group-ids sg-xxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=arb-trader}]' \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]'

# 2. Allocate & associate Elastic IP
aws ec2 allocate-address --domain vpc
aws ec2 associate-address --instance-id i-xxx --allocation-id eipalloc-xxx

# 3. Security group rules
aws ec2 authorize-security-group-ingress --group-id sg-xxx \
    --protocol tcp --port 22 --cidr YOUR_IP/32      # SSH
aws ec2 authorize-security-group-ingress --group-id sg-xxx \
    --protocol tcp --port 443 --cidr 0.0.0.0/0      # HTTPS (API + Grafana)
aws ec2 authorize-security-group-ingress --group-id sg-xxx \
    --protocol tcp --port 80 --cidr 0.0.0.0/0       # HTTP (certbot redirect)
```

### Option B: CloudFormation Template

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Arbitrage Trader — EC2 spot + security groups

Parameters:
  KeyPairName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: SSH key pair
  AllowedSSHCidr:
    Type: String
    Default: "0.0.0.0/0"
    Description: CIDR for SSH access (restrict to your IP)

Resources:
  TraderSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Arbitrage Trader SG
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: !Ref AllowedSSHCidr
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  TraderInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t3.small
      ImageId: ami-0c7217cdde317cfec  # Ubuntu 22.04 us-east-1
      KeyName: !Ref KeyPairName
      SecurityGroupIds:
        - !Ref TraderSecurityGroup
      InstanceMarketOptions:
        MarketType: spot
        SpotOptions:
          SpotInstanceType: persistent
      BlockDeviceMappings:
        - DeviceName: /dev/sda1
          Ebs:
            VolumeSize: 20
            VolumeType: gp3
      Tags:
        - Key: Name
          Value: arb-trader
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          apt-get update
          apt-get install -y docker.io docker-compose-v2
          systemctl enable docker
          usermod -aG docker ubuntu

  TraderEIP:
    Type: AWS::EC2::EIP
    Properties:
      InstanceId: !Ref TraderInstance

Outputs:
  PublicIP:
    Value: !Ref TraderEIP
    Description: Elastic IP for the trader instance
  InstanceId:
    Value: !Ref TraderInstance
```

---

## Deployment Steps

### First-Time Setup

```bash
# 1. SSH into instance
ssh -i arb-trader-key.pem ubuntu@<ELASTIC_IP>

# 2. Clone repo
git clone <REPO_URL> /opt/arb-trader
cd /opt/arb-trader

# 3. Create .env from template
cp .env.example .env
nano .env   # fill in: RPCs, DATABASE_URL, TELEGRAM, DISCORD, etc.

# 4. Set DATABASE_URL to Neon
# DATABASE_URL=postgres://user:pass@ep-xxx.us-east-1.aws.neon.tech/arbitrage?sslmode=require

# 5. SSL certificate (Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d trader.yeda-ai.com
mkdir -p certbot/conf && sudo cp -rL /etc/letsencrypt/* certbot/conf/

# 6. Start everything
docker compose up -d

# 7. Verify
curl https://trader.yeda-ai.com/health
# → {"status":"ok","execution_enabled":false}
```

### Neon Database Setup

1. Go to https://neon.tech → Create project → "arbitrage-trader"
2. Copy connection string → paste into `.env` as `DATABASE_URL`
3. Tables auto-create on first bot startup (via `db.py` init_schema)
4. Free tier: 0.5 GB storage, auto-suspend after 5 min idle

### DNS (Route 53 or GoDaddy)

Add an A record:
```
trader.yeda-ai.com → <ELASTIC_IP>
```

---

## CI/CD — GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Arbitrage Trader

on:
  push:
    branches: [master]
    paths:
      - 'src/**'
      - 'config/**'
      - 'Dockerfile'
      - 'docker-compose.yml'
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: PYTHONPATH=src pytest tests/ -q

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/master'
    steps:
      - uses: actions/checkout@v4

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
        with:
          registry-type: private
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1

      - name: Build & push image
        run: |
          docker build -t arb-trader .
          docker tag arb-trader:latest ${{ secrets.ECR_REPO }}:latest
          docker tag arb-trader:latest ${{ secrets.ECR_REPO }}:${{ github.sha }}
          docker push ${{ secrets.ECR_REPO }}:latest
          docker push ${{ secrets.ECR_REPO }}:${{ github.sha }}

      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /opt/arb-trader
            docker compose pull bot
            docker compose up -d bot
            sleep 5
            curl -sf http://localhost:8000/health || exit 1
```

### GitHub Secrets Required

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user with ECR push access |
| `AWS_SECRET_ACCESS_KEY` | IAM secret |
| `ECR_REPO` | `123456789.dkr.ecr.us-east-1.amazonaws.com/arb-trader` |
| `EC2_HOST` | Elastic IP of the instance |
| `EC2_SSH_KEY` | Private key for SSH |

---

## Secrets Management

**On EC2**, secrets live in `.env` (not committed). For better security:

```bash
# Store secrets in AWS Secrets Manager (optional, $0.40/secret/month)
aws secretsmanager create-secret \
    --name arb-trader/prod \
    --secret-string file://.env

# Fetch at startup (add to docker entrypoint)
aws secretsmanager get-secret-value --secret-id arb-trader/prod \
    --query SecretString --output text > /app/.env
```

Or keep it simple: `.env` on disk, `chmod 600 .env`, only `ubuntu` user can read.

---

## Runtime Schedule

Per architecture doc — bot runs Saturday 10 PM → Friday 1 PM:

```bash
# crontab -e
0 22 * * 6  cd /opt/arb-trader && docker compose up -d bot
0 13 * * 5  cd /opt/arb-trader && docker compose stop bot
```

Or run 24/7 in dry-run mode and only enable execution during trading windows via the API kill switch.

---

## Rollback

```bash
# SSH into instance
ssh ubuntu@<ELASTIC_IP>

# Roll back to previous image
cd /opt/arb-trader
docker compose pull bot  # pulls :latest
# If latest is broken, use a specific SHA:
docker compose down bot
docker pull $ECR_REPO:<previous-sha>
docker tag $ECR_REPO:<previous-sha> arb-trader:latest
docker compose up -d bot
```

---

## Spot Instance Interruption Handling

EC2 spot gives a 2-minute warning before reclaim. Handle it:

```bash
# /opt/arb-trader/spot-monitor.sh (runs as systemd service)
#!/bin/bash
while true; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        http://169.254.169.254/latest/meta-data/spot/instance-action)
    if [ "$HTTP_CODE" -eq 200 ]; then
        logger "Spot interruption notice — draining bot"
        cd /opt/arb-trader && docker compose stop bot
        exit 0
    fi
    sleep 5
done
```

The bot's graceful shutdown handler (SIGTERM) ensures no trade is left mid-execution.

---

## Health Checks & Alerts

### Application Level
- `GET /health` returns execution status — nginx can use this for uptime checks
- Circuit breaker auto-pauses on repeated failures
- Alerts fire to Telegram/Discord on reverts and system errors

### Infrastructure Level (Grafana Alerts)
- **Bot down**: no `/metrics` scrape for 2 minutes → Telegram alert
- **High revert rate**: >20% reverts in 1h window → Telegram alert
- **Disk space**: >80% → Telegram alert
- **RPC errors**: >10 failovers in 15m → Telegram alert

---

## Monitoring vs CloudWatch — Why Self-Hosted Wins Here

| Feature | CloudWatch | Self-Hosted (Prometheus + Grafana + Loki) |
|---------|-----------|------------------------------------------|
| Cost | $3+ per custom metric, $0.50/GB logs | $0 |
| Custom dashboards | Limited, clunky | Grafana — industry standard |
| Log search | CloudWatch Insights ($$$) | Loki + LogQL (free) |
| Alerting | SNS + Lambda (complex) | Grafana → Telegram/Discord (already built) |
| Retention | Priced per GB-month | Local disk (20 GB gp3 included) |
| Setup effort | Less | More (but docker-compose handles it) |

For a single-instance trading bot, self-hosted monitoring is the clear winner.

---

## Summary — What to Build

### In ArbitrageTrader repo (this repo)

| Item | Priority | Status |
|------|----------|--------|
| Fix pyproject.toml dependencies | P0 | DONE |
| Add graceful shutdown (SIGTERM) | P0 | DONE |
| Dockerfile (multi-stage, health check) | P0 | DONE |
| docker-compose.yml (6 services) | P0 | DONE |
| .dockerignore | P0 | DONE |
| Alert dispatcher wired into bot.py | P0 | DONE |
| Alert dispatcher wired into pipeline/lifecycle.py | P0 | DONE |
| Full backend init in run_live_with_dashboard.py | P0 | DONE |
| Alert wiring tests (14 new tests) | P0 | DONE |
| Dashboard API_BASE auto-detection | P0 | DONE |
| monitoring/ config files (7 files) | P1 | DONE |
| .github/workflows/deploy.yml | P1 | DONE |
| CloudFormation template (deploy/cloudformation.yml) | P2 | DONE |
| spot-monitor.sh (scripts/spot-monitor.sh) | P2 | DONE |

### In yeda-ai.com repo

| Item | Priority | Status |
|------|----------|--------|
| Add vercel.json with /apps/arb-trader rewrite | P1 | DONE |
| Deploy yeda-ai.com to Vercel | P1 | TODO (user) |
| Add product entry in DashboardPage.tsx | P2 | TODO |
| DNS: trader.yeda-ai.com A record → EC2 Elastic IP | P1 | TODO |
