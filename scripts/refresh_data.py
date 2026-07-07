"""Refresh all market data: the 44-instrument multi-asset universe (Study 1)
and the S&P 500 equity universe (Study 2)."""

import argparse

from quark.data.quality import count_db_duplicates, quality_report
from quark.data.loader import load_prices
from quark.data.refresh import fetch_sp500_universe, refresh_tickers
from quark.universe import load_universe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-multi", action="store_true", help="skip the 44-ticker refresh")
    ap.add_argument("--skip-equities", action="store_true", help="skip the S&P 500 pull")
    args = ap.parse_args()

    if not args.skip_multi:
        uni = load_universe()
        print(f"Refreshing {len(uni)} multi-asset tickers...")
        refresh_tickers(list(uni.index))

    if not args.skip_equities:
        print("Fetching S&P 500 universe...")
        fetch_sp500_universe()

    print(f"\nDB duplicate (ticker,date) rows: {count_db_duplicates()}")
    uni = load_universe()
    prices = load_prices(tickers=list(uni.index))
    print(f"Multi-asset panel: {prices.shape[0]} days x {prices.shape[1]} tickers, "
          f"{prices.index.min().date()} -> {prices.index.max().date()}")
    print(quality_report(prices).summary())


if __name__ == "__main__":
    main()
