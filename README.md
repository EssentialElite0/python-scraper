# 🇰🇪 KES Market Intelligence Platform

A comprehensive financial data pipeline that scrapes live fiat and cryptocurrency rates against the Kenyan Shilling, stores them in a SQLite database, and provides a full analytics suite including trends, statistics, arbitrage scanning, portfolio tracking, and price alerts.

## 📦 Modules

| File | Purpose |
| :--- | :--- |
| `scraper.py` | Fetches live rates from currency-api.com (fiat) and CoinGecko (crypto). Saves to CSV and database. |
| `database.py` | SQLite storage engine. Creates tables, saves historical rates, logs runs, provides query functions. |
| `analytics.py` | Interactive intelligence suite with six modules. |

## 🧠 Analytics Features

1. **Latest Rates** – Quick snapshot of all tracked assets.
2. **Asset Statistics** – Min, max, average over entire history.
3. **Trends Engine** – Direction, percent change, and volatility over custom periods.
4. **Arbitrage Scanner** – Implied cross‑rates for fiat pairs and BTC/USD path.
5. **Portfolio Tracker** – Define holdings and value them in real‑time KES.
6. **Alert System** – Set price thresholds; get notified when conditions are met.

## 📊 Tracked Assets

- **Fiat (13):** USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR, BRL, ZAR, AED, SAR
- **Crypto (10):** BTC, ETH, XRP, SOL, ADA, AVAX, DOT, MATIC, LINK, UNI, LTC

## 🚀 How to Use

1. **Clone the repository**
   ```bash
   git clone https://github.com/essentialelite0/python-scraper.git
   cd python-scraper
