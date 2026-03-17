# ORB Institutional Screener

> **Real-time Open Range Breakout (ORB) stock screener for NSE equities**, powered by Kite Connect WebSocket streaming.

![Dashboard Screenshot](docs/dashboard.png)

## What it does

The ORB Screener monitors **500+ NSE stocks in real-time** during market hours (9:15 AM – 3:30 PM IST). It detects institutional breakout activity by comparing live 5-minute candle metrics against 20-day historical baselines.

### Key Features

- **🔥 Heat % Engine** — Compares current volume, value (turnover), and candle body size against the 20-day average across all 5-minute candles. Shows how much above/below baseline the stock is trading.
- **📊 Composite Scoring (0–100)** — Ranks stocks using a weighted score from three components:
  - **Ignition** (Volume, Value, Body heat)
  - **Continuation** (Speed, Pullback, Deceleration)
  - **Quality** (ORB validity, positive change, direction)
- **⚡ ORB State Machine** — Tracks each stock through: `IDLE → IGNITION → ORB_FORMED → ORB_TESTING → ORB_BROKEN`
- **💹 Pre-Breakout Pullback** — Measures how deep the price retraced from ORB high before breaking out. Shallow pullbacks suggest stronger conviction.
- **🔄 Live WebSocket Streaming** — Sub-second tick data from Kite Connect, aggregated into 5-minute candles.
- **🎨 Premium Dark UI** — Glassmorphism design with sparkline charts, direction badges, and color-coded heat indicators.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Kite WebSocket  │────▶│  Live Stream      │────▶│  Scoring        │
│  (tick data)     │     │  Engine           │     │  Engine         │
│                  │     │  • 5m candles     │     │  • Heat %       │
│                  │     │  • ORB state      │     │  • Composite    │
│                  │     │    machine        │     │    score        │
└─────────────────┘     └──────────────────┘     └────────┬───────┘
                                                          │
┌─────────────────┐                              ┌────────▼───────┐
│  Kite Historical │────▶│  Baseline Engine  │     │  FastAPI +      │
│  API (20 days)   │     │  • avg volume     │────▶│  WebSocket      │
│                  │     │  • avg body       │     │  broadcast      │
│                  │     │  • avg value      │     └────────┬───────┘
└─────────────────┘     └──────────────────┘              │
                                                          │
                                                 ┌────────▼───────┐
                                                 │  React Frontend │
                                                 │  (Vite + TW)   │
                                                 └────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, Uvicorn, WebSocket |
| **Data Feed** | Kite Connect API + KiteTicker WebSocket |
| **Frontend** | React 18, Vite, Tailwind CSS |
| **Scoring** | NumPy, Pandas, Pydantic |
| **Auth** | TOTP-based automated Kite login |

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Kite Connect API credentials

### 1. Backend
```bash
pip install -r requirements.txt
python run.py
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Dashboard will be live at `http://localhost:5173`

---

## Configuration

The admin panel (⚙️ button in navbar) lets you tune in real-time:
- **Volume Multiplier** — Minimum volume vs baseline (default: 5x)
- **Value Threshold** — Minimum turnover in Crores
- **Body Threshold** — Minimum candle body multiplier
- **Score Threshold** — Minimum composite score to display
- **Baseline Days** — Number of historical days for averaging
- **Heat Max %** — Cap for heat normalization

---

## Credential Security

Credentials are **never committed to the repository**.

- 🔒 `credentials.json` and `token.txt` are in `.gitignore`
- On VPS: credentials load from environment variables (`KITE_API_KEY`, etc.)
- Locally: falls back to `credentials.json` file

---

## Deployment (VPS)

Push to `main` branch triggers automatic deployment via GitHub Actions:
1. SSH into VPS
2. Pull latest code
3. Install dependencies
4. Build frontend
5. Restart backend + frontend services

See `.github/workflows/deploy.yml` for the workflow.

---

## License

Private project. All rights reserved.
