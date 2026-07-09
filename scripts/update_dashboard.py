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

    # morning push: the one-line desk summary a terminal would give you
    try:
        import subprocess
        h = result.get("health", {})
        trades_line = " · ".join(f"{t['side']} {t['ticker']}"
                                 for t in result["trades"])
        msg = (f"{trades_line} — edge {h.get('model_status', '?')}"
               f" (26w IC {h.get('ic_mean', float('nan')):+.3f})")
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "Vig — desk is set"'],
                       check=False, capture_output=True, timeout=10)
    except Exception:  # noqa: BLE001 — notification is garnish
        pass


if __name__ == "__main__":
    main()
