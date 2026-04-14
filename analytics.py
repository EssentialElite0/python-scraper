import database as db
from datetime import datetime, timedelta
import json
import os

PORTFOLIO_FILE = "portfolio.json"
ALERTS_FILE = "alerts.json"

# ==================== WAVE 1 & 2: BASIC ANALYTICS ====================
def show_latest():
    """Display the most recent rates for all assets."""
    print("\n" + "="*50)
    print("   📊 LATEST MARKET RATES (KES)")
    print("="*50)
    
    rates = db.get_latest_rates()
    if not rates:
        print("📭 No data in database. Run scraper.py first.")
        return
    
    for asset, asset_type, rate, source, timestamp in rates:
        if asset_type == "Fiat":
            print(f"  💵 1 {asset:<5} = KES {rate:>10,.2f}  | {source}")
        else:
            print(f"  🪙 1 {asset:<5} = KES {rate:>10,.2f}  | {source}")

def show_stats():
    """Display min, max, average for a specific asset."""
    assets = db.get_all_assets()
    if not assets:
        print("📭 No data in database. Run scraper.py first.")
        return
    
    print("\nAvailable assets:")
    for i, (asset, atype) in enumerate(assets, 1):
        print(f"  {i}. {asset} ({atype})")
    
    try:
        choice = int(input("\nAsset number: ").strip()) - 1
        asset = assets[choice][0]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return
    
    conn = db.sqlite3.connect(db.DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT MIN(rate), MAX(rate), AVG(rate), COUNT(*)
        FROM rates_history
        WHERE asset = ?
    ''', (asset,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[3] > 0:
        print(f"\n--- {asset} Statistics (from {row[3]} data points) ---")
        print(f"  Minimum: KES {row[0]:,.2f}")
        print(f"  Maximum: KES {row[1]:,.2f}")
        print(f"  Average: KES {row[2]:,.2f}")
    else:
        print(f"📭 No data for {asset}.")

# ==================== WAVE 3: TRENDS ENGINE ====================
def calculate_trend(asset, days=7):
    """Calculate trend metrics for an asset over specified days."""
    conn = db.sqlite3.connect(db.DB_FILE)
    cursor = conn.cursor()
    
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        SELECT timestamp, rate FROM rates_history
        WHERE asset = ? AND timestamp >= ?
        ORDER BY timestamp ASC
    ''', (asset, cutoff))
    
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) < 2:
        return None
    
    first_rate = rows[0][1]
    last_rate = rows[-1][1]
    
    absolute_change = last_rate - first_rate
    percent_change = (absolute_change / first_rate) * 100
    
    # Volatility (standard deviation of percent changes between consecutive readings)
    pct_changes = []
    for i in range(1, len(rows)):
        pct = ((rows[i][1] - rows[i-1][1]) / rows[i-1][1]) * 100
        pct_changes.append(pct)
    
    mean_pct = sum(pct_changes) / len(pct_changes)
    variance = sum((x - mean_pct) ** 2 for x in pct_changes) / len(pct_changes)
    volatility = variance ** 0.5
    
    if percent_change > 1:
        direction = "📈 KES weakening (asset getting expensive)"
    elif percent_change < -1:
        direction = "📉 KES strengthening (asset getting cheaper)"
    else:
        direction = "➡️ Stable"
    
    return {
        'asset': asset,
        'days': days,
        'data_points': len(rows),
        'first_rate': first_rate,
        'last_rate': last_rate,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'volatility': volatility,
        'direction': direction
    }

def show_trends():
    """Display trends for selected assets."""
    print("\n" + "="*60)
    print("   📈 CURRENCY TRENDS ENGINE")
    print("="*60)
    
    assets = db.get_all_assets()
    if not assets:
        print("📭 No data in database. Run scraper.py first.")
        return
    
    print("\nSelect assets to analyze (comma-separated numbers, or 'all'):")
    for i, (asset, atype) in enumerate(assets, 1):
        print(f"  {i}. {asset} ({atype})")
    
    choice = input("\nSelection: ").strip().lower()
    
    days_str = input("Analysis period in days [7]: ").strip()
    try:
        days = int(days_str) if days_str else 7
    except ValueError:
        days = 7
    
    selected = []
    if choice == 'all':
        selected = [a[0] for a in assets]
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [assets[i][0] for i in indices if 0 <= i < len(assets)]
        except (ValueError, IndexError):
            print("❌ Invalid selection.")
            return
    
    print(f"\n--- Trend Analysis ({days} days) ---")
    print(f"{'Asset':<8} {'Direction':<32} {'Change %':<12} {'Volatility':<12}")
    print("-"*70)
    
    for asset in selected:
        trend = calculate_trend(asset, days)
        if trend:
            arrow = "↑" if trend['percent_change'] > 0 else "↓" if trend['percent_change'] < 0 else "→"
            print(f"{asset:<8} {trend['direction']:<32} {arrow} {abs(trend['percent_change']):>6.2f}%    {trend['volatility']:>6.2f}%")
        else:
            print(f"{asset:<8} Insufficient data (need at least 2 points in period)")

