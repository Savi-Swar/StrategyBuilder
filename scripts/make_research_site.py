"""Builds screen 06 RESEARCH for Vig: research.html (the hub) plus every
research document rendered as a Vig-shelled page under
reports/dashboard/research/. Rerun whenever the markdown changes:

    python scripts/make_research_site.py
"""
import datetime
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / "reports" / "dashboard"
RDIR = DASH / "research"
RDIR.mkdir(exist_ok=True)

INK, MUT, DIM = "#e6e2d8", "#8a9199", "#6d747c"
GRN, RED, AMB = "#46ff9a", "#ff5d5d", "#ffb000"

TABS = [("index.html", "01", "DESK"), ("analysis.html", "02", "ANALYSIS"),
        ("screener.html", "03", "SCREENER"), ("past_trades.html", "04", "PAST TRADES"),
        ("portfolio.html", "05", "PORTFOLIO"), ("research.html", "06", "RESEARCH"),
        ("desk.html", "07", "PREDMKT")]

CSS = """
* { box-sizing: border-box; margin: 0 }
body { background: #0b0d10; color: #e6e2d8;
  font: 13px "SF Mono", ui-monospace, Menlo, monospace; }
header { display: flex; justify-content: space-between; align-items: flex-end;
  padding: 18px 26px 14px; }
.wordmark { font-size: 30px; font-weight: 800; letter-spacing: 3px }
.tagline { color: #6d747c; font-size: 11px; letter-spacing: 1px }
.tagline b { color: #8a9199 }
.stamp-date { color: #6d747c; font-size: 11px }
.tabs { display: flex; border-top: 1px solid #22262c; border-bottom: 1px solid #22262c;
  position: sticky; top: 0; background: #0b0d10; z-index: 5; flex-wrap: wrap }
.tab { padding: 11px 18px; color: #8a9199; text-decoration: none; font-size: 12px;
  letter-spacing: 1.5px; border-right: 1px solid #22262c }
.tab .k { color: #6d747c; margin-right: 7px; font-size: 10px }
.tab.active { color: #e6e2d8; background: #0e1114; box-shadow: inset 0 2px 0 #ffb000 }
.tab:hover { color: #e6e2d8 }
.wrap { padding: 20px 26px 60px; max-width: 980px }
h2.sect { font-size: 11px; letter-spacing: 2.5px; color: #ffb000; margin: 30px 0 10px;
  text-transform: uppercase }
h2.sect::before { content: "▚ " }
h2.sect .dim { text-transform: none; letter-spacing: .5px }
.dim { color: #6d747c; font-size: 12px }
.htiles { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px }
.htile { border: 1px solid #22262c; background: #0e1114; padding: 12px 16px;
  min-width: 170px; flex: 1 }
.hlabel { color: #6d747c; font-size: 10px; letter-spacing: 2px; text-transform: uppercase }
.hval { font-size: 24px; font-weight: 700; margin: 6px 0 3px }
.hsub { color: #8a9199; font-size: 11px }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px; margin: 12px 0 }
.card { border: 1px solid #22262c; background: #0e1114; padding: 14px 16px;
  text-decoration: none; display: block }
.card:hover { border-color: #ffb000 }
.card .t { color: #e6e2d8; font-size: 13px; font-weight: 700 }
.card .s { color: #8a9199; font-size: 11px; margin-top: 6px; line-height: 1.5 }
.card .m { color: #6d747c; font-size: 10px; margin-top: 8px; letter-spacing: 1px;
  text-transform: uppercase }
a { color: #e6e2d8 }
footer { color: #6d747c; font-size: 11px; padding: 0 26px 40px }
img { max-width: 100%; border: 1px solid #22262c; margin: 8px 0 }
/* rendered markdown */
.md { line-height: 1.65; font-size: 13px }
.md h1 { font-size: 20px; margin: 24px 0 12px; letter-spacing: .5px }
.md h2 { font-size: 14px; color: #ffb000; margin: 26px 0 10px; letter-spacing: 1px;
  text-transform: uppercase; font-size: 12px; letter-spacing: 2px }
.md h2::before { content: "▚ " }
.md h3 { font-size: 13px; color: #e6e2d8; margin: 18px 0 8px }
.md p { margin: 10px 0; color: #c9c4b8 }
.md li { margin: 6px 0 6px 18px; color: #c9c4b8 }
.md strong { color: #e6e2d8 }
.md em { color: #9fb0c0; font-style: normal }
.md code { background: #14171b; padding: 1px 5px; font-size: 12px; color: #9fe0b8 }
.md pre { background: #0e1114; border: 1px solid #22262c; padding: 12px 14px;
  overflow-x: auto; margin: 10px 0 }
.md pre code { background: none; padding: 0 }
.md table { border-collapse: collapse; width: 100%; margin: 10px 0 }
.md td, .md th { border-bottom: 1px solid #14171b; padding: 5px 10px; text-align: left;
  font-size: 12px }
.md th { color: #6d747c; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase }
.md tr:hover td { background: #0e1114 }
.md blockquote { border-left: 2px solid #ffb000; padding-left: 14px; color: #9fb0c0;
  margin: 10px 0 }
.md hr { border: none; border-top: 1px solid #22262c; margin: 22px 0 }
.crumb { color: #6d747c; font-size: 11px; margin-bottom: 14px }
.crumb a { color: #8a9199; text-decoration: none }
.crumb a:hover { color: #ffb000 }
"""

