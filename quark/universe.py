"""Static universe metadata — the single source of truth for asset class,
transaction-cost assumptions, tradability, and FX quote conventions.

Cost assumptions are half-spread-plus-slippage estimates in basis points,
charged on turnover. They are deliberately conservative round numbers; see
README "Transaction costs" for sources and caveats.

``^TNX`` is the CBOE 10-Year Treasury yield *index* (yield x 10), not a price
series — pct_change on it is not a tradable return. It is kept as a
non-tradable instrument so the ML feature set can use rate levels/changes.

S&P 500 single stocks (Study 2) are not enumerated here; they share uniform
metadata via :func:`equity_meta` and their membership lives in the
``sp500_members`` table written by ``quark.data.refresh``.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AssetMeta:
    ticker: str
    asset_class: str        # fx_g10 | fx_em | fx_cross | equity_index | commodity
                            #   | bond_fut | rate_index | crypto | stock
    cost_bps: float
    tradable: bool = True
    quote_convention: str = ""   # USD_base | FOR_base | cross (FX only)
    hindsight_picked: bool = False  # single names chosen with hindsight; excluded
                                    # from Study 1 headline portfolio


_UNIVERSE: list[AssetMeta] = [
    # --- FX G10 (2 bps) ---
    AssetMeta("EURUSD=X", "fx_g10", 2.0, quote_convention="FOR_base"),
    AssetMeta("GBPUSD=X", "fx_g10", 2.0, quote_convention="FOR_base"),
    AssetMeta("AUDUSD=X", "fx_g10", 2.0, quote_convention="FOR_base"),
    AssetMeta("NZDUSD=X", "fx_g10", 2.0, quote_convention="FOR_base"),
    AssetMeta("JPY=X", "fx_g10", 2.0, quote_convention="USD_base"),
    AssetMeta("CAD=X", "fx_g10", 2.0, quote_convention="USD_base"),
    AssetMeta("CHF=X", "fx_g10", 2.0, quote_convention="USD_base"),
    # --- FX EM (8 bps: wider spreads, some managed regimes) ---
    AssetMeta("THB=X", "fx_em", 8.0, quote_convention="USD_base"),
    AssetMeta("KRW=X", "fx_em", 8.0, quote_convention="USD_base"),
    # CNH=X excluded: Yahoo carries no usable history (1 observation as of 2026-07)
    AssetMeta("USDMXN=X", "fx_em", 8.0, quote_convention="USD_base"),
    AssetMeta("USDINR=X", "fx_em", 8.0, quote_convention="USD_base"),
    AssetMeta("USDZAR=X", "fx_em", 8.0, quote_convention="USD_base"),
    # --- FX crosses (3 bps) ---
    AssetMeta("EURGBP=X", "fx_cross", 3.0, quote_convention="cross"),
    AssetMeta("EURJPY=X", "fx_cross", 3.0, quote_convention="cross"),
    AssetMeta("GBPJPY=X", "fx_cross", 3.0, quote_convention="cross"),
    AssetMeta("CHFJPY=X", "fx_cross", 3.0, quote_convention="cross"),
    # --- Equity indices, traded as futures proxies (1.5 bps) ---
    AssetMeta("^GSPC", "equity_index", 1.5),
    AssetMeta("^DJI", "equity_index", 1.5),
    AssetMeta("^IXIC", "equity_index", 1.5),
    AssetMeta("^RUT", "equity_index", 1.5),
    AssetMeta("^FTSE", "equity_index", 1.5),
    AssetMeta("^N225", "equity_index", 1.5),
    AssetMeta("^HSI", "equity_index", 1.5),
    AssetMeta("^FCHI", "equity_index", 1.5),
    AssetMeta("^AXJO", "equity_index", 1.5),
    AssetMeta("^GDAXI", "equity_index", 1.5),
    AssetMeta("^KS11", "equity_index", 1.5),
    AssetMeta("^STI", "equity_index", 1.5),
    # --- Commodity futures, front-month chains (3 bps) ---
    AssetMeta("GC=F", "commodity", 3.0),
    AssetMeta("SI=F", "commodity", 3.0),
    AssetMeta("CL=F", "commodity", 3.0),
    AssetMeta("BZ=F", "commodity", 3.0),
    AssetMeta("NG=F", "commodity", 3.0),
    AssetMeta("HG=F", "commodity", 3.0),
    # --- Bond futures (1 bp) ---
    AssetMeta("ZB=F", "bond_fut", 1.0),
    AssetMeta("ZN=F", "bond_fut", 1.0),
    AssetMeta("ZF=F", "bond_fut", 1.0),
    # --- Rate index: feature input only, never traded ---
    AssetMeta("^TNX", "rate_index", 0.0, tradable=False),
    # --- Crypto (10 bps) ---
    AssetMeta("BTC-USD", "crypto", 10.0),
    AssetMeta("ETH-USD", "crypto", 10.0),
    # --- Single stocks: hindsight-picked mega caps, shown with/without ---
    AssetMeta("MSFT", "stock", 5.0, hindsight_picked=True),
    AssetMeta("NVDA", "stock", 5.0, hindsight_picked=True),
    AssetMeta("META", "stock", 5.0, hindsight_picked=True),
    AssetMeta("GOOGL", "stock", 5.0, hindsight_picked=True),
]

EQUITY_COST_BPS = 5.0  # Study 2 large-cap US equities


def load_universe() -> pd.DataFrame:
    """Universe metadata as a DataFrame indexed by ticker."""
    df = pd.DataFrame([vars(a) for a in _UNIVERSE]).set_index("ticker")
    assert df.index.is_unique
    return df


def equity_meta(tickers: list[str]) -> pd.DataFrame:
    """Uniform metadata frame for Study 2 equities."""
    return pd.DataFrame(
        {
            "asset_class": "stock",
            "cost_bps": EQUITY_COST_BPS,
            "tradable": True,
            "quote_convention": "",
            "hindsight_picked": False,
        },
        index=pd.Index(tickers, name="ticker"),
    )
