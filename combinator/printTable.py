import sqlite3
import os
import pandas as pd
from collections import Counter

# Set path to quant.db
quant_db_path = "quant.db"

def print_daily_return_tables_info(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find all daily return tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'daily_returns_%'")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"🔍 Found {len(tables)} daily return tables in {os.path.basename(db_path)}\n")

    for table in tables:
        print(f"📈 {table}")
        
        # Print schema
        cursor.execute(f"PRAGMA table_info({table})")
        schema = cursor.fetchall()
        print("   📐 Schema:")
        for col in schema:
            print(f"     - {col}")

        df = pd.read_sql(f"SELECT * FROM {table}", conn)

        if df.empty:
            print("   ⚠️ No data found.\n")
            continue

        df['date'] = pd.to_datetime(df['date'])

        # Summary stats
        start = df['date'].min().date()
        end = df['date'].max().date()
        tickers = df['ticker'].nunique()

        print(f"   ▶️ Start Date: {start}")
        print(f"   ⏹️  End Date:   {end}")
        print(f"   📊 Tickers:    {tickers}")
        print(f"   🧾 Rows:       {len(df)}")

        # Check for duplicates (date + ticker + strategy)
        if {'strategy', 'ticker', 'date'}.issubset(df.columns):
            key_counts = df.groupby(['date', 'ticker', 'strategy']).size()
            dupes = key_counts[key_counts > 1]
            if not dupes.empty:
                print(f"   ❗ Found {len(dupes)} duplicate (date, ticker, strategy) keys!")
            else:
                print("   ✅ No duplicates in (date, ticker, strategy).")

        print()

    conn.close()

# Run it
print_daily_return_tables_info(quant_db_path)
