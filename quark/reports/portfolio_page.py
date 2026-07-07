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
    return `<tr><td><b>${LABELS[k]}</b></td><td class="muted">${vehicle}</td>
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
    `<tr><td class="neg">${pct(d.depth)}</td><td class="muted">${d.peak}</td>
     <td class="muted">${d.trough}</td><td>${d.recovered}</td>
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

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("cap").addEventListener("input", render);
  document.querySelectorAll(".seg button").forEach(b =>
    b.addEventListener("click", () => { profile = b.dataset.p; render(); }));
  render();
});
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
short rate — conservative profiles are understated here). Historical CAGR is
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
{data_js}"""

    return page_shell("Vig — Portfolio Builder", generated_at, "portfolio", body)
