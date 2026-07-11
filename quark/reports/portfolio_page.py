"""The Portfolio Builder page: capital + risk appetite in, allocation out.
All math beyond the daily precomputation happens in vanilla JS against the
embedded JSON, so the page works from file:// with zero dependencies."""

import json

from quark.reports.dashboard import page_shell

EXTRA_CSS = """
<style>
.pform { display: flex; gap: 26px; flex-wrap: wrap; align-items: flex-end;
         background: #0b0d10; border: 1px solid #22262c; padding: 20px 24px; }
.pfield label { display: block; font-size: 10px; letter-spacing: 2px;
                text-transform: uppercase; color: #8a9199; margin-bottom: 8px; }
input[type=text] {
  background: #060708; border: 1px solid #2a2e35; color: #e6e2d8;
  font: 20px "SF Mono", ui-monospace, Menlo, monospace; padding: 9px 14px; width: 220px;
}
input[type=text]:focus { outline: none; border-color: #ffb000; }
.seg { display: flex; }
.seg button {
  background: #060708; border: 1px solid #2a2e35; color: #8a9199;
  font: 12px "SF Mono", ui-monospace, Menlo, monospace; letter-spacing: 1px;
  padding: 11px 18px; cursor: pointer; text-transform: uppercase;
}
.seg button + button { border-left: none; }
.seg button.on { background: #ffb000; color: #060708; font-weight: 700; }
.allocbar { display: flex; height: 26px; border: 1px solid #22262c; margin: 18px 0 6px; }
.allocbar div { height: 100%; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 11px; color: #8a9199; }
.legend i { display: inline-block; width: 9px; height: 9px; margin-right: 5px; }
.warn { color: #ffb000; font-size: 12px; margin-top: 10px; }
.tk-form { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end;
  background: #0b0d10; border: 1px solid #22262c; padding: 16px 18px; }
.tk-form input { background: #060708; border: 1px solid #2a2e35; color: #e6e2d8;
  font: 14px "SF Mono", ui-monospace, Menlo, monospace; padding: 9px 12px; }
#tk-t { width: 110px; text-transform: uppercase; } #tk-sh { width: 110px; }
#tk-basis { width: 130px; }
.tk-form button, .tk-tools span { background: none; border: 1px solid #ffb000;
  color: #ffb000; font: 700 12px "SF Mono", ui-monospace, Menlo, monospace;
  padding: 10px 16px; cursor: pointer; letter-spacing: 1px; }
.tk-form button:hover, .tk-tools span:hover { background: #ffb000; color: #060708; }
.tk-tools { display: flex; gap: 8px; margin-top: 10px; }
.tk-tools span { padding: 6px 12px; font-weight: 400; border-color: #2a2e35;
  color: #8a9199; }
.tk-x { color: #ff5d5d; cursor: pointer; }
ul.recs { list-style: none; }
ul.recs li { padding: 9px 14px 9px 30px; position: relative; margin-bottom: 8px;
  background: #0b0d10; border: 1px solid #22262c; font-size: 12.5px;
  color: #c9c4b8; }
ul.recs li::before { content: "»"; position: absolute; left: 12px; color: #ffb000; }
ul.recs li.flag { border-left: 3px solid #ff5d5d; }
ul.recs li.good { border-left: 3px solid #46ff9a; }
</style>"""

COLORS = {
    "us_equity": "#46ff9a", "intl_equity": "#2fbf71", "bonds": "#6ea8fe",
    "long_bonds": "#3f6fd8", "gold": "#ffb000", "crypto": "#c084fc",
    "alpha": "#ff8fab", "cash": "#3a4048",
}

LABELS = {
    "us_equity": "US equities", "intl_equity": "Intl equities",
    "bonds": "Bonds 7-10y", "long_bonds": "Long bonds 20y+", "gold": "Gold",
    "crypto": "Bitcoin", "alpha": "Vig alpha sleeve", "cash": "Cash / T-bills",
}

