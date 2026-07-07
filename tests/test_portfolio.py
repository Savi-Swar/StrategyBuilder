import numpy as np
import pandas as pd

from quark.insights.portfolio import PROFILES, _profile_weights, _sleeve_returns


def synthetic_ma_panel(n=1600, seed=11):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2019-01-01", periods=n)
    # Vols high enough that the diversified basket exceeds every profile's
    # target — otherwise all profiles hit the no-leverage cap identically.
    vols = {"^GSPC": 0.028, "^FTSE": 0.026, "^N225": 0.030, "^GDAXI": 0.030,
            "ZN=F": 0.011, "ZB=F": 0.018, "GC=F": 0.024, "BTC-USD": 0.080}
    return pd.DataFrame(
        {t: 100 * np.cumprod(1 + rng.normal(2e-4, v, n)) for t, v in vols.items()},
        index=idx)


def test_profile_weights_are_sane():
    sr = _sleeve_returns(synthetic_ma_panel())
    for name, prof in PROFILES.items():
        p = _profile_weights(sr, prof)
        total = sum(p["weights"].values()) + p["alpha_w"] + p["cash_w"]
        assert abs(total - 1.0) < 0.01, name          # fully accounted
        assert all(w >= 0 for w in p["weights"].values())  # no shorts/leverage
        assert p["est_vol"] <= prof["target_vol"] + 0.01   # never over target


def test_risk_ordering_and_features():
    sr = _sleeve_returns(synthetic_ma_panel())
    cons = _profile_weights(sr, PROFILES["conservative"])
    bal = _profile_weights(sr, PROFILES["balanced"])
    agg = _profile_weights(sr, PROFILES["aggressive"])
    assert cons["est_vol"] < bal["est_vol"] < agg["est_vol"]
    assert cons["cash_w"] >= agg["cash_w"]         # less risk -> more cash
    assert cons["alpha_w"] == 0.0
    assert agg["alpha_w"] > bal["alpha_w"] > 0.0
    assert cons["weights"].get("crypto", 0) == 0
    assert agg["weights"].get("crypto", 0) > 0     # capped satellite
    # conservative = de-risked parity basket: bonds outweigh equities there
    assert cons["weights"]["bonds"] > cons["weights"]["us_equity"]
    # aggressive tilts toward equities vs conservative
    agg_eq = agg["weights"].get("us_equity", 0) + agg["weights"].get("intl_equity", 0)
    cons_eq = cons["weights"].get("us_equity", 0) + cons["weights"].get("intl_equity", 0)
    assert agg_eq > cons_eq
