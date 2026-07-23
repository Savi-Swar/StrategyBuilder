"""WSB historical attention data via Arctic Shift (top-100-by-score daily)."""
import json, time, urllib.request, urllib.parse
import pandas as pd
from quark import config
UA = {"User-Agent": "quark-research saviswarup@gmail.com"}
out, day = [], pd.Timestamp("2019-01-01")
cache = config.REPORTS_DIR.parent / "data" / "wsb_top_daily.csv"
try:
    done = pd.read_csv(cache); day = pd.Timestamp(done["day"].max()) + pd.Timedelta(days=1)
    out = done.values.tolist()
except FileNotFoundError:
    done = None
while day < pd.Timestamp("2026-07-23"):
    url = ("https://arctic-shift.photon-reddit.com/api/posts/search?"
           f"subreddit=wallstreetbets&after={day.date()}T00:00:00&before={(day+pd.Timedelta(days=1)).date()}T00:00:00"
           "&limit=100&fields=title,created_utc,score")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            for p in json.loads(r.read()).get("data", []):
                out.append([str(day.date()), p.get("title","")[:300], p.get("score",0)])
    except Exception:
        time.sleep(3)
    time.sleep(0.7)
    day += pd.Timedelta(days=1)
    if day.day == 1:
        pd.DataFrame(out, columns=["day","title","score"]).to_csv(cache, index=False)
        print(f"  {day.date()}: {len(out):,} rows", flush=True)
pd.DataFrame(out, columns=["day","title","score"]).to_csv(cache, index=False)
print(f"WSB daily top posts: {len(out):,} rows")
