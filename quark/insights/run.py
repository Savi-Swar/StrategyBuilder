"""One entry point for the daily pipeline — shared by the CLI scripts, the
scheduled job, and the Trader app."""

import json
from datetime import date, datetime

from quark import config
from quark.data.loader import load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import fetch_sp500_universe, load_sp500_tickers, refresh_tickers
from quark.insights.brief import build_brief, llm_commentary, payload_for_llm
from quark.insights.knowledge import build_dossier
from quark.insights.ledger import health_summary, record_predictions, update_realized
from quark.insights.review import build_review, llm_self_review
from quark.insights.news import get_headlines
from quark.insights.signals import multi_asset_snapshot, xsec_latest_predictions
from quark.insights.trades import top_trades
from quark.universe import load_universe

SPARK_DAYS = 90


def run_daily(refresh: bool = True, news: bool = True, llm: bool = True) -> dict:
    uni = load_universe()
    if refresh:
        try:
            print("Refreshing multi-asset universe...")
            refresh_tickers(list(uni.index))
            print("Refreshing S&P 500 universe...")
            fetch_sp500_universe()
        except Exception as exc:  # noqa: BLE001 — offline must not kill the brief
            print(f"[run] refresh failed ({exc}); continuing with existing data")

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

    print("Updating the prediction ledger and model health...")
    record_predictions(xsec["as_of"], xsec["table"]["prob_outperform"], source="live")
    ic_history = update_realized(eq_prices)
    health = health_summary(ic_history, data_through=eq_prices.index[-1])
    print(f"  model: {health['model_status']} — {health['model_detail']}")

    print("Grading the past year of top-3 calls...")
    review = build_review(eq_prices, weeks=52)

    print("Building portfolio profiles...")
    from quark.insights.portfolio import build_portfolio_config
    portfolio = build_portfolio_config(ma_prices, xsec, eq_prices)

    # Industry-style positioning intelligence: sector tilts of the books,
    # factor loadings, and the stock-bond correlation regime.
    from collections import Counter
    from quark.data.refresh import load_sp500_sectors
    sec = load_sp500_sectors()
    sectors = {
        "long": dict(Counter(sec.get(t, "Unknown") for t in xsec["longs"])),
        "short": dict(Counter(sec.get(t, "Unknown") for t in xsec["shorts"])),
    }
    tilt_feats = {"mom_252": "12m momentum", "mom_21": "1m momentum",
                  "vol_ratio_21_63": "short-term vol", "dist_52w_high": "52w-high proximity"}
    f = xsec["features"]
    factor_tilts = {
        label: {
            "long": round(float((f.loc[[t for t in xsec["longs"] if t in f.index],
                                       col] + 0.5).mean() * 100), 1),
            "short": round(float((f.loc[[t for t in xsec["shorts"] if t in f.index],
                                        col] + 0.5).mean() * 100), 1),
        }
        for col, label in tilt_feats.items() if col in f.columns
    }
    ma_rets = ma_prices.pct_change(fill_method=None)
    regime = {}
    if "^GSPC" in ma_rets.columns and "ZN=F" in ma_rets.columns:
        # pairwise-complete days only: holiday NaNs would void every window
        pair = ma_rets[["^GSPC", "ZN=F"]].dropna()
        corr = pair["^GSPC"].rolling(63).corr(pair["ZN=F"]).dropna()
        if not corr.empty:
            regime["stock_bond_corr63"] = round(float(corr.iloc[-1]), 2)

    headlines: dict = {}
    if news:
        picks = xsec["longs"][:6] + xsec["shorts"][:6]
        print(f"Fetching headlines for {len(picks)} picks...")
        headlines = get_headlines(picks)

    trades = top_trades(xsec, headlines, n=3)

    sparks = {
        t["ticker"]: [round(float(v), 2) for v in
                      eq_prices[t["ticker"]].dropna().tail(SPARK_DAYS)]
        for t in trades if t["ticker"] in eq_prices.columns
    }

    commentary = None
    self_review = None
    if llm:
        print("Requesting Vig's commentary...")
        commentary = llm_commentary(
            payload_for_llm(snapshot, xsec, headlines),
            dossier=build_dossier(health),
        )
        if review["summary"]:
            self_review = llm_self_review(review["summary"], review["lessons"])

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_through": str(eq_prices.index[-1].date()),
        "snapshot": snapshot,
        "xsec": xsec,
        "headlines": headlines,
        "trades": trades,
        "sparks": sparks,
        "health": health,
        "review": review,
        "self_review": self_review,
        "portfolio": portfolio,
        "sectors": sectors,
        "factor_tilts": factor_tilts,
        "regime": regime,
        "commentary": commentary,
    }


def write_outputs(result: dict) -> dict:
    """Write the markdown brief, ranking CSV, dashboard HTML, and meta.json.
    Returns the paths."""
    from quark.reports.dashboard import render_dashboard

    today = date.today().isoformat()
    briefs = config.REPORTS_DIR / "briefs"
    briefs.mkdir(parents=True, exist_ok=True)
    dash_dir = config.REPORTS_DIR / "dashboard"
    dash_dir.mkdir(parents=True, exist_ok=True)

    md = build_brief(result["snapshot"], result["xsec"], result["headlines"],
                     result["commentary"])
    brief_path = briefs / f"brief_{today}.md"
    brief_path.write_text(md)
    result["xsec"]["table"].to_csv(briefs / f"ranking_{today}.csv")

    html = render_dashboard(result)
    dash_path = dash_dir / "index.html"
    dash_path.write_text(html)

    from quark.reports.review_page import render_review_page
    (dash_dir / "past_trades.html").write_text(
        render_review_page(result["review"], result["generated_at"],
                           result.get("self_review")))

    from quark.reports.portfolio_page import render_portfolio_page
    (dash_dir / "portfolio.html").write_text(
        render_portfolio_page(result["portfolio"], result["generated_at"]))

    (dash_dir / "meta.json").write_text(json.dumps(
        {"generated_at": result["generated_at"],
         "data_through": result["data_through"]}))

    return {"brief": brief_path, "dashboard": dash_path}
