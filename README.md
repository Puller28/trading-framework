# TradingFramework — Freqtrade Dry-Run on Binance Testnet

Freqtrade bot configured for **dry-run (paper trading)** against the Binance testnet, with FreqUI enabled and 5 strategy slots ready to fill.

---

## Project structure

```
TradingFramework/
├── config.json                        # Main bot config (sandbox=true, dry_run=true)
├── Dockerfile                         # Railway-ready image
├── docker-compose.yml                 # Local dev convenience
├── .env.example                       # Environment variable template
├── .gitignore
└── user_data/
    └── strategies/
        ├── Strategy01.py              # Slot 1: RSI + EMA crossover skeleton
        ├── Strategy02.py              # Slot 2: RSI + MACD skeleton
        ├── Strategy03.py              # Slot 3: RSI + Bollinger Bands skeleton
        ├── Strategy04.py              # Slot 4: EMA 9/21 crossover skeleton
        └── Strategy05.py              # Slot 5: Trend-filter + ADX skeleton
```

---

## Prerequisites

- Docker (local) **or** a [Railway](https://railway.app) account (cloud)
- Binance Testnet API keys — create at <https://testnet.binance.vision>

---

## Local quick-start

```bash
# 1. Clone / enter project
cd TradingFramework

# 2. Create your .env
cp .env.example .env
# Edit .env with your testnet keys and desired credentials

# 3. Run with Docker Compose
docker compose up --build

# 4. Open FreqUI
# Visit http://localhost:8080 and log in with FREQTRADE_API_USER / FREQTRADE_API_PASS
```

To switch strategies without rebuilding, edit the `--strategy` value in `Dockerfile` or override at runtime:

```bash
docker compose run --rm freqtrade trade \
  --config /freqtrade/config.json \
  --strategy Strategy02
```

---

## Deploying to Railway

### 1. Create a new Railway project

```bash
# Install Railway CLI if needed
npm install -g @railway/cli
railway login
railway init
```

Or use the Railway web UI: **New Project → Deploy from GitHub repo**.

### 2. Set environment variables

In the Railway dashboard go to **Variables** and add:

| Variable | Value |
|---|---|
| `BINANCE_API_KEY` | Your Binance testnet key |
| `BINANCE_API_SECRET` | Your Binance testnet secret |
| `FREQTRADE_API_USER` | Dashboard username |
| `FREQTRADE_API_PASS` | Dashboard password |
| `FREQTRADE_JWT_SECRET` | Long random string |
| `TELEGRAM_TOKEN` | *(optional)* |
| `TELEGRAM_CHAT_ID` | *(optional)* |

### 3. Expose the port

Railway auto-detects `EXPOSE 8080` from the Dockerfile. In the service settings, set the **Port** to `8080` and enable **Public networking** to get a public URL for FreqUI.

### 4. Deploy

```bash
railway up
```

Railway builds the Dockerfile, injects env vars, and starts the container. Deployments are triggered automatically on every `git push` to the connected branch.

### 5. Access FreqUI

Open `https://<your-service>.up.railway.app` — log in with the credentials you set in Variables.

---

## Filling in a strategy

Each `StrategyXX.py` file has three methods to implement:

| Method | Purpose |
|---|---|
| `populate_indicators` | Add TA-Lib / pandas-ta columns to the OHLCV dataframe |
| `populate_entry_trend` | Set `enter_long = 1` rows where you want to buy |
| `populate_exit_trend` | Set `exit_long = 1` rows where you want to sell |

Change the active strategy in `config.json`:

```json
"strategy": "Strategy02"
```

Or pass `--strategy StrategyXX` on the command line.

---

## Switching from testnet to live

1. Obtain **real** Binance API keys (read + trade permissions, no withdrawal).
2. Update `.env` / Railway variables with the live keys.
3. In `config.json` set `"sandbox": false` and `"dry_run": false`.
4. Redeploy.

> **Warning:** live trading risks real funds. Backtest thoroughly first with `freqtrade backtesting`.

---

## Useful Freqtrade commands

```bash
# Backtest a strategy (run inside container or local venv)
freqtrade backtesting --config config.json --strategy Strategy01 \
  --timerange 20240101-20240401

# Download historical data
freqtrade download-data --config config.json --timerange 20240101-20240401

# Hyperopt (optimise parameters)
freqtrade hyperopt --config config.json --strategy Strategy01 \
  --hyperopt-loss SharpeHyperOptLoss --epochs 200
```
