# KES Multi-Asset Price Tracker

A robust Python script that fetches live exchange rates for **13 global fiat currencies** and **10 major cryptocurrencies** against the **Kenyan Shilling (KES)** . Data is saved to a timestamped CSV file for analysis and tracking.

## Features
- Fetches fiat rates using the free [currency-api.com](https://currency-api.com) service.
- Fetches crypto prices using the [CoinGecko API](https://www.coingecko.com/en/api) (free tier).
- Automatic retry logic for unreliable network connections.
- Saves all data to `exchange_rates_master.csv` with timestamps.
- Failover system built-in—if primary fiat source fails, it attempts a calculated fallback.

## Supported Assets
**Fiat (13):** USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR, BRL, ZAR, AED, SAR  
**Crypto (10):** BTC, ETH, XRP, SOL, ADA, AVAX, DOT, MATIC, LINK, UNI, LTC

## Technologies Used
- Python 3
- Requests (with custom retry adapters)
- CSV & Datetime modules
- CoinGecko API
- currency-api.com

## How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/essentialelite0/python-scraper.git
   cd python-scraper
