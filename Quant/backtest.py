import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from portfolio_optimizer import optimize_portfolio, get_strategy_returns

STOCK_DB_PATH = "Quark.db"

def get_benchmark_returns():
    """Fetches S&P 500 returns from database."""
    conn = sqlite3.connect(STOCK_DB_PATH)
    query = "SELECT date, close FROM stocks WHERE ticker = '^GSPC' ORDER BY date ASC;"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df["Return"] = df["close"].pct_change()
    conn.close()
    return df["Return"].dropna()

def backtest_portfolio():
    """Backtests optimized portfolio and compares to S&P 500."""
    weights, strategies = optimize_portfolio()
    returns = get_strategy_returns()
    portfolio_returns = returns.dot(weights)

    sp500_returns = get_benchmark_returns()

    # Compare performance
    plt.figure(figsize=(10, 5))
    portfolio_returns.cumsum().plot(label="Optimized Portfolio", color="b")
    sp500_returns.cumsum().plot(label="S&P 500", color="r")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title("Portfolio vs S&P 500")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    backtest_portfolio()
