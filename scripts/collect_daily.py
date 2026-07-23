"""Ephemeral-data collectors: run daily; history accrues into a moat.
1) IBKR shortable-stock snapshot (borrow availability/fee indicators)
2) Binance funding-rate snapshot (all USDT perps)"""
import datetime, io, urllib.request
import pandas as pd
from quark import config
D = config.REPORTS_DIR.parent / "data" / "collected"
D.mkdir(exist_ok=True)
today = datetime.date.today().isoformat()
try:
    req = urllib.request.Request("https://ftp3.interactivebrokers.com/usa.txt")
    raw = urllib.request.urlopen(req, timeout=60).read().decode("latin-1")
    df = pd.read_csv(io.StringIO(raw), sep="|", skiprows=1, on_bad_lines="skip")
    df.to_csv(D / f"ibkr_shortable_{today}.csv.gz", index=False, compression="gzip")
    print(f"IBKR shortable: {len(df):,} rows")
except Exception as e:
    print("IBKR snapshot failed:", type(e).__name__, e)
try:
    import ccxt
    ex = ccxt.binance()
    fr = ex.fetch_funding_rates()
    pd.DataFrame([{"symbol": k, "rate": v.get("fundingRate"),
                   "ts": v.get("timestamp")} for k, v in fr.items()]).to_csv(
        D / f"funding_{today}.csv.gz", index=False, compression="gzip")
    print(f"Funding snapshot: {len(fr):,} perps")
except Exception as e:
    print("Funding snapshot failed:", type(e).__name__, e)
