import sqlite3
import pandas as pd
import numpy as np

STOCK_DB_PATH = "Quark.db"
RESULTS_DB_PATH = "quant.db"

def get_stock_data(ticker):
    """Fetches stock data from Quark.db."""
    conn = sqlite3.connect(STOCK_DB_PATH)
    query = f"SELECT date, close FROM stocks WHERE ticker = '{ticker}' ORDER BY date ASC;"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    df.drop_duplicates(subset="date", keep="last", inplace=True)
    df.set_index("date", inplace=True)
    conn.close()
    return df

def store_results(ticker, strategy_name, total_return, sharpe_ratio, max_drawdown=None, win_rate=None):
    """Stores summary stats in strategy_results table."""
    if total_return is None or sharpe_ratio is None:
        print(f"❌ Skipping {strategy_name} for {ticker}: Missing required fields.")
        return

    conn = sqlite3.connect(RESULTS_DB_PATH)
    cursor = conn.cursor()

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
    """, (ticker, strategy_name, total_return, sharpe_ratio, max_drawdown, win_rate))

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

def trend_following_strategy(ticker):
    print(f"\n🚀 Running Bollinger Band Strategy for {ticker}...")

    df = get_stock_data(ticker)
    if len(df) < 30:
        print(f"⚠️ Not enough data for {ticker}. Skipping...")
        return

    # Calculate Bollinger Bands
    df["MA20"] = df["close"].rolling(window=20).mean()
    df["STD20"] = df["close"].rolling(window=20).std()
    df["Upper"] = df["MA20"] + 2 * df["STD20"]
    df["Lower"] = df["MA20"] - 2 * df["STD20"]

    df["Position"] = 0
    holding = False

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        prev_price = df["close"].iloc[i - 1]
        lower = df["Lower"].iloc[i]
        prev_lower = df["Lower"].iloc[i - 1]
        ma = df["MA20"].iloc[i]
        prev_ma = df["MA20"].iloc[i - 1]

        if not holding and prev_price > prev_lower and price < lower:
            df.iat[i, df.columns.get_loc("Position")] = 1
            holding = True
        elif holding and prev_price < prev_ma and price > ma:
            df.iat[i, df.columns.get_loc("Position")] = 0
            holding = False
        else:
            df.iat[i, df.columns.get_loc("Position")] = df["Position"].iloc[i - 1]

    df["Daily Return"] = df["close"].pct_change() * df["Position"].shift(1)
    df.dropna(inplace=True)

    sharpe_ratio = (df["Daily Return"].mean() / df["Daily Return"].std()) * np.sqrt(252) if df["Daily Return"].std() != 0 else 0
    total_return = df["Daily Return"].sum() * 100
    max_drawdown = (df["close"].cummax() - df["close"]).max() / df["close"].cummax().max() * 100 if not df.empty else None
    win_rate = (df["Daily Return"] > 0).mean() * 100 if not df.empty else None

    store_results(ticker, "Bollinger", total_return, sharpe_ratio, max_drawdown, win_rate)

    daily_returns_list = list(zip(df.index, df["Daily Return"]))
    store_daily_returns_unified(ticker, "Bollinger", daily_returns_list, RESULTS_DB_PATH)

    print("📊 Bollinger Band Strategy Results")
    print("───────────────────────────────────────────────")
    print(f"💰 Total Return:       {total_return:.2f}%")
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
        trend_following_strategy(ticker)
