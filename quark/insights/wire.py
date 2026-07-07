"""The Analysis page's data: today's wire cross-referenced against the
desk's actual positioning, plus an optional grounded LLM synthesis."""

import json

import pandas as pd


def _stance_for(ticker: str, snapshot: pd.DataFrame, xsec: dict) -> dict:
    """What the desk actually thinks about this instrument right now."""
    if ticker in snapshot.index:
        r = snapshot.loc[ticker]
        pos = float(r["target_position"])
        side = "LONG" if pos > 0 else ("SHORT" if pos < 0 else "FLAT")
        return {"kind": "trend", "side": side, "size": round(abs(pos), 2),
                "ret_5d": None if pd.isna(r["ret_5d"]) else round(float(r["ret_5d"]), 4)}
    t = xsec["table"]
    if ticker in t.index:
        prob = float(t.at[ticker, "prob_outperform"])
        if ticker in xsec["longs"]:
            side = "LONG BOOK"
        elif ticker in xsec["shorts"]:
            side = "SHORT BOOK"
        else:
            side = "NO POSITION"
        return {"kind": "xsec", "side": side, "prob": round(prob, 3)}
    return {"kind": "none", "side": "NOT COVERED"}


def build_wire_view(articles: list[dict], snapshot: pd.DataFrame,
                    xsec: dict) -> dict:
    for a in articles:
        a["stance"] = _stance_for(a["ticker"], snapshot, xsec)

    # wire-vs-desk: article count per instrument next to the desk's stance
    heat: dict[str, dict] = {}
    for a in articles:
        h = heat.setdefault(a["ticker"], {"n": 0, "stance": a["stance"]})
        h["n"] += 1
    heat_rows = sorted(heat.items(), key=lambda kv: -kv[1]["n"])

    bullets = []
    for tick, h in heat_rows[:8]:
        s = h["stance"]
        if s["kind"] == "trend":
            desk = f"desk is {s['side']} {s['size']}x" if s["side"] != "FLAT" else "desk is flat"
        elif s["kind"] == "xsec":
            desk = f"{s['side'].lower()} at P(out) {s['prob']}"
        else:
            desk = "not in the tradable universe"
        bullets.append(f"{tick}: {h['n']} on the wire — {desk}")

    return {"articles": articles, "heat": heat_rows, "bullets": bullets}


def llm_wire_analysis(wire: dict, health: dict | None) -> str | None:
    """Grounded synthesis of the day's wire vs the desk's book. Same
    graceful-degradation contract as every other LLM layer."""
    try:
        import anthropic
    except ImportError:
        return None
    payload = {
        "headlines": [{"ticker": a["ticker"], "title": a["title"],
                       "stance": a["stance"]} for a in wire["articles"]],
        "health": health or {},
    }
    prompt = (
        "You are Vig, a systematic desk's analyst. Below are today's "
        "headlines, each tagged with the desk's ACTUAL current stance in the "
        "related instrument, plus model health. Write a 150-250 word desk "
        "read in markdown: 2-3 themes on the wire, where the news agrees or "
        "COLLIDES with the desk's positioning (call collisions out "
        "explicitly), and what would actually change the systematic view "
        "(hint: prices, not narratives — say so). Ground every claim in the "
        "payload; invent nothing. No investment advice.\n\n"
        + json.dumps(payload)
    )
    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-opus-4-8", max_tokens=3000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        if resp.stop_reason == "refusal":
            return None
        return next((b.text for b in resp.content if b.type == "text"), None)
    except Exception:  # noqa: BLE001 — optional layer, never fatal
        return None
