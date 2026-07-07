"""Daily pipeline entry point: refresh data, retrain rankings, scrape news,
write the markdown brief + Trader dashboard. Run by launchd every morning and
by the Trader app when the dashboard is stale.

Usage:
    python scripts/update_dashboard.py [--skip-refresh] [--no-llm] [--no-news]
"""

import argparse

from quark.insights.run import run_daily, write_outputs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-refresh", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-news", action="store_true")
    args = ap.parse_args()

    result = run_daily(refresh=not args.skip_refresh, news=not args.no_news,
                       llm=not args.no_llm)
    paths = write_outputs(result)
    print(f"\nDashboard: {paths['dashboard']}")
    print(f"Brief:     {paths['brief']}")
    print("Top trades: " + ", ".join(
        f"{t['side']} {t['ticker']} (p={t['prob']:.3f})" for t in result["trades"]))


if __name__ == "__main__":
    main()
