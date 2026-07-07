import numpy as np
import pandas as pd

from quark.insights.technicals import build_board


def make_universe(tickers, classes):
    return pd.DataFrame(
        {"asset_class": classes, "cost_bps": 3.0, "tradable": True},
        index=pd.Index(tickers, name="ticker"))


def test_board_reads_trend_correctly():
    idx = pd.bdate_range("2023-01-02", periods=400)
    up = 100 * np.linspace(1, 2.2, len(idx))          # steady uptrend
    down = 100 * np.linspace(1, 0.45, len(idx))       # steady downtrend
    prices = pd.DataFrame({"UP": up, "DN": down}, index=idx)
    volumes = pd.DataFrame(1e6, index=idx, columns=["UP", "DN"])
    uni = make_universe(["UP", "DN"], ["commodity", "commodity"])

    board = build_board(prices, volumes, uni)
    u, d = board.loc["UP"], board.loc["DN"]
    assert u["consensus"] == 6 and d["consensus"] == -6  # full agreement
    assert u["rsi14"] > 50 > d["rsi14"]
    assert u["golden"] and not d["golden"]
    assert u["vwap_dist"] > 0 > d["vwap_dist"]
    assert u["pctb"] > 0.5 > d["pctb"]
    # sorted by consensus descending
    assert list(board.index) == ["UP", "DN"]

    # 6-month mode: weekly bars, same verdict on a clean trend
    pos = build_board(prices, volumes, uni, mode="position")
    assert pos.loc["UP", "consensus"] == 6
    assert pos.loc["DN", "consensus"] == -6
    assert pos.loc["UP", "mom"] > 0 > pos.loc["DN", "mom"]  # 26w momentum


def test_board_handles_missing_volume():
    idx = pd.bdate_range("2023-01-02", periods=400)
    prices = pd.DataFrame({"FX": 1.1 + 0.1 * np.sin(np.arange(400) / 25)}, index=idx)
    volumes = pd.DataFrame(0.0, index=idx, columns=["FX"])  # FX has no volume
    uni = make_universe(["FX"], ["fx_g10"])
    board = build_board(prices, volumes, uni)
    assert np.isnan(board.loc["FX", "vwap_dist"])   # VWAP undefined, not fake
    assert -6 <= board.loc["FX", "consensus"] <= 6
