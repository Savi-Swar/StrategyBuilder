"""Prediction-market monitor (READ-ONLY, no account, no keys).
Hunts the documented inefficiency: mutually-exclusive outcome sets whose
best asks sum < $1 (buy-all arb) or best bids sum > $1 (sell-all arb).
Each run = one timestamped snapshot appended to the collector ledger."""
import datetime, json, time, urllib.request
import pandas as pd
from quark import config

UA = {"User-Agent": "research-monitor saviswarup@gmail.com"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes")
rows = []

# --- Polymarket (gamma API, public) ---
try:
    events = get("https://gamma-api.polymarket.com/events?closed=false&limit=300&order=volume24hr&ascending=false")
    n_ev = 0
    for ev in events:
        mkts = ev.get("markets", [])
        if len(mkts) < 3 or not ev.get("negRisk", False): continue
        asks, bids, ok = [], [], True
        for mk in mkts:
            try:
                ba, bb = float(mk.get("bestAsk") or 0), float(mk.get("bestBid") or 0)
            except (TypeError, ValueError): ok = False; break
            if not (0 < ba <= 1 and 0 <= bb < 1): ok = False; break
            asks.append(ba); bids.append(bb)
        if not ok or not asks: continue
        n_ev += 1
        sa, sb = sum(asks), sum(bids)
        if sa < 0.995:
            rows.append((now, "polymarket", ev.get("title","")[:70], "BUY-ALL", round(1-sa,4), len(mkts)))
        if sb > 1.005:
            rows.append((now, "polymarket", ev.get("title","")[:70], "SELL-ALL", round(sb-1,4), len(mkts)))
    print(f"polymarket: scanned {n_ev} neg-risk multi-outcome events")
except Exception as e:
    print("polymarket failed:", type(e).__name__, str(e)[:80])

# --- Kalshi (public market data) ---
try:
    evs = get("https://api.elections.kalshi.com/trade-api/v2/events?status=open&limit=200&with_nested_markets=true")
    n_ev = 0
    for ev in evs.get("events", []):
        mkts = ev.get("markets") or []
        if len(mkts) < 3: continue
        if ev.get("mutually_exclusive") is False: continue
        asks = [m.get("yes_ask") for m in mkts]
        bids = [m.get("yes_bid") for m in mkts]
        if any(a is None or a <= 0 or a > 100 for a in asks): continue
        n_ev += 1
        sa, sb = sum(asks)/100.0, sum(b or 0 for b in bids)/100.0
        if sa < 0.99:
            rows.append((now, "kalshi", ev.get("title","")[:70], "BUY-ALL", round(1-sa,4), len(mkts)))
        if sb > 1.01:
            rows.append((now, "kalshi", ev.get("title","")[:70], "SELL-ALL", round(sb-1,4), len(mkts)))
    print(f"kalshi: scanned {n_ev} multi-outcome events")
except Exception as e:
    print("kalshi failed:", type(e).__name__, str(e)[:80])

led = config.REPORTS_DIR.parent / "data" / "collected" / "predmkt_ledger.csv"
led.parent.mkdir(exist_ok=True)
df = pd.DataFrame(rows, columns=["ts","venue","event","type","edge","n_outcomes"])
if led.exists():
    df = pd.concat([pd.read_csv(led), df], ignore_index=True)
df.to_csv(led, index=False)
new = rows
print(f"\nopportunities this snapshot: {len(new)}")
for r in sorted(new, key=lambda x: -x[4])[:10]:
    print(f"  [{r[1]}] {r[3]} edge {r[4]*100:.1f}c on '{r[2]}' ({r[5]} outcomes)")
