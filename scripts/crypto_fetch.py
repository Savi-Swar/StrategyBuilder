"""Crypto branch data layer: daily OHLCV panel for all Binance USDT spot
markets (to each coin's listing date), cached to data/crypto_prices.csv /
crypto_volumes.csv.

HONESTY NOTE (documented before first result, per house rules): this panel
has LISTING BIAS — coins delisted from Binance (LUNA classic, FTT, dead
alts) vanish from ccxt's market list, so the panel is 'coins that survived
to today', the same upward bias as the equity current-members panel was.
CoinGecko (key in .env) retains dead coins and will be used to measure the
bias in a later cycle, exactly like the equity PIT study. Until then every
crypto result is an UPPER BOUND and gets said that way.
"""

import time

import ccxt
import pandas as pd

from quark import config

START = pd.Timestamp("2019-01-01", tz="UTC")


def main() -> None:
    ex = ccxt.binance()
    markets = ex.load_markets()
    symbols = sorted(
        s for s, m in markets.items()
        if m.get("spot") and m.get("active") and m.get("quote") == "USDT"
        and not any(x in m.get("base", "") for x in ("UP", "DOWN", "BULL", "BEAR"))
    )
    print(f"{len(symbols)} active USDT spot markets")

    closes, vols = {}, {}
    since0 = int(START.timestamp() * 1000)
    for i, sym in enumerate(symbols):
        rows, since = [], since0
        while True:
            try:
                batch = ex.fetch_ohlcv(sym, "1d", since=since, limit=1000)
            except Exception as e:
                print(f"  {sym}: {type(e).__name__}, skipped")
                batch = []
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < 1000:
                break
            since = batch[-1][0] + 1
            time.sleep(ex.rateLimit / 1000)
        if len(rows) >= 90:                      # need some history to matter
            df = pd.DataFrame(rows, columns=["ts", "o", "h", "l", "c", "v"])
            idx = pd.to_datetime(df["ts"], unit="ms")
            base = sym.split("/")[0]
            closes[base] = pd.Series(df["c"].values, index=idx)
            vols[base] = pd.Series((df["c"] * df["v"]).values, index=idx)  # $ volume
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(symbols)} fetched, {len(closes)} kept")
        time.sleep(ex.rateLimit / 1000)

    prices = pd.DataFrame(closes).sort_index()
    volumes = pd.DataFrame(vols).sort_index()
    data_dir = config.REPORTS_DIR.parent / "data"
    prices.to_csv(data_dir / "crypto_prices.csv")
    volumes.to_csv(data_dir / "crypto_volumes.csv")
    print(f"Panel: {prices.shape[1]} coins x {prices.shape[0]} days "
          f"({prices.index[0].date()} -> {prices.index[-1].date()})")


if __name__ == "__main__":
    main()
