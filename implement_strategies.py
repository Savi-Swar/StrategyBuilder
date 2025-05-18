import sqlite3
import os
import importlib
import inspect
import pandas as pd
import numpy as np

# Database Paths
DAILY_RETURNS_DB = "strategy_dailyreturns.db"
STRATEGY_DIR = "algos"

# ✅ Setup Database
def setup_database():
    """Creates the daily returns table if it does not exist."""
    conn = sqlite3.connect(DAILY_RETURNS_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_dailyreturns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strategy TEXT NOT NULL,
            date DATE NOT NULL,
            daily_return REAL NOT NULL,
            sharpe_ratio REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# ✅ Store Daily Returns
def store_daily_returns(ticker, strategy_name, daily_returns):
    """Stores daily returns for a given strategy and stock in the database."""
    conn = sqlite3.connect(DAILY_RETURNS_DB)
    cursor = conn.cursor()

    for date, ret in daily_returns.iterrows():
        cursor.execute("""
            INSERT INTO strategy_dailyreturns (ticker, strategy, date, daily_return)
            VALUES (?, ?, ?, ?)
        """, (ticker, strategy_name, date, ret[0]))

    conn.commit()
    conn.close()

# ✅ Calculate Sharpe Ratios
def calculate_sharpe_ratios():
    """Calculates Sharpe ratios for each stock and updates the database."""
    conn = sqlite3.connect(DAILY_RETURNS_DB)
    query = "SELECT ticker, daily_return FROM strategy_dailyreturns"
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("⚠️ No daily returns found. Cannot calculate Sharpe ratios.")
        return

    # Compute Sharpe ratio per stock
    sharpe_ratios = df.groupby("ticker")["daily_return"].apply(
        lambda x: (x.mean() / x.std()) * np.sqrt(252) if x.std() != 0 else 0
    ).reset_index()
    sharpe_ratios.columns = ["ticker", "sharpe_ratio"]

    # Store Sharpe ratios in the database
    conn = sqlite3.connect(DAILY_RETURNS_DB)
    cursor = conn.cursor()
    for _, row in sharpe_ratios.iterrows():
        cursor.execute("""
            UPDATE strategy_dailyreturns 
            SET sharpe_ratio = ? 
            WHERE ticker = ? 
        """, (row["sharpe_ratio"], row["ticker"]))

    conn.commit()
    conn.close()
    print("✅ Updated Sharpe Ratios in Database.")

# ✅ Run Strategy
def run_strategy(strategy_function, ticker):
    """Executes a strategy function and stores results in the database."""
    try:
        daily_returns = strategy_function(ticker)  # ✅ Expecting a DataFrame of daily returns

        if daily_returns is not None:
            store_daily_returns(ticker, strategy_function.__name__, daily_returns)
            print(f"✅ {strategy_function.__name__} completed for {ticker}")

    except Exception as e:
        print(f"❌ Error in {strategy_function.__name__}: {e}")

# ✅ Run All Strategies
def execute_all_strategies():
    """Dynamically imports and runs all strategies from `algos/` directory."""
    tickers = ["MSFT", "NVDA", "META", "GOOGL", "^GSPC", "^DJI", "BTC-USD"]
    setup_database()

    strategy_files = [f for f in os.listdir(STRATEGY_DIR) if f.endswith(".py") and f != "__init__.py"]

    for strategy_file in strategy_files:
        module_name = strategy_file[:-3]  # Remove .py extension
        try:
            strategy_module = importlib.import_module(f"{STRATEGY_DIR}.{module_name}")

            # Find all functions with "strategy" in their name
            strategy_functions = [
                func for name, func in inspect.getmembers(strategy_module, inspect.isfunction)
                if "strategy" in name.lower()
            ]

            for strategy_function in strategy_functions:
                for ticker in tickers:
                    run_strategy(strategy_function, ticker)

        except Exception as e:
            print(f"⚠️ Failed to import {strategy_file}: {e}")

    # ✅ After running all strategies, calculate Sharpe Ratios
    calculate_sharpe_ratios()

# ✅ Run the strategy runner
if __name__ == "__main__":
    execute_all_strategies()