JS = """
<script>
const DATA = __DATA__;
const COLORS = __COLORS__;
const LABELS = __LABELS__;
let profile = "balanced";

const fmt$ = x => "$" + Math.round(x).toLocaleString("en-US");
const pct = x => (100 * x).toFixed(1) + "%";

function capital() {
  const raw = document.getElementById("cap").value.replace(/[^0-9.]/g, "");
  return Math.max(0, parseFloat(raw) || 0);
}

function render() {
  const p = DATA.profiles[profile];
  const cap = capital();
  document.querySelectorAll(".seg button").forEach(b =>
    b.classList.toggle("on", b.dataset.p === profile));

  const parts = Object.entries(p.weights).map(([k, w]) => [k, w]);
  if (p.alpha_w > 0) parts.push(["alpha", p.alpha_w]);
  if (p.cash_w > 0.001) parts.push(["cash", p.cash_w]);

  document.getElementById("bar").innerHTML = parts.map(([k, w]) =>
    `<div style="width:${100 * w}%;background:${COLORS[k]}" title="${LABELS[k]} ${pct(w)}"></div>`).join("");
  document.getElementById("legend").innerHTML = parts.map(([k, w]) =>
    `<span><i style="background:${COLORS[k]}"></i>${LABELS[k]} ${pct(w)}</span>`).join("");

  document.getElementById("rows").innerHTML = parts.map(([k, w]) => {
    const vehicle = k === "cash" ? "SGOV / cash" :
                    k === "alpha" ? `${DATA.alpha_names.length} single names below` :
                    DATA.sleeve_etfs[k];
    return `<tr><td><b>${LABELS[k]}</b></td><td class="muted tl">${vehicle}</td>
      <td>${pct(w)}</td><td><b>${fmt$(cap * w)}</b></td></tr>`;
  }).join("");

  const var95d = 1.645 * p.est_vol / Math.sqrt(252) * cap;
  const var95m = 1.645 * p.est_vol / Math.sqrt(12) * cap;
  const stats = [
    ["Target vol", pct(p.est_vol) + "/yr"],
    ["Hist. CAGR (2004-now, this mix)", pct(p.hist_cagr) + "/yr"],
    ["Worst drawdown (incl. 2008)", pct(p.hist_max_dd)],
    ["Worst year", `${p.worst_year.year}: ${pct(p.worst_year.ret)}`],
    ["VaR 95% (parametric)", `${fmt$(var95d)} / day · ${fmt$(var95m)} / month`],
    ["Expected on your capital", `${fmt$(cap * p.hist_cagr)} avg/yr · swing of ${fmt$(Math.abs(cap * p.hist_max_dd))} at the historical worst`],
  ];
  document.getElementById("stats").innerHTML = stats.map(([k, v]) =>
    `<div class="htile"><div class="hlabel">${k}</div><div class="hval">${v}</div></div>`).join("");

  document.getElementById("ddrows").innerHTML = (p.top_dd || []).map(d =>
    `<tr><td class="neg">${pct(d.depth)}</td><td class="muted tl">${d.peak}</td>
     <td class="muted tl">${d.trough}</td><td class="tl">${d.recovered}</td>
     <td>${fmt$(Math.abs(cap * d.depth))}</td></tr>`).join("");

  const an = document.getElementById("alpharows");
  if (p.alpha_w > 0 && DATA.alpha_names.length) {
    const per = cap * p.alpha_w / DATA.alpha_names.length;
    an.innerHTML = DATA.alpha_names.map(a =>
      `<tr><td><b>${a.ticker}</b></td><td>${a.prob.toFixed(3)}</td>
       <td>${fmt$(a.last)}</td><td><b>${fmt$(per)}</b></td>
       <td>${per >= a.last ? Math.floor(per / a.last) + " sh" : "&lt;1 sh (fractional)"}</td></tr>`).join("");
    document.getElementById("alphasec").style.display = "";
  } else {
    document.getElementById("alphasec").style.display = "none";
  }
}

/* ── MY BOOK: holdings tracker + rebalance recommendations ───────── */
const ETF_MAP = { SPY: "us_equity", VOO: "us_equity", IVV: "us_equity",
  VTI: "us_equity", QQQ: "us_equity", VXUS: "intl_equity", VEA: "intl_equity",
  EFA: "intl_equity", IEFA: "intl_equity", IEF: "bonds", AGG: "bonds",
  BND: "bonds", TLT: "long_bonds", VGLT: "long_bonds", GLD: "gold",
  IAU: "gold", IBIT: "crypto", FBTC: "crypto", "BTC-USD": "crypto",
  SGOV: "cash", BIL: "cash" };
const SLEEVE_LBL = { us_equity: "US equities", intl_equity: "Intl equities",
  bonds: "Bonds", long_bonds: "Long bonds", gold: "Gold", crypto: "Crypto",
  cash: "Cash" };

let book = JSON.parse(localStorage.getItem("vig_holdings") || "[]");
const saveBook = () => localStorage.setItem("vig_holdings", JSON.stringify(book));

function classify(t) {
  if (ETF_MAP[t]) return { sleeve: ETF_MAP[t], sector: "ETF",
                           last: null, etf: true };
  const m = DATA.ticker_meta[t];
  if (m) return { sleeve: "us_equity", sector: m.sector, last: m.last, etf: false };
  return null;
}

function modelView(t) {
  if (DATA.short_decile.includes(t))
    return ['<span class="neg">SHORT decile — model ranks it bottom 10%</span>', "flag"];
  if (DATA.long_decile.includes(t))
    return ['<span class="pos">LONG decile</span>', "good"];
  if (DATA.ticker_meta[t]) return ['<span class="muted">mid-book</span>', ""];
  return ['<span class="muted">not covered</span>', ""];
}

function renderTracker() {
  const rows = [];
  let total = 0, pnlTotal = 0, basisTotal = 0;
  const sleeves = {}, sectors = {}, positions = [];
  for (const h of book) {
    const c = classify(h.t);
    const last = c ? (c.last ?? h.basis ?? null) : null;  // ETFs: no embedded px
    const value = last != null ? h.sh * last : null;
    if (value != null && c) {
      total += value;
      sleeves[c.sleeve] = (sleeves[c.sleeve] || 0) + value;
      if (!c.etf) sectors[c.sector] = (sectors[c.sector] || 0) + value;
      positions.push({ t: h.t, value });
      if (h.basis) { pnlTotal += (last - h.basis) * h.sh; basisTotal += h.basis * h.sh; }
    }
    rows.push({ h, c, last, value });
  }

  document.getElementById("tk-rows").innerHTML = rows.map((r, i) => {
    const c = r.c;
    const sleeve = c ? `${SLEEVE_LBL[c.sleeve]} <span class="muted">${c.sector}</span>`
                     : '<span class="neg">unknown ticker</span>';
    const pnl = (r.h.basis && r.last != null)
      ? `<span class="${r.last >= r.h.basis ? "pos" : "neg"}">` +
        `${(100 * (r.last / r.h.basis - 1)).toFixed(1)}%</span>` : "—";
    const note = c && c.etf && r.last == null
      ? ' <span class="muted">(enter basis to price ETFs)</span>' : "";
    const [mv] = modelView(r.h.t);
    return `<tr><td><b>${r.h.t}</b></td><td class="tl">${sleeve}${note}</td>
      <td>${r.h.sh}</td><td>${r.last != null ? fmt$(r.last) : "—"}</td>
      <td>${r.value != null ? fmt$(r.value) : "—"}</td>
      <td>${r.value != null && total ? pct(r.value / total) : "—"}</td>
      <td>${pnl}</td><td class="tl">${mv}</td>
      <td><span class="tk-x" data-i="${i}">✕</span></td></tr>`;
  }).join("");
  document.querySelectorAll(".tk-x").forEach(x =>
    x.addEventListener("click", () => { book.splice(+x.dataset.i, 1);
      saveBook(); renderTracker(); }));

  const biggest = positions.sort((a, b) => b.value - a.value)[0];
  document.getElementById("tk-tiles").innerHTML = total ? [
    ["Book value (priced positions)", fmt$(total)],
    ["Unrealized P&L (where basis given)",
     basisTotal ? `<span class="${pnlTotal >= 0 ? "pos" : "neg"}">${fmt$(pnlTotal)}` +
       ` (${(100 * pnlTotal / basisTotal).toFixed(1)}%)</span>` : "—"],
    ["Largest position", biggest ? `${biggest.t} · ${pct(biggest.value / total)}` : "—"],
  ].map(([k, v]) =>
    `<div class="htile"><div class="hlabel">${k}</div><div class="hval">${v}</div></div>`
  ).join("") : "";

  // ── recommendations vs the selected profile ──
  const recs = [];
  const p = DATA.profiles[profile];
  if (total > 0) {
    // target sleeves: profile weights, alpha counted as US equity,
    // renormalized to the invested (non-cash) book we can actually see
    const tgt = { ...p.weights };
    tgt.us_equity = (tgt.us_equity || 0) + p.alpha_w;
    const investedT = Object.values(tgt).reduce((a, b) => a + b, 0);
    for (const k of Object.keys(tgt)) tgt[k] /= investedT;
    const gaps = [];
    const allSleeves = new Set([...Object.keys(tgt), ...Object.keys(sleeves)]);
    for (const s of allSleeves) {
      if (s === "cash") continue;
      const cur = (sleeves[s] || 0) / total;
      const gap = (tgt[s] || 0) - cur;
      if (Math.abs(gap) >= 0.03) gaps.push({ s, gap, d: gap * total });
    }
    gaps.sort((a, b) => Math.abs(b.d) - Math.abs(a.d));
    for (const g of gaps.slice(0, 4)) {
      const etf = DATA.sleeve_etfs[g.s] || "";
      recs.push([g.gap > 0
        ? `<b>Add ~${fmt$(g.d)}</b> to ${SLEEVE_LBL[g.s]}${etf ? ` (${etf})` : ""} — ` +
          `you hold ${pct((sleeves[g.s] || 0) / total)} vs ${pct(tgt[g.s] || 0)} target ` +
          `for the <b>${profile}</b> profile`
        : `<b>Trim ~${fmt$(-g.d)}</b> from ${SLEEVE_LBL[g.s]} — ` +
          `${pct((sleeves[g.s] || 0) / total)} held vs ${pct(tgt[g.s] || 0)} target ` +
          `(or just direct new money elsewhere — fewer taxable events)`, ""]);
    }
    if (biggest && biggest.value / total > 0.15)
      recs.push([`<b>${biggest.t} is ${pct(biggest.value / total)} of your book.</b> ` +
        `Single-name risk dwarfs any model edge — the backtests here assume ` +
        `50-name diversification. Consider capping single positions near 10%.`, "flag"]);
    for (const [sec, v] of Object.entries(sectors))
      if (v / total > 0.30)
        recs.push([`<b>${pct(v / total)} in ${sec}.</b> Sector concentration — ` +
          `one macro story moves most of your book.`, "flag"]);
    for (const h of book) {
      const [, cls] = modelView(h.t);
      if (cls === "flag")
        recs.push([`<b>${h.t} sits in Vig's SHORT decile (1W model).</b> Not a ` +
          `sell order — the edge is thin — but the model would not be long it ` +
          `this week.`, "flag"]);
    }
    if (!recs.length)
      recs.push(["Book is within 3pp of the selected profile on every sleeve, " +
        "no concentration flags. Nothing to do — which is usually the right trade.",
        "good"]);
  } else {
    recs.push(["Add positions above (or paste a JSON book) and Vig will " +
      "compare you against the selected profile.", ""]);
  }
  document.getElementById("tk-recs").innerHTML =
    recs.map(([txt, cls]) => `<li class="${cls}">${txt}</li>`).join("");
}

function addPosition() {
  const t = document.getElementById("tk-t").value.trim().toUpperCase();
  const sh = parseFloat(document.getElementById("tk-sh").value);
  const basis = parseFloat(document.getElementById("tk-basis").value) || null;
  if (!t || !(sh > 0)) return;
  book.push({ t, sh, basis });
  saveBook();
  ["tk-t", "tk-sh", "tk-basis"].forEach(id => document.getElementById(id).value = "");
  renderTracker();
}

document.addEventListener("DOMContentLoaded", () => {
  // MYVIG defaults
  try {
    const acct = JSON.parse(localStorage.getItem("vig_account") || "{}");
    if (acct.capital) document.getElementById("cap").value = acct.capital;
    if (DATA.profiles[acct.profile]) profile = acct.profile;
  } catch {}
  document.getElementById("cap").addEventListener("input", () => render());
  document.querySelectorAll(".seg button").forEach(b =>
    b.addEventListener("click", () => { profile = b.dataset.p; render(); }));
  document.getElementById("tk-add").addEventListener("click", addPosition);
  ["tk-t", "tk-sh", "tk-basis"].forEach(id =>
    document.getElementById(id).addEventListener("keydown",
      e => { if (e.key === "Enter") addPosition(); }));
  document.getElementById("tk-export").addEventListener("click", () =>
    navigator.clipboard.writeText(JSON.stringify(book)));
  document.getElementById("tk-import").addEventListener("click", () => {
    const j = prompt("Paste your book JSON:");
    if (!j) return;
    try { book = JSON.parse(j); saveBook(); renderTracker(); }
    catch { alert("invalid JSON"); }
  });
  document.getElementById("tk-clear").addEventListener("click", () => {
    if (confirm("Clear all tracked positions?")) { book = []; saveBook(); renderTracker(); }
  });
  render();
});

const _renderOrig = render;
render = function() { _renderOrig(); renderTracker(); };
</script>"""


