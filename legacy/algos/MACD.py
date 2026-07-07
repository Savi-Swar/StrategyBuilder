import sqlite3
import pandas as pd
import numpy as np

# Database Paths
STOCK_DB_PATH = "Quark.db"   # Stock price data
RESULTS_DB_PATH = "quant.db" # Store strategy results

def get_stock_data(ticker):
    """Fetches stock data from Quark.db."""
    conn = sqlite3.connect(STOCK_DB_PATH)
    query = f"SELECT date, close FROM stocks WHERE ticker = '{ticker}' ORDER BY date ASC;"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    conn.close()
    return df

def store_results(ticker, strategy_name, total_return, sharpe_ratio, max_drawdown=None, win_rate=None):
    """Stores strategy results in quant.db, handling NULL values properly."""
    if total_return is None or sharpe_ratio is None:
        print(f"❌ Skipping {strategy_name} for {ticker}: Missing required fields.")
        return
    
    conn = sqlite3.connect(RESULTS_DB_PATH)
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strategy TEXT NOT NULL,
            total_return REAL NOT NULL,
            sharpe_ratio REAL NOT NULL,
            max_drawdown REAL,
            win_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO strategy_results (ticker, strategy, total_return, sharpe_ratio, max_drawdown, win_rate)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ticker, strategy_name, total_return, sharpe_ratio, 
          max_drawdown if max_drawdown is not None else None, 
          win_rate if win_rate is not None else None))
    
    conn.commit()
    conn.close()
    print(f"✅ Stored {strategy_name} for {ticker}: {total_return:.2f}% Return, Sharpe {sharpe_ratio:.2f}")

def store_daily_returns_unified(ticker, strategy_name, daily_returns_list, db_path):
    """Stores daily returns in unified table with overwrite per ticker+strategy."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_returns_table (
            date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            strategy TEXT NOT NULL,
            return REAL NOT NULL,
            PRIMARY KEY (date, ticker, strategy)
        )
    """)

    cursor.execute("""
        DELETE FROM daily_returns_table WHERE ticker = ? AND strategy = ?
    """, (ticker, strategy_name))

    rows_to_insert = [(str(date), ticker, strategy_name, float(ret)) for date, ret in daily_returns_list]
    cursor.executemany("""
        INSERT INTO daily_returns_table (date, ticker, strategy, return) VALUES (?, ?, ?, ?)
    """, rows_to_insert)

    conn.commit()
    conn.close()
    print(f"🧼 Replaced {len(rows_to_insert)} daily returns for {ticker} [{strategy_name}]")

def macd_strategy(ticker):
    print(f"\n🚀 Running MACD Strategy for {ticker}...")

    df = get_stock_data(ticker)
    if len(df) < 50:
        print(f"⚠️ Not enough data for {ticker}. Skipping...")
        return

    df["EMA12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    
    df["Signal"] = np.where(df["MACD"] > 0, 1, 0)
    df["Signal"] = np.where(df["MACD"] < 0, 0, df["Signal"])
    df["Daily Return"] = df["close"].pct_change() * df["Signal"].shift(1)
    df.dropna(inplace=True)
    
    sharpe_ratio = (df["Daily Return"].mean() / df["Daily Return"].std()) * np.sqrt(252) if df["Daily Return"].std() != 0 else None
    total_return = df["Daily Return"].sum() * 100 if not df.empty else None
    max_drawdown = (df["close"].cummax() - df["close"]).max() / df["close"].cummax().max() * 100 if not df.empty else None
    win_rate = (df["Daily Return"] > 0).mean() * 100 if not df.empty else None

    # Store results
    store_results(ticker, "MACD", total_return, sharpe_ratio, max_drawdown, win_rate)

    # Store daily returns
    daily_returns_list = list(zip(df.index, df["Daily Return"]))
    store_daily_returns_unified(ticker, "MACD", daily_returns_list, RESULTS_DB_PATH)

    print("📊 MACD Strategy Results")
    print("───────────────────────────────────────────────")
    print(f"💰 Total Return:       {total_return:.2f}% 📈")
    print(f"⚡ Sharpe Ratio:       {sharpe_ratio:.2f}")
    if max_drawdown is not None:
        print(f"🔻 Max Drawdown:       {max_drawdown:.2f}%")
    if win_rate is not None:
        print(f"✅ Win Rate:           {win_rate:.2f}%")
    print("───────────────────────────────────────────────\n")

if __name__ == "__main__":
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

    for ticker in tickers:
        macd_strategy(ticker)
