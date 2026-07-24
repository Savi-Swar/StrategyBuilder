"""8-K Item 2.02 announcement dates via the shared async fetch layer.

Same source and parsing as fetch_8k_fast.py; the difference is the engine:
weekly windows fan out concurrently through quark.data.fetchlib, which holds
the SEC request rate at its configured ceiling with a token bucket instead of
sleep() calls, retries with jittered backoff, and reports run counters.

    python scripts/fetch_8k_async.py --start 2012-01-01 --end 2026-07-24
    python scripts/fetch_8k_async.py --start 2026-01-01 --end 2026-06-30 \
        --out /tmp/slice.csv       # fixed slice, used for benchmarking
"""
import argparse
import re
import urllib.parse

import pandas as pd

from quark import config
from quark.data.contracts import validate_ann_dates
from quark.data.fetchlib import Fetcher

Q = urllib.parse.quote('"Results of Operations and Financial Condition"')
TICKER_RE = re.compile(r"\(([A-Z][A-Z.\-]{0,9})\)\s+\(CIK")


async def fetch_week(fl: Fetcher, start: pd.Timestamp, end: pd.Timestamp) -> list:
    """All (ticker, file_date) rows for one week window; pagination inside a
    window is sequential (page N+1 depends on N existing), windows are not."""
    rows, frm = [], 0
    while True:
        url = (f"https://efts.sec.gov/LATEST/search-index?q={Q}&forms=8-K"
               f"&startdt={start.date()}&enddt={end.date()}&size=100&from={frm}")
        d = await fl.get_json(url, api="sec")
        hits = d.get("hits", {}).get("hits", [])
        for h in hits:
            s = h["_source"]
            for dn in s.get("display_names", []):
                m = TICKER_RE.search(dn)
                if m:
                    rows.append((m.group(1), s["file_date"]))
        if len(hits) < 100 or frm >= 9900:
            return rows
        frm += 100


async def fetch_range(fl: Fetcher, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    weeks = []
    cur = start
    while cur < end:
        weeks.append((cur, min(cur + pd.Timedelta(days=6), end)))
        cur += pd.Timedelta(days=7)
    per_week = await fl.gather(fetch_week(fl, a, b) for a, b in weeks)
    rows = [r for wk in per_week for r in wk]
    return pd.DataFrame(rows, columns=["ticker", "ann_date"]).drop_duplicates()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2012-01-01")
    ap.add_argument("--end", default="2026-07-24")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or (config.REPORTS_DIR.parent / "data" / "ann_dates_8k.csv")

    fl = Fetcher(run_id=f"edgar8k_{args.start}_{args.end}")
    df = fl.run(fetch_range(fl, pd.Timestamp(args.start), pd.Timestamp(args.end)))
    df = validate_ann_dates(df)
    df.to_csv(out, index=False)
    print(f"DONE: {len(df):,} announcements, {df['ticker'].nunique():,} tickers -> {out}")
    print(fl.summary())


if __name__ == "__main__":
    main()
