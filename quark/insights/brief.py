"""Assemble the daily markdown brief; optionally add Claude-written analyst
commentary grounded strictly in the computed payload.

The LLM layer is optional by design: with no Anthropic credentials the brief
still generates fully from model outputs. Commentary is generated with
claude-opus-4-8 and is instructed to cite only numbers present in the
payload — the model narrates the data, it does not invent views.
"""

import json
from datetime import date

import pandas as pd

DISCLAIMER = (
    "*Research tooling output — signals from backtested models with known "
    "limitations (see RESEARCH_NOTES.md). Not investment advice.*"
)

SYSTEM_PROMPT = """You are Vig, the analyst for a systematic trading desk of \
one. You are rigorous, direct, and allergic to hype: your job is to protect \
the trader's capital and calibration, not to excite them. You receive a \
research dossier (the desk's complete backtest evidence and live track \
record) and a JSON payload of today's model outputs.

Rules:
- Ground every claim in the dossier or payload. Never invent numbers, \
tickers, events, or causal stories not supported by the data provided.
- Weigh today's signals against the LIVE track record in the dossier's IC \
ledger and health status — if the trailing edge is weak or inverted, say so \
prominently and advise sizing down or standing down.
- Headlines may be connected to picks, but label such connections as \
interpretation, not model output.
- Quantify honestly: this desk's edge is a weekly IC around 0.017. That is \
real but thin — consistency and cost control matter more than any single \
pick. Never imply a pick is a sure thing; probabilities near 0.55 ARE the \
honest size of this edge.
- End with one line: "What would change my mind:" and the specific evidence \
that would flip today's stance.
- 250-450 words, markdown, sections: **Market state**, **Model positioning**, \
**Watch-outs**, and the closing line.
- Research commentary, not investment advice; write accordingly."""


def _fmt_pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{x * +100:.2f}%"


def build_brief(
    snapshot: pd.DataFrame,
    xsec: dict,
    headlines: dict[str, list[dict]],
    commentary: str | None = None,
) -> str:
    today = date.today().isoformat()
    lines = [f"# Vig Daily Brief — {today}", ""]

    if commentary:
        lines += ["## Vig's commentary (grounded in the research dossier)",
                  "", commentary, ""]

    lines += [
        f"## Cross-sectional equity model (as of {xsec['as_of'].date()}, "
        f"{xsec['n_universe']} eligible names)",
        "",
        "| Long candidates (top decile) | P(outperform) | Short candidates (bottom decile) | P(outperform) |",
        "|---|---|---|---|",
    ]
    t = xsec["table"]
    shown = 0
    for lo, sh in zip(xsec["longs"], reversed(xsec["shorts"])):
        lines.append(
            f"| **{lo}** | {t.at[lo, 'prob_outperform']:.3f} "
            f"| {sh} | {t.at[sh, 'prob_outperform']:.3f} |"
        )
        shown += 1
        if shown >= 15:
            remaining = len(xsec["longs"]) - shown
            if remaining > 0:
                lines.append(f"| _…{remaining} more per leg in the full ranking CSV_ | | | |")
            break
    lines += ["", f"_Model trained on {xsec['n_trained']:,} weekly observations; "
              "5-day horizon; weekly IC ≈ 0.017 (t=3.2) in walk-forward — a modest, "
              "long-side-driven edge. Dollar-neutral decile spread is the "
              "backtested implementation._", ""]

    lines += ["## Multi-asset trend & risk snapshot", "",
              "| Ticker | Class | 1d | 5d | 21d | Ann vol | Trend | Target pos |",
              "|---|---|---|---|---|---|---|---|"]
    for tick, row in snapshot.iterrows():
        arrow = {1: "LONG", -1: "SHORT", 0: "flat"}.get(int(row["trend_signal"])
                                                        if pd.notna(row["trend_signal"]) else 0, "flat")
        lines.append(
            f"| {tick} | {row['asset_class']} | {_fmt_pct(row['ret_1d'])} "
            f"| {_fmt_pct(row['ret_5d'])} | {_fmt_pct(row['ret_21d'])} "
            f"| {_fmt_pct(row['ann_vol_63d'])} | {arrow} | {row['target_position']:+.2f} |"
        )
    lines.append("")

    if headlines:
        lines += ["## Headlines for model picks", ""]
        for tick, items in headlines.items():
            lines.append(f"**{tick}**")
            for it in items:
                src = f" — {it['provider']}" if it["provider"] else ""
                lines.append(f"- [{it['title']}]({it['url']}){src}")
            lines.append("")

    lines += ["---", DISCLAIMER, ""]
    return "\n".join(lines)


def payload_for_llm(snapshot: pd.DataFrame, xsec: dict,
                    headlines: dict[str, list[dict]]) -> str:
    payload = {
        "as_of": str(xsec["as_of"].date()),
        "xsec": {
            "longs": {t: round(float(xsec["table"].at[t, "prob_outperform"]), 4)
                      for t in xsec["longs"]},
            "shorts": {t: round(float(xsec["table"].at[t, "prob_outperform"]), 4)
                       for t in xsec["shorts"]},
            "n_universe": xsec["n_universe"],
            "backtest_context": "weekly IC 0.0165 (t=3.22), long-side driven, "
                                "net Sharpe 0.05 weekly / 0.26 monthly",
        },
        "multi_asset": json.loads(snapshot.round(4).to_json(orient="index")),
        "headlines": {t: [i["title"] for i in items]
                      for t, items in headlines.items()},
    }
    return json.dumps(payload, sort_keys=True)


def llm_commentary(payload_json: str, dossier: str | None = None) -> str | None:
    """Vig's commentary via claude-opus-4-8, grounded in the research
    dossier. Returns None (with a notice) when the SDK or credentials are
    unavailable — the brief works without it."""
    try:
        import anthropic
    except ImportError:
        print("[brief] anthropic SDK not installed — skipping commentary "
              "(pip install anthropic)")
        return None

    system = [{"type": "text", "text": SYSTEM_PROMPT}]
    if dossier:
        system.append({"type": "text", "text": dossier})

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{
                "role": "user",
                "content": "Today's model payload:\n" + payload_json,
            }],
        )
        if response.stop_reason == "refusal":
            print("[brief] commentary request was declined — skipping")
            return None
        return next((b.text for b in response.content if b.type == "text"), None)
    except anthropic.AuthenticationError:
        print("[brief] no valid Anthropic credentials — skipping commentary. "
              "Set ANTHROPIC_API_KEY (or `ant auth login`) to enable it.")
        return None
    except anthropic.APIConnectionError:
        print("[brief] network error reaching the Anthropic API — skipping commentary")
        return None
    except anthropic.APIStatusError as exc:
        print(f"[brief] Anthropic API error {exc.status_code} — skipping commentary")
        return None
