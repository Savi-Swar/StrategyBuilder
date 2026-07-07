"""Vig's in-page assistant — a slide-in drawer, serverless: the browser
calls the Anthropic API directly (CORS-enabled via
anthropic-dangerous-direct-browser-access) with client-side tools that act
on the page (filters, portfolio inputs, navigation). The API key is pasted
once and lives in localStorage on this machine only."""

import json

CHAT_CSS = """
#vc-toggle { position: fixed; right: 26px; bottom: 24px; z-index: 60;
  background: #0b0d10; border: 1px solid #ffb000; color: #ffb000;
  font: 12px "SF Mono", ui-monospace, Menlo, monospace; letter-spacing: 2px;
  padding: 12px 20px; cursor: pointer; box-shadow: 0 6px 24px rgba(0,0,0,.5); }
#vc-toggle:hover { background: #ffb000; color: #060708; }
#vc-panel { position: fixed; right: 0; top: 0; bottom: 0; z-index: 70;
  width: 470px; max-width: 94vw; display: flex; flex-direction: column;
  background: #0a0c0f; border-left: 1px solid #2a2e35;
  box-shadow: -30px 0 60px rgba(0,0,0,.55);
  transform: translateX(102%); transition: transform .22s ease; }
#vc-panel.open { transform: translateX(0); }
#vc-head { padding: 16px 20px; border-bottom: 1px solid #22262c;
  display: flex; justify-content: space-between; align-items: center; }
#vc-head .t { font-size: 13px; letter-spacing: 3px; color: #ffb000; font-weight: 700; }
#vc-head .s { font-size: 10px; color: #6d747c; letter-spacing: 1px; margin-top: 3px; }
#vc-close { cursor: pointer; color: #8a9199; font-size: 18px; padding: 4px 8px;
  border: 1px solid transparent; }
#vc-close:hover { color: #e6e2d8; border-color: #2a2e35; }
#vc-msgs { flex: 1; overflow-y: auto; padding: 18px 20px; }
.vc-m { margin-bottom: 18px; }
.vc-tag { font-size: 10px; letter-spacing: 2px; margin-bottom: 5px; font-weight: 700; }
.vc-m.you .vc-tag { color: #46ff9a; }
.vc-m.vig .vc-tag { color: #ffb000; }
.vc-body { font-size: 13px; line-height: 1.7; color: #d9d4c8; }
.vc-m.you .vc-body { color: #9fa8b2; }
.vc-body b { color: #ffffff; }
.vc-body code { background: #14171b; border: 1px solid #22262c; padding: 1px 5px;
  font-size: 12px; }
.vc-body ul { margin: 6px 0 6px 18px; }
.vc-body li { margin-bottom: 3px; }
.vc-act { font-size: 11px; color: #46ff9a; background: rgba(52,211,153,.06);
  border-left: 2px solid #46ff9a; padding: 6px 10px; margin: 8px 0; }
.vc-err { font-size: 11.5px; color: #ff5d5d; background: rgba(248,113,113,.06);
  border-left: 2px solid #ff5d5d; padding: 6px 10px; margin: 8px 0; }
#vc-think { display: none; padding: 0 20px 12px; color: #ffb000; font-size: 12px;
  letter-spacing: 2px; }
#vc-think.on { display: block; }
#vc-think span { animation: vcpulse 1.2s infinite; display: inline-block; }
#vc-think span:nth-child(2) { animation-delay: .2s; }
#vc-think span:nth-child(3) { animation-delay: .4s; }
@keyframes vcpulse { 0%,100% { opacity: .2; } 50% { opacity: 1; } }
#vc-chips { padding: 0 20px 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.vc-chip { border: 1px solid #2a2e35; color: #9fa8b2; font-size: 11px;
  padding: 7px 12px; cursor: pointer; background: #0e1114; }
.vc-chip:hover { border-color: #ffb000; color: #ffb000; }
#vc-inrow { display: flex; border-top: 1px solid #22262c; }
#vc-in { flex: 1; background: #0a0c0f; border: none; color: #e6e2d8;
  font: 13.5px "SF Mono", ui-monospace, Menlo, monospace; padding: 17px 20px; }
#vc-in:focus { outline: none; }
#vc-in:disabled { opacity: .4; }
#vc-send { background: none; border: none; border-left: 1px solid #22262c;
  color: #ffb000; font: 700 13px "SF Mono", ui-monospace, Menlo, monospace;
  padding: 0 22px; cursor: pointer; letter-spacing: 1px; }
#vc-send:hover { background: #ffb000; color: #060708; }
#vc-send:disabled { opacity: .3; pointer-events: none; }
#vc-foot { padding: 8px 20px 12px; font-size: 10px; color: #565d64;
  display: flex; justify-content: space-between; }
#vc-forget { cursor: pointer; color: #565d64; text-decoration: underline; }
#vc-keywrap { padding: 26px 22px; }
#vc-keywrap h3 { font-size: 13px; letter-spacing: 2px; color: #ffb000; margin-bottom: 12px; }
#vc-keywrap p { font-size: 12px; line-height: 1.7; color: #9fa8b2; margin-bottom: 16px; }
#vc-keywrap a { color: #ffb000; }
#vc-keyrow { display: flex; border: 1px solid #2a2e35; }
#vc-key { flex: 1; background: #060708; border: none; color: #e6e2d8;
  font: 13px "SF Mono", ui-monospace, Menlo, monospace; padding: 13px 14px; }
#vc-key:focus { outline: none; }
#vc-savekey { background: #ffb000; border: none; color: #060708;
  font: 700 12px "SF Mono", ui-monospace, Menlo, monospace; padding: 0 18px;
  cursor: pointer; }
"""

