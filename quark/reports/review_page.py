"""The Past Trades page: YOUR journal graded trade by trade (with a coach
that refines its diagnosis as the record grows), followed by the model's own
graded record and self-diagnosis. Same standard for human and machine."""

import html as html_mod

from quark.reports.dashboard import _spark_svg, page_shell

JOURNAL_JS = r"""
<script>
(() => {
const $ = id => document.getElementById(id);
const INST = () => window.VIG_INSTRUMENTS || {};
const DATES = () => window.VIG_DATES || [];
const J = () => JSON.parse(localStorage.getItem("vig_journal") || "[]");
const saveJ = j => localStorage.setItem("vig_journal", JSON.stringify(j));
const fmt$ = x => (x < 0 ? "-$" : "$") + Math.abs(Math.round(x)).toLocaleString();
const pctf = x => (x >= 0 ? "+" : "") + (100 * x).toFixed(1) + "%";
const cls = x => x >= 0 ? "pos" : "neg";
const todayISO = () => new Date().toISOString().slice(0, 10);

function pxOn(t, iso) {
  const d = INST()[t]; if (!d) return null;
  const ds = DATES();
  let i = ds.indexOf(iso);
  if (i < 0) { i = ds.findIndex(x => x > iso); i = i < 0 ? ds.length - 1 : i - 1; }
  for (; i >= 0; i--) if (d.px[i] != null) return d.px[i];
  return null;
}
function spxWin(fromISO, toISO) {
  const a = pxOn("^GSPC", fromISO);
  const b = toISO ? pxOn("^GSPC", toISO) : (INST()["^GSPC"] || {}).l;
  return (a && b) ? b / a - 1 : null;
}
function grade(tr) {
  const last = tr.exit ?? (INST()[tr.t] || {}).l ?? null;
  if (!tr.entry || !last) return null;
  const raw = last / tr.entry - 1;
  const signed = tr.side === "SHORT" ? -raw : raw;
  const spx = spxWin(tr.entryDate, tr.exitDate) ?? 0;
  const end = tr.exitDate ? new Date(tr.exitDate) : new Date();
  const days = Math.max(1, Math.round((end - new Date(tr.entryDate)) / 864e5));
  return { signed, pnl: tr.usd * signed, alpha: signed - spx, spx, days, last };
}
const mv = tr => tr.mdec === "L" ? '<span class="pos">agreed (long decile)</span>'
  : tr.mdec === "S" ? '<span class="neg">AGAINST model (short decile)</span>'
  : `<span class="muted">${tr.mprob != null ? "P " + tr.mprob : "no view"}</span>`;

function coach(closed) {
  const out = [];
  const g = closed.map(tr => ({ tr, r: grade(tr) })).filter(x => x.r);
  const n = g.length;
  if (!n) return ["No closed trades yet. Log every trade — especially the " +
    "embarrassing ones; a journal that flatters you teaches nothing."];
  if (n < 5) out.push(`${n} closed trade(s) — patterns below are provisional; ` +
    "verdicts need 10+. Keep logging.");
  const wins = g.filter(x => x.r.pnl > 0), losses = g.filter(x => x.r.pnl <= 0);
  const hit = wins.length / n;
  const aHit = g.filter(x => x.r.alpha > 0).length / n;
  const t = (hit - 0.5) / Math.sqrt(0.25 / n);
  out.push(`Hit rate ${(100 * hit).toFixed(0)}% over ${n} closed ` +
    `(t≈${t.toFixed(1)} vs coin-flip); beating the S&P over the same windows ` +
    `${(100 * aHit).toFixed(0)}% of the time.`);
  const totPnl = g.reduce((s, x) => s + x.r.pnl, 0);
  const totAlpha = g.reduce((s, x) => s + x.r.alpha * x.tr.usd, 0);
  if (totPnl > 0 && totAlpha < 0)
    out.push(`You are UP ${fmt$(totPnl)} but ${fmt$(totAlpha)} vs just holding ` +
      "SPY over the same windows — that profit is beta, not skill. The tape " +
      "was your edge, not the picks.");
  if (wins.length && losses.length) {
    const aw = wins.reduce((s, x) => s + x.r.signed, 0) / wins.length;
    const al = -losses.reduce((s, x) => s + x.r.signed, 0) / losses.length;
    if (al > aw * 1.3)
      out.push(`Average loss ${pctf(-al)} vs average win ${pctf(aw)} — the ` +
        "classic asymmetry: winners cut early, losers given 'time to come " +
        "back'. Decide the exit BEFORE entry.");
    const dw = wins.reduce((s, x) => s + x.r.days, 0) / wins.length;
    const dl = losses.reduce((s, x) => s + x.r.days, 0) / losses.length;
    if (dl > dw * 1.5)
      out.push(`Losers held ${dl.toFixed(0)} days on average vs ` +
        `${dw.toFixed(0)} for winners — hope is not a holding period.`);
  }
  const against = g.filter(x => x.tr.mdec === "S" && x.tr.side === "LONG");
  if (against.length >= 3) {
    const ah = against.filter(x => x.r.pnl > 0).length / against.length;
    out.push(`${against.length} longs entered while the name sat in Vig's ` +
      `SHORT decile: hit ${(100 * ah).toFixed(0)}%. ` +
      (ah < hit ? "Fighting the model has cost you — at least size those smaller."
                : "You've beaten the model on these — noted, but the sample is small."));
  }
  if (n >= 10) {
    const gw = wins.reduce((s, x) => s + x.r.pnl, 0);
    const gl = -losses.reduce((s, x) => s + x.r.pnl, 0);
    out.push(`Profit factor ${(gl > 0 ? gw / gl : Infinity).toFixed(2)} ` +
      "(gross wins / gross losses) — above ~1.5 is a real edge, near 1.0 is " +
      "churn paying your broker.");
  }
  return out;
}

function render() {
  const j = J();
  const open = j.filter(x => !x.exitDate), closed = j.filter(x => x.exitDate);

  $("jn-open").innerHTML = open.map((tr, i) => {
    const r = grade(tr);
    return `<tr data-search="${tr.t}"><td><b>${tr.t}</b> <span class="${tr.side === "LONG" ? "pos" : "neg"}">${tr.side}</span></td>
      <td class="tl muted">${tr.entryDate}${tr.note ? " · " + tr.note : ""}</td>
      <td>${fmt$(tr.usd)}</td><td>${tr.entry}</td>
      <td>${r ? r.last.toLocaleString() : "—"}</td>
      <td class="${r ? cls(r.pnl) : "muted"}">${r ? fmt$(r.pnl) + " (" + pctf(r.signed) + ")" : "—"}</td>
      <td class="${r ? cls(r.alpha) : "muted"}">${r ? pctf(r.alpha) : "—"}</td>
      <td class="tl">${mv(tr)}</td>
      <td class="tl">${(() => { const d = INST()[tr.t]; const p = d && d.h && d.h["1W"];
        return p != null ? "P " + p.toFixed(3) : "—"; })()}</td>
      <td><span class="tk-x" data-close="${j.indexOf(tr)}" style="color:#ffb000">CLOSE</span>
      <span class="tk-x" data-del="${j.indexOf(tr)}">✕</span></td></tr>`;
  }).join("") || '<tr><td colspan="10" class="muted tl">no open positions</td></tr>';

  $("jn-closed").innerHTML = closed.map(tr => {
    const r = grade(tr);
    if (!r) return "";
    const win = r.pnl > 0, awin = r.alpha > 0;
    return `<tr data-search="${tr.t}"><td><b>${tr.t}</b> <span class="${tr.side === "LONG" ? "pos" : "neg"}">${tr.side}</span></td>
      <td class="tl muted">${tr.entryDate} → ${tr.exitDate} (${r.days}d)</td>
      <td>${fmt$(tr.usd)}</td><td>${tr.entry} → ${tr.exit}</td>
      <td class="${cls(r.pnl)}">${fmt$(r.pnl)}</td>
      <td class="${cls(r.signed)}">${pctf(r.signed)}</td>
      <td class="${cls(r.alpha)}">${pctf(r.alpha)}</td>
      <td>${win ? '<span class="win">✓' : '<span class="loss">✗'}${awin ? " +α" : ""}</span></td>
      <td class="tl">${mv(tr)}</td>
      <td><span class="tk-x" data-del="${j.indexOf(tr)}">✕</span></td></tr>`;
  }).join("") || '<tr><td colspan="10" class="muted tl">nothing closed yet</td></tr>';

  const g = closed.map(tr => grade(tr)).filter(Boolean);
  const totPnl = g.reduce((s, r) => s + r.pnl, 0);
  const openPnl = open.map(tr => grade(tr)).filter(Boolean)
                      .reduce((s, r) => s + r.pnl, 0);
  const totAlpha$ = closed.map((tr, i) => ({ tr, r: grade(tr) }))
    .filter(x => x.r).reduce((s, x) => s + x.r.alpha * x.tr.usd, 0);
  $("jn-tiles").innerHTML = [
    ["Realized P&L", `<span class="${cls(totPnl)}">${fmt$(totPnl)}</span>`,
     `${closed.length} closed`],
    ["Open P&L (marked)", `<span class="${cls(openPnl)}">${fmt$(openPnl)}</span>`,
     `${open.length} open`],
    ["Alpha vs S&P, realized", `<span class="${cls(totAlpha$)}">${fmt$(totAlpha$)}</span>`,
     "same-window benchmark — profit isn't skill if SPY did better"],
  ].map(([k, v, d]) => `<div class="htile"><div class="hlabel">${k}</div>
    <div class="hval">${v}</div><div class="hdetail">${d}</div></div>`).join("");

  $("jn-coach").innerHTML = coach(closed).map(x => `<li>${x}</li>`).join("");

  document.querySelectorAll("[data-close]").forEach(el =>
    el.addEventListener("click", () => {
      const j2 = J(), tr = j2[+el.dataset.close];
      const d = INST()[tr.t];
      const px = prompt(`Exit price for ${tr.t}:`, d ? d.l : tr.entry);
      if (px == null) return;
      tr.exit = parseFloat(px); tr.exitDate = todayISO();
      saveJ(j2); render();
    }));
  document.querySelectorAll("[data-del]").forEach(el =>
    el.addEventListener("click", () => {
      if (!confirm("Delete this trade from the journal?")) return;
      const j2 = J(); j2.splice(+el.dataset.del, 1); saveJ(j2); render();
    }));
}

document.addEventListener("DOMContentLoaded", () => {
  $("jn-date").value = todayISO();
  $("jn-t").addEventListener("blur", () => {
    const d = INST()[$("jn-t").value.trim().toUpperCase()];
    if (d && !$("jn-px").value) $("jn-px").value = d.l;
  });
  $("jn-add").addEventListener("click", () => {
    const t = $("jn-t").value.trim().toUpperCase();
    const usd = parseFloat($("jn-usd").value.replace(/[^0-9.]/g, ""));
    const entry = parseFloat($("jn-px").value);
    const entryDate = $("jn-date").value;
    if (!t || !(usd > 0) || !(entry > 0) || !entryDate)
      { alert("need ticker, size, entry price, entry date"); return; }
    const d = INST()[t];
    const j = J();
    j.push({ t, side: $("jn-side").value, usd, entry, entryDate,
             note: $("jn-note").value.trim(),
             mprob: d && d.h ? d.h["1W"] : null,
             mdec: d && d.hd ? d.hd["1W"] : "" });
    saveJ(j);
    ["jn-t", "jn-usd", "jn-px", "jn-note"].forEach(id => $(id).value = "");
    render();
  });
  $("jn-claude").addEventListener("click", () => {
    const closed = J().filter(x => x.exitDate);
    navigator.clipboard.writeText(
      "You are a trading coach. Here is my real trade journal, each trade " +
      "graded against price and against the S&P over the same window, plus " +
      "rule-based diagnostics. Give me an honest, specific coaching read — " +
      "patterns, sizing, discipline. Do not flatter me.\n\n" +
      JSON.stringify({ trades: J(), diagnostics: coach(closed) }, null, 1));
  });
  render();
});
})();
</script>"""

