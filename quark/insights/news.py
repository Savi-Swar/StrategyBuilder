"""Headline context via Yahoo Finance (yfinance .news). Best-effort: a
failure for one ticker never blocks the brief."""

import pandas as pd
import yfinance as yf


def _parse_item(item: dict) -> dict | None:
    # yfinance >=0.2.50 nests under "content"; older versions are flat.
    content = item.get("content", item)
    title = content.get("title")
    if not title:
        return None
    url = (content.get("canonicalUrl") or {}).get("url") or content.get("link", "")
    provider = (content.get("provider") or {}).get("displayName") or content.get(
        "publisher", ""
    )
    published = content.get("pubDate") or content.get("providerPublishTime", "")
    return {"title": title, "provider": provider, "url": url, "published": str(published)}


def get_headlines(tickers: list[str], max_per: int = 3) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for t in tickers:
        try:
            raw = yf.Ticker(t).news or []
        except Exception:  # noqa: BLE001 — news is garnish, never fatal
            raw = []
        parsed = [p for p in (_parse_item(i) for i in raw) if p]
        if parsed:
            out[t] = parsed[:max_per]
    return out


MACRO_WIRE = ["^GSPC", "^IXIC", "GC=F", "CL=F", "NG=F", "BTC-USD",
              "EURUSD=X", "ZN=F"]


def get_wire(pick_tickers: list[str], max_macro: int = 4,
             max_pick: int = 2) -> list[dict]:
    """Broad daily wire: macro instruments + current picks, deduped by
    title. Each item carries its associated ticker."""
    seen, items = set(), []
    for group, ticks, cap in (("macro", MACRO_WIRE, max_macro),
                              ("picks", pick_tickers, max_pick)):
        for t, arts in get_headlines(ticks, max_per=cap).items():
            for a in arts:
                key = a["title"].strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                items.append({**a, "ticker": t, "group": group})
    return items
