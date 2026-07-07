"""Generate the daily research brief: refresh data, compute current model
signals, pull headlines for the picks, and write reports/briefs/<date>.md
(with optional Claude analyst commentary when credentials are available).

Usage:
    python scripts/daily_brief.py                 # full run (refresh + brief)
    python scripts/daily_brief.py --skip-refresh  # reuse existing DB data
    python scripts/daily_brief.py --no-llm        # skip Claude commentary
"""

import argparse
from datetime import date

from quark import config
from quark.data.loader import load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import fetch_sp500_universe, load_sp500_tickers, refresh_tickers
from quark.insights.brief import build_brief, llm_commentary, payload_for_llm
from quark.insights.news import get_headlines
from quark.insights.signals import multi_asset_snapshot, xsec_latest_predictions
from quark.universe import load_universe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-refresh", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-news", action="store_true")
    args = ap.parse_args()

    uni = load_universe()
    if not args.skip_refresh:
        print("Refreshing multi-asset universe...")
        refresh_tickers(list(uni.index))
        print("Refreshing S&P 500 universe...")
        fetch_sp500_universe()

    print("Computing multi-asset snapshot...")
    ma_prices = clean_panel(load_prices(tickers=list(uni.index)))
    snapshot = multi_asset_snapshot(ma_prices, uni)

    print("Scoring the equity cross-section...")
    eq_tickers = load_sp500_tickers()
    eq_prices = load_prices(tickers=eq_tickers, start="2005-01-01")
    eq_prices = clean_panel(eq_prices, quality_report(eq_prices)).dropna(how="all")
    eq_volumes = load_prices(tickers=eq_tickers, start="2005-01-01",
                             field="volume").reindex(eq_prices.index)
    xsec = xsec_latest_predictions(eq_prices, eq_volumes)

    headlines = {}
    if not args.no_news:
        picks = xsec["longs"][:6] + xsec["shorts"][:6]
        print(f"Fetching headlines for {len(picks)} picks...")
        headlines = get_headlines(picks)

    commentary = None
    if not args.no_llm:
        print("Requesting analyst commentary from Claude...")
        commentary = llm_commentary(payload_for_llm(snapshot, xsec, headlines))

    md = build_brief(snapshot, xsec, headlines, commentary)
    out_dir = config.REPORTS_DIR / "briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"brief_{date.today().isoformat()}.md"
    out_path.write_text(md)
    xsec["table"].to_csv(out_dir / f"ranking_{date.today().isoformat()}.csv")

    print(f"\nWrote {out_path}")
    print(f"Longs:  {', '.join(xsec['longs'][:10])}")
    print(f"Shorts: {', '.join(xsec['shorts'][:10])}")


if __name__ == "__main__":
    main()
