"""One-time: seed Vig's ledger with genuine walk-forward (out-of-sample)
predictions from the backtest, then score everything whose horizon has
completed. Gives the health panel years of real history from day one."""

from quark.data.loader import load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import load_sp500_tickers
from quark.insights.ledger import record_predictions, update_realized
from quark.ml.xsec import run_xsec_strategy

WEEKS = 156  # ~3 years of walk-forward history


def main() -> None:
    tickers = load_sp500_tickers()
    prices = load_prices(tickers=tickers, start="2005-01-01")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    volumes = load_prices(tickers=tickers, start="2005-01-01",
                          field="volume").reindex(prices.index)

    print("Running walk-forward to extract OOS predictions...")
    res = run_xsec_strategy(prices, volumes)
    preds = res.predictions.tail(WEEKS)

    added = 0
    for as_of, row in preds.iterrows():
        added += record_predictions(as_of, row.dropna(), source="walkforward")
    print(f"Recorded {added} walk-forward weeks (skipped {len(preds) - added} already present)")

    ic = update_realized(prices)
    print(f"Scored {len(ic)} weeks. Trailing 26w IC: "
          f"{ic['ic'].tail(26).mean():+.4f}")


if __name__ == "__main__":
    main()
