import numpy as np
import pandas as pd

from quark import config
from quark.backtest.sizing import vol_target_positions


def alternating_returns(n=300, mag=0.01):
    idx = pd.bdate_range("2019-01-01", periods=n)
    vals = np.tile([mag, -mag], n // 2 + 1)[:n]
    return pd.DataFrame({"A": vals}, index=idx)


def test_known_vol_gives_exact_position():
    rets = alternating_returns(mag=0.01)
    signals = pd.DataFrame(1.0, index=rets.index, columns=["A"])
    pos = vol_target_positions(signals, rets, vol_target=0.10, lookback=64,
                               max_leverage=10.0)
    # Window of 64 alternating +/-1%: mean 0, sample std = 0.01*sqrt(64/63)
    expected = 0.10 / (0.01 * np.sqrt(64 / 63) * np.sqrt(config.ANN_FACTOR))
    assert np.isclose(pos.iloc[-1]["A"], expected, rtol=1e-6)


def test_leverage_cap_binds_in_quiet_markets():
    rets = alternating_returns(mag=1e-6)  # near-zero vol
    signals = pd.DataFrame(1.0, index=rets.index, columns=["A"])
    pos = vol_target_positions(signals, rets, max_leverage=4.0)
    assert np.isclose(pos.iloc[-1]["A"], 4.0)


def test_warmup_and_nan_signal_give_zero_position():
    rets = alternating_returns()
    signals = pd.DataFrame(np.nan, index=rets.index, columns=["A"])
    pos = vol_target_positions(signals, rets)
    assert (pos["A"] == 0.0).all()

    signals2 = pd.DataFrame(1.0, index=rets.index, columns=["A"])
    pos2 = vol_target_positions(signals2, rets, lookback=63)
    assert (pos2["A"].iloc[:20] == 0.0).all()  # inside min_periods warmup


def test_short_signal_gives_negative_position():
    rets = alternating_returns()
    signals = pd.DataFrame(-1.0, index=rets.index, columns=["A"])
    pos = vol_target_positions(signals, rets)
    assert pos.iloc[-1]["A"] < 0
