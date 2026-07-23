"""Cycle-4 data prefetch: EDGAR fundamentals for the PIT panel.

Pure I/O, no modeling — run in parallel with training jobs. Cached and
resumable (data/edgar_fundamentals.csv). ~5 tags x ~650 names at ~9 req/s.
Feature construction happens in the cycle-4 study script once the second
deep-research run has ranked the families.
"""

import pandas as pd

from quark import config
from quark.data.edgar import fetch_fundamentals_panel
from quark.data.loader import load_prices
from quark.data.quality import clean_panel, quality_report


def main() -> None:
    pit = pd.read_csv(config.REPORTS_DIR / "pit_membership.csv",
                      parse_dates=["month_end"])
    tickers = sorted(pit["ticker"].unique())
    prices = load_prices(tickers=tickers, start="2005-01-01")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    cache = config.REPORTS_DIR.parent / "data" / "edgar_fundamentals.csv"
    cache.parent.mkdir(exist_ok=True)
    fetch_fundamentals_panel(list(prices.columns), cache)


if __name__ == "__main__":
    main()
