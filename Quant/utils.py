import sqlite3
import pandas as pd

STOCK_DB_PATH = "Quark.db"
RESULTS_DB_PATH = "quant.db"

def get_stock_data(ticker):
    conn = sqlite3.connect(STOCK_DB_PATH)
    query = f"SELECT date, close, volume FROM stocks WHERE ticker = '{ticker}' ORDER BY date ASC;"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    conn.close()
    return df

def store_results(ticker, strategy, total_return, sharpe_ratio, max_drawdown=None, win_rate=None):
    conn = sqlite3.connect(RESULTS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO strategy_results VALUES (?, ?, ?, ?, ?, ?)", (ticker, strategy, total_return, sharpe_ratio, max_drawdown, win_rate))
    conn.commit()
    conn.close()