JOURNAL_HTML = """
<style>
.tk-form { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end;
  background: #0b0d10; border: 1px solid #22262c; padding: 16px 18px; }
.tk-form input { background: #060708; border: 1px solid #2a2e35; color: #e6e2d8;
  font: 14px "SF Mono", ui-monospace, Menlo, monospace; padding: 9px 12px; }
.tk-form input:focus { outline: none; border-color: #ffb000; }
.pfield label { display: block; font-size: 10px; letter-spacing: 2px;
  text-transform: uppercase; color: #8a9199; margin-bottom: 6px; }
.tk-form button { background: none; border: 1px solid #ffb000; color: #ffb000;
  font: 700 12px "SF Mono", ui-monospace, Menlo, monospace; padding: 10px 16px;
  cursor: pointer; letter-spacing: 1px; }
.tk-form button:hover { background: #ffb000; color: #060708; }
.tk-x { color: #ff5d5d; cursor: pointer; font-size: 12px; margin-left: 6px; }
.tk-tools { display: flex; gap: 8px; margin-top: 10px; align-items: center; }
.tk-tools span { border: 1px solid #2a2e35; color: #8a9199; font-size: 11px;
  padding: 6px 12px; cursor: pointer; }
.tk-tools span:hover { border-color: #ffb000; color: #ffb000; }
</style>
<h2>My journal <span class="dim">/ log your own trades — Vig grades every one
against price AND against the S&amp;P over the same window, then coaches</span></h2>
<div class="tk-form" style="margin-bottom:10px">
  <div class="pfield"><label>Ticker</label><input id="jn-t" placeholder="NVDA" style="width:100px;text-transform:uppercase"></div>
  <div class="pfield"><label>Side</label><select id="jn-side" style="background:#060708;border:1px solid #2a2e35;color:#e6e2d8;padding:10px;font:13px 'SF Mono',monospace"><option>LONG</option><option>SHORT</option></select></div>
  <div class="pfield"><label>Size (USD)</label><input id="jn-usd" inputmode="decimal" placeholder="1,000" style="width:110px"></div>
  <div class="pfield"><label>Entry price</label><input id="jn-px" inputmode="decimal" placeholder="auto" style="width:110px"></div>
  <div class="pfield"><label>Entry date</label><input id="jn-date" type="date" style="background:#060708;border:1px solid #2a2e35;color:#e6e2d8;padding:9px;font:13px 'SF Mono',monospace"></div>
  <div class="pfield"><label>Thesis <span class="muted">(optional)</span></label><input id="jn-note" placeholder="why?" style="width:190px"></div>
  <button id="jn-add">LOG TRADE</button>
</div>
<div class="health" id="jn-tiles" style="margin-bottom:14px"></div>
<div class="vi-sect" style="margin-top:4px">OPEN — marked to last close</div>
<table><tr><th>Trade</th><th class="tl">Entered</th><th>Size</th><th>Entry</th>
<th>Last</th><th>P&amp;L</th><th>vs S&amp;P</th><th class="tl">Model @ entry</th>
<th class="tl">Model now</th><th></th></tr><tbody id="jn-open"></tbody></table>
<div class="vi-sect">CLOSED — the record</div>
<table><tr><th>Trade</th><th class="tl">Held</th><th>Size</th><th>Entry→Exit</th>
<th>P&amp;L $</th><th>P&amp;L %</th><th>vs S&amp;P</th><th>Grade</th>
<th class="tl">Model @ entry</th><th></th></tr><tbody id="jn-closed"></tbody></table>
<div class="vi-sect">The coach <span class="dim" style="text-transform:none;letter-spacing:0">
— rule-based, recomputed on every trade; sharpens as your sample grows</span></div>
<div class="commentary"><ul class="why" id="jn-coach"></ul></div>
<div class="tk-tools"><span id="jn-claude">copy record for Claude</span>
<span class="muted" style="border:none;cursor:default">paste into claude.ai for a
deep coaching read — free with your subscription</span></div>
"""


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
            f'<tr data-search="{r["ticker"]}" data-side="{r["side"]}" '
            f'data-prob="{r["prob"]:.3f}">'
            f'<td class="muted">{r["as_of"].date()}</td>'
            f'<td class="tl"><b>{r["ticker"]}</b></td>'
            f'<td class="{side_cls} tl">{r["side"]}</td>'
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
    from quark.reports.dashboard import filter_bar
    trades, s = review["trades"], review["summary"]
    if trades is None or trades.empty:
        body = ('<h2>Past trades</h2><p class="muted">No scored history yet — '
                'run scripts/backfill_ledger.py.</p>')
        return page_shell("Vig — Past Trades", generated_at,
                          '<a class="btn" href="index.html">◈ desk</a> '
                      '<a class="btn" href="analysis.html">◈ analysis</a> '
                      '<a class="btn" href="portfolio.html">◈ portfolio</a>', body)

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
{JOURNAL_HTML}
{JOURNAL_JS}
<h2>Vig&rsquo;s record <span class="dim">/ weekly top-3, graded after each 5-day horizon
— the machine is held to the same standard as you</span></h2>
{_tiles(s)}
<h2>Cumulative edge <span class="dim">/ mean top-3 return vs S&amp;P median,
summed arithmetically week by week — not compounded, not a P&amp;L</span></h2>
<div class="bigchart">{curve}
  <div class="hdetail">final: {s["cum_rel"][-1] * 100:+.1f} percentage points of
  cumulative relative edge over {s["n_weeks"]} weeks (gross, before costs —
  a yardstick of pick quality)</div></div>
<h2>Where the edge lives</h2>
{_breakdown_tables(s)}
<h2>Self-diagnosis <span class="dim">/ computed from the record, regenerated daily</span></h2>
<div class="commentary"><ul class="why">{lessons}</ul></div>
{self_html}
<h2>Every call <span class="dim">/ most recent first</span></h2>
{filter_bar(classes=None, show_prob=True, show_side=True)}
{_log_table(trades)}"""

    return page_shell("Vig — Past Trades", generated_at, "past_trades", body)
