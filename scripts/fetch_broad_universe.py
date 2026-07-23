"""Cycle 10 data layer: broad US common-stock daily panel, 2012+.

Universe: every common stock in the official NASDAQ symbol directories
(nasdaqlisted.txt + otherlisted.txt), filtered to exclude ETFs, test
issues, warrants/units/rights/preferred/depositary shares. No index
membership needed — eligibility inside the backtest is a CAUSAL rolling
dollar-volume screen, which is PIT-safe by construction.

HONESTY NOTE (before any result): this is a CURRENT-listing panel — names
delisted before today are absent, the same upward bias class as the old
equity current-members panel (measured there at roughly -0.2 to -0.3
Sharpe). Every cycle-10 result is an upper bound until a delisting-bias
measurement exists for this panel. Say it every time.

Output: data/broad_prices.parquet, data/broad_volumes.parquet
"""

import io
import urllib.request

import pandas as pd
import yfinance as yf

from quark import config

BAD_NAME = ("Warrant", "Unit", "Right", "Preferred", "Depositary",
            " ETN", "Notes", "Trust Units")


def load_symbols() -> list[str]:
    def fetch(url):
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode()

    nq = pd.read_csv(io.StringIO(fetch(
        "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt")),
        sep="|")
    nq = nq[(nq["ETF"] == "N") & (nq["Test Issue"] == "N")]
    nq_sym = nq[~nq["Security Name"].str.contains("|".join(BAD_NAME), na=False)]["Symbol"]

    ol = pd.read_csv(io.StringIO(fetch(
        "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt")),
        sep="|")
    ol = ol[(ol["ETF"] == "N") & (ol["Test Issue"] == "N")]
    ol_sym = ol[~ol["Security Name"].str.contains("|".join(BAD_NAME), na=False)]["ACT Symbol"]

    syms = sorted({s for s in pd.concat([nq_sym, ol_sym]).dropna()
                   if isinstance(s, str) and s.isalpha() and len(s) <= 5})
    return syms


def main() -> None:
    symbols = load_symbols()
    print(f"{len(symbols)} common-stock symbols")
    closes, vols = [], []
    chunk = 200
    for i in range(0, len(symbols), chunk):
        batch = symbols[i:i + chunk]
        df = yf.download(batch, start="2012-01-01", auto_adjust=True,
                         progress=False, threads=True)
        if df.empty:
            continue
        closes.append(df["Close"])
        vols.append(df["Close"] * df["Volume"])   # dollar volume
        print(f"  {min(i + chunk, len(symbols))}/{len(symbols)}")

    prices = pd.concat(closes, axis=1)
    volumes = pd.concat(vols, axis=1)
    # drop all-NaN columns (never had data)
    prices = prices.dropna(axis=1, how="all")
    volumes = volumes[prices.columns]
    data_dir = config.REPORTS_DIR.parent / "data"
    prices.to_parquet(data_dir / "broad_prices.parquet")
    volumes.to_parquet(data_dir / "broad_volumes.parquet")
    print(f"Panel: {prices.shape[1]} names x {prices.shape[0]} days")


if __name__ == "__main__":
    main()
