# Groceries Optimizer

Route optimizer across multiple grocery chains in Metro Vancouver.

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 20+ |
| Python | 3.10+ |

## Setup

### 1. Backend

```bash
cd backend
npm install
```

### 2. Python scraper dependencies

```bash
pip install "camoufox[geoip]"
python3 -m camoufox fetch   # downloads the hardened Firefox binary (~100 MB, once)
```

### 3. Seed the database (T&T mock data — no browser needed)

```bash
cd backend
npm run scrape -- --chain tnt --seed-mock
```

### 4. Frontend

```bash
cd frontend
npm install
```

## Running

```bash
# Terminal 1 — backend (port 3001)
cd backend && npm run dev

# Terminal 2 — frontend (port 3000)
cd frontend && npm run dev
```

## Scraping

```bash
# Scrape all chains (Walmart, Safeway, Save-On-Foods, T&T live)
npm run scrape

# Scrape one chain
npm run scrape -- --chain walmart
npm run scrape -- --chain safeway
npm run scrape -- --chain saveon
npm run scrape -- --chain tnt

# Reset T&T to mock dataset
npm run scrape -- --chain tnt --seed-mock
```

Scrapers use [Camoufox](https://camoufox.com) (hardened Firefox with fingerprint spoofing) to
reduce bot-detection risk. A `SCRAPE_DELAY_MS` env var (default `1500`) controls the delay
between page requests per chain. Daily auto-scrape runs at 03:00 via `node-cron`
(override with `SCRAPE_CRON` env var, e.g. `"0 */6 * * *"` for every 6 h).

> **Note**: Scraping is for personal/educational use only. Do not distribute scraped data
> or run at aggressive rates. Selectors and API patterns may need updating if sites change.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3001` | Backend port |
| `DB_PATH` | `backend/groceries.db` | SQLite file path |
| `SCRAPE_DELAY_MS` | `1500` | Ms between page requests |
| `SCRAPE_CRON` | `0 3 * * *` | Cron schedule for auto-scrape |

## Running tests

```bash
cd backend && npm test
```