# ==================== WAVE 4: ARBITRAGE & PORTFOLIO ====================
def find_arbitrage():
    """Scan for cross-rate arbitrage opportunities."""
    print("\n" + "="*60)
    print("   💹 CROSS-RATE ARBITRAGE SCANNER")
    print("="*60)
    
    rates = db.get_latest_rates()
    if not rates:
        print("📭 No data. Run scraper.py first.")
        return
    
    rate_dict = {r[0]: r[2] for r in rates}
    
    # BTC arbitrage via USD
    if 'BTC' in rate_dict and 'USD' in rate_dict:
        btc_kes_direct = rate_dict['BTC']
        print("\n--- BTC Cross-Check ---")
        print(f"BTC/KES Direct:        KES {btc_kes_direct:,.2f}")
        print("⚠️  Full arbitrage requires BTC/USD market rate. Feature ready for integration.")
    
    # Fiat cross-rates
    if all(k in rate_dict for k in ['USD', 'EUR', 'GBP']):
        usd = rate_dict['USD']
        eur = rate_dict['EUR']
        gbp = rate_dict['GBP']
        
        eur_usd_implied = eur / usd
        gbp_usd_implied = gbp / usd
        eur_gbp_implied = eur / gbp
        
        print("\n--- Fiat Implied Cross Rates ---")
        print(f"EUR/USD (implied): {eur_usd_implied:.4f}")
        print(f"GBP/USD (implied): {gbp_usd_implied:.4f}")
        print(f"EUR/GBP (implied): {eur_gbp_implied:.4f}")
        print("(Compare with actual market cross rates for opportunities)")

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_portfolio(pf):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(pf, f, indent=2)

def manage_portfolio():
    """Add/remove holdings."""
    pf = load_portfolio()
    print("\n--- Portfolio Manager ---")
    print("Current holdings:")
    if pf:
        for asset, amount in pf.items():
            print(f"  {asset}: {amount}")
    else:
        print("  (Empty)")
    
    print("\n1. Add/Update")
    print("2. Remove")
    print("3. Back")
    choice = input("Choice: ").strip()
    
    if choice == '1':
        assets = db.get_all_assets()
        for i, (asset, _) in enumerate(assets, 1):
            print(f"  {i}. {asset}")
        try:
            idx = int(input("Asset number: ").strip()) - 1
            asset = assets[idx][0]
            amount = float(input(f"Amount of {asset} held: ").strip())
            pf[asset] = amount
            save_portfolio(pf)
            print(f"✅ Updated {asset}: {amount}")
        except (ValueError, IndexError):
            print("❌ Invalid input.")
    elif choice == '2':
        asset = input("Asset to remove: ").strip().upper()
        if asset in pf:
            del pf[asset]
            save_portfolio(pf)
            print(f"✅ Removed {asset}.")
        else:
            print("❌ Not found.")

def value_portfolio():
    """Calculate total portfolio value in KES."""
    pf = load_portfolio()
    if not pf:
        print("📭 Portfolio empty. Use 'Manage Portfolio' to add holdings.")
        return
    
    rates = db.get_latest_rates()
    rate_dict = {r[0]: r[2] for r in rates}
    
    print("\n" + "="*60)
    print("   💰 PORTFOLIO VALUATION (KES)")
    print("="*60)
    print(f"{'Asset':<8} {'Holding':<14} {'Rate (KES)':<14} {'Value (KES)':<14}")
    print("-"*56)
    
    total = 0
    for asset, amount in pf.items():
        if asset in rate_dict:
            rate = rate_dict[asset]
            value = amount * rate
            total += value
            print(f"{asset:<8} {amount:<14,.4f} {rate:<14,.2f} {value:<14,.2f}")
        else:
            print(f"{asset:<8} {amount:<14} {'N/A':<14} {'N/A':<14}")
    
    print("-"*56)
    print(f"{'TOTAL':<8} {'':<14} {'':<14} {total:<14,.2f}")
    print(f"📅 Valued at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==================== WAVE 5: ALERT SYSTEM ====================
def load_alerts():
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_alerts(alerts):
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)

