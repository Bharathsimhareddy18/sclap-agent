# ScalpAgent

LangChain-based paper trading scalp agent. Flask + SQLite. No APScheduler — agent loop starts on boot.

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
python app.py
```

Open http://localhost:5000

## What it does

- On startup, immediately begins an infinite agent loop
- Every 5 minutes, the LangChain agent:
  1. Calls `get_stock_data` for AAPL, TSLA, NVDA, MSFT, META
  2. Analyses momentum + price position within day range
  3. Calls `execute_trade` for each ticker (BUY / SELL / HOLD)
- All trades and logs are persisted to SQLite (`trades.db`)
- UI auto-refreshes every 10 seconds

## Strategy logic (inside the LLM prompt)

| Condition | Action | Strategy |
|---|---|---|
| momentum_5 > 1.0 | BUY | MOMENTUM |
| momentum_5 < -1.0 | SELL | MOMENTUM |
| momentum_5 > 0.5 AND price near day_high | SELL | SCALP |
| momentum_5 < -0.5 AND price near day_low | BUY | SCALP |
| else | HOLD | HOLD |

## API endpoints

| Route | Method | Description |
|---|---|---|
| `/api/trades` | GET | Last 50 trades |
| `/api/logs` | GET | Last 30 agent logs |
| `/api/stats` | GET | Aggregate counts |
| `/api/force_cycle` | POST | Trigger cycle immediately |

## Tickers

Edit `TICKERS` list in `app.py` to change watched stocks.
