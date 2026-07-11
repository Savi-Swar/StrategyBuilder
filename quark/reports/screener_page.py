"""The Screener: every covered S&P name in one sortable, filterable table —
model probabilities at two horizons, factor percentiles, returns. Rendered
entirely client-side from the security master, so it is always in sync with
the rest of the desk and costs nothing to regenerate."""

from quark.reports.dashboard import filter_bar, page_shell

SECTORS = ["Communication Services", "Consumer Discretionary",
           "Consumer Staples", "Energy", "Financials", "Health Care",
           "Industrials", "Information Technology", "Materials",
           "Real Estate", "Utilities"]

SCREENER_JS = r"""
<script>
document.addEventListener("DOMContentLoaded", () => {
  const INST = window.VIG_INSTRUMENTS || {};
  const pct = x => x == null ? "—" : (x >= 0 ? "+" : "") + (100 * x).toFixed(1) + "%";
  const cls = x => x == null ? "muted" : (x >= 0 ? "pos" : "neg");
  const badge = s => s === "L" ? ' <span class="pos">▲L</span>'
               : s === "S" ? ' <span class="neg">▼S</span>' : "";

  const rows = Object.entries(INST)
    .filter(([, d]) => d.k === "stock")
    .map(([t, d]) => {
      const p1 = (d.h || {})["1W"], p3 = (d.h || {})["3M"];
      const f = d.f || {};
      return { t, d, p1, p3, f };
    })
    .sort((a, b) => (b.p1 ?? 0) - (a.p1 ?? 0));

  document.getElementById("sc-rows").innerHTML = rows.map(r => `
    <tr data-search="${r.t} ${(r.d.n || "").toLowerCase()}"
        data-class="${r.d.c}" ${r.p1 != null ? `data-prob="${r.p1}"` : ""}>
      <td><b>${r.t}</b></td>
      <td class="tl muted">${r.d.n || ""}</td>
      <td class="tl muted">${r.d.c}</td>
      <td>${r.d.l.toLocaleString()}</td>
      <td class="${cls(r.d.r21)}">${pct(r.d.r21)}</td>
      <td class="${cls(r.d.r252)}">${pct(r.d.r252)}</td>
      <td class="${r.p1 > 0.5 ? "pos" : "neg"}">${r.p1?.toFixed(3) ?? "—"}${badge((r.d.hd || {})["1W"])}</td>
      <td class="${r.p3 > 0.5 ? "pos" : "neg"}">${r.p3?.toFixed(3) ?? "—"}${badge((r.d.hd || {})["3M"])}</td>
      <td>${r.f.m12 != null ? r.f.m12 + "th" : "—"}</td>
      <td>${r.f.hi != null ? r.f.hi + "th" : "—"}</td>
      <td>${r.f.vol != null ? r.f.vol + "th" : "—"}</td>
    </tr>`).join("");
  document.getElementById("sc-n").textContent = rows.length + " names";
});
</script>"""


def render_screener_page(generated_at: str, as_of: str) -> str:
    body = f"""
<h2>Screener <span class="dim">/ the whole coverage universe — click a ticker
for its security page, any header to sort, filters to cut</span></h2>
<div class="tagline" style="margin-bottom:10px">model as-of <b>{as_of}</b> ·
probabilities are P(beat the S&amp;P median) per horizon · factor columns are
cross-sectional percentiles · <span id="sc-n" class="muted"></span></div>
{filter_bar(SECTORS, show_prob=True, show_side=False)}
<table>
<tr><th>Ticker</th><th class="tl">Name</th><th class="tl">Sector</th><th>Last</th>
<th>1m</th><th>12m</th><th>P 1W</th><th>P 3M</th>
<th>12m mom</th><th>52w-high</th><th>ST vol</th></tr>
<tbody id="sc-rows"></tbody></table>
<div class="edgemath">HONESTY — 1W and 1D are the validated horizons
(IC ≈ 0.017–0.019, t &gt; 2.8); 3M is suggestive only (t = 1.87). A 0.55
probability is a thin, real edge — screen with it, don't worship it.</div>
{SCREENER_JS}"""
    return page_shell("Vig — Screener", generated_at, "screener", body)