def create_alert():
    """Create a new price alert."""
    print("\n--- Create Price Alert ---")
    
    assets = db.get_all_assets()
    if not assets:
        print("📭 No assets in database.")
        return
    
    for i, (asset, atype) in enumerate(assets, 1):
        print(f"  {i}. {asset} ({atype})")
    
    try:
        idx = int(input("Asset number: ").strip()) - 1
        asset = assets[idx][0]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return
    
    try:
        threshold = float(input("Threshold price (KES): ").strip())
    except ValueError:
        print("❌ Invalid price.")
        return
    
    condition = input("Alert when price goes [above/below]: ").strip().lower()
    if condition not in ['above', 'below']:
        print("❌ Must be 'above' or 'below'.")
        return
    
    alerts = load_alerts()
    alerts.append({
        'asset': asset,
        'threshold': threshold,
        'condition': condition,
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    save_alerts(alerts)
    print(f"✅ Alert created: {asset} {condition} KES {threshold:,.2f}")

def check_alerts():
    """Check all alerts against latest rates."""
    print("\n--- Checking Alerts ---")
    
    rates = db.get_latest_rates()
    if not rates:
        print("📭 No rates data.")
        return
    
    rate_dict = {r[0]: r[2] for r in rates}
    alerts = load_alerts()
    
    if not alerts:
        print("📭 No active alerts.")
        return
    
    triggered = []
    remaining = []
    
    for alert in alerts:
        asset = alert['asset']
        if asset not in rate_dict:
            remaining.append(alert)
            continue
        
        current = rate_dict[asset]
        cond = alert['condition']
        threshold = alert['threshold']
        
        if (cond == 'above' and current > threshold) or (cond == 'below' and current < threshold):
            print(f"🚨 ALERT TRIGGERED: {asset} is {cond} KES {threshold:,.2f}")
            print(f"   Current rate: KES {current:,.2f}")
            triggered.append(alert)
        else:
            remaining.append(alert)
    
    if triggered:
        save_alerts(remaining)
        print(f"\n✅ {len(triggered)} alert(s) triggered and removed.")
    else:
        print("✅ No alerts triggered.")

def manage_alerts():
    """View and delete existing alerts."""
    alerts = load_alerts()
    
    if not alerts:
        print("📭 No active alerts.")
        return
    
    print("\n--- Active Alerts ---")
    for i, alert in enumerate(alerts, 1):
        print(f"{i}. {alert['asset']} {alert['condition']} KES {alert['threshold']:,.2f} (created {alert['created']})")
    
    choice = input("\nDelete alert number (or Enter to skip): ").strip()
    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(alerts):
                deleted = alerts.pop(idx)
                save_alerts(alerts)
                print(f"✅ Deleted alert for {deleted['asset']}.")
        except ValueError:
            pass

# ==================== MAIN MENU ====================
def main():
    db.init_db()
    
    while True:
        print("\n" + "="*50)
        print("   📈 KES MARKET ANALYTICS")
        print("="*50)
        print("1. View Latest Rates")
        print("2. View Asset Statistics (Min/Max/Avg)")
        print("3. Trends Engine (Direction & Volatility)")
        print("4. Arbitrage Scanner")
        print("5. Portfolio Tracker")
        print("6. Alert System")
        print("7. Exit")
        print("-"*50)
        
        choice = input("Choice: ").strip()
        
        if choice == '1':
            show_latest()
        elif choice == '2':
            show_stats()
        elif choice == '3':
            show_trends()
        elif choice == '4':
            find_arbitrage()
        elif choice == '5':
            print("\n--- Portfolio ---")
            print("1. Manage Holdings")
            print("2. Value Portfolio")
            sub = input("Choice: ").strip()
            if sub == '1':
                manage_portfolio()
            elif sub == '2':
                value_portfolio()
        elif choice == '6':
            print("\n--- Alert System ---")
            print("1. Create Alert")
            print("2. Check Alerts")
            print("3. Manage Alerts")
            sub = input("Choice: ").strip()
            if sub == '1':
                create_alert()
            elif sub == '2':
                check_alerts()
            elif sub == '3':
                manage_alerts()
        elif choice == '7':
            print("👋 Analytics signing off.")
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    main()