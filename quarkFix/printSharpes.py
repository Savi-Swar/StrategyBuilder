import sqlite3
import pandas as pd

DB_PATH = "quant.db"
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
def print_top_sharpes():
    conn = sqlite3.connect(DB_PATH)

    for ticker in tickers:
        print(f"\n📊 Top 3 Strategies for {ticker}")
        print("─────────────────────────────────────")

        query = """
            SELECT strategy, total_return, sharpe_ratio
            FROM strategy_results
            WHERE ticker = ?
            ORDER BY sharpe_ratio DESC
            LIMIT 7;
        """
        df = pd.read_sql(query, conn, params=(ticker,))

        if df.empty:
            print("⚠️ No data found.")
            continue

        for i, row in df.iterrows():
            print(f"{i+1}. {row['strategy']} → Return: {row['total_return']:.2f}%, Sharpe: {row['sharpe_ratio']:.2f}")
    
    conn.close()

if __name__ == "__main__":
    print_top_sharpes()
