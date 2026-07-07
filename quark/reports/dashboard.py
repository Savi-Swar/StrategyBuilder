"""Vig's daily desk — self-contained HTML, no external assets, opened
straight from disk. Aesthetic: phosphor terminal, not SaaS dashboard."""

import html as html_mod

import pandas as pd

CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #060708; color: #e6e2d8;
  font: 14px/1.6 "SF Mono", ui-monospace, "JetBrains Mono", Menlo, monospace;
  padding: 0 0 70px;
}
body::after {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 9;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,.018) 0 1px, transparent 1px 3px);
}
.wrap { padding: 26px 44px 0; }
a { color: #ffb000; }

/* ── masthead ─────────────────────────────────────────── */
header { display: flex; align-items: flex-end; justify-content: space-between;
         flex-wrap: wrap; gap: 12px; padding: 30px 44px 18px; }
.wordmark { font-size: 58px; font-weight: 800; letter-spacing: -2px; line-height: 1; }
.tagline { color: #8a9199; font-size: 12px; letter-spacing: 1px; margin-top: 6px; }
.tagline b { color: #ffb000; font-weight: 600; }
.stamp-date { color: #8a9199; font-size: 12px; text-align: right; }
.btn {
  display: inline-block; border: 1px solid #ffb000; color: #ffb000;
  padding: 8px 18px; font-size: 12px; letter-spacing: 2px; text-decoration: none;
  text-transform: uppercase; transition: all .12s;
}
.btn:hover { background: #ffb000; color: #060708; }

/* ── tape ─────────────────────────────────────────────── */
.tape { border-top: 1px dashed #2a2e35; border-bottom: 1px dashed #2a2e35;
        overflow: hidden; white-space: nowrap; padding: 7px 0; margin: 8px 0 26px; }
.tape-inner { display: inline-block; animation: tape 55s linear infinite; }
@keyframes tape { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.tape span { margin: 0 18px; font-size: 12px; color: #8a9199; }
.tape .up { color: #46ff9a; } .tape .dn { color: #ff5d5d; }

/* ── sections ─────────────────────────────────────────── */
h2 { font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
     color: #ffb000; margin: 40px 0 16px; font-weight: 600; }
h2::before { content: "▚▚ "; }
h2 .dim { color: #8a9199; }

/* ── health tiles ─────────────────────────────────────── */
.health { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }
.htile { background: #0b0d10; border: 1px solid #22262c; padding: 14px 18px; }
.hlabel { font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
          color: #8a9199; margin-bottom: 7px; }
.hval { font-size: 17px; }
.led { display: inline-block; width: 9px; height: 9px; margin-right: 9px; }
.led.green  { background: #46ff9a; box-shadow: 0 0 10px #46ff9a; }
.led.yellow { background: #ffb000; box-shadow: 0 0 10px #ffb000; }
.led.red    { background: #ff5d5d; box-shadow: 0 0 10px #ff5d5d; }
.led.warming{ background: #6ea8fe; box-shadow: 0 0 10px #6ea8fe; }
.hdetail { font-size: 11.5px; color: #8a9199; margin-top: 6px; }
.edgemath { font-size: 11.5px; color: #6d747c; margin-top: 12px; max-width: 920px;
            border-left: 2px solid #22262c; padding-left: 14px; }

/* ── trade cards ──────────────────────────────────────── */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 16px; }
.card { background: #0b0d10; border: 1px solid #22262c; padding: 20px 22px 16px; position: relative; }
.card.long  { border-top: 3px solid #46ff9a; }
.card.short { border-top: 3px solid #ff5d5d; }
.cardtop { display: flex; justify-content: space-between; align-items: center; }
.tick { font-size: 34px; font-weight: 800; letter-spacing: 1px; }
.stamp { border: 2px double; padding: 3px 12px; font-weight: 700; font-size: 13px;
         letter-spacing: 2px; transform: rotate(-4deg); }
.stamp.long  { color: #46ff9a; border-color: #46ff9a; }
.stamp.short { color: #ff5d5d; border-color: #ff5d5d; }
.spark { margin: 12px 0 8px; display: block; }
.probrow { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.probbar { flex: 1; height: 5px; background: #191d22; }
.probfill { height: 100%; }
.probtxt { font-size: 11.5px; color: #8a9199; white-space: nowrap; }
ul.why { list-style: none; margin-bottom: 10px; }
ul.why li { padding-left: 16px; position: relative; margin-bottom: 5px;
            color: #c9c4b8; font-size: 12.5px; }
ul.why li::before { content: ">"; position: absolute; left: 0; color: #ffb000; }
.news a { font-size: 12px; text-decoration: none; }
.news a:hover { text-decoration: underline; }
.sizing { margin-top: 10px; font-size: 10.5px; color: #6d747c;
          border-top: 1px dashed #22262c; padding-top: 8px; }

/* ── tables ───────────────────────────────────────────── */
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 980px) { .cols { grid-template-columns: 1fr; } }
table { width: 100%; border-collapse: collapse; background: #0b0d10; border: 1px solid #22262c; }
th { text-align: left; font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
     color: #ffb000; padding: 9px 13px; border-bottom: 1px double #2a2e35; font-weight: 600; }
td { padding: 7px 13px; font-size: 12.5px; border-bottom: 1px solid #14171b; }
tr:last-child td { border-bottom: none; }
.pos { color: #46ff9a; } .neg { color: #ff5d5d; } .muted { color: #6d747c; }
.win { color: #46ff9a; font-weight: 700; } .loss { color: #ff5d5d; font-weight: 700; }

.commentary { background: #0b0d10; border: 1px solid #22262c;
              border-left: 3px solid #ffb000; padding: 20px 26px; max-width: 880px; }
.commentary p { margin-bottom: 11px; color: #c9c4b8; font-size: 13px; }
.commentary strong { color: #e6e2d8; }
footer { margin: 48px 44px 0; color: #565d64; font-size: 11px; max-width: 880px;
         border-top: 1px dashed #2a2e35; padding-top: 14px; }
.bigchart { background: #0b0d10; border: 1px solid #22262c; padding: 18px; }
"""


def _spark_svg(values: list[float], width: int = 270, height: int = 52,
               color: str | None = None, cls: str = "spark") -> str:
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1.0
    pts = " ".join(
        f"{i * width / (len(values) - 1):.1f},"
        f"{height - 4 - (v - lo) / rng * (height - 8):.1f}"
        for i, v in enumerate(values)
    )
    if color is None:
        color = "#46ff9a" if values[-1] >= values[0] else "#ff5d5d"
    return (f'<svg class="{cls}" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linejoin="round"/></svg>')


def page_shell(title: str, generated_at: str, nav_html: str, body: str,
               tape_html: str = "", chat_html: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="900">
<title>{title}</title><style>{CSS}</style></head><body>
<header>
  <div>
    <div class="wordmark">VIG</div>
    <div class="tagline">the house takes its cut — <b>systematic daily desk</b></div>
  </div>
  <div class="stamp-date">{generated_at.replace("T", " · ")}<br>{nav_html}</div>
</header>
{tape_html}
<div class="wrap">{body}</div>
<footer>Research tooling output — signals from backtested models with modest,
documented edges (weekly IC ≈ 0.017; see RESEARCH_NOTES.md). Probabilities are
calibrated conviction, not certainty. Not investment advice.</footer>
{chat_html}
</body></html>"""


def _tape(snapshot: pd.DataFrame) -> str:
    bits = []
    for tick, r in snapshot.iterrows():
        if pd.isna(r["ret_1d"]):
            continue
        cls = "up" if r["ret_1d"] >= 0 else "dn"
        arrow = "▲" if r["ret_1d"] >= 0 else "▼"
        side = "L" if r["target_position"] > 0 else ("S" if r["target_position"] < 0 else "·")
        bits.append(f'<span><b>{tick}</b> <span class="{cls}">{arrow} '
                    f'{r["ret_1d"] * 100:+.2f}%</span> {side}{abs(r["target_position"]):.1f}</span>')
    row = "".join(bits)
    return f'<div class="tape"><div class="tape-inner">{row}{row}</div></div>'


def _health_panel(health: dict | None) -> str:
    if not health:
        return ""
    model_led = health.get("model_status", "warming")
    ic_t = health.get("ic_t")
    ic_line = ("—" if pd.isna(health.get("ic_mean", float("nan")))
               else f'{health["ic_mean"]:+.3f} <span class="muted">'
                    f'(t={ic_t:.1f}, {health["n_scored"]} wks)</span>')
    spread = health.get("spread_bps")
    spread_line = ("—" if spread is None or pd.isna(spread)
                   else f"{spread:+.0f} bps / 5d")
    data_led = health.get("data_status", "yellow")
    age = health.get("data_age_bdays", "?")
    return f"""
<h2>Model health <span class="dim">/ trust gate</span></h2>
<div class="health">
  <div class="htile"><div class="hlabel">Live edge — trailing {health.get("window", 26)}w IC</div>
    <div class="hval"><span class="led {model_led}"></span>{ic_line}</div>
    <div class="hdetail">{html_mod.escape(str(health.get("model_detail", "")))}</div></div>
  <div class="htile"><div class="hlabel">Realized decile spread</div>
    <div class="hval"><span class="led {model_led}"></span>{spread_line}</div>
    <div class="hdetail">top vs bottom decile, realized, gross</div></div>
  <div class="htile"><div class="hlabel">Data freshness</div>
    <div class="hval"><span class="led {data_led}"></span>{age} bday(s) old</div>
    <div class="hdetail">every prediction is scored once its 5-day horizon completes</div></div>
</div>
<div class="edgemath">EDGE MATH, HONESTLY — at the backtested best case (monthly
config, net Sharpe ≈ 0.26) the half-Kelly growth rate is ≈ Sharpe²/4 ≈
<b>1.7%/yr</b> per unit of gross. Vig compounds calibration and discipline;
the money, if ever, follows the process — not the other way round.</div>"""


def _trade_card(trade: dict, spark: list[float]) -> str:
    side = trade["side"].lower()
    fill = "#46ff9a" if side == "long" else "#ff5d5d"
    why = "".join(f"<li>{html_mod.escape(d)}</li>" for d in trade["drivers"])
    news = ""
    if trade["headline"]:
        h = trade["headline"]
        provider = f' <span class="muted">— {html_mod.escape(h["provider"])}</span>' if h["provider"] else ""
        news = (f'<div class="news">▤ <a href="{html_mod.escape(h["url"])}" '
                f'target="_blank">{html_mod.escape(h["title"])}</a>{provider}</div>')
    pct90 = ""
    if len(spark) > 1 and spark[0]:
        chg = (spark[-1] / spark[0] - 1) * 100
        cls = "pos" if chg >= 0 else "neg"
        pct90 = f'<span class="{cls}">{chg:+.1f}%/90d</span>'
    return f"""
<div class="card {side}">
  <div class="cardtop">
    <span class="tick">{trade["ticker"]}</span>
    <span class="stamp {side}">{trade["side"]}</span>
  </div>
  {_spark_svg(spark)}
  <div class="probrow">
    <div class="probbar"><div class="probfill" style="width:{trade["prob"] * 100:.0f}%;background:{fill}"></div></div>
    <span class="probtxt">P(out) {trade["prob"]:.3f} · edge {trade["edge_pct"]:+.1f}pp {pct90}</span>
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
            f'<tr data-search="{lo} {sh}" data-class="stock" '
            f'data-prob="{t.at[lo, "prob_outperform"]:.3f}">'
            f'<td><b>{lo}</b></td>'
            f'<td class="pos">{t.at[lo, "prob_outperform"]:.3f}</td>'
            f'<td><b>{sh}</b></td>'
            f'<td class="neg">{t.at[sh, "prob_outperform"]:.3f}</td></tr>'
        )
    return ("<table><tr><th>Long book</th><th>P(out)</th>"
            "<th>Short book</th><th>P(out)</th></tr>" + "".join(rows) + "</table>")


def _trend_table(snapshot: pd.DataFrame, k: int = 18) -> str:
    top = snapshot.reindex(
        snapshot["target_position"].abs().sort_values(ascending=False).index
    ).head(k)
    rows = []
    for tick, r in top.iterrows():
        side = "LONG" if r["target_position"] > 0 else ("SHORT" if r["target_position"] < 0 else "—")
        cls = "pos" if r["target_position"] > 0 else "neg"
        r21 = "—" if pd.isna(r["ret_21d"]) else f"{r['ret_21d'] * 100:+.1f}%"
        rows.append(
            f'<tr data-search="{tick}" data-class="{r["asset_class"]}" data-side="{side}">'
            f'<td><b>{tick}</b> <span class="muted">{r["asset_class"]}</span></td>'
            f'<td>{r21}</td><td>{r["ann_vol_63d"] * 100:.0f}%</td>'
            f'<td class="{cls}">{side} {abs(r["target_position"]):.2f}x</td></tr>'
        )
    return ("<table><tr><th>Instrument</th><th>21d</th><th>Vol</th>"
            "<th>Trend position</th></tr>" + "".join(rows) + "</table>")


def _positioning_panel(sectors: dict, tilts: dict, regime: dict) -> str:
    if not sectors and not tilts:
        return ""
    sec_rows = []
    if sectors:
        all_secs = sorted(set(sectors["long"]) | set(sectors["short"]),
                          key=lambda s: -(sectors["long"].get(s, 0)
                                          - sectors["short"].get(s, 0)))
        max_n = max([*sectors["long"].values(), *sectors["short"].values(), 1])
        for s in all_secs:
            ln, sh = sectors["long"].get(s, 0), sectors["short"].get(s, 0)
            net = ln - sh
            cls = "pos" if net > 0 else ("neg" if net < 0 else "muted")
            lbar = f'<div style="display:inline-block;height:8px;width:{ln / max_n * 70}px;background:#46ff9a"></div>'
            sbar = f'<div style="display:inline-block;height:8px;width:{sh / max_n * 70}px;background:#ff5d5d"></div>'
            sec_rows.append(
                f'<tr><td>{s}</td><td>{lbar} {ln}</td><td>{sbar} {sh}</td>'
                f'<td class="{cls}">{net:+d}</td></tr>')
    tilt_rows = []
    for label, d in tilts.items():
        spread = d["long"] - d["short"]
        cls = "pos" if spread > 0 else "neg"
        tilt_rows.append(
            f'<tr><td>{label}</td><td class="pos">{d["long"]:.0f}th</td>'
            f'<td class="neg">{d["short"]:.0f}th</td>'
            f'<td class="{cls}">{spread:+.0f}pp</td></tr>')
    corr = regime.get("stock_bond_corr63")
    if corr is None:
        regime_line = ""
    else:
        verdict = ("bonds are hedging equities — diversification working"
                   if corr < -0.2 else
                   "stocks and bonds moving TOGETHER — diversification weak, "
                   "risk-parity style books run hotter than their vol suggests"
                   if corr > 0.2 else "neutral coupling")
        regime_line = (f'<div class="edgemath">REGIME — 63d stock-bond correlation '
                       f'<b>{corr:+.2f}</b>: {verdict}.</div>')
    return f"""
<h2>Positioning intelligence <span class="dim">/ what the books are actually made of</span></h2>
<div class="cols">
  <div><table><tr><th>Sector</th><th>Longs</th><th>Shorts</th><th>Net</th></tr>
  {"".join(sec_rows)}</table></div>
  <div><table><tr><th>Factor (avg xsec percentile)</th><th>Long book</th><th>Short book</th><th>Spread</th></tr>
  {"".join(tilt_rows)}</table>
  {regime_line}</div>
</div>"""


def _commentary_html(text: str) -> str:
    paras = []
    for block in text.split("\n\n"):
        b = html_mod.escape(block.strip())
        if not b:
            continue
        while "**" in b:
            b = b.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
        paras.append(f"<p>{b}</p>")
    return "".join(paras)


def _desk_context(result: dict) -> dict:
    t = result["xsec"]["table"]
    snap = result["snapshot"]
    top_trend = snap.reindex(
        snap["target_position"].abs().sort_values(ascending=False).index).head(12)
    return {
        "data_through": result["data_through"],
        "health": result.get("health", {}),
        "top_trades": [{k: tr[k] for k in ("ticker", "side", "prob", "drivers")}
                       for tr in result["trades"]],
        "long_book": {x: round(float(t.at[x, "prob_outperform"]), 3)
                      for x in result["xsec"]["longs"][:10]},
        "short_book": {x: round(float(t.at[x, "prob_outperform"]), 3)
                       for x in result["xsec"]["shorts"][-10:]},
        "trend_book": {i: {"class": r["asset_class"],
                           "position": round(float(r["target_position"]), 2),
                           "ret_21d": None if pd.isna(r["ret_21d"])
                           else round(float(r["ret_21d"]), 4)}
                       for i, r in top_trend.iterrows()},
        "n_instruments_trend": int(snap.shape[0]),
        "sectors": result.get("sectors", {}),
        "factor_tilts": result.get("factor_tilts", {}),
        "regime": result.get("regime", {}),
        "backtest": "xsec weekly IC 0.0165 (t=3.22); trend/timing do not "
                    "clear costs decisively; see RESEARCH_NOTES",
    }


def render_dashboard(result: dict) -> str:
    from quark.reports.chat_widget import chat_widget
    trades_html = "".join(
        _trade_card(t, result["sparks"].get(t["ticker"], []))
        for t in result["trades"]
    )
    commentary = ""
    if result["commentary"]:
        commentary = (f'<h2>Vig&rsquo;s commentary</h2>'
                      f'<div class="commentary">{_commentary_html(result["commentary"])}</div>')

    body = f"""
<div class="tagline" style="margin-bottom:6px">data through
<b>{result["data_through"]}</b> · universe <b>{result["xsec"]["n_universe"]}</b> names ·
as-of rebalance <b>{result["xsec"]["as_of"].date()}</b> · horizon <b>5 trading days</b></div>
{_health_panel(result.get("health"))}
<h2>Top trades <span class="dim">/ today</span></h2>
<div class="cards">{trades_html}</div>
{_positioning_panel(result.get("sectors", {}), result.get("factor_tilts", {}),
                    result.get("regime", {}))}
{commentary}
<h2>The books</h2>
<div class="cols">
  <div>{_xsec_table(result["xsec"])}</div>
  <div>{_trend_table(result["snapshot"])}</div>
</div>"""

    return page_shell(
        "Vig — Daily Desk", result["generated_at"],
        '<a class="btn" href="analysis.html">◈ analysis</a> '
        '<a class="btn" href="portfolio.html">◈ portfolio</a> '
        '<a class="btn" href="past_trades.html">◈ past trades</a>',
        body, tape_html=_tape(result["snapshot"]),
        chat_html=chat_widget(_desk_context(result), "desk"),
    )