def render_portfolio_page(pconf: dict, generated_at: str) -> str:
    data_js = (JS.replace("__DATA__", json.dumps(pconf))
                 .replace("__COLORS__", json.dumps(COLORS))
                 .replace("__LABELS__", json.dumps(LABELS)))
    body = f"""{EXTRA_CSS}
<h2>Portfolio builder <span class="dim">/ capital in, allocation out — risk parity core,
vol-targeted, Vig alpha capped</span></h2>
<div class="pform">
  <div class="pfield"><label>Capital (USD)</label>
    <input type="text" id="cap" value="10,000" inputmode="decimal"></div>
  <div class="pfield"><label>Risk appetite</label>
    <div class="seg">
      <button data-p="conservative">Conservative · 6%</button>
      <button data-p="balanced" class="on">Balanced · 10%</button>
      <button data-p="aggressive">Aggressive · 14%</button>
    </div></div>
</div>
<div class="allocbar" id="bar"></div>
<div class="legend" id="legend"></div>

<h2>The allocation</h2>
<table><tr><th>Sleeve</th><th>Vehicle</th><th>Weight</th><th>Dollars</th></tr>
<tbody id="rows"></tbody></table>

<h2>What history says about this mix <span class="dim">/ today's weights replayed through
2004-present — pain included, promises excluded</span></h2>
<div class="health" id="stats"></div>
<div class="warn">Cash sleeve is modeled at 0% return (T-bills would add ~the
short rate — conservative profiles are understated here). History assumes
daily rebalancing to fixed weights; a real quarterly-rebalanced book drifts
and would show modestly deeper drawdowns. Sleeves enter history at their
inception (BTC 2014+), weights renormalized before that. Historical CAGR is
what this mix DID, not what it will do. Rebalance quarterly; more often just
pays your broker.</div>

<h2>Worst episodes for this mix <span class="dim">/ peak → trough → recovery,
2004-present — know the pain before you size</span></h2>
<table><tr><th>Depth</th><th>Peak</th><th>Trough</th><th>Recovered</th><th>On your capital</th></tr>
<tbody id="ddrows"></tbody></table>

<div id="alphasec">
<h2>Alpha sleeve <span class="dim">/ Vig long book as of {pconf["as_of"]} —
long-only top decile, equal weight; treat as equity risk with a thin tilt</span></h2>
<table><tr><th>Ticker</th><th>P(out)</th><th>Last</th><th>Dollars</th><th>Shares</th></tr>
<tbody id="alpharows"></tbody></table>
</div>

<h2>My book <span class="dim">/ track your actual positions — stored only in this
browser; recommendations rebalance you toward the selected profile above</span></h2>
<div class="tk-form">
  <div class="pfield"><label>Ticker</label><input id="tk-t" placeholder="AAPL / SPY / IEF"></div>
  <div class="pfield"><label>Shares</label><input id="tk-sh" inputmode="decimal" placeholder="10"></div>
  <div class="pfield"><label>Cost basis / share <span class="muted">(optional)</span></label>
    <input id="tk-basis" inputmode="decimal" placeholder="182.50"></div>
  <button id="tk-add">ADD</button>
</div>
<div class="tk-tools"><span id="tk-export">copy JSON</span>
<span id="tk-import">paste JSON</span><span id="tk-clear">clear book</span></div>
<div class="health" id="tk-tiles" style="margin-top:14px"></div>
<table style="margin-top:14px"><tr><th>Position</th><th class="tl">Sleeve / sector</th>
<th>Shares</th><th>Last</th><th>Value</th><th>Weight</th><th>P&amp;L</th>
<th class="tl">Model view (1W)</th><th></th></tr>
<tbody id="tk-rows"></tbody></table>
<h2>Rebalance me <span class="dim">/ vs the selected profile — dollar moves, honestly sized</span></h2>
<ul class="recs" id="tk-recs"></ul>
{data_js}"""

    return page_shell("Vig — Portfolio Builder", generated_at, "portfolio", body)
