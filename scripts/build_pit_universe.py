"""Build a best-effort point-in-time S&P 500 membership table.

Walks Wikipedia's constituent-changes table BACKWARD from today's membership:
before an addition date the added name is out; before a removal date the
removed name is in. Month-end snapshots land in reports/pit_membership.csv
(long format: month_end,ticker).

Then it tries to recover price history for every REMOVED name still absent
from the DB — this is where the honest limitation bites: Yahoo drops most
delisted tickers, so recovery is partial and the rate is printed and stored,
not hidden.
"""

import sqlite3

import pandas as pd

from quark import config
from quark.data.refresh import (get_sp500_changes, get_sp500_members,
                                refresh_tickers)

SNAP_START = "2005-01-31"


def build_membership(current: set[str], changes: pd.DataFrame) -> pd.DataFrame:
    """Month-end membership snapshots, newest -> oldest backward walk."""
    month_ends = pd.date_range(SNAP_START, pd.Timestamp.today(), freq="ME")
    ch = changes.sort_values("date", ascending=False)
    members = set(current)
    rows = []
    i = 0
    for me in month_ends[::-1]:
        # undo every change that took effect AFTER this month-end
        while i < len(ch) and ch.iloc[i]["date"] > me:
            r = ch.iloc[i]
            if pd.notna(r["added"]):
                members.discard(r["added"])
            if pd.notna(r["removed"]):
                members.add(r["removed"])
            i += 1
        rows.extend((me, t) for t in sorted(members))
    return pd.DataFrame(rows, columns=["month_end", "ticker"])


def main() -> None:
    changes = get_sp500_changes()
    current = set(get_sp500_members()["ticker"])
    print(f"{len(changes)} change events "
          f"({changes['date'].min().date()} → {changes['date'].max().date()}), "
          f"{len(current)} current members")

    pit = build_membership(current, changes)
    out = config.REPORTS_DIR / "pit_membership.csv"
    pit.to_csv(out, index=False)
    n_names = pit["ticker"].nunique()
    print(f"Wrote {out}: {pit['month_end'].nunique()} month-ends, "
          f"{n_names} distinct names ever-members since 2005")

    # Recover history for ever-members missing from the DB (mostly delisted).
    with sqlite3.connect(str(config.DB_PATH)) as conn:
        have = {t for (t,) in
                conn.execute("SELECT DISTINCT ticker FROM stocks")}
    missing = sorted(set(pit["ticker"]) - have)
    print(f"{len(missing)} ever-member tickers have no price history — "
          "attempting Yahoo recovery (delisted names usually fail)...")
    if missing:
        rep = refresh_tickers(missing, start="2005-01-01")
        ok = int((rep["status"] == "ok").sum())
        rep.to_csv(config.REPORTS_DIR / "pit_recovery_report.csv", index=False)
        print(f"RECOVERY RATE: {ok}/{len(missing)} "
              f"({ok / len(missing):.0%}) — the unrecovered rest are exactly "
              "the names survivorship bias deletes. Documented in "
              "RESEARCH_NOTES.md.")


if __name__ == "__main__":
    main()
