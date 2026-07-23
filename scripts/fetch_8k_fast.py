"""8-K Item 2.02 announcement dates — fast version (size=100, 10x)."""
import json, re, time, urllib.request, urllib.parse
import pandas as pd
from quark import config
UA = {"User-Agent": "Savitur Swarup saviswarup@gmail.com research"}
Q = urllib.parse.quote('"Results of Operations and Financial Condition"')
out = config.REPORTS_DIR.parent / "data" / "ann_dates_8k.csv"
rows, start = [], pd.Timestamp("2012-01-01")
week = 0
while start < pd.Timestamp("2026-07-24"):
    end = start + pd.Timedelta(days=6)
    frm = 0
    while True:
        url = (f"https://efts.sec.gov/LATEST/search-index?q={Q}&forms=8-K"
               f"&startdt={start.date()}&enddt={end.date()}&size=100&from={frm}")
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
        except Exception:
            time.sleep(2); continue
        hits = d.get("hits", {}).get("hits", [])
        for h in hits:
            s = h["_source"]
            for dn in s.get("display_names", []):
                m = re.search(r"\(([A-Z][A-Z.\-]{0,9})\)\s+\(CIK", dn)
                if m: rows.append((m.group(1), s["file_date"]))
        if len(hits) < 100 or frm >= 9900: break
        frm += 100
        time.sleep(0.12)
    time.sleep(0.12)
    start = end + pd.Timedelta(days=1); week += 1
    if week % 26 == 0:
        pd.DataFrame(rows, columns=["ticker","ann_date"]).drop_duplicates().to_csv(out, index=False)
        print(f"  {start.date()}: {len(rows):,}", flush=True)
df = pd.DataFrame(rows, columns=["ticker","ann_date"]).drop_duplicates()
df.to_csv(out, index=False)
print(f"DONE: {len(df):,} announcements, {df['ticker'].nunique():,} tickers")
