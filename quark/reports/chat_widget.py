"""Vig's in-page assistant: a serverless agentic chat that runs entirely in
the browser. Calls the Anthropic API directly (CORS-enabled via the
anthropic-dangerous-direct-browser-access header) and exposes client-side
tools the model can call: filter the visible tables, drive the portfolio
builder, switch pages. The API key is pasted once and kept in localStorage
on this machine only."""

import json

CHAT_CSS = """
#vc-toggle { position: fixed; right: 26px; bottom: 24px; z-index: 50;
  background: #060708; border: 1px solid #ffb000; color: #ffb000;
  font: 12px "SF Mono", ui-monospace, Menlo, monospace; letter-spacing: 2px;
  padding: 11px 18px; cursor: pointer; }
#vc-toggle:hover { background: #ffb000; color: #060708; }
#vc-panel { position: fixed; right: 26px; bottom: 74px; z-index: 50;
  width: 420px; max-width: calc(100vw - 52px); height: 540px;
  max-height: calc(100vh - 120px); display: flex; flex-direction: column;
  background: #0b0d10; border: 1px solid #ffb000; box-shadow: 0 0 40px rgba(0,0,0,.7); }
#vc-head { padding: 10px 14px; border-bottom: 1px dashed #2a2e35;
  font-size: 11px; letter-spacing: 2px; color: #ffb000; display: flex;
  justify-content: space-between; }
#vc-head a { cursor: pointer; color: #8a9199; text-decoration: none; }
#vc-msgs { flex: 1; overflow-y: auto; padding: 12px 14px; font-size: 12.5px; }
.vc-m { margin-bottom: 12px; white-space: pre-wrap; }
.vc-m.you { color: #8a9199; }
.vc-m.you::before { content: "you › "; color: #46ff9a; }
.vc-m.vig { color: #e6e2d8; }
.vc-m.vig::before { content: "vig › "; color: #ffb000; }
.vc-m.sys { color: #6d747c; font-size: 11px; }
#vc-inrow, #vc-keyrow { display: flex; border-top: 1px solid #22262c; }
#vc-inrow input, #vc-keyrow input { flex: 1; background: #060708; border: none;
  color: #e6e2d8; font: 13px "SF Mono", ui-monospace, Menlo, monospace;
  padding: 12px 14px; }
#vc-inrow input:focus, #vc-keyrow input:focus { outline: none; }
#vc-inrow button, #vc-keyrow button { background: #ffb000; border: none;
  color: #060708; font: 700 12px "SF Mono", ui-monospace, Menlo, monospace;
  padding: 0 16px; cursor: pointer; letter-spacing: 1px; }
"""

CHAT_HTML = """
<button id="vc-toggle">▣ ASK VIG</button>
<div id="vc-panel" hidden>
  <div id="vc-head"><span>VIG — DESK ASSISTANT</span>
    <span><a id="vc-forget" title="forget API key">key×</a>&nbsp;&nbsp;<a id="vc-close">✕</a></span></div>
  <div id="vc-msgs"><div class="vc-m sys">Ask about today's picks, the record,
or the portfolio — or tell me to filter what you see ("only commodities",
"longs above 0.57"), set the builder ("$50k aggressive"), or switch pages.
Grounded in this page's data; not investment advice.</div></div>
  <div id="vc-keyrow" hidden>
    <input id="vc-key" type="password" placeholder="paste Anthropic API key (stored only in this browser)">
    <button id="vc-savekey">SAVE</button></div>
  <div id="vc-inrow"><input id="vc-in" placeholder="ask vig…">
    <button id="vc-send">SEND</button></div>
</div>
"""

