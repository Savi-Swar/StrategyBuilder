"""The Analysis page: today's wire as linked article cards, cross-referenced
against the desk's live positioning, with a grounded desk read."""

import html as html_mod
from datetime import datetime, timezone

from quark.reports.chat_widget import chat_widget
from quark.reports.dashboard import page_shell

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
        cards.append(f"""
<div class="art">
  <div class="meta"><span>{provider}</span><span>{_ago(a.get("published", ""))}</span></div>
  <a class="t" href="{html_mod.escape(a["url"])}" target="_blank">{html_mod.escape(a["title"])}</a>
  <div class="foot"><span class="tickchip">{a["ticker"]}</span>{_stance_chip(a["stance"])}</div>
</div>""")
    return f'<div class="wiregrid">{"".join(cards)}</div>' if cards else \
        '<p class="muted">nothing on this wire today</p>'


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
                         desk_read: str | None = None) -> str:
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

    body = f"""{EXTRA_CSS}
<h2>Macro wire <span class="dim">/ indices, rates, energy, gold, crypto, fx</span></h2>
{_cards(wire["articles"], "macro")}
<h2>Single names on the desk <span class="dim">/ today's picks in the news</span></h2>
{_cards(wire["articles"], "picks")}
<h2>Wire vs desk <span class="dim">/ what's loud vs where the book stands</span></h2>
{_heat_table(wire["heat"])}
{read_html}"""

    ctx = {"articles": [{"ticker": a["ticker"], "title": a["title"],
                         "stance": a["stance"]} for a in wire["articles"]],
           "wire_vs_desk": wire["bullets"]}
    return page_shell(
        "Vig — Analysis", generated_at,
        '<a class="btn" href="index.html">◈ desk</a> '
        '<a class="btn" href="past_trades.html">◈ past trades</a> '
        '<a class="btn" href="portfolio.html">◈ portfolio</a>',
        body, chat_html=chat_widget(ctx, "analysis"))
