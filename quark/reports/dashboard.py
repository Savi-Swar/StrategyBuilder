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
  font-variant-numeric: tabular-nums lining-nums;
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

/* ── tabs (sticky: the screens are always one keystroke away) ── */
.tabs { display: flex; border-top: 1px solid #22262c; border-bottom: 1px solid #22262c;
  position: sticky; top: 0; z-index: 40; background: #060708; }
.tab { flex: 1; text-align: center; padding: 13px 10px; font-size: 12px;
  letter-spacing: 3px; color: #8a9199; text-decoration: none;
  border-right: 1px solid #22262c; }
.tab:last-child { border-right: none; }
.tab:hover { color: #ffb000; background: rgba(255,176,0,.05); }
.tab.active { background: #ffb000; color: #060708; font-weight: 700; }
.tab .k { color: inherit; opacity: .55; margin-right: 8px; }

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
.hval { font-size: 21px; font-weight: 600; }
.hval .muted { font-size: 12px; font-weight: 400; }
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
table { width: 100%; border-collapse: separate; border-spacing: 0;
        background: #0b0d10; border: 1px solid #22262c; }
/* numbers read right-to-left: numeric columns right-aligned, headers match;
   first column (names) left; .tl marks additional text columns */
th, td { text-align: right; }
th:first-child, td:first-child, th.tl, td.tl { text-align: left; }
th { font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
     color: #ffb000; padding: 9px 13px; border-bottom: 1px double #2a2e35;
     font-weight: 600; cursor: pointer; user-select: none;
     position: sticky; top: var(--tabs-h, 47px); background: #0e1114; z-index: 5; }
th:hover { color: #ffd668; }
th[data-dir="desc"]::after { content: " ▾"; }
th[data-dir="asc"]::after { content: " ▴"; }
td { padding: 7px 13px; font-size: 12.5px; border-bottom: 1px solid #14171b; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,176,0,.035); }
.pos { color: #46ff9a; } .neg { color: #ff5d5d; } .muted { color: #6d747c; }
.win { color: #46ff9a; font-weight: 700; } .loss { color: #ff5d5d; font-weight: 700; }

/* ── filter bar ───────────────────────────────────────── */
.fbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  background: #0b0d10; border: 1px solid #22262c; padding: 12px 16px;
  margin: 6px 0 18px; }
.fbar input[type=text] { background: #060708; border: 1px solid #2a2e35;
  color: #e6e2d8; font: 12.5px "SF Mono", ui-monospace, Menlo, monospace;
  padding: 8px 12px; width: 170px; }
.fbar input[type=text]:focus { outline: none; border-color: #ffb000; }
.fb-chip, .fb-side, .bm-btn { border: 1px solid #2a2e35; color: #8a9199;
  font-size: 11px; padding: 6px 11px; cursor: pointer; background: #0e1114;
  letter-spacing: .5px; }
.fb-chip.on, .fb-side.on, .bm-btn.on { border-color: #ffb000; color: #ffb000;
  background: rgba(255,176,0,.08); }
.bm-btn.on { font-weight: 700; }
.fb-prob { display: flex; align-items: center; gap: 8px; font-size: 11px;
  color: #8a9199; }
.fb-prob input { accent-color: #ffb000; width: 110px; }
.fb-reset { color: #6d747c; font-size: 11px; cursor: pointer;
  text-decoration: underline; margin-left: auto; }
.fb-count { color: #ffb000; font-size: 11px; }

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


PAGES = [
    ("desk", "index.html", "01", "DESK"),
    ("analysis", "analysis.html", "02", "ANALYSIS"),
    ("screener", "screener.html", "03", "SCREENER"),
    ("past_trades", "past_trades.html", "04", "PAST TRADES"),
    ("portfolio", "portfolio.html", "05", "PORTFOLIO"),
]

PALETTE_CSS = """
td b:hover { color: #ffb000; cursor: pointer; }
#vp-scrim, #vi-scrim { position: fixed; inset: 0; background: rgba(3,4,5,.82);
  z-index: 80; display: none; }
#vp-scrim.open, #vi-scrim.open { display: block; }
#vp-box { position: fixed; top: 14vh; left: 50%; transform: translateX(-50%);
  width: 560px; max-width: 92vw; z-index: 90; background: #0b0d10;
  border: 1px solid #ffb000; box-shadow: 0 30px 80px rgba(0,0,0,.7); }
#vp-in { width: 100%; background: #060708; border: none; border-bottom: 1px solid #22262c;
  color: #e6e2d8; font: 18px "SF Mono", ui-monospace, Menlo, monospace;
  padding: 16px 18px; }
#vp-in:focus { outline: none; }
#vp-list { max-height: 320px; overflow-y: auto; }
.vp-row { display: flex; justify-content: space-between; padding: 10px 18px;
  cursor: pointer; font-size: 13px; border-bottom: 1px solid #14171b; }
.vp-row:hover, .vp-row.sel { background: rgba(255,176,0,.08); }
.vp-row .m { color: #6d747c; font-size: 11px; }
#vi-card { position: fixed; top: 7vh; left: 50%; transform: translateX(-50%);
  width: 920px; max-width: 94vw; max-height: 86vh; overflow-y: auto; z-index: 90;
  background: #0a0c0f; border: 1px solid #ffb000; padding: 26px 30px;
  box-shadow: 0 30px 80px rgba(0,0,0,.75); }
#vi-head { display: flex; justify-content: space-between; align-items: baseline;
  flex-wrap: wrap; gap: 10px; }
#vi-tick { font-size: 44px; font-weight: 800; letter-spacing: 1px; }
#vi-sub { color: #8a9199; font-size: 12px; letter-spacing: 1px; }
#vi-last { font-size: 26px; }
.vi-chips { display: flex; gap: 10px; flex-wrap: wrap; margin: 14px 0; }
.vi-chip { border: 1px solid #22262c; padding: 5px 13px; font-size: 12px;
  color: #9fb0c0; background: #0e1114; }
.vi-chip b { color: #e6e2d8; }
#vi-close { cursor: pointer; color: #8a9199; font-size: 18px; }
#vi-close:hover { color: #e6e2d8; }
.vi-sect { font-size: 11px; letter-spacing: 2.5px; color: #ffb000;
  margin: 20px 0 10px; text-transform: uppercase; }
.vi-sect::before { content: "▚ "; }
"""

PALETTE_JS = r"""
<script>
(() => {
const INST = window.VIG_INSTRUMENTS || {};
const KEYS = Object.keys(INST);
const CMDS = [
  { n: "01 DESK", m: "screen", go: () => location.href = "index.html" },
  { n: "02 ANALYSIS", m: "screen", go: () => location.href = "analysis.html" },
  { n: "03 SCREENER", m: "screen", go: () => location.href = "screener.html" },
  { n: "04 PAST TRADES", m: "screen", go: () => location.href = "past_trades.html" },
  { n: "05 PORTFOLIO", m: "screen", go: () => location.href = "portfolio.html" },
  ...["1D", "1W", "3M", "6M", "2Y"].map(h => ({
    n: "HORIZON " + h, m: "setting",
    go: () => { localStorage.setItem("vig_hz", h); location.href = "index.html"; } })),
];
const getWatch = () => JSON.parse(localStorage.getItem("vig_watchlist") || "[]");
const setWatch = w => localStorage.setItem("vig_watchlist", JSON.stringify(w));
const $ = id => document.getElementById(id);
const pct = x => (x >= 0 ? "+" : "") + (100 * x).toFixed(1) + "%";
const cls = x => x >= 0 ? "pos" : "neg";

function chart(px, w = 850, h = 230) {
  if (!px || px.length < 2) return "";
  const lo = Math.min(...px), hi = Math.max(...px), rng = (hi - lo) || 1;
  const pts = px.map((v, i) =>
    `${(i * w / (px.length - 1)).toFixed(1)},${(h - 8 - (v - lo) / rng * (h - 16)).toFixed(1)}`
  ).join(" ");
  const color = px[px.length - 1] >= px[0] ? "#46ff9a" : "#ff5d5d";
  return `<svg width="100%" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"
    style="border:1px solid #22262c;background:#0b0d10">
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.6"/>
    <text x="6" y="14" fill="#6d747c" font-size="11">${hi.toLocaleString()}</text>
    <text x="6" y="${h - 6}" fill="#6d747c" font-size="11">${lo.toLocaleString()}</text>
  </svg>`;
}

function openInst(t) {
  const d = INST[t];
  if (!d) return;
  closePalette();
  let html = `<div id="vi-head"><div><div id="vi-tick">${t}</div>
    <div id="vi-sub">${d.c} · ${d.k === "stock" ? "S&P 500 universe" : "trend universe"} · 1y daily</div></div>
    <div style="text-align:right"><div id="vi-last">${d.l.toLocaleString()}</div>
    <div class="${cls(d.r1 ?? 0)}">${d.r1 != null ? pct(d.r1) + " today" : ""}</div></div>
    <span id="vi-watch" style="cursor:pointer;color:#ffb000;font-size:12px;
      letter-spacing:1px;border:1px solid #2a2e35;padding:5px 10px"></span>
    <span id="vi-close">✕</span></div>
    ${chart(d.px)}
    <div class="vi-chips">
      ${d.r21 != null ? `<span class="vi-chip">1m <b class="${cls(d.r21)}">${pct(d.r21)}</b></span>` : ""}
      ${d.r252 != null ? `<span class="vi-chip">12m <b class="${cls(d.r252)}">${pct(d.r252)}</b></span>` : ""}
      ${d.tp != null ? `<span class="vi-chip">trend book <b class="${cls(d.tp)}">${d.tp > 0 ? "LONG" : d.tp < 0 ? "SHORT" : "FLAT"} ${Math.abs(d.tp)}x</b></span>` : ""}
    </div>`;
  if (d.h && Object.keys(d.h).length) {
    html += `<div class="vi-sect">Model view by horizon — P(outperform S&P median)</div><div class="vi-chips">` +
      Object.entries(d.h).map(([k, p]) => {
        const side = (d.hd || {})[k];
        const badge = side === "L" ? ' <b class="pos">LONG BOOK</b>'
                    : side === "S" ? ' <b class="neg">SHORT BOOK</b>' : "";
        return `<span class="vi-chip">${k} <b>${p.toFixed(3)}</b>${badge}</span>`;
      }).join("") + `</div>
      <div class="edgemath">probabilities near 0.55 are the honest size of this
      edge (weekly IC ≈ 0.017) — conviction, not certainty.</div>`;
  }
  if (d.b) {
    const g = d.b.gold == null ? "—" : (d.b.gold ? "GOLDEN" : "DEATH");
    html += `<div class="vi-sect">Technicals (tactical board)</div><div class="vi-chips">
      <span class="vi-chip">RSI14 <b>${d.b.rsi}</b></span>
      <span class="vi-chip">%B <b>${d.b.pctb}</b></span>
      <span class="vi-chip">MACD <b>${d.b.macd} bps</b></span>
      <span class="vi-chip">50/200 <b>${g}</b></span>
      ${d.b.vwap != null ? `<span class="vi-chip">vs VWAP20 <b class="${cls(d.b.vwap)}">${pct(d.b.vwap)}</b></span>` : ""}
      <span class="vi-chip">consensus <b class="${d.b.cons >= 3 ? "pos" : d.b.cons <= -3 ? "neg" : "muted"}">${d.b.cons >= 0 ? "+" : ""}${d.b.cons}</b></span>
    </div>`;
  }
  $("vi-card").innerHTML = html;
  $("vi-scrim").classList.add("open");
  $("vi-card").style.display = "";
  $("vi-close").addEventListener("click", closeInst);
  const wb = $("vi-watch");
  const paint = () => wb.textContent =
    getWatch().includes(t) ? "★ WATCHING" : "☆ WATCH";
  paint();
  wb.addEventListener("click", () => {
    const w = getWatch();
    setWatch(w.includes(t) ? w.filter(x => x !== t) : [...w, t]);
    paint(); renderWatch();
  });
}

function renderWatch() {
  const el = $("vig-watch");
  if (!el) return;
  const wl = getWatch().filter(t => INST[t]);
  if (!wl.length) {
    el.innerHTML = '<p class="muted" style="font-size:12px">nothing starred ' +
      'yet — open any instrument (⌘K or click a ticker) and hit ☆ WATCH</p>';
    return;
  }
  el.innerHTML = '<table><tr><th>Ticker</th><th class="tl">Name</th>' +
    '<th>Last</th><th>1d</th><th>1m</th><th>12m</th><th>P 1W</th></tr>' +
    wl.map(t => {
      const d = INST[t], p = (d.h || {})["1W"];
      const cells = ["r1", "r21", "r252"].map(k =>
        `<td class="${(d[k] ?? 0) >= 0 ? "pos" : "neg"}">` +
        `${d[k] != null ? pct(d[k]) : "—"}</td>`).join("");
      return `<tr data-search="${t}"><td><b>${t}</b></td>` +
        `<td class="tl muted">${d.n || d.c}</td>` +
        `<td>${d.l.toLocaleString()}</td>${cells}` +
        `<td class="${p > 0.5 ? "pos" : "neg"}">${p?.toFixed(3) ?? "—"}</td></tr>`;
    }).join("") + "</table>";
}
function closeInst() {
  $("vi-scrim").classList.remove("open");
  $("vi-card").style.display = "none";
}

function matches(q) {
  q = q.trim().toUpperCase();
  if (!q) {
    const wl = getWatch().filter(t => INST[t]).map(t => ({
      label: "★ " + t, meta: INST[t].n || INST[t].c, go: () => openInst(t) }));
    return [...wl.slice(0, 5),
            ...CMDS.slice(0, 5).map(c => ({ label: c.n, meta: c.m, go: c.go }))]
           .slice(0, 9);
  }
  // rank: ticker prefix > name prefix > any substring (ticker/name/sector)
  const scored = [];
  for (const t of KEYS) {
    const d = INST[t], name = (d.n || "").toUpperCase();
    let s = -1;
    if (t.toUpperCase().startsWith(q)) s = 0;
    else if (name.startsWith(q)) s = 1;
    else if (t.toUpperCase().includes(q) || name.includes(q)
             || (d.c || "").toUpperCase().includes(q)) s = 2;
    if (s >= 0) scored.push([s, t]);
  }
  scored.sort((a, b) => a[0] - b[0] || a[1].localeCompare(b[1]));
  const out = scored.slice(0, 7).map(([, t]) => ({
    label: t, meta: [INST[t].n, INST[t].c].filter(Boolean).join(" · "),
    go: () => openInst(t) }));
  for (const c of CMDS)
    if (c.n.toUpperCase().includes(q)) out.push({ label: c.n, meta: c.m, go: c.go });
  return out.slice(0, 9);
}

let sel = 0;
function renderList() {
  const rows = matches($("vp-in").value);
  sel = Math.min(sel, Math.max(0, rows.length - 1));
  $("vp-list").innerHTML = rows.map((r, i) =>
    `<div class="vp-row${i === sel ? " sel" : ""}" data-i="${i}">
     <span>${r.label}</span><span class="m">${r.meta}</span></div>`).join("");
  document.querySelectorAll(".vp-row").forEach(el =>
    el.addEventListener("click", () => rows[+el.dataset.i].go()));
  $("vp-list")._rows = rows;
}
function openPalette() {
  $("vp-scrim").classList.add("open");
  $("vp-box").style.display = "";
  $("vp-in").value = ""; sel = 0; renderList();
  $("vp-in").focus();
}
function closePalette() {
  $("vp-scrim").classList.remove("open");
  $("vp-box").style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  const wrap = document.createElement("div");
  wrap.innerHTML = `<div id="vp-scrim"></div>
    <div id="vp-box" style="display:none">
      <input id="vp-in" placeholder="ticker or command… (esc to close)">
      <div id="vp-list"></div></div>
    <div id="vi-scrim"></div><div id="vi-card" style="display:none"></div>`;
  document.body.appendChild(wrap);
  $("vp-in").addEventListener("input", () => { sel = 0; renderList(); });
  $("vp-in").addEventListener("keydown", e => {
    const rows = $("vp-list")._rows || [];
    if (e.key === "ArrowDown") { sel = Math.min(sel + 1, rows.length - 1); renderList(); e.preventDefault(); }
    if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); renderList(); e.preventDefault(); }
    if (e.key === "Enter" && rows[sel]) rows[sel].go();
  });
  $("vp-scrim").addEventListener("click", closePalette);
  $("vi-scrim").addEventListener("click", closeInst);

  renderWatch();
  document.addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault(); openPalette(); return;
    }
    if (e.key === "Escape") { closePalette(); closeInst(); }
  });
  // any bold ticker anywhere becomes a security link
  document.addEventListener("click", e => {
    const b = e.target.closest("b");
    if (b && INST[b.textContent.trim()]) openInst(b.textContent.trim());
  });
});
})();
</script>"""

ACCOUNT_CSS = """
#va-btn { cursor: pointer; color: #ffb000; font-size: 11px; letter-spacing: 2px;
  border: 1px solid #2a2e35; padding: 4px 10px; margin-left: 10px; }
#va-btn:hover { border-color: #ffb000; }
#va-panel { position: fixed; right: 0; top: 0; bottom: 0; width: 380px;
  max-width: 92vw; z-index: 75; background: #0a0c0f; border-left: 1px solid #ffb000;
  transform: translateX(102%); transition: transform .2s ease; padding: 24px 22px;
  overflow-y: auto; box-shadow: -30px 0 60px rgba(0,0,0,.55); }
#va-panel.open { transform: translateX(0); }
#va-panel h3 { font-size: 13px; letter-spacing: 3px; color: #ffb000; margin-bottom: 4px; }
#va-panel .s { font-size: 11px; color: #6d747c; margin-bottom: 18px; }
.va-field { margin-bottom: 14px; }
.va-field label { display: block; font-size: 10px; letter-spacing: 2px;
  text-transform: uppercase; color: #8a9199; margin-bottom: 6px; }
.va-field input, .va-field select { width: 100%; background: #060708;
  border: 1px solid #2a2e35; color: #e6e2d8; padding: 9px 12px;
  font: 13px "SF Mono", ui-monospace, Menlo, monospace; }
.va-field input:focus, .va-field select:focus { outline: none; border-color: #ffb000; }
.va-row { display: flex; gap: 8px; margin-top: 18px; flex-wrap: wrap; }
.va-row span { border: 1px solid #2a2e35; color: #8a9199; font-size: 11px;
  padding: 7px 12px; cursor: pointer; }
.va-row span:hover { border-color: #ffb000; color: #ffb000; }
.va-row span.primary { border-color: #ffb000; color: #ffb000; font-weight: 700; }
.va-note { font-size: 10.5px; color: #565d64; margin-top: 14px; line-height: 1.6; }
"""

ACCOUNT_JS = r"""
<script>
(() => {
const $ = id => document.getElementById(id);
const load = () => JSON.parse(localStorage.getItem("vig_account") || "{}");

document.addEventListener("DOMContentLoaded", () => {
  const dateBox = document.querySelector(".stamp-date");
  if (dateBox) dateBox.insertAdjacentHTML("beforeend",
    '<br><span id="va-btn">◈ MYVIG</span>');
  document.body.insertAdjacentHTML("beforeend", `
<div id="va-panel">
  <h3>MYVIG</h3><div class="s">your desk identity — stored only in this browser</div>
  <div class="va-field"><label>Callsign</label>
    <input id="va-name" placeholder="how the desk greets you"></div>
  <div class="va-field"><label>Default capital (USD)</label>
    <input id="va-cap" inputmode="decimal" placeholder="10,000"></div>
  <div class="va-field"><label>Default risk profile</label>
    <select id="va-prof"><option value="">—</option>
    <option>conservative</option><option>balanced</option><option>aggressive</option></select></div>
  <div class="va-field"><label>Default horizon</label>
    <select id="va-hz"><option value="">—</option><option>1D</option>
    <option>1W</option><option>3M</option><option>6M</option><option>2Y</option></select></div>
  <div class="va-field"><label>Tiingo API key (optional — upgrades the data cross-check)</label>
    <input id="va-tiingo" type="password" placeholder="free at tiingo.com"></div>
  <div class="va-row">
    <span class="primary" id="va-save">SAVE</span>
    <span id="va-export">EXPORT ALL</span>
    <span id="va-backup">BACKUP &#8595;</span>
    <span id="va-import">IMPORT</span>
    <span id="va-close2">CLOSE</span>
  </div>
  <div class="va-note">EXPORT ALL copies your entire desk state (account,
  holdings, watchlist, journal, horizon — including your Tiingo key, so
  treat the JSON like a password) — paste it into Vig on any machine.
  BACKUP downloads the same JSON as a dated file; IMPORT restores either.
  Pipeline note: the daily refresh reads TIINGO_API_KEY from the
  environment — after saving here, also run once in Terminal:<br>
  <code>launchctl setenv TIINGO_API_KEY &lt;your key&gt;</code></div>
</div>`);

  const acct = load();
  $("va-name").value = acct.callsign || "";
  $("va-cap").value = acct.capital || "";
  $("va-prof").value = acct.profile || "";
  $("va-hz").value = acct.horizon || "";
  $("va-tiingo").value = acct.tiingo || "";
  if (acct.callsign) {
    const b = document.querySelector(".tagline b");
    if (b) b.textContent = acct.callsign + "'s systematic desk";
  }

  $("va-btn").addEventListener("click", () => $("va-panel").classList.toggle("open"));
  $("va-close2").addEventListener("click", () => $("va-panel").classList.remove("open"));
  $("va-save").addEventListener("click", () => {
    const a = { callsign: $("va-name").value.trim(),
                capital: $("va-cap").value.trim(),
                profile: $("va-prof").value,
                horizon: $("va-hz").value,
                tiingo: $("va-tiingo").value.trim() };
    localStorage.setItem("vig_account", JSON.stringify(a));
    if (a.horizon) localStorage.setItem("vig_hz", a.horizon);
    location.reload();
  });
  const deskState = () => JSON.stringify({
    account: load(),
    holdings: JSON.parse(localStorage.getItem("vig_holdings") || "[]"),
    watchlist: JSON.parse(localStorage.getItem("vig_watchlist") || "[]"),
    journal: JSON.parse(localStorage.getItem("vig_journal") || "[]"),
    hz: localStorage.getItem("vig_hz") || "1W",
  });
  $("va-export").addEventListener("click", () => {
    navigator.clipboard.writeText(deskState()).then(
      () => { $("va-export").textContent = "COPIED ✓";
              setTimeout(() => $("va-export").textContent = "EXPORT ALL", 1500); },
      () => alert("clipboard blocked — use BACKUP instead"));
  });
  $("va-backup").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([deskState()],
                                          { type: "application/json" }));
    a.download = "vig_backup_" + new Date().toISOString().slice(0, 10) + ".json";
    a.click();
    // Safari aborts the download if the URL is revoked synchronously
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  });
  $("va-import").addEventListener("click", () => {
    const j = prompt("Paste your Vig desk JSON:");
    if (!j) return;
    try {
      const d = JSON.parse(j);
      if (d.account) localStorage.setItem("vig_account", JSON.stringify(d.account));
      if (d.holdings) localStorage.setItem("vig_holdings", JSON.stringify(d.holdings));
      if (d.watchlist) localStorage.setItem("vig_watchlist", JSON.stringify(d.watchlist));
      if (d.journal) localStorage.setItem("vig_journal", JSON.stringify(d.journal));
      if (d.hz) localStorage.setItem("vig_hz", d.hz);
      location.reload();
    } catch { alert("invalid JSON"); }
  });
});
})();
</script>"""

# Terminal behaviors, page-wide: numbered-key screen switching ("/" focuses
# search), sticky-header offset tracking, and click-to-sort on every table.
GLOBAL_JS = """
<script>
(() => {
  const pages = { "1": "index.html", "2": "analysis.html",
                  "3": "screener.html", "4": "past_trades.html",
                  "5": "portfolio.html" };
  document.addEventListener("keydown", e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target instanceof Element && e.target.matches("input,textarea")) return;
    if (pages[e.key]) location.href = pages[e.key];
    if (e.key === "/") {
      const q = document.getElementById("fb-q");
      if (q) { e.preventDefault(); q.focus(); }
    }
  });

  const setTabsH = () => {
    const t = document.querySelector(".tabs");
    if (t) document.documentElement.style.setProperty("--tabs-h", t.offsetHeight + "px");
  };
  window.addEventListener("resize", setTabsH);
  document.addEventListener("DOMContentLoaded", setTabsH);

  const num = s => {
    const v = parseFloat(s.replace(/[▮$,]/g, "").replace(/(bps|wks|sh|OB|OS|pp|[%x+])/g, ""));
    return isNaN(v) ? null : v;
  };
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("table").forEach(tb => {
      const headers = [...tb.querySelectorAll("th")];
      headers.forEach((th, i) => th.addEventListener("click", () => {
        const desc = th.dataset.dir !== "desc";
        headers.forEach(h => delete h.dataset.dir);
        th.dataset.dir = desc ? "desc" : "asc";
        const rows = [...tb.querySelectorAll("tr")].filter(r => r.querySelector("td"));
        rows.sort((a, b) => {
          const x = (a.cells[i]?.innerText ?? "").trim();
          const y = (b.cells[i]?.innerText ?? "").trim();
          const nx = num(x), ny = num(y);
          const c = (nx !== null && ny !== null) ? nx - ny : x.localeCompare(y);
          return desc ? -c : c;
        });
        rows.forEach(r => r.parentNode.appendChild(r));
      }));
    });
  });
})();
</script>"""


def page_shell(title: str, generated_at: str, active: str, body: str,
               tape_html: str = "") -> str:
    tabs = "".join(
        f'<a class="tab{" active" if key == active else ""}" href="{href}">'
        f'<span class="k">{num}</span>{label}</a>'
        for key, href, num, label in PAGES
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="900">
<title>{title}</title><style>{CSS}{PALETTE_CSS}{ACCOUNT_CSS}</style></head><body>
<header>
  <div>
    <div class="wordmark">VIG</div>
    <div class="tagline">the house takes its cut — <b>systematic daily desk</b></div>
  </div>
  <div class="stamp-date">{generated_at.replace("T", " · ")}</div>
</header>
<nav class="tabs">{tabs}</nav>
{tape_html}
<div class="wrap">{body}</div>
<footer><span class="muted">keys: <b>⌘K</b> any ticker or command ·
<b>1–5</b> screens · <b>/</b> search · click a ticker for its security page ·
click any column header to sort</span><br><br>
Research tooling output — signals from backtested models with modest,
documented edges (weekly IC ≈ 0.017; see RESEARCH_NOTES.md). Probabilities are
calibrated conviction, not certainty. Not investment advice.</footer>
<script src="instruments.js"></script>
{PALETTE_JS}
{ACCOUNT_JS}
{GLOBAL_JS}
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


def _data_check_tile(dc: dict) -> str:
    if not dc or not dc.get("n_checked"):
        return ('<div class="htile"><div class="hlabel">Cross-source check</div>'
                '<div class="hval"><span class="led warming"></span>inactive</div>'
                '<div class="hdetail">verifies Yahoo returns against an '
                'independent provider on each refresh — add a free Tiingo API '
                'key in MYVIG to activate (keyless stooq is bot-walled)</div></div>')
    flagged = (", ".join(dc["flagged"]) if dc.get("flagged")
               else "no disagreements beyond tolerance")
    return (f'<div class="htile"><div class="hlabel">Cross-source check '
            f'({dc["source"]})</div>'
            f'<div class="hval"><span class="led {dc["status"]}"></span>'
            f'{dc["n_checked"] - dc["n_flagged"]}/{dc["n_checked"]} agree</div>'
            f'<div class="hdetail">{flagged}</div></div>')


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
  {_data_check_tile(health.get("data_check", {}))}
</div>
<div class="edgemath">EDGE MATH, HONESTLY — at the backtested best case (monthly
config, net Sharpe ≈ 0.26) the full-Kelly growth rate is S²/2 ≈ <b>3.4%/yr</b>
per unit of gross; at the half-Kelly a sane desk actually runs, ≈ 3S²/8 ≈
<b>2.5%/yr</b>. Vig compounds calibration and discipline; the money, if ever,
follows the process — not the other way round.</div>"""


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
            f'<td class="tl"><b>{sh}</b></td>'
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


def filter_bar(classes: list[str] | None = None, show_prob: bool = True,
               show_side: bool = True) -> str:
    """Manual pick-and-choose filters. Pure client-side JS operating on every
    element carrying data-search (table rows and article cards alike)."""
    chips = "".join(f'<span class="fb-chip" data-c="{c}">{c}</span>'
                    for c in (classes or []))
    side = ('<span class="fb-side" data-s="LONG">LONG</span>'
            '<span class="fb-side" data-s="SHORT">SHORT</span>') if show_side else ""
    prob = ('<span class="fb-prob">P(out) ≥ <b id="fb-pv">0.00</b>'
            '<input type="range" id="fb-prob" min="0" max="0.65" step="0.01" value="0">'
            '</span>') if show_prob else ""
    return f"""
<div class="fbar">
  <input type="text" id="fb-q" placeholder="search ticker…">
  {chips}{side}{prob}
  <span class="fb-count" id="fb-n"></span>
  <span class="fb-reset" id="fb-reset">reset</span>
</div>
<script>
(() => {{
  const st = {{ q: "", cls: new Set(), side: null, minp: 0 }};
  const $ = id => document.getElementById(id);
  function apply() {{
    let n = 0, total = 0;
    document.querySelectorAll("[data-search]").forEach(el => {{
      total++;
      let ok = true;
      if (st.q) ok = ok && el.dataset.search.toLowerCase().includes(st.q);
      if (st.cls.size) ok = ok && [...st.cls].some(c =>
        (el.dataset.class || "").includes(c));
      if (st.side) ok = ok && (el.dataset.side || "") === st.side;
      if (st.minp > 0) ok = ok && el.dataset.prob != null &&
        parseFloat(el.dataset.prob) >= st.minp;
      el.style.display = ok ? "" : "none";
      if (ok) n++;
    }});
    $("fb-n").textContent = (st.q || st.cls.size || st.side || st.minp > 0)
      ? n + "/" + total + " shown" : "";
  }}
  $("fb-q").addEventListener("input", e => {{
    st.q = e.target.value.trim().toLowerCase(); apply(); }});
  document.querySelectorAll(".fb-chip").forEach(ch =>
    ch.addEventListener("click", () => {{
      const c = ch.dataset.c;
      st.cls.has(c) ? st.cls.delete(c) : st.cls.add(c);
      ch.classList.toggle("on"); apply(); }}));
  document.querySelectorAll(".fb-side").forEach(b =>
    b.addEventListener("click", () => {{
      st.side = st.side === b.dataset.s ? null : b.dataset.s;
      document.querySelectorAll(".fb-side").forEach(x =>
        x.classList.toggle("on", st.side === x.dataset.s));
      apply(); }}));
  const pr = $("fb-prob");
  if (pr) pr.addEventListener("input", e => {{
    st.minp = parseFloat(e.target.value);
    $("fb-pv").textContent = st.minp.toFixed(2); apply(); }});
  $("fb-reset").addEventListener("click", () => {{
    st.q = ""; st.cls.clear(); st.side = null; st.minp = 0;
    $("fb-q").value = ""; if (pr) {{ pr.value = 0; $("fb-pv").textContent = "0.00"; }}
    document.querySelectorAll(".fb-chip.on,.fb-side.on").forEach(x =>
      x.classList.remove("on"));
    apply(); }});
}})();
</script>"""


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
                f'<tr><td>{s}</td><td class="tl">{lbar} {ln}</td>'
                f'<td class="tl">{sbar} {sh}</td>'
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


def _validation_line(label: str, validation: dict) -> str:
    v = validation.get(label)
    if not v:
        return ('<span class="muted">walk-forward validation pending for this '
                'horizon — treat picks as unproven</span>')
    tone = "pos" if v["ic_t"] > 2 else ("muted" if v["ic_t"] > 1 else "neg")
    return (f'walk-forward IC <b class="{tone}">{v["ic_mean"]:+.4f}</b> '
            f'(t={v["ic_t"]:+.1f}, n={v["n_periods"]} periods) '
            f'— every horizon is a counted trial')


def _horizon_views(result: dict) -> str:
    horizons = result.get("horizons") or {}
    if not horizons:  # fallback: single-horizon desk
        cards = "".join(_trade_card(t, result["sparks"].get(t["ticker"], []))
                        for t in result["trades"])
        return (f'<h2>Top trades <span class="dim">/ today</span></h2>'
                f'<div class="cards">{cards}</div>')

    strip = "".join(
        f'<span class="bm-btn hz" data-hz="{label}">{label}</span>'
        for label in horizons
    )
    views = []
    for label, hv in horizons.items():
        cards = "".join(_trade_card(t, hv["sparks"].get(t["ticker"], []))
                        for t in hv["trades"])
        views.append(f"""
<div data-hzview="{label}" style="display:none">
  <div class="tagline" style="margin:4px 0 14px">as-of
  <b>{hv["xsec"]["as_of"].date()}</b> · {hv["h"]} trading-day horizon ·
  {_validation_line(label, result.get("horizon_validation", {}))}</div>
  <div class="cards">{cards}</div>
  <h2>The equity book <span class="dim">/ at this horizon</span></h2>
  {_xsec_table(hv["xsec"])}
</div>""")

    return f"""
<h2>Top trades <span class="dim">/ pick your horizon — the whole desk view follows</span></h2>
<div class="fbar" style="margin-bottom:14px">
  <span class="hlabel" style="margin:0">HORIZON</span>{strip}
  <span class="muted" style="font-size:11px">each horizon is its own retrained
  model; 1W is the desk default and carries the live track record</span>
</div>
{"".join(views)}
<script>
(() => {{
  const btns = document.querySelectorAll(".hz");
  const views = document.querySelectorAll("[data-hzview]");
  const set = k => {{
    views.forEach(v => v.style.display = v.dataset.hzview === k ? "" : "none");
    btns.forEach(b => b.classList.toggle("on", b.dataset.hz === k));
    localStorage.setItem("vig_hz", k);
  }};
  btns.forEach(b => b.addEventListener("click", () => set(b.dataset.hz)));
  const saved = localStorage.getItem("vig_hz");
  set([...btns].some(b => b.dataset.hz === saved) ? saved : "1W");
}})();
</script>"""


def render_dashboard(result: dict) -> str:
    commentary = ""
    if result["commentary"]:
        commentary = (f'<h2>Vig&rsquo;s commentary</h2>'
                      f'<div class="commentary">{_commentary_html(result["commentary"])}</div>')

    health = dict(result.get("health") or {})
    health["data_check"] = result.get("data_check", {})
    body = f"""
<div class="tagline" style="margin-bottom:6px">data through
<b>{result["data_through"]}</b> · universe <b>{result["xsec"]["n_universe"]}</b> names</div>
{_health_panel(health)}
<h2>Watchlist <span class="dim">/ yours — star anything from its security page</span></h2>
<div id="vig-watch"></div>
{_horizon_views(result)}
{_positioning_panel(result.get("sectors", {}), result.get("factor_tilts", {}),
                    result.get("regime", {}))}
{commentary}
<h2>The trend book <span class="dim">/ multi-asset, 12m trend, vol-targeted</span></h2>
{filter_bar(sorted(result["snapshot"]["asset_class"].unique()) + ["stock"])}
{_trend_table(result["snapshot"])}"""

    return page_shell(
        "Vig — Daily Desk", result["generated_at"], "desk",
        body, tape_html=_tape(result["snapshot"]),
    )
