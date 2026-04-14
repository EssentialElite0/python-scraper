import requests
from requests.adapters import HTTPAdapter, Retry
import csv
from datetime import datetime
import database as db

# --- CONFIGURATION ---
BASE_CURRENCY = "KES"
# IMPORTANT: Get your free API key from https://www.coingecko.com/en/developers/dashboard
COINGECKO_API_KEY = "CG-mH4qCJ8ns3ZjwwUjbrn4unZw"

# Fiat currencies we want to track
FIAT_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL", "ZAR", "AED", "SAR"]

# Crypto assets supported by CoinGecko (use their API IDs)
CRYPTO_IDS = [
    "bitcoin", "ethereum", "ripple", "solana", "cardano", "avalanche-2",
    "polkadot", "matic-network", "chainlink", "uniswap", "litecoin"
]
CRYPTO_MAP = {
    "bitcoin": "BTC", "ethereum": "ETH", "ripple": "XRP", "solana": "SOL",
    "cardano": "ADA", "avalanche-2": "AVAX", "polkadot": "DOT",
    "matic-network": "MATIC", "chainlink": "LINK", "uniswap": "UNI", "litecoin": "LTC"
}
# --- END CONFIGURATION ---

def create_session_with_retries():
    """Creates a requests Session that automatically retries on failure."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

def fetch_fiat_rates():
    """Fetch fiat rates against KES from currency-api.com, then invert to Foreign->KES."""
    url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/kes.json"
    print("Fetching fiat rates from currency-api.com...")
    try:
        session = create_session_with_retries()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "kes" in data:
            raw_rates = data["kes"]
            inverted_rates = {}
            for currency in FIAT_CURRENCIES:
                raw = raw_rates.get(currency.lower())
                if raw and raw > 0:
                    inverted_rates[currency] = 1 / raw
            return inverted_rates, "currency-api.com"
    except Exception as e:
        print(f"Fiat API failed: {e}")
    return None, None

def fetch_crypto_rates():
    """Fetch crypto rates against KES using CoinGecko API."""
    if COINGECKO_API_KEY == "YOUR_COINGECKO_API_KEY_HERE":
        print("ERROR: Please replace 'YOUR_COINGECKO_API_KEY_HERE' with your actual CoinGecko API key.")
        return None

    crypto_ids_param = ",".join(CRYPTO_IDS)
    url = "https://api.coingecko.com/api/v3/simple/price"
    headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
    params = {"ids": crypto_ids_param, "vs_currencies": BASE_CURRENCY.lower()}
    
    print("Fetching crypto rates from CoinGecko...")
    try:
        session = create_session_with_retries()
        response = session.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Crypto API Request Failed: {e}")
        return None

def save_to_csv(data, filename="exchange_rates_master.csv"):
    """Save combined fiat and crypto data to CSV."""
    if not data:
        print("No data to save.")
        return

    file_exists = False
    try:
        with open(filename, 'r') as f:
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'base_currency', 'asset', 'asset_type', 'rate', 'source']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)
    print(f"Data for {len(data)} assets saved to {filename}")

def main():
    all_asset_data = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. Fiat rates (inverted: 1 Foreign = X KES)
    fiat_rates, fiat_source = fetch_fiat_rates()
    if fiat_rates:
        for currency, rate_kes in fiat_rates.items():
            all_asset_data.append({
                'timestamp': timestamp,
                'base_currency': BASE_CURRENCY,
                'asset': currency,
                'asset_type': 'Fiat',
                'rate': rate_kes,
                'source': fiat_source
            })
            print(f"  1 {currency} = {rate_kes:.2f} {BASE_CURRENCY}")

    # 2. Crypto rates
    crypto_rates = fetch_crypto_rates()
    if crypto_rates:
        for coin_id, price_data in crypto_rates.items():
            symbol = CRYPTO_MAP.get(coin_id, coin_id.upper())
            price = price_data.get(BASE_CURRENCY.lower())
            if price:
                all_asset_data.append({
                    'timestamp': timestamp,
                    'base_currency': BASE_CURRENCY,
                    'asset': symbol,
                    'asset_type': 'Crypto',
                    'rate': price,
                    'source': 'CoinGecko'
                })
                print(f"  1 {symbol} = {price:,.2f} {BASE_CURRENCY}")

    # 3. Save to database and CSV
    db.init_db()
    if all_asset_data:
        db.save_rates(all_asset_data)
        db.log_run(len(all_asset_data), "success")
        save_to_csv(all_asset_data)
    else:
        db.log_run(0, "failed")
        print("No data fetched. Check your API key and internet connection.")

if __name__ == "__main__":
    main()
