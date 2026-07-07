"""The Analysis page: today's wire as linked article cards, cross-referenced
against the desk's live positioning, with a grounded desk read."""

import html as html_mod
from datetime import datetime, timezone

import pandas as pd

from quark.reports.dashboard import filter_bar, page_shell

EXTRA_CSS = """
<style>
.wiregrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }
.art { background: #0b0d10; border: 1px solid #22262c; padding: 16px 18px;
       display: flex; flex-direction: column; gap: 9px; }
.art .meta { display: flex; justify-content: space-between; font-size: 10.5px;
             color: #6d747c; letter-spacing: 1px; text-transform: uppercase; }
.art a.t { color: #e6e2d8; text-decoration: none; font-size: 13.5px;
           line-height: 1.55; font-weight: 600; }
.art a.t:hover { color: #ffb000; }
.art .foot { display: flex; gap: 8px; align-items: center; margin-top: auto; }
.tickchip { border: 1px solid #2a2e35; padding: 2px 9px; font-size: 11px;
            color: #ffb000; }
.stance { font-size: 10.5px; letter-spacing: 1px; padding: 2px 8px; border: 1px solid; }
.stance.l { color: #46ff9a; border-color: rgba(52,211,153,.4); }
.stance.s { color: #ff5d5d; border-color: rgba(248,113,113,.4); }
.stance.n { color: #6d747c; border-color: #2a2e35; }
</style>"""


def _ago(published: str) -> str:
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        hrs = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        if hrs < 1:
            return f"{int(hrs * 60)}m ago"
        if hrs < 36:
            return f"{int(hrs)}h ago"
        return f"{int(hrs / 24)}d ago"
    except (ValueError, TypeError):
        return ""


def _stance_chip(stance: dict) -> str:
    side = stance.get("side", "")
    cls = "l" if "LONG" in side else ("s" if "SHORT" in side else "n")
    if stance["kind"] == "trend" and side != "FLAT":
        label = f'{side} {stance["size"]}x'
    elif stance["kind"] == "xsec" and "BOOK" in side:
        label = f'{side} · P {stance["prob"]}'
    elif stance["kind"] == "xsec":
        label = f'no position · P {stance["prob"]}'
    else:
        label = side
    return f'<span class="stance {cls}">{label}</span>'


def _cards(articles: list[dict], group: str) -> str:
    cards = []
    for a in articles:
        if a["group"] != group:
            continue
        provider = html_mod.escape(a.get("provider") or "wire")
        side = a["stance"].get("side", "")
        side_attr = "LONG" if "LONG" in side else ("SHORT" if "SHORT" in side else "")
        prob = a["stance"].get("prob")
        cards.append(f"""
<div class="art" data-search="{a["ticker"]} {html_mod.escape(a["title"].lower())}"
     data-class="{a["group"]}" data-side="{side_attr}"
     {f'data-prob="{prob}"' if prob is not None else ""}>
  <div class="meta"><span>{provider}</span><span>{_ago(a.get("published", ""))}</span></div>
  <a class="t" href="{html_mod.escape(a["url"])}" target="_blank">{html_mod.escape(a["title"])}</a>
  <div class="foot"><span class="tickchip">{a["ticker"]}</span>{_stance_chip(a["stance"])}</div>
</div>""")
    return f'<div class="wiregrid">{"".join(cards)}</div>' if cards else \
        '<p class="muted">nothing on this wire today</p>'


def _board_table(board: pd.DataFrame) -> str:
    rows = []
    for tick, r in board.iterrows():
        c = int(r["consensus"])
        ccls = "pos" if c >= 3 else ("neg" if c <= -3 else "muted")
        side_attr = "LONG" if c > 0 else ("SHORT" if c < 0 else "")
        rsi_cls = "pos" if r["rsi14"] > 50 else "neg"
        rsi_note = " OB" if r["rsi14"] > 70 else (" OS" if r["rsi14"] < 30 else "")
        vwap = ("—" if pd.isna(r["vwap_dist"])
                else f'<span class="{"pos" if r["vwap_dist"] > 0 else "neg"}">'
                     f'{r["vwap_dist"] * 100:+.1f}%</span>')
        mom = ("—" if pd.isna(r["mom252"])
               else f'<span class="{"pos" if r["mom252"] > 0 else "neg"}">'
                    f'{r["mom252"] * 100:+.0f}%</span>')
        rows.append(
            f'<tr data-search="{tick}" data-class="{r["asset_class"]}" '
            f'data-side="{side_attr}">'
            f'<td><b>{tick}</b> <span class="muted">{r["asset_class"]}</span></td>'
            f'<td class="{rsi_cls}">{r["rsi14"]:.0f}{rsi_note}</td>'
            f'<td class="{"pos" if r["pctb"] > 0.5 else "neg"}">{r["pctb"]:.2f}</td>'
            f'<td class="{"pos" if r["macd_bps"] > 0 else "neg"}">{r["macd_bps"]:+.1f}</td>'
            f'<td class="{"pos" if r["golden"] else "neg"}">'
            f'{"GOLDEN" if r["golden"] else "DEATH"}</td>'
            f'<td>{vwap}</td><td>{mom}</td>'
            f'<td class="{ccls}"><b>{c:+d}</b></td></tr>')
    return ("<table><tr><th>Instrument</th><th>RSI14</th><th>Boll %B</th>"
            "<th>MACD bps</th><th>50/200</th><th>vs VWAP20</th><th>12m</th>"
            "<th>Consensus</th></tr>" + "".join(rows) + "</table>")


