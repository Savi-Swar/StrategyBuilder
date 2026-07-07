"""The Past Trades page: a year of weekly top-3 calls, each graded against
what actually happened, plus Vig's self-diagnosis."""

import html as html_mod

from quark.reports.dashboard import _spark_svg, page_shell


def _tiles(s: dict) -> str:
    return f"""
<div class="health">
  <div class="htile"><div class="hlabel">Relative hit rate</div>
    <div class="hval">{s["hit_rel"]:.0%} <span class="muted">of {s["n_trades"]} calls</span></div>
    <div class="hdetail">beat the S&P median over 5d (the model's actual claim)</div></div>
  <div class="htile"><div class="hlabel">Avg edge per call</div>
    <div class="hval">{s["avg_rel_bps"]:+.0f} bps <span class="muted">/ 5d, vs median</span></div>
    <div class="hdetail">absolute P&amp;L basis: {s["avg_pnl_bps"]:+.0f} bps, hit {s["hit_abs"]:.0%}</div></div>
  <div class="htile"><div class="hlabel">Coverage</div>
    <div class="hval">{s["n_weeks"]} weeks</div>
    <div class="hdetail">longest losing streak: {s["max_losing_streak"]} weeks</div></div>
</div>"""


def _breakdown_tables(s: dict) -> str:
    side_rows = "".join(
        f'<tr><td><b>{side}</b></td><td>{d["n"]}</td>'
        f'<td>{d["hit_rel"]:.0%}</td><td class="{"pos" if d["avg_rel_bps"] >= 0 else "neg"}">'
        f'{d["avg_rel_bps"]:+.0f} bps</td></tr>'
        for side, d in s["by_side"].items()
    )
    conv_rows = "".join(
        f'<tr><td><b>{b["bucket"]}</b></td><td>{b["n"]}</td>'
        f'<td>{b["hit_rel"]:.0%}</td><td class="{"pos" if b["avg_rel_bps"] >= 0 else "neg"}">'
        f'{b["avg_rel_bps"]:+.0f} bps</td></tr>'
        for b in s["by_conviction"]
    )
    return f"""
<div class="cols">
  <div><table><tr><th>Side</th><th>N</th><th>Hit</th><th>Avg edge</th></tr>{side_rows}</table></div>
  <div><table><tr><th>Conviction</th><th>N</th><th>Hit</th><th>Avg edge</th></tr>{conv_rows}</table></div>
</div>"""


def _log_table(trades) -> str:
    rows = []
    for _, r in trades.sort_values(["as_of", "conviction"],
                                   ascending=[False, False]).iterrows():
        side_cls = "pos" if r["side"] == "LONG" else "neg"
        grade = '<span class="win">✓ WIN</span>' if r["win_rel"] else '<span class="loss">✗ LOSS</span>'
        rows.append(
            f'<tr><td class="muted">{r["as_of"].date()}</td>'
            f'<td><b>{r["ticker"]}</b></td>'
            f'<td class="{side_cls}">{r["side"]}</td>'
            f'<td>{r["prob"]:.3f}</td>'
            f'<td class="{"pos" if r["ret_5d"] >= 0 else "neg"}">{r["ret_5d"] * 100:+.2f}%</td>'
            f'<td class="{"pos" if r["rel_5d"] >= 0 else "neg"}">{r["rel_5d"] * 100:+.2f}%</td>'
            f'<td>{grade}</td></tr>'
        )
    return ("<table><tr><th>Week</th><th>Ticker</th><th>Side</th><th>P(out)</th>"
            "<th>5d return</th><th>vs median</th><th>Grade</th></tr>"
            + "".join(rows) + "</table>")


def render_review_page(review: dict, generated_at: str,
                       self_review: str | None = None) -> str:
    trades, s = review["trades"], review["summary"]
    if trades is None or trades.empty:
        body = ('<h2>Past trades</h2><p class="muted">No scored history yet — '
                'run scripts/backfill_ledger.py.</p>')
        return page_shell("Vig — Past Trades", generated_at,
                          '<a class="btn" href="index.html">◈ back to desk</a>', body)

    curve = _spark_svg(s["cum_rel"], width=920, height=140, color="#ffb000",
                       cls="spark")
    lessons = "".join(f"<li>{html_mod.escape(x)}</li>" for x in review["lessons"])
    self_html = ""
    if self_review:
        paras = "".join(f"<p>{html_mod.escape(p)}</p>"
                        for p in self_review.split("\n\n") if p.strip())
        self_html = (f'<h2>Vig&rsquo;s self-review</h2>'
                     f'<div class="commentary">{paras}</div>')

    body = f"""
<h2>The record <span class="dim">/ weekly top-3, graded after each 5-day horizon</span></h2>
{_tiles(s)}
<h2>Cumulative edge <span class="dim">/ mean top-3 return vs S&amp;P median, compounding weekly</span></h2>
<div class="bigchart">{curve}
  <div class="hdetail">final: {s["cum_rel"][-1] * 100:+.1f}% relative over {s["n_weeks"]} weeks
  (gross, before costs — the honest yardstick of pick quality, not a P&amp;L)</div></div>
<h2>Where the edge lives</h2>
{_breakdown_tables(s)}
<h2>Self-diagnosis <span class="dim">/ computed from the record, regenerated daily</span></h2>
<div class="commentary"><ul class="why">{lessons}</ul></div>
{self_html}
<h2>Every call <span class="dim">/ most recent first</span></h2>
{_log_table(trades)}"""

    return page_shell("Vig — Past Trades", generated_at,
                      '<a class="btn" href="index.html">◈ back to desk</a>', body)
