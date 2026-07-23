"""Earnings ANNOUNCEMENT dates from 8-K Item 2.02 filings (EDGAR EFTS).
Day-precision announcement vintages — the fix for the 10-Q timing trap."""
import json, re, time, urllib.request, urllib.parse
import pandas as pd
from quark import config
UA = {"User-Agent": "Savitur Swarup saviswarup@gmail.com research"}
Q = urllib.parse.quote('"Results of Operations and Financial Condition"')
rows, start = [], pd.Timestamp("2012-01-01")
while start < pd.Timestamp("2026-07-23"):
    end = start + pd.Timedelta(days=6)
    url = (f"https://efts.sec.gov/LATEST/search-index?q={Q}&forms=8-K"
           f"&startdt={start.date()}&enddt={end.date()}")
    frm = 0
    while True:
        try:
            req = urllib.request.Request(url + f"&from={frm}", headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
        except Exception:
            time.sleep(2); break
        hits = d.get("hits", {}).get("hits", [])
        for h in hits:
            s = h["_source"]
            for dn in s.get("display_names", []):
                m = re.search(r"\(([A-Z][A-Z.\-]{0,9})\)\s+\(CIK", dn)
                if m:
                    rows.append((m.group(1), s["file_date"]))
        if len(hits) < 10 or frm >= 9990: break
        frm += 10
        time.sleep(0.15)
    time.sleep(0.15)
    start = end + pd.Timedelta(days=1)
    if start.month == 1 and start.day <= 7:
        print(f"  {start.year}: {len(rows):,} announcements so far", flush=True)
        pd.DataFrame(rows, columns=["ticker","ann_date"]).drop_duplicates().to_csv(
            config.REPORTS_DIR.parent / "data" / "ann_dates_8k.csv", index=False)
out = pd.DataFrame(rows, columns=["ticker","ann_date"]).drop_duplicates()
out.to_csv(config.REPORTS_DIR.parent / "data" / "ann_dates_8k.csv", index=False)
print(f"8-K announcement dates: {len(out):,} rows, {out['ticker'].nunique():,} tickers")