JS = """
<script>
(() => {
  const pages = { "1": "index.html", "2": "analysis.html", "3": "screener.html",
                  "4": "past_trades.html", "5": "portfolio.html",
                  "6": "research.html", "7": "desk.html" };
  document.addEventListener("keydown", e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target instanceof Element && e.target.matches("input,textarea")) return;
    const p = pages[e.key];
    if (p) location.href = (location.pathname.includes("/research/") ? "../" : "") + p;
  });
})();
</script>"""

MD = markdown.Markdown(extensions=["tables", "fenced_code"])


def shell(title, body, active="research.html", depth=0):
    pre = "../" * depth
    tabs = "".join(
        f'<a class="tab{" active" if h == active else ""}" href="{pre}{h}">'
        f'<span class="k">{n}</span>{t}</a>' for h, n, t in TABS)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{title}</title><style>{CSS}</style></head><body>
<header>
  <div>
    <div class="wordmark">VIG</div>
    <div class="tagline">the house takes its cut — <b>the research record</b></div>
  </div>
  <div class="stamp-date">{now}</div>
</header>
<nav class="tabs">{tabs}</nav>
<div class="wrap">{body}</div>
<footer>keys: <b>1–7</b> screens · every claim links to the trial that produced it ·
negative results are kept, not buried</footer>
{JS}
</body></html>"""


def render_doc(src: pathlib.Path, out_name: str, title: str) -> str:
    """Render one markdown file to research/<out_name>; returns relative href."""
    text = src.read_text()
    MD.reset()
    body = ('<div class="crumb"><a href="../research.html">← 06 RESEARCH</a>'
            f' / {src.name}</div><div class="md">{MD.convert(text)}</div>')
    (RDIR / out_name).write_text(shell(f"VIG · {title}", body, depth=1))
    return f"research/{out_name}"


def first_para(src: pathlib.Path, n=170) -> str:
    """First non-heading prose line, as the card blurb."""
    for line in src.read_text().splitlines():
        s = line.strip().lstrip("*_ ").rstrip("*_ ")
        if s and not s.startswith(("#", "-", "|", "```", ">")):
            s = re.sub(r"[*_`\[\]]", "", s)
            return s[:n] + ("…" if len(s) > n else "")
    return ""


def card(href, title, sub, meta):
    return (f'<a class="card" href="{href}"><div class="t">{title}</div>'
            f'<div class="s">{sub}</div><div class="m">{meta}</div></a>')


# ── render the core documents ────────────────────────────────────────────
core = [
    (ROOT / "RESEARCH_STORY.md", "story.html", "The campaign, start to finish",
     "How three days of research went: the equity work, the anomaly audit, the prediction-market falsification, and why the Desk exists."),
    (ROOT / "KNOWLEDGE_BASE.md", "knowledge_base.html", "Knowledge base",
     "The condensed brain: verified edges, falsified claims, the math that matters, operating doctrine."),
    (ROOT / "RESEARCH_NOTES.md", "notes.html", "The full trial log",
     "Chronological record of every registered trial, decision, and negative result. The paper trail behind every number."),
]
core_cards = ""
for src, out, title, sub in core:
    href = render_doc(src, out, title)
    n_sect = len(re.findall(r"^## ", src.read_text(), re.M))
    core_cards += card(href, title, sub, f"{n_sect} sections · {src.name}")

# ── render the deep-research library ─────────────────────────────────────
PRETTY = {
    "net_alpha": "Net alpha: costs and construction",
    "edges": "Where edges still exist",
    "families": "Factor families, replicated",
    "math": "The quant math that matters",
    "engineering": "ML, systems and data engineering",
    "risk": "Risk, sizing and decision theory",
    "masters": "Masters of niche edges",
    "predmkt": "Prediction markets: the venue",
    "predmkt_institutions": "Who trades prediction markets",
    "wsb_method": "Attention signals: the WSB postmortem",
    "backtest_method": "Backtesting without lying to yourself",
}
lib_cards = ""
for src in sorted(ROOT.glob("reports/deep_research_*.md")):
    key = re.sub(r"^deep_research_|_\d{4}-\d{2}-\d{2}$", "", src.stem)
    title = PRETTY.get(key, key.replace("_", " "))
    date = re.search(r"(\d{4}-\d{2}-\d{2})", src.stem)
    href = render_doc(src, f"{key}.html", title)
    lib_cards += card(href, title, first_para(src),
                      f"deep research · {date.group(1) if date else ''}")

# ── the hub ──────────────────────────────────────────────────────────────
def tile(label, value, sub="", color=INK):
    return (f'<div class="htile"><div class="hlabel">{label}</div>'
            f'<div class="hval" style="color:{color}">{value}</div>'
            f'<div class="hsub">{sub}</div></div>')


hub = f"""
<p class="dim">Everything below is the actual research record — the trials,
the numbers, the negative results. The paper sim on
<a href="desk.html">07 PREDMKT</a> only trades what survived this page.</p>

