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

    # morning push, event alerts, Sunday digest, state backup — outputs are
    # already written above; nothing here may fail the daily job
    from quark.insights.alerts import (_fmt_ic, backup_state, notify,
                                       run_alerts, weekly_digest)
    h = result.get("health", {})
    trades_line = " · ".join(f"{t['side']} {t['ticker']}"
                             for t in result["trades"])
    notify("Vig — desk is set",
           f"{trades_line} — edge {h.get('model_status', '?')}"
           f" (26w IC {_fmt_ic(h.get('ic_mean'))})")
    try:
        for e in run_alerts(result):
            print("ALERT:", e)
        digest = weekly_digest(result)
        if digest:
            print(f"Digest:    {digest}")
    except Exception as exc:  # noqa: BLE001
        print(f"alerts/digest skipped: {exc}")
    backup_state()


if __name__ == "__main__":
    main()