def _heat_table(heat: list) -> str:
    rows = []
    for tick, h in heat[:12]:
        s = h["stance"]
        if s["kind"] == "trend":
            desk = f'{s["side"]} {s.get("size", "")}x' if s["side"] != "FLAT" else "flat"
            cls = "pos" if s["side"] == "LONG" else ("neg" if s["side"] == "SHORT" else "muted")
        elif s["kind"] == "xsec":
            desk, cls = f'{s["side"]} · P {s.get("prob", "")}', \
                ("pos" if "LONG" in s["side"] else ("neg" if "SHORT" in s["side"] else "muted"))
        else:
            desk, cls = "not covered", "muted"
        rows.append(f'<tr data-search="{tick}"><td><b>{tick}</b></td>'
                    f'<td>{"▮" * min(h["n"], 8)} {h["n"]}</td>'
                    f'<td class="{cls}">{desk}</td></tr>')
    return ("<table><tr><th>Instrument</th><th>Wire heat</th><th>Desk stance</th></tr>"
            + "".join(rows) + "</table>")


def render_analysis_page(wire: dict, generated_at: str,
                         desk_read: str | None = None,
                         board: pd.DataFrame | None = None) -> str:
    from quark.reports.dashboard import _commentary_html
    read_html = ""
    if desk_read:
        read_html = (f'<h2>Desk read <span class="dim">/ Vig, grounded in the wire '
                     f'and the book</span></h2>'
                     f'<div class="commentary">{_commentary_html(desk_read)}</div>')
    else:
        bullets = "".join(f"<li>{html_mod.escape(b)}</li>" for b in wire["bullets"])
        read_html = (f'<h2>Desk read <span class="dim">/ computed — the written '
                     f'synthesis activates with an API key</span></h2>'
                     f'<div class="commentary"><ul class="why">{bullets}</ul>'
                     f'<p class="muted" style="margin-top:10px;font-size:11.5px">'
                     f'Vig trades prices, not narratives: headlines here are context '
                     f'for the human, never inputs to the model.</p></div>')

    board_html = ""
    fb_classes = ["macro", "picks"]
    if board is not None and not board.empty:
        fb_classes = sorted(board["asset_class"].unique()) + ["macro", "picks"]
        board_html = f"""
<h2>Technical board <span class="dim">/ the original toolkit — RSI, Bollinger,
MACD, golden cross, VWAP, momentum — as a read of the tape</span></h2>
{_board_table(board)}
<div class="edgemath">HONESTY — these are the exact indicators Study 1
backtested; net of costs none cleared the Deflated Sharpe bar as standalone
strategies (best DSR 0.29). The board describes market state; the consensus
column measures agreement, not edge.</div>"""

    body = f"""{EXTRA_CSS}
{filter_bar(fb_classes)}
{board_html}
<h2>Macro wire <span class="dim">/ indices, rates, energy, gold, crypto, fx</span></h2>
{_cards(wire["articles"], "macro")}
<h2>Single names on the desk <span class="dim">/ today's picks in the news</span></h2>
{_cards(wire["articles"], "picks")}
<h2>Wire vs desk <span class="dim">/ what's loud vs where the book stands</span></h2>
{_heat_table(wire["heat"])}
{read_html}"""

    return page_shell(
        "Vig — Analysis", generated_at,
        '<a class="btn" href="index.html">◈ desk</a> '
        '<a class="btn" href="past_trades.html">◈ past trades</a> '
        '<a class="btn" href="portfolio.html">◈ portfolio</a>',
        body)