CHAT_JS = r"""
<script>
(() => {
const CTX = __CTX__;
const PAGE = "__PAGE__";
const MODEL = "claude-opus-4-8";
const SYS = `You are Vig's in-page desk assistant on the "${PAGE}" page of a
personal systematic-trading dashboard. Be terse and quantitative. Ground every
claim in PAGE CONTEXT below; if it isn't there, say so rather than guessing.
The desk's edge is real but thin (weekly IC ~0.017): never oversell, never
imply certainty. Research tooling, not investment advice — no need to repeat
that disclaimer unless asked about real-money decisions.
Use tools when the user wants to change what they see (filters, portfolio
inputs, navigation). After filtering, summarize what remains.
PAGE CONTEXT: ` + JSON.stringify(CTX);

const TOOLS = [
  { name: "filter_view",
    description: "Hide table rows on the current page that do not match. " +
      "Args (all optional, AND-combined): query = substring match on tickers; " +
      "asset_class = e.g. commodity, fx_g10, fx_cross, fx_em, equity_index, bond_fut, crypto; " +
      "side = LONG or SHORT (trend/past-trades rows); min_prob = 0-1 threshold " +
      "on the row's model probability. Returns the visible-row count.",
    input_schema: { type: "object", properties: {
      query: { type: "string" }, asset_class: { type: "string" },
      side: { type: "string" }, min_prob: { type: "number" } },
      additionalProperties: false } },
  { name: "reset_view", description: "Clear all filters; show every row.",
    input_schema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "set_portfolio",
    description: "Portfolio page only: set capital (USD) and/or risk profile " +
      "(conservative | balanced | aggressive) in the builder.",
    input_schema: { type: "object", properties: {
      capital: { type: "number" }, profile: { type: "string" } },
      additionalProperties: false } },
  { name: "open_page",
    description: "Navigate after replying: desk | past_trades | portfolio.",
    input_schema: { type: "object", properties: { page: { type: "string" } },
      required: ["page"], additionalProperties: false } },
];

let navTarget = null;

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
    const cap = document.getElementById("cap");
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
    return "will navigate to " + input.page + " after this reply";
  }
  return "error: unknown tool";
}

const $ = id => document.getElementById(id);
const msgs = [];

function addMsg(cls, text) {
  const d = document.createElement("div");
  d.className = "vc-m " + cls;
  d.textContent = text;
  $("vc-msgs").appendChild(d);
  $("vc-msgs").scrollTop = 1e9;
}

async function callClaude() {
  const key = localStorage.getItem("vig_key");
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": key, "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
      "content-type": "application/json",
    },
    body: JSON.stringify({ model: MODEL, max_tokens: 1500, system: SYS,
                           tools: TOOLS, messages: msgs }),
  });
  if (!resp.ok) throw new Error("API " + resp.status + ": " +
    (await resp.text()).slice(0, 160));
  return resp.json();
}

async function send() {
  const text = $("vc-in").value.trim();
  if (!text) return;
  if (!localStorage.getItem("vig_key")) {
    $("vc-keyrow").hidden = false;
    addMsg("sys", "paste your Anthropic API key first (console.anthropic.com)");
    return;
  }
  $("vc-in").value = "";
  addMsg("you", text);
  msgs.push({ role: "user", content: text });
  addMsg("sys", "…");
  try {
    for (let hop = 0; hop < 6; hop++) {
      const r = await callClaude();
      msgs.push({ role: "assistant", content: r.content });
      const texts = r.content.filter(b => b.type === "text").map(b => b.text);
      const tools = r.content.filter(b => b.type === "tool_use");
      $("vc-msgs").lastChild.remove();  // the "…"
      texts.forEach(t => addMsg("vig", t));
      if (r.stop_reason !== "tool_use") break;
      const results = tools.map(t => ({ type: "tool_result",
        tool_use_id: t.id, content: runTool(t.name, t.input) }));
      tools.forEach((t, i) => addMsg("sys",
        `[${t.name}] ${results[i].content}`));
      msgs.push({ role: "user", content: results });
      addMsg("sys", "…");
    }
  } catch (e) {
    if ($("vc-msgs").lastChild.textContent === "…") $("vc-msgs").lastChild.remove();
    addMsg("sys", "error — " + e.message);
  }
  if (navTarget) { const t = navTarget; navTarget = null;
    setTimeout(() => location.href = t, 600); }
}

document.addEventListener("DOMContentLoaded", () => {
  $("vc-toggle").addEventListener("click", () => {
    $("vc-panel").hidden = !$("vc-panel").hidden;
    if (!localStorage.getItem("vig_key")) $("vc-keyrow").hidden = false;
    $("vc-in").focus();
  });
  $("vc-close").addEventListener("click", () => $("vc-panel").hidden = true);
  $("vc-savekey").addEventListener("click", () => {
    const k = $("vc-key").value.trim();
    if (k) { localStorage.setItem("vig_key", k); $("vc-keyrow").hidden = true;
             addMsg("sys", "key saved to this browser"); }
  });
  $("vc-forget").addEventListener("click", () => {
    localStorage.removeItem("vig_key"); $("vc-keyrow").hidden = false;
    addMsg("sys", "key forgotten");
  });
  $("vc-send").addEventListener("click", send);
  $("vc-in").addEventListener("keydown", e => { if (e.key === "Enter") send(); });
});
})();
</script>"""


def chat_widget(context: dict, page: str) -> str:
    """CSS + HTML + JS for the assistant, with page context embedded."""
    js = (CHAT_JS
          .replace("__CTX__", json.dumps(context, default=str))
          .replace("__PAGE__", page))
    return f"<style>{CHAT_CSS}</style>{CHAT_HTML}{js}"
