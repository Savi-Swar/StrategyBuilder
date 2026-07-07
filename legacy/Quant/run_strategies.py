import sqlite3
import pandas as pd
import numpy as np
from utils import get_stock_data, store_results

STRATEGIES = [
    "EMA Crossover", "VWAP", "RSI Reversal", "Mean Reversion",
    "Golden Cross", "MACD", "Momentum", "SMA200", "Pairs Trading"
]

def run_strategy(ticker, strategy_name):
    """Executes the given strategy and stores results."""
    df = get_stock_data(ticker)
    if df is None or len(df) < 50:
        print(f"⚠️ Not enough data for {ticker}. Skipping {strategy_name}...")
        return

    # 🚀 Define strategy logic dynamically
    if strategy_name == "EMA Crossover":
        df["EMA50"] = df["close"].ewm(span=50).mean()
        df["EMA200"] = df["close"].ewm(span=200).mean()
        df["Signal"] = np.where(df["EMA50"] > df["EMA200"], 1, 0)

    elif strategy_name == "VWAP":
        df["VWAP"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
        df["Signal"] = np.where(df["close"] < df["VWAP"], 1, 0)

    elif strategy_name == "RSI Reversal":
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        df["Signal"] = np.where(df["RSI"] < 30, 1, 0)

    elif strategy_name == "SMA200":
        df["SMA200"] = df["close"].rolling(window=200).mean()
        df["Signal"] = np.where(df["close"] > df["SMA200"], 1, 0)

    elif strategy_name == "Momentum":
        df["SMA50"] = df["close"].rolling(window=50).mean()
        df["Signal"] = np.where(df["close"] > df["SMA50"], 1, 0)

    elif strategy_name == "MACD":
        df["EMA12"] = df["close"].ewm(span=12).mean()
        df["EMA26"] = df["close"].ewm(span=26).mean()
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = np.where(df["MACD"] > 0, 1, 0)

    df["Daily Return"] = df["close"].pct_change() * df["Signal"].shift(1)
    df.dropna(inplace=True)

    sharpe_ratio = (df["Daily Return"].mean() / df["Daily Return"].std()) * np.sqrt(252) if df["Daily Return"].std() != 0 else None
    total_return = df["Daily Return"].sum() * 100
    max_drawdown = (df["close"].cummax() - df["close"]).max() / df["close"].cummax().max() * 100 if not df.empty else None
    win_rate = (df["Daily Return"] > 0).mean() * 100 if not df.empty else None

    store_results(ticker, strategy_name, total_return, sharpe_ratio, max_drawdown, win_rate)

if __name__ == "__main__":
    tickers = ["MSFT", "NVDA", "META", "GOOGL", "^GSPC", "^DJI", "BTC-USD"]
    for ticker in tickers:
        for strategy in STRATEGIES:
            run_strategy(ticker, strategy)
