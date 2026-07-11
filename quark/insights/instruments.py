"""The security master: one compact record per instrument, embedded as a
generated JS file so every page can open a full instrument view (chart,
returns, technicals, the model's opinion at every horizon) from a click or
the command palette — serverless, straight off disk."""

import json

import numpy as np
import pandas as pd

PX_DAYS = 252


def _series_block(px: pd.Series) -> dict:
    px = px.dropna()
    tail = px.tail(PX_DAYS)
    out = {"l": round(float(px.iloc[-1]), 2),
           "px": [round(float(v), 2) for v in tail]}
    for key, n in (("r1", 1), ("r21", 21), ("r252", 252)):
        if len(px) > n:
            out[key] = round(float(px.iloc[-1] / px.iloc[-(n + 1)] - 1), 4)
    return out


FACTOR_COLS = {"mom_252": "m12", "mom_21": "m1",
               "vol_ratio_21_63": "vol", "dist_52w_high": "hi"}


def build_instruments(eq_prices: pd.DataFrame, ma_prices: pd.DataFrame,
                      universe: pd.DataFrame, sectors: dict,
                      horizon_models: dict, snapshot: pd.DataFrame,
                      board: pd.DataFrame, names: dict | None = None) -> dict:
    inst: dict[str, dict] = {}
    names = names or {}
    feats = horizon_models.get("1W", {}).get("features")

    for t in eq_prices.columns:
        px = eq_prices[t].dropna()
        if px.empty:
            continue
        rec = _series_block(px)
        rec["c"] = sectors.get(t, "US equity")
        rec["k"] = "stock"
        if t in names:
            rec["n"] = names[t]
        h_probs, h_side = {}, {}
        for label, xs in horizon_models.items():
            tab = xs["table"]
            if t in tab.index:
                h_probs[label] = round(float(tab.at[t, "prob_outperform"]), 3)
                h_side[label] = ("L" if t in xs["longs"]
                                 else "S" if t in xs["shorts"] else "")
        rec["h"], rec["hd"] = h_probs, h_side
        if feats is not None and t in feats.index:
            row = feats.loc[t]
            rec["f"] = {short: int(round((float(row[col]) + 0.5) * 100))
                        for col, short in FACTOR_COLS.items()
                        if col in row.index and pd.notna(row[col])}
        inst[t] = rec

    for t in ma_prices.columns:
        px = ma_prices[t].dropna()
        if px.empty or t in inst:
            continue
        rec = _series_block(px)
        rec["c"] = (universe.at[t, "asset_class"]
                    if t in universe.index else "multi-asset")
        rec["k"] = "macro"
        if t in snapshot.index:
            rec["tp"] = round(float(snapshot.at[t, "target_position"]), 2)
        if board is not None and t in board.index:
            r = board.loc[t]
            rec["b"] = {
                "rsi": round(float(r["rsi14"]), 0),
                "pctb": round(float(r["pctb"]), 2),
                "macd": round(float(r["macd_bps"]), 1),
                "gold": None if pd.isna(r["golden"]) else bool(r["golden"]),
                "vwap": None if pd.isna(r["vwap_dist"]) else round(float(r["vwap_dist"]), 4),
                "mom": None if pd.isna(r["mom"]) else round(float(r["mom"]), 4),
                "cons": int(r["consensus"]),
            }
        inst[t] = rec

    return inst


def render_instruments_js(inst: dict) -> str:
    def clean(o):
        if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
            return None
        return o
    return ("window.VIG_INSTRUMENTS = "
            + json.dumps(inst, default=clean, separators=(",", ":"))
            + ";")
