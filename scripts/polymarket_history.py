"""Polymarket resolved-market dataset: outcomes + price histories.
Foundation for our own calibration study (favorite-longshot bias measured
first-hand). Public APIs, no keys. Resumable cache."""
import json, time, urllib.request
import pandas as pd
from quark import config

UA = {"User-Agent": "research saviswarup@gmail.com"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

out = config.REPORTS_DIR.parent / "data" / "polymarket_resolved.csv"
rows = []
# top-volume resolved markets, paged
for offset in range(0, 2000, 100):
    try:
        mkts = get(f"https://gamma-api.polymarket.com/markets?closed=true&order=volumeNum&ascending=false&limit=100&offset={offset}")
    except Exception as e:
        print("page fail", offset, type(e).__name__); break
    if not mkts: break
    for mk in mkts:
        try:
            outcomes = json.loads(mk.get("outcomes","[]"))
            prices = json.loads(mk.get("outcomePrices","[]"))
            toks = json.loads(mk.get("clobTokenIds","[]"))
            if len(outcomes) != 2 or len(prices) != 2 or not toks: continue
            winner_yes = float(prices[0]) > 0.5      # resolved: prices go to 1/0
            rows.append({
                "id": mk.get("id"), "q": (mk.get("question") or "")[:80],
                "end": mk.get("endDate"), "volume": mk.get("volumeNum"),
                "cat": (mk.get("category") or ""), "yes_won": winner_yes,
                "tok_yes": toks[0],
            })
        except Exception:
            continue
    time.sleep(0.3)
df = pd.DataFrame(rows).drop_duplicates("id")
df.to_csv(out, index=False)
print(f"resolved binary markets: {len(df):,} | yes-won rate {df['yes_won'].mean():.1%}")

# price histories for top 600 by volume -> calibration points
hist_rows = []
top = df.nlargest(600, "volume")
for i, r in enumerate(top.itertuples()):
    try:
        h = get(f"https://clob.polymarket.com/prices-history?market={r.tok_yes}&interval=max&fidelity=720")
        pts = h.get("history", [])
        for p in pts:
            hist_rows.append({"id": r.id, "ts": p["t"], "price": p["p"],
                              "yes_won": r.yes_won, "end": r.end})
    except Exception:
        pass
    if (i+1) % 100 == 0:
        print(f"  {i+1}/600 histories, {len(hist_rows):,} points", flush=True)
        pd.DataFrame(hist_rows).to_csv(config.REPORTS_DIR.parent / "data" / "polymarket_pricehist.csv", index=False)
    time.sleep(0.25)
pd.DataFrame(hist_rows).to_csv(config.REPORTS_DIR.parent / "data" / "polymarket_pricehist.csv", index=False)
print(f"price history points: {len(hist_rows):,} across {len(top)} markets")