CHAT_HTML = """
<button id="vc-toggle">▣ ASK VIG</button>
<div id="vc-panel">
  <div id="vc-head">
    <div><div class="t">ASK VIG</div>
    <div class="s">grounded in this page · can filter &amp; drive the UI · not investment advice</div></div>
    <span id="vc-close">✕</span>
  </div>
  <div id="vc-keywrap" hidden>
    <h3>ONE-TIME SETUP</h3>
    <p>Vig's assistant talks to the Anthropic API straight from this browser —
    no server, nothing running. Paste an API key from
    <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a>.
    It is stored only in this browser's localStorage and sent only to
    api.anthropic.com. A conversation costs a few cents.</p>
    <div id="vc-keyrow">
      <input id="vc-key" type="password" placeholder="sk-ant-…">
      <button id="vc-savekey">START</button>
    </div>
  </div>
  <div id="vc-msgs"></div>
  <div id="vc-think">thinking<span>.</span><span>.</span><span>.</span></div>
  <div id="vc-chips"></div>
  <div id="vc-inrow">
    <input id="vc-in" placeholder="ask, or tell me what to show…">
    <button id="vc-send">SEND</button>
  </div>
  <div id="vc-foot"><span>claude-opus-4-8 · serverless</span>
    <span id="vc-forget">forget key</span></div>
</div>
"""

