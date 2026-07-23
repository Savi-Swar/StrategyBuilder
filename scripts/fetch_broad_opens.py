"""Overnight/intraday decomposition data: Open prices for the broad panel."""
import pandas as pd, yfinance as yf
from quark import config
prices = pd.read_parquet(config.REPORTS_DIR.parent / "data" / "broad_prices.parquet")
symbols = list(prices.columns)
parts = []
for i in range(0, len(symbols), 200):
    df = yf.download(symbols[i:i+200], start="2012-01-01", auto_adjust=True, progress=False, threads=True)
    if not df.empty:
        parts.append(df["Open"])
    print(f"  {min(i+200, len(symbols))}/{len(symbols)}", flush=True)
opens = pd.concat(parts, axis=1).dropna(axis=1, how="all")
opens.to_parquet(config.REPORTS_DIR.parent / "data" / "broad_opens.parquet")
print(f"Opens: {opens.shape[1]} names x {opens.shape[0]} days")
