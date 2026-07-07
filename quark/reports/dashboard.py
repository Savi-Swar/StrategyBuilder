"""Self-contained HTML dashboard for the Trader app. No external assets, no
JS frameworks — one file the browser opens instantly from disk."""

import html as html_mod

import pandas as pd

CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0b0f14; color: #e6edf3;
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  padding: 32px 40px 60px;
}
.num, .mono { font-family: "SF Mono", ui-monospace, Menlo, monospace; }
header { display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap; margin-bottom: 6px; }
.wordmark { font-size: 26px; font-weight: 800; letter-spacing: 3px; }
.wordmark span { color: #60a5fa; }
.date { color: #8b949e; font-size: 15px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; margin: 14px 0 30px; }
.chip {
  background: #131a22; border: 1px solid #1f2937; border-radius: 999px;
  padding: 4px 14px; font-size: 12.5px; color: #9fb0c0;
}
.chip b { color: #e6edf3; font-weight: 600; }
h2 { font-size: 13px; letter-spacing: 2.5px; text-transform: uppercase;
     color: #8b949e; margin: 34px 0 14px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
.card {
  background: linear-gradient(180deg, #141c26 0%, #10161d 100%);
  border: 1px solid #1f2937; border-radius: 16px; padding: 22px;
}
.cardtop { display: flex; justify-content: space-between; align-items: center; }
.tick { font-size: 30px; font-weight: 800; letter-spacing: 1px; }
.badge { border-radius: 8px; padding: 3px 12px; font-weight: 700; font-size: 13px; }
.long  { background: rgba(52,211,153,.14); color: #34d399; border: 1px solid rgba(52,211,153,.35); }
.short { background: rgba(248,113,113,.14); color: #f87171; border: 1px solid rgba(248,113,113,.35); }
.spark { margin: 14px 0 10px; }
.probrow { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.probbar { flex: 1; height: 6px; background: #1f2937; border-radius: 3px; overflow: hidden; }
.probfill { height: 100%; border-radius: 3px; }
.probtxt { font-size: 13px; color: #9fb0c0; white-space: nowrap; }
ul.why { list-style: none; margin-bottom: 12px; }
ul.why li { padding-left: 18px; position: relative; margin-bottom: 6px;
            color: #c7d2dc; font-size: 13.5px; }
ul.why li::before { content: "▸"; position: absolute; left: 0; color: #60a5fa; }
.news a { color: #93c5fd; text-decoration: none; font-size: 13px; }
.news a:hover { text-decoration: underline; }
.sizing { margin-top: 12px; font-size: 12px; color: #7d8a97; border-top: 1px solid #1f2937; padding-top: 10px; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 980px) { .cols { grid-template-columns: 1fr; } }
table { width: 100%; border-collapse: collapse; background: #10161d;
        border: 1px solid #1f2937; border-radius: 12px; overflow: hidden; }
th { text-align: left; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase;
     color: #8b949e; padding: 10px 14px; border-bottom: 1px solid #1f2937; }
td { padding: 8px 14px; font-size: 13.5px; border-bottom: 1px solid #161d27; }
tr:last-child td { border-bottom: none; }
.pos { color: #34d399; } .neg { color: #f87171; } .muted { color: #7d8a97; }
.commentary { background: #10161d; border: 1px solid #1f2937; border-radius: 16px;
              padding: 24px 28px; max-width: 860px; }
.commentary p { margin-bottom: 12px; color: #c7d2dc; }
.commentary strong { color: #e6edf3; }
footer { margin-top: 44px; color: #58656f; font-size: 12px; max-width: 860px; }
.health { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 14px; margin-bottom: 8px; }
.htile { background: #10161d; border: 1px solid #1f2937; border-radius: 12px;
         padding: 14px 18px; }
.htile .hlabel { font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase;
                 color: #8b949e; margin-bottom: 6px; }
.dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%;
       margin-right: 7px; vertical-align: 1px; }
.dot.green { background: #34d399; box-shadow: 0 0 8px rgba(52,211,153,.6); }
.dot.yellow { background: #fbbf24; box-shadow: 0 0 8px rgba(251,191,36,.6); }
.dot.red { background: #f87171; box-shadow: 0 0 8px rgba(248,113,113,.6); }
.dot.warming { background: #60a5fa; box-shadow: 0 0 8px rgba(96,165,250,.6); }
.hdetail { font-size: 12.5px; color: #9fb0c0; margin-top: 4px; }
.edgemath { font-size: 12.5px; color: #7d8a97; margin: 10px 2px 0; max-width: 900px; }
"""


def _health_panel(health: dict | None) -> str:
    if not health:
        return ""
    model_dot = health.get("model_status", "warming")
    ic_t = health.get("ic_t")
    ic_line = ("—" if pd.isna(health.get("ic_mean", float("nan")))
               else f'{health["ic_mean"]:+.3f} <span class="muted">'
                    f'(t={ic_t:.1f}, {health["n_scored"]} wks scored)</span>')
    spread = health.get("spread_bps")
    spread_line = ("—" if spread is None or pd.isna(spread)
                   else f"{spread:+.0f} bps / 5d")
    data_dot = health.get("data_status", "yellow")
    age = health.get("data_age_bdays", "?")
    return f"""
<h2>Model health — trust gate</h2>
<div class="health">
  <div class="htile"><div class="hlabel">Live edge (trailing {health.get("window", 26)}w IC)</div>
    <div><span class="dot {model_dot}"></span><span class="num">{ic_line}</span></div>
    <div class="hdetail">{html_mod.escape(str(health.get("model_detail", "")))}</div></div>
  <div class="htile"><div class="hlabel">Realized decile spread</div>
    <div><span class="dot {model_dot}"></span><span class="num">{spread_line}</span></div>
    <div class="hdetail">top-vs-bottom decile, realized, gross</div></div>
  <div class="htile"><div class="hlabel">Data freshness</div>
    <div><span class="dot {data_dot}"></span><span class="num">{age} business day(s) old</span></div>
    <div class="hdetail">walk-forward + live predictions, scored after each 5-day horizon completes</div></div>
</div>
<div class="edgemath">Edge math, honestly: at the backtested best case (monthly
config, net Sharpe ≈ 0.26), the half-Kelly growth rate is ≈ Sharpe²/4 ≈
<b>1.7%/yr</b> per unit of gross exposure. Vig's value is consistency and
calibration — it compounds knowledge and discipline, not (yet) capital.</div>"""


def _spark_svg(values: list[float], width: int = 264, height: int = 54) -> str:
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1.0
    pts = " ".join(
        f"{i * width / (len(values) - 1):.1f},"
        f"{height - 4 - (v - lo) / rng * (height - 8):.1f}"
        for i, v in enumerate(values)
    )
    up = values[-1] >= values[0]
    color = "#34d399" if up else "#f87171"
    return (
        f'<svg class="spark" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.8" stroke-linejoin="round"/></svg>'
    )


def _trade_card(trade: dict, spark: list[float]) -> str:
    side_cls = "long" if trade["side"] == "LONG" else "short"
    fill = "#34d399" if trade["side"] == "LONG" else "#f87171"
    why = "".join(f"<li>{html_mod.escape(d)}</li>" for d in trade["drivers"])
    news = ""
    if trade["headline"]:
        h = trade["headline"]
        provider = f' <span class="muted">— {html_mod.escape(h["provider"])}</span>' if h["provider"] else ""
        news = (f'<div class="news">📰 <a href="{html_mod.escape(h["url"])}" '
                f'target="_blank">{html_mod.escape(h["title"])}</a>{provider}</div>')
    pct90 = ""
    if len(spark) > 1 and spark[0]:
        chg = (spark[-1] / spark[0] - 1) * 100
        cls = "pos" if chg >= 0 else "neg"
        pct90 = f'<span class="num {cls}">{chg:+.1f}% / 90d</span>'
    return f"""
<div class="card">
  <div class="cardtop">
    <span class="tick">{trade["ticker"]}</span>
    <span class="badge {side_cls}">{trade["side"]}</span>
  </div>
  {_spark_svg(spark)}
  <div class="probrow">
    <div class="probbar"><div class="probfill" style="width:{trade["prob"] * 100:.0f}%;background:{fill}"></div></div>
    <span class="probtxt num">P(outperform) {trade["prob"]:.3f} · edge {trade["edge_pct"]:+.1f}pp {pct90}</span>
  </div>
  <ul class="why">{why}</ul>
  {news}
  <div class="sizing">{html_mod.escape(trade["sizing"])}</div>
</div>"""


def _xsec_table(xsec: dict, k: int = 10) -> str:
    t = xsec["table"]
    rows = []
    for lo, sh in zip(xsec["longs"][:k], list(reversed(xsec["shorts"]))[:k]):
        rows.append(
            f'<tr><td><b>{lo}</b></td>'
            f'<td class="num pos">{t.at[lo, "prob_outperform"]:.3f}</td>'
            f'<td><b>{sh}</b></td>'
            f'<td class="num neg">{t.at[sh, "prob_outperform"]:.3f}</td></tr>'
        )
    return (
        "<table><tr><th>Long book</th><th>P(out)</th>"
        "<th>Short book</th><th>P(out)</th></tr>" + "".join(rows) + "</table>"
    )


def _trend_table(snapshot: pd.DataFrame, k: int = 10) -> str:
    top = snapshot.reindex(
        snapshot["target_position"].abs().sort_values(ascending=False).index
    ).head(k)
    rows = []
    for tick, r in top.iterrows():
        side = "LONG" if r["target_position"] > 0 else ("SHORT" if r["target_position"] < 0 else "—")
        cls = "pos" if r["target_position"] > 0 else "neg"
        r21 = "—" if pd.isna(r["ret_21d"]) else f"{r['ret_21d'] * 100:+.1f}%"
        rows.append(
            f'<tr><td><b>{tick}</b> <span class="muted">{r["asset_class"]}</span></td>'
            f'<td class="num">{r21}</td>'
            f'<td class="num">{r["ann_vol_63d"] * 100:.0f}%</td>'
            f'<td class="num {cls}">{side} {abs(r["target_position"]):.2f}x</td></tr>'
        )
    return ("<table><tr><th>Instrument</th><th>21d</th><th>Vol</th>"
            "<th>Trend position</th></tr>" + "".join(rows) + "</table>")


def _commentary_html(text: str) -> str:
    paras = []
    for block in text.split("\n\n"):
        b = html_mod.escape(block.strip())
        if not b:
            continue
        # minimal markdown: **bold** only
        while "**" in b:
            b = b.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
        paras.append(f"<p>{b}</p>")
    return "".join(paras)


def render_dashboard(result: dict) -> str:
    trades_html = "".join(
        _trade_card(t, result["sparks"].get(t["ticker"], []))
        for t in result["trades"]
    )
    commentary = ""
    if result["commentary"]:
        commentary = (f'<h2>Vig&rsquo;s commentary</h2>'
                      f'<div class="commentary">{_commentary_html(result["commentary"])}</div>')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="900">
<title>Vig — Daily Desk</title>
<style>{CSS}</style></head><body>
<header>
  <div class="wordmark">VIG <span>DAILY DESK</span></div>
  <div class="date">{result["generated_at"].replace("T", " · ")}</div>
</header>
<div class="chips">
  <span class="chip">data through <b>{result["data_through"]}</b></span>
  <span class="chip">universe <b>{result["xsec"]["n_universe"]}</b> names</span>
  <span class="chip">as-of rebalance <b>{result["xsec"]["as_of"].date()}</b></span>
  <span class="chip">backtested IC <b>0.017</b> (t=3.2, 756 wks)</span>
  <span class="chip">horizon <b>5 trading days</b></span>
</div>

{_health_panel(result.get("health"))}

<h2>Top trades today</h2>
<div class="cards">{trades_html}</div>

{commentary}

<h2>The books</h2>
<div class="cols">
  <div>{_xsec_table(result["xsec"])}</div>
  <div>{_trend_table(result["snapshot"])}</div>
</div>

<footer>Research tooling output — signals from backtested models with modest,
documented edges (weekly IC ≈ 0.017; see RESEARCH_NOTES.md). Probabilities are
calibrated conviction, not certainty. Not investment advice.
Generated {result["generated_at"]}.</footer>
</body></html>"""
