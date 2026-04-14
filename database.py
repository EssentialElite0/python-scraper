import sqlite3
from datetime import datetime

DB_FILE = "market_history.db"

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            asset TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            rate REAL NOT NULL,
            source TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time DATETIME NOT NULL,
            assets_fetched INTEGER,
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_rates(data):
    """Save a batch of rates to the database."""
    if not data:
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for entry in data:
        cursor.execute('''
            INSERT INTO rates_history (timestamp, asset, asset_type, rate, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry['timestamp'], entry['asset'], entry['asset_type'], entry['rate'], entry['source']))
    
    conn.commit()
    conn.close()
    print(f"✅ Saved {len(data)} rates to database.")

def log_run(assets_count, status="success"):
    """Log a scraper execution run."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO runs (run_time, assets_fetched, status)
        VALUES (?, ?, ?)
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), assets_count, status))
    conn.commit()
    conn.close()

def get_latest_rates():
    """Get the most recent rate for each asset with full details."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r1.asset, r1.asset_type, r1.rate, r1.source, r1.timestamp
        FROM rates_history r1
        INNER JOIN (
            SELECT asset, MAX(timestamp) as max_ts
            FROM rates_history
            GROUP BY asset
        ) r2 ON r1.asset = r2.asset AND r1.timestamp = r2.max_ts
        ORDER BY r1.asset_type, r1.asset
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_assets():
    """List all unique assets in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT asset, asset_type FROM rates_history ORDER BY asset_type, asset")
    rows = cursor.fetchall()
    conn.close()
    return rows