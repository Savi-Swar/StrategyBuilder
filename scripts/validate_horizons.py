"""One-time (rerun after major data changes): walk-forward validation of the
cross-sectional model at every desk horizon. Each horizon is a TRIAL and is
recorded as such — the UI quotes these numbers next to each horizon's picks.

Cadence note (audit fix 2026-07-08): a calendar week averages ~4.83 TRADING
days, so cadences are sized on 4.6 td/week to keep scored label windows
non-overlapping at 3M/6M/2Y. 1W at weekly cadence retains ~20% single-day
overlaps on holiday weeks — immaterial and documented, kept for sample size.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.data.loader import load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import load_sp500_tickers
from quark.ml.xsec import run_xsec_strategy

HORIZONS = [("1D", 1, 1), ("1W", 5, 1), ("3M", 63, 14),
            ("6M", 126, 28), ("2Y", 504, 110)]


def main() -> None:
    tickers = load_sp500_tickers()
    prices = load_prices(tickers=tickers, start="2005-01-01")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    volumes = load_prices(tickers=tickers, start="2005-01-01",
                          field="volume").reindex(prices.index)

    rows = []
    for label, h, cadence in HORIZONS:
        print(f"validating {label} (h={h}, rebal every {cadence}w)...")
        res = run_xsec_strategy(prices, volumes, horizon=h, rebal_every=cadence)
        ic = res.ic.dropna()
        t = float(ic.mean() / ic.std() * np.sqrt(len(ic))) if len(ic) > 2 else np.nan
        rows.append({
            "label": label, "horizon_days": h, "rebal_weeks": cadence,
            "ic_mean": round(float(ic.mean()), 4), "ic_t": round(t, 2),
            "n_periods": int(len(ic)),
            "auc_mean": round(float(res.fold_stats["auc"].mean()), 4),
        })
        print(f"  IC {ic.mean():+.4f} (t={t:+.2f}, n={len(ic)})")

    out = pd.DataFrame(rows)
    config.REPORTS_DIR.mkdir(exist_ok=True)
    out.to_csv(config.REPORTS_DIR / "xsec_horizons.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
