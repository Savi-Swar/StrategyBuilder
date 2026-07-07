"""Portfolio builder: capital + risk appetite -> a balanced allocation,
constructed from the desk's own 20-year covariance estimates.

Method (documented so every number is defensible):
1. Core sleeves are ETF-investable asset classes, proxied by the index/futures
   series in Quark.db (proxy mapping below). Base weights are inverse-vol
   risk parity over the trailing 3 years of daily returns.
2. The whole basket is scaled so its covariance-implied annual vol matches
   the profile's target (6% / 10% / 14%). No leverage: if the target exceeds
   what a fully-invested basket delivers, we invest 100% and say so. The
   remainder sits in cash (T-bills in practice; modeled at zero here, which
   UNDERSTATES the conservative profiles — noted on the page).
3. The alpha sleeve (balanced/aggressive only) is a small, capped carve-out
   into Vig's long book — top-decile names, long-only, equal weight. Sized
   far below full Kelly on purpose: the live edge is thin and the sleeve is
   equity-beta-dominated, so it is modeled as equity risk in the vol math.
4. Historical stats (CAGR, worst drawdown, worst year) are computed by
   running TODAY'S weights through the full 2004+ history — including 2008
   and 2020. Past performance, not a promise; it's there so the user sees
   the pain before the pleasure.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.metrics import max_drawdown, summary_stats

# sleeve -> (proxy tickers in Quark.db, investable ETF suggestion)
SLEEVES = {
    "us_equity":   (["^GSPC"], "VOO / SPY"),
    "intl_equity": (["^FTSE", "^N225", "^GDAXI"], "VXUS / VEA"),
    "bonds":       (["ZN=F"], "IEF"),
    "long_bonds":  (["ZB=F"], "TLT"),
    "gold":        (["GC=F"], "GLD"),
    "crypto":      (["BTC-USD"], "IBIT / FBTC"),
}

PROFILES = {
    "conservative": {"target_vol": 0.06, "alpha_w": 0.00, "crypto_cap": 0.00},
    "balanced":     {"target_vol": 0.10, "alpha_w": 0.05, "crypto_cap": 0.00},
    "aggressive":   {"target_vol": 0.14, "alpha_w": 0.10, "crypto_cap": 0.03},
}

VOL_WINDOW = 756  # ~3y daily, for weights
ANN = config.ANN_FACTOR


def _sleeve_returns(prices: pd.DataFrame) -> pd.DataFrame:
    rets = prices.pct_change(fill_method=None)
    out = {}
    for name, (proxies, _) in SLEEVES.items():
        cols = [c for c in proxies if c in rets.columns]
        if cols:
            out[name] = rets[cols].mean(axis=1)
    return pd.DataFrame(out)


def _vol_of(w: pd.Series, cov: pd.DataFrame) -> float:
    w = w.reindex(cov.index).fillna(0.0)
    return float(np.sqrt(w.values @ cov.values @ w.values))


def _profile_weights(sleeve_rets: pd.DataFrame, profile: dict) -> dict:
    """No-leverage vol targeting via basket blending: mix a defensive
    inverse-vol risk-parity basket D with a growth (equity) basket G until
    the covariance-implied vol matches the target. Below vol(D), de-risk
    into cash; above vol(G), hold G fully invested and say so."""
    recent = sleeve_rets.tail(VOL_WINDOW)
    cov = recent.cov() * ANN

    core = [s for s in SLEEVES if s != "crypto" and s in recent.columns]
    inv_vol = 1.0 / (recent[core].std() * np.sqrt(ANN))
    d = inv_vol / inv_vol.sum()

    g = pd.Series({"us_equity": 0.60, "intl_equity": 0.40})
    if profile["crypto_cap"] > 0 and "crypto" in recent.columns:
        g = g * (1.0 - profile["crypto_cap"])
        g["crypto"] = profile["crypto_cap"]

    target = profile["target_vol"]
    vol_d, vol_g = _vol_of(d, cov), _vol_of(g, cov)

    if target <= vol_d:                      # de-risk parity basket into cash
        invested = target / vol_d
        w = d * invested
    elif target >= vol_g:                    # cap: fully-invested growth basket
        invested, w = 1.0, g.copy()
    else:                                    # blend D -> G to hit the target
        invested = 1.0
        alphas = np.linspace(0.0, 1.0, 201)
        vols = [_vol_of((1 - a) * d.reindex(cov.index, fill_value=0)
                        + a * g.reindex(cov.index, fill_value=0), cov)
                for a in alphas]
        a = float(alphas[int(np.argmin(np.abs(np.array(vols) - target)))])
        w = ((1 - a) * d.reindex(cov.index, fill_value=0)
             + a * g.reindex(cov.index, fill_value=0))
        w = w[w > 1e-6]

    est_vol = _vol_of(w, cov)
    alpha_w = profile["alpha_w"] * invested
    if alpha_w > 0:                          # carve alpha out of US equity
        take = min(alpha_w, float(w.get("us_equity", 0.0)))
        w["us_equity"] = float(w.get("us_equity", 0.0)) - take
        alpha_w = take

    return {
        "weights": {k: round(float(v), 4) for k, v in w.items() if v > 1e-6},
        "alpha_w": round(alpha_w, 4),
        "cash_w": round(max(0.0, 1.0 - invested), 4),
        "est_vol": round(est_vol, 4),
        "fully_invested": invested >= 0.999,
        "capped_at_growth": target >= vol_g,
    }


def _mix_history(sleeve_rets: pd.DataFrame, weights: dict,
                 alpha_w: float) -> dict:
    """Run today's weights through the full history. The alpha sleeve is
    modeled as US-equity risk (it is long-only large caps)."""
    w = dict(weights)
    w["us_equity"] = w.get("us_equity", 0.0) + alpha_w
    cols = [c for c in w if c in sleeve_rets.columns]
    port = (sleeve_rets[cols] * pd.Series({c: w[c] for c in cols})).sum(axis=1)
    port = port.dropna()
    stats = summary_stats(port)
    yearly = port.groupby(port.index.year).apply(lambda x: float((1 + x).prod() - 1))
    return {
        "hist_cagr": round(stats["cagr"], 4),
        "hist_vol": round(stats["ann_vol"], 4),
        "hist_max_dd": round(max_drawdown((1 + port).cumprod()), 4),
        "worst_year": {"year": int(yearly.idxmin()), "ret": round(float(yearly.min()), 4)},
        "n_years": round(len(port) / ANN, 1),
    }


def build_portfolio_config(ma_prices: pd.DataFrame, xsec: dict,
                           eq_prices: pd.DataFrame, n_alpha: int = 10) -> dict:
    """Everything the portfolio page needs, embedded as JSON: per-profile
    weights + stats, and the current alpha-sleeve names with last prices."""
    sleeve_rets = _sleeve_returns(ma_prices)

    alpha_names = []
    for t in xsec["longs"][:n_alpha]:
        px = eq_prices[t].dropna()
        if not px.empty:
            alpha_names.append({
                "ticker": t,
                "prob": round(float(xsec["table"].at[t, "prob_outperform"]), 3),
                "last": round(float(px.iloc[-1]), 2),
            })

    profiles = {}
    for name, prof in PROFILES.items():
        pw = _profile_weights(sleeve_rets, prof)
        pw.update(_mix_history(sleeve_rets, pw["weights"], pw["alpha_w"]))
        profiles[name] = pw

    return {
        "profiles": profiles,
        "sleeve_etfs": {k: v[1] for k, v in SLEEVES.items()},
        "alpha_names": alpha_names,
        "as_of": str(xsec["as_of"].date()),
    }
