import numpy as np
import pandas as pd

from quark.insights.wire import build_wire_view
from quark.reports.analysis_page import render_analysis_page


def fixtures():
    snap = pd.DataFrame(
        {"asset_class": ["commodity"], "target_position": [-0.85],
         "ret_5d": [-0.021]}, index=pd.Index(["CL=F"], name="ticker"))
    xsec = {
        "table": pd.DataFrame({"prob_outperform": [0.589, 0.422]},
                              index=["AES", "WDAY"]),
        "longs": ["AES"], "shorts": ["WDAY"],
    }
    articles = [
        {"ticker": "CL=F", "group": "macro", "title": "Oil slides on supply",
         "provider": "Reuters", "url": "http://x", "published": "2026-07-07T10:00:00Z"},
        {"ticker": "CL=F", "group": "macro", "title": "OPEC watch",
         "provider": "BBG", "url": "http://y", "published": "2026-07-07T09:00:00Z"},
        {"ticker": "AES", "group": "picks", "title": "AES wins contract",
         "provider": "Zacks", "url": "http://z", "published": "2026-07-07T08:00:00Z"},
    ]
    return articles, snap, xsec


def test_wire_view_cross_references_positions():
    articles, snap, xsec = fixtures()
    wire = build_wire_view(articles, snap, xsec)
    assert wire["heat"][0][0] == "CL=F" and wire["heat"][0][1]["n"] == 2
    cl = next(a for a in wire["articles"] if a["ticker"] == "CL=F")
    assert cl["stance"]["side"] == "SHORT" and cl["stance"]["kind"] == "trend"
    aes = next(a for a in wire["articles"] if a["ticker"] == "AES")
    assert aes["stance"]["side"] == "LONG BOOK"
    assert any("CL=F: 2 on the wire" in b for b in wire["bullets"])


def test_analysis_page_renders_with_and_without_llm():
    articles, snap, xsec = fixtures()
    wire = build_wire_view(articles, snap, xsec)
    html = render_analysis_page(wire, "2026-07-07T08:00:00")
    assert "Oil slides on supply" in html
    assert "Wire vs desk" in html
    assert "activates with an API key" in html  # computed fallback shown
    html2 = render_analysis_page(wire, "2026-07-07T08:00:00",
                                 desk_read="**Theme**: energy softening.")
    assert "energy softening" in html2 and "activates with" not in html2