<div class="htiles">
{tile("Registered experiments", "~70", "every variant counted, none hidden")}
{tile("Strategies killed", "15", "including the flagship (0.28 → 0.05)", RED)}
{tile("Survivor", "0.85", "walk-forward Sharpe · 77-instrument xsec · 12/15 yrs+", GRN)}
{tile("Original finding", "0.87", "2026 calibration slope — FLB reversed vs literature", AMB)}
</div>

<h2 class="sect">The record <span class="dim">— read in this order</span></h2>
<div class="cards">{core_cards}</div>

<h2 class="sect">Headline artifacts</h2>
<div class="cards">
{card("research/notes.html", "Walk-forward config selection — the honest number",
      "The harshest gate in the repo: choose configs on trailing data only, measure forward. In-sample Sharpe 0.28 became 0.05. Signal real, money gone.",
      "cycle 9 · the one to read first")}
{card("../study2_tearsheet.png", "Study 2 tearsheet — cross-sectional equity",
      "IC t=3.35 over 756 weeks, clean shuffled-label control, and why it still doesn't pay after costs.", "flagship · falsified")}
{card("../study1_tearsheet.png", "Study 1 tearsheet — multi-asset",
      "78 instruments, classic indicators dead after costs (best DSR 0.19), ML timing an honest failure.", "baselines")}
{card("../quark_onepager.pdf", "The one-pager",
      "The whole argument on one page.", "pdf")}
</div>

<h2 class="sect">Deep-research library <span class="dim">— 11 verified literature reviews</span></h2>
<div class="cards">{lib_cards}</div>

<h2 class="sect">Where it leads</h2>
<p class="dim" style="font-size:13px;line-height:1.6">Every directional
strategy on the prediction-market venue pays a spread wider than the
mispricing — measured both ways. The only structural winner is the maker.
That hypothesis is now running live on paper, self-grading:
<a href="desk.html">07 PREDMKT →</a></p>
"""

(DASH / "research.html").write_text(shell("VIG · 06 RESEARCH", hub))
n_docs = len(core) + len(list(ROOT.glob("reports/deep_research_*.md")))
print(f"research.html + {n_docs} rendered docs -> {RDIR}")
