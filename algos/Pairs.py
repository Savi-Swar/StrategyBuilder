import sqlite3
import pandas as pd
import numpy as np
from itertools import combinations
from statsmodels.tsa.stattools import coint
import warnings

# Database Paths
STOCK_DB_PATH = "Quark.db"
RESULTS_DB_PATH = "quant.db"

def get_stock_data(ticker):
    conn = sqlite3.connect(STOCK_DB_PATH)
    query = f"SELECT date, close FROM stocks WHERE ticker = '{ticker}' ORDER BY date ASC;"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    conn.close()
    return df

def store_results(ticker, strategy_name, total_return, sharpe_ratio, max_drawdown=None, win_rate=None):
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
    """, (ticker, strategy_name, total_return, sharpe_ratio, 
          max_drawdown if max_drawdown is not None else None, 
          win_rate if win_rate is not None else None))
    conn.commit()
    conn.close()
    print(f"✅ Stored {strategy_name} for {ticker}: {total_return:.2f}% Return, Sharpe {sharpe_ratio:.2f}")

def store_daily_returns_unified(ticker, strategy_name, daily_returns_list, db_path):
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

def is_cointegrated(df1, df2):
    common_dates = df1.index.intersection(df2.index)
    df1 = df1.loc[common_dates]
    df2 = df2.loc[common_dates]
    if len(df1) < 50 or len(df2) < 50:
        return False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            score, p_value, _ = coint(df1["close"], df2["close"], maxlag=5)
        return p_value < 0.05
    except Exception as e:
        print(f"⚠️ Cointegration test failed for pair: {df1.name}, {df2.name}. Error: {e}")
        return False

def find_cointegrated_pairs(tickers):
    valid_pairs = []
    for ticker1, ticker2 in combinations(tickers, 2):
        df1 = get_stock_data(ticker1)
        df2 = get_stock_data(ticker2)
        if is_cointegrated(df1, df2):
            valid_pairs.append((ticker1, ticker2))
    return valid_pairs

def pairs_trading_strategy(ticker1, ticker2):
    print(f"\n🚀 Running Pairs Trading Strategy for {ticker1} & {ticker2}...")

    df1 = get_stock_data(ticker1)
    df2 = get_stock_data(ticker2)

    common_dates = df1.index.intersection(df2.index)
    df1 = df1.loc[common_dates]
    df2 = df2.loc[common_dates]

    if not is_cointegrated(df1, df2):
        print(f"⚠️ {ticker1} & {ticker2} are NOT cointegrated. Skipping...")
        return

    df = df1.join(df2, lsuffix="_1", rsuffix="_2", how="inner").dropna()

    df["Hedge Ratio"] = df["close_1"].rolling(30).mean() / df["close_2"].rolling(30).mean()
    df.dropna(inplace=True)

    df["Spread"] = df["close_1"] - (df["close_2"] * df["Hedge Ratio"])
    df["Z-Score"] = (df["Spread"] - df["Spread"].rolling(20).mean()) / df["Spread"].rolling(20).std()

    df["Signal"] = 0
    df.loc[df["Z-Score"] > 1.5, "Signal"] = -1
    df.loc[df["Z-Score"] < -1.5, "Signal"] = 1
    df.loc[abs(df["Z-Score"]) < 0.5, "Signal"] = 0
    df["Signal"] = df["Signal"].ffill()

    df["Daily Return"] = (df["close_1"].pct_change() - df["close_2"].pct_change()) * df["Signal"].shift(1)
    df.dropna(inplace=True)

    sharpe_ratio = (df["Daily Return"].mean() / df["Daily Return"].std()) * np.sqrt(252) if df["Daily Return"].std() != 0 else None
    total_return = df["Daily Return"].sum() * 100 if not df.empty else None
    max_drawdown = (df["Spread"].cummax() - df["Spread"]).max() / df["Spread"].cummax().max() * 100 if not df.empty else None
    win_rate = (df["Daily Return"] > 0).mean() * 100 if not df.empty else None

    pair_name = f"{ticker1}-{ticker2}"
    store_results(pair_name, "Pairs Trading", total_return, sharpe_ratio, max_drawdown, win_rate)

    # ✅ Store Daily Returns
    daily_returns_list = list(zip(df.index, df["Daily Return"]))
    store_daily_returns_unified(pair_name, "Pairs Trading", daily_returns_list, RESULTS_DB_PATH)

    print("📊 Pairs Trading Strategy Results")
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

    valid_pairs = find_cointegrated_pairs(tickers)

    if not valid_pairs:
        print("🚫 No cointegrated pairs found. Exiting...")
    else:
        for ticker1, ticker2 in valid_pairs:
            pairs_trading_strategy(ticker1, ticker2)
