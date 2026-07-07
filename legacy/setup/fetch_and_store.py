import sqlite3
import yfinance as yf
import pandas as pd

# ✅ List of instruments with correct Yahoo Finance tickers
tickers = [
    # FX Pairs
    "EURUSD=X", "GBPUSD=X", "JPY=X", "AUDUSD=X", "CAD=X", "CHF=X", "NZDUSD=X",
    "THB=X", "KRW=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "CHFJPY=X",
    "USDMXN=X", "USDINR=X", "USDZAR=X", "CNH=X",

    # Equity Indices
    "^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^N225", "^HSI", "^FCHI",
    "^AXJO", "^GDAXI", "^KS11", "^STI",

    # Commodities
    "GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "BZ=F",

    # Bonds & Treasuries
    "ZB=F", "ZN=F", "ZF=F", "^TNX",

    # Cryptocurrencies
    "BTC-USD", "ETH-USD",

    # Stocks
    "MSFT", "NVDA", "META", "GOOGL"
]

# ✅ Date range (20 years of data)
start_date = "2004-01-01"
end_date = "2025-03-01"

# ✅ Connect to SQLite database
conn = sqlite3.connect("Quark.db")
cursor = conn.cursor()

# ✅ Create table if it doesn’t exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER
    )
""")
conn.commit()

# ✅ Function to fetch and insert data
def fetch_and_store(ticker):
    print(f"📡 Fetching data for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        # ✅ Ensure data is available
        if df.empty:
            print(f"⚠️ No data found for {ticker}!")
            return

        # ✅ Reset index to get 'Date' as a column
        df.reset_index(inplace=True)

        # ✅ Insert data into SQLite
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO stocks (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ticker, row["Date"].strftime("%Y-%m-%d"), row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]))

        conn.commit()
        print(f"✅ Data for {ticker} stored successfully!")

    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")

# ✅ Fetch and store data for all tickers
for ticker in tickers:
    fetch_and_store(ticker)

# ✅ Close database connection
conn.close()
print("🚀 All data fetched and stored successfully!")