CHAT_JS = r"""
<script>
(() => {
const CTX = __CTX__;
const PAGE = "__PAGE__";
const CHIPS = __CHIPS__;
const MODEL = "claude-opus-4-8";
const SYS = `You are Vig's in-page desk assistant on the "${PAGE}" page of a
personal systematic-trading dashboard. Be terse and quantitative; markdown is
rendered (bold, bullets, inline code). Ground every claim in PAGE CONTEXT; if
it isn't there, say so rather than guessing. The desk's edge is real but thin
(weekly IC ~0.017): never oversell, never imply certainty. Use tools whenever
the user wants to change what they see (filters, portfolio inputs,
navigation); after filtering, summarize what remains in one line.
PAGE CONTEXT: ` + JSON.stringify(CTX);

const TOOLS = [
  { name: "filter_view",
    description: "Hide table rows on the current page that do not match. " +
      "Args (optional, AND-combined): query = ticker substring; asset_class " +
      "(commodity, fx_g10, fx_cross, fx_em, equity_index, bond_fut, crypto, stock); " +
      "side = LONG|SHORT; min_prob = 0-1 on the row's model probability. " +
      "Returns visible-row count.",
    input_schema: { type: "object", properties: {
      query: { type: "string" }, asset_class: { type: "string" },
      side: { type: "string" }, min_prob: { type: "number" } },
      additionalProperties: false } },
  { name: "reset_view", description: "Clear all filters; show every row.",
    input_schema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "set_portfolio",
    description: "Portfolio page only: set capital (USD) and/or profile " +
      "(conservative|balanced|aggressive).",
    input_schema: { type: "object", properties: {
      capital: { type: "number" }, profile: { type: "string" } },
      additionalProperties: false } },
  { name: "open_page",
    description: "Navigate after replying: desk | past_trades | portfolio.",
    input_schema: { type: "object", properties: { page: { type: "string" } },
      required: ["page"], additionalProperties: false } },
];

let navTarget = null;
const msgs = [];
const $ = id => document.getElementById(id);

function runTool(name, input) {
  if (name === "reset_view") {
    document.querySelectorAll("tr[data-search]").forEach(r => r.style.display = "");
    return "all rows visible";
  }
  if (name === "filter_view") {
    let shown = 0;
    document.querySelectorAll("tr[data-search]").forEach(r => {
      let ok = true;
      if (input.query) ok = ok && r.dataset.search.toLowerCase()
        .includes(input.query.toLowerCase());
      if (input.asset_class) ok = ok && (r.dataset.class || "")
        .includes(input.asset_class.toLowerCase());
      if (input.side) ok = ok && (r.dataset.side || "") === input.side.toUpperCase();
      if (input.min_prob != null && r.dataset.prob)
        ok = ok && parseFloat(r.dataset.prob) >= input.min_prob;
      r.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    return shown + " rows visible after filter";
  }
  if (name === "set_portfolio") {
    const cap = $("cap");
    if (!cap) return "error: not on the portfolio page — call open_page first";
    if (input.capital != null) {
      cap.value = Math.round(input.capital).toLocaleString("en-US");
      cap.dispatchEvent(new Event("input"));
    }
    if (input.profile) {
      const b = document.querySelector(`.seg button[data-p="${input.profile}"]`);
      if (!b) return "error: unknown profile " + input.profile;
      b.click();
    }
    return "portfolio set";
  }
  if (name === "open_page") {
    const map = { desk: "index.html", past_trades: "past_trades.html",
                  portfolio: "portfolio.html" };
    if (!map[input.page]) return "error: unknown page";
    navTarget = map[input.page];
    return "navigating to " + input.page + " after this reply";
  }
  return "error: unknown tool";
}

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function md(text) {  // markdown-lite: bold, code, bullets, paragraphs
  const blocks = esc(text).split(/\n\n+/).map(b => {
    const lines = b.split("\n");
    if (lines.every(l => /^\s*[-•]\s+/.test(l)))
      return "<ul>" + lines.map(l =>
        "<li>" + l.replace(/^\s*[-•]\s+/, "") + "</li>").join("") + "</ul>";
    return "<p>" + b.replace(/\n/g, "<br>") + "</p>";
  }).join("");
  return blocks
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function addMsg(cls, html, tag) {
  const d = document.createElement("div");
  d.className = "vc-m " + cls;
  d.innerHTML = (tag ? `<div class="vc-tag">${tag}</div>` : "") +
                `<div class="vc-body">${html}</div>`;
  $("vc-msgs").appendChild(d);
  $("vc-msgs").scrollTop = 1e9;
}
const addNote = (cls, text) => {
  const d = document.createElement("div");
  d.className = cls;
  d.textContent = text;
  $("vc-msgs").appendChild(d);
  $("vc-msgs").scrollTop = 1e9;
};

function busy(on) {
  $("vc-think").classList.toggle("on", on);
  $("vc-in").disabled = on;
  $("vc-send").disabled = on;
  if (!on) $("vc-in").focus();
}

async function callClaude() {
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": localStorage.getItem("vig_key"),
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
      "content-type": "application/json",
    },
    body: JSON.stringify({ model: MODEL, max_tokens: 1500, system: SYS,
                           tools: TOOLS, messages: msgs }),
  });
  if (!resp.ok) throw new Error("API " + resp.status + " — " +
    (await resp.text()).slice(0, 200));
  return resp.json();
}

async function send(text) {
  text = (text ?? $("vc-in").value).trim();
  if (!text || $("vc-send").disabled) return;
  $("vc-in").value = "";
  $("vc-chips").innerHTML = "";
  addMsg("you", md(text), "YOU");
  msgs.push({ role: "user", content: text });
  busy(true);
  try {
    for (let hop = 0; hop < 6; hop++) {
      const r = await callClaude();
      msgs.push({ role: "assistant", content: r.content });
      r.content.filter(b => b.type === "text")
        .forEach(b => addMsg("vig", md(b.text), "VIG"));
      if (r.stop_reason !== "tool_use") break;
      const tools = r.content.filter(b => b.type === "tool_use");
      const results = tools.map(t => {
        const out = runTool(t.name, t.input);
        addNote(out.startsWith("error") ? "vc-err" : "vc-act",
                `${t.name} → ${out}`);
        return { type: "tool_result", tool_use_id: t.id, content: out };
      });
      msgs.push({ role: "user", content: results });
    }
  } catch (e) {
    addNote("vc-err", e.message);
  }
  busy(false);
  if (navTarget) { const t = navTarget; navTarget = null;
    setTimeout(() => location.href = t, 700); }
}

function showChips() {
  $("vc-chips").innerHTML = CHIPS.map(c =>
    `<span class="vc-chip">${esc(c)}</span>`).join("");
  document.querySelectorAll(".vc-chip").forEach(el =>
    el.addEventListener("click", () => send(el.textContent)));
}

function keyState() {
  const has = !!localStorage.getItem("vig_key");
  $("vc-keywrap").hidden = has;
  $("vc-inrow").style.display = has ? "" : "none";
  $("vc-chips").style.display = has ? "" : "none";
}

document.addEventListener("DOMContentLoaded", () => {
  $("vc-toggle").addEventListener("click", () => {
    const p = $("vc-panel");
    p.classList.toggle("open");
    keyState();
    if (p.classList.contains("open") && !$("vc-msgs").hasChildNodes()) showChips();
    if (p.classList.contains("open")) $("vc-in").focus();
  });
  $("vc-close").addEventListener("click", () => $("vc-panel").classList.remove("open"));
  $("vc-savekey").addEventListener("click", () => {
    const k = $("vc-key").value.trim();
    if (!k) return;
    localStorage.setItem("vig_key", k);
    keyState(); showChips(); $("vc-in").focus();
  });
  $("vc-key").addEventListener("keydown", e => {
    if (e.key === "Enter") $("vc-savekey").click(); });
  $("vc-forget").addEventListener("click", () => {
    localStorage.removeItem("vig_key"); keyState(); });
  $("vc-send").addEventListener("click", () => send());
  $("vc-in").addEventListener("keydown", e => { if (e.key === "Enter") send(); });
});
})();
</script>"""

DEFAULT_CHIPS = {
    "desk": ["why these three picks?", "show only commodities",
             "longs above 0.57", "how's the edge holding up?"],
    "past_trades": ["what should I learn from the record?",
                    "show only losses", "shorts only",
                    "is the losing streak normal?"],
    "portfolio": ["$50k balanced — walk me through it",
                  "set it to $25k aggressive",
                  "how bad can conservative get?",
                  "why so much in bonds?"],
}


def chat_widget(context: dict, page: str) -> str:
    """CSS + HTML + JS for the assistant, with page context embedded."""
    js = (CHAT_JS
          .replace("__CTX__", json.dumps(context, default=str))
          .replace("__PAGE__", page)
          .replace("__CHIPS__", json.dumps(DEFAULT_CHIPS.get(page, []))))
    return f"<style>{CHAT_CSS}</style>{CHAT_HTML}{js}"
