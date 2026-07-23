# Quark Knowledge Base

*The consolidated brain: every verified finding, dead end, formula, and rule from
the 2026-07 research campaign. Primary sources in `reports/deep_research_*.md`;
empirical trial log in `RESEARCH_NOTES.md`. Confidence flags: **[V]** adversarially
verified (3-vote), **[E]** our own empirical result, **[U]** unverified lead.*

---

## 0. The one-paragraph thesis
Edges are inventory, not assets — they decay after publication (58% in US large
caps, worst where arbitrage capital concentrates). An individual's only durable
advantage is **capacity**: edges too small ($50k–$2M) for institutions to touch.
The job is a pipeline: find candidate edges, validate them cheaply and honestly
(PIT + walk-forward + shuffled control + efficient-market null), size survivors as
if the estimate is wrong (fractional Kelly), and re-hunt as they die. The machine
that runs this loop is worth more than any single edge.

---

## 1. VERIFIED EDGES (with effect sizes)

### Cross-sectional / factor
- **[E] Cross-asset relative value is the pond.** Ranking 77 instruments across 7
  asset classes against each other (not time-series) → walk-forward net Sharpe
  **0.85**, shuffled-control clean, 12/15 positive years, +0.08 corr to equity.
  The edge lives outside the most-arbitraged universe.
- **[V] Gross profitability (Novy-Marx) survives in large caps**: 26bp/mo (t=1.88)
  in the largest quintile, incremental to value; the two are −0.57 correlated so a
  50/50 mix ~doubles Sharpe (in-sample 0.74; halve it for post-decay estimate).
- **[E] Garleanu-Pedersen partial rebalancing** (trade a fraction τ toward target,
  tilt to persistent signals) delivered the literature's promised +~0.2 net Sharpe
  on the PIT panel. Cost side is *solved*; the binding constraint is gross signal.
- **[E] Composite IC adds in quadrature**: √(IC₁²+IC₂²). Adding one uncorrelated
  IC-0.02 signal beats improving the existing signal 20% — new families dominate.
  Broad-panel composite (price+insider+overnight) reached IC t=3.9.

### Prediction markets (the chosen niche)
- **[V] Favorite-longshot bias is universal, worsens with horizon**: calibration
  slope 0.99 (≤1h to resolution) → 1.32 (>1 month). Strongest in **politics**.
  → buy the favorite side at medium horizon; the crowd underprices near-certainties.
- **[V] Sub-10¢ longshots lose buyers >60%; contracts >70¢ earn positive post-fee
  returns.** Never hold lottery tickets; the favorite side is where net-positive lives.
- **[V] ~$40M arbitrage extracted (Apr'24–Apr'25)** from mispriced mutually-exclusive
  sets (buy-all <$1 / sell-all >$1). Median depth ~15 shares — retail-only by construction.
- **[E] The telegraph**: longshot *surprises* that resolved YES showed a 3–4 day
  price *staircase* before the jump (e.g. 0.04→0.14→0.24→0.82). A *rising* longshot
  is informed money arriving. Read the slope, not the level. (News-shock surprises
  give no warning — uncatchable from odds.)
- **[V] Always be the maker**: makers structurally out-earn takers; Polymarket pays
  daily quadratic LP rewards S=((v−s)/v)²·b for tight two-sided quotes.
- **[E] My edge = semantic verification, not information.** Naive date-ladder arb
  scans are ~90% false positives (survival-ladders, snapshot vs cumulative,
  different-event). The value is *reading resolution rules* to filter them — a
  language strength, immune to my Jan-2026 knowledge cutoff.

### Timing / regime
- **[E] Turn-of-month lives** (+0.5 Sharpe, 58yrs post-publication) — loser is the
  payroll calendar, a structural counterparty no fund can arbitrage. Usable as a
  free execution-timing overlay.
- **[E] Storms are learnable — but NOT tradable**: OOS AUC 0.76, 2.6× lift, 11/11
  years (real screen). RETURN GATE FAILED (2026-07-24): top-5% states net +5.5% vs
  baseline +5.9%, median negative, 10.6% lose >50% — a lottery bag with no premium.
  Status: scanner in the drawer; classification ≠ strategy, proven on itself.

---

## 2. FALSIFIED — do not re-run without new construction
- **[E] S&P cross-sectional flagship**: IC real (t=2.2–2.4) but walk-forward config
  selection → net Sharpe **~0.05**. Economic edge indistinguishable from zero.
- **[E] Monthly S&P signal was 100% survivorship** (PIT IC = 0.0000).
- **[E] XBRL-timed PEAD/SUE**: features *subtract* (both horizons). 10-Q filed dates
  lag the 8-K announcement 2–4 weeks; drift already spent. Needs announcement dates.
- **[E] 8-K micro-cap earnings drift**: extinct at all sizes (small-cap −0.05%,
  t=−0.40, n=11.8k). Machines read every filing now — the barrier commoditized.
- **[E] Crypto cross-sectional momentum**: IC real (t=1.99 clean) but extremes
  mean-revert → net negative every τ.
- **[E] WSB attention**: clean null (t=0.15). Edge died Jan-2021 (member explosion);
  data is adversarial (users post fake tickers to poison scrapers).
- **[E] Broad-universe price-only economics**: IC t=3.11 but gross spread thinner
  than S&P; extremes reverse. Signal ≠ money.
- **[E] Realized weather → nat gas**: fully priced (t=0.44 vs control). The edge is
  upstream in forecast *errors*, not realizations.
- **[V] Most published anomalies**: 6 of 8 tested dead or *inverted* on our panel;
  the crowded ones (reversal, low-vol) became anti-edges that pay the other side.
- **[E] FLB harvesting on Polymarket (2026)**: FALSIFIED as-implemented. 55-trial
  campaign (Jan-Feb steer, Mar-Jul test): frozen config −$2,111 at MC pct 2.4%
  (significantly below the efficient-market null); best of 50 variants = breakeven.
  Stretch strength monotonically WORSE; politics the poison category. The 2021-25
  documented bias is compressed/dead in 2026 tail markets — the institutional-entry
  edge-death clock, confirmed on our own data. Cluster caps robustly saved money in
  every variant (permanent doctrine). CLV called the verdict from month one.
  STILL-LIVE untested families: telegraph/slope momentum, pure arb, maker rewards,
  whale-following — all queued for live-forward paper (Aug+), the only clean data.

---

## 3. THE MATH (verified formula sheet)
- **[V] Fundamental law, corrected**: IR = IC/√(1/(φN)+σ²_IC), capped at IC/σ_IC as
  N→∞. Naive IR=IC√breadth overstates wildly. Our IC 0.0125, t=2.35 ⇒ σ_IC≈0.146 ⇒
  gross IR ceiling ≈0.62, effective breadth ~45–50 independent bets/wk (not 470).
  **IC *volatility* bounds you as hard as mean IC** — stabilizing IC (ensembling,
  horizon-blend, family diversification) is worth as much as raising it.
- **[V] Transfer coefficient**: IR = TC·IC·√BR; constrained books capture only
  30–80% of theoretical IR. Decile books discard information; rank-linear + inverse-vol
  construction recovered +34% Sharpe where gross edge existed.
- **[V] Kelly (continuous)**: f* = μ/σ² single-asset; F* = Σ⁻¹(μ−r) multi-asset.
  **Fractional Kelly is mandatory**: overestimate edge by 2× → full-Kelly gives
  *negative* growth. Benter ran ½–⅓ Kelly. Empirically (our 50-variant game) median
  wealth peaked at 1.25× leverage and *fell* at 1.5× — the inverted-U is real.
- **[V] Publication decay**: 58% in US large caps, worst in liquid/large/low-idio-vol
  names. Haircut every published effect ~half before believing it.
- **CLV (to build)**: beating the *closing* price predicts long-run profit better
  than short-run ROI; converges in hundreds of bets, not thousands.

### Betting-backtest methodology [V] (reports/deep_research_backtest_method)
- **[V] Sharp-reference-price / CLV is the gold standard**: EV vs a sharp book's
  margin-removed price predicts realized returns ~1:1 (Buchdahl, 37k matches); soft
  prices carry no info. Our CLV-analogue = entry price vs later pre-resolution price.
- **[V] Significance gate = Monte-Carlo efficient-market null, NOT a t-test**:
  simulate outcomes drawn from market-implied probabilities; a record is real only
  if it beats that distribution (Kaunitz 10.82σ template). Per-period testing gives
  **78% family-wise false positives** — test the full period, correct for variants.
- **[V] Documented FLB frequently does NOT survive net of spread+fees**: soccer/tennis
  every odds decile pays <1 per unit at closing odds. Calibration bias ≠ profit.
  The report card requires BOTH Monte-Carlo-null-significant net return AND positive CLV.
- **[V] Entry realism, conditioned on price level** (Polymarket order-book): median
  spread ~400bps at 0.4–0.6, **1,300–1,800bps below 0.10**, ~53bps half-spread above
  0.90. Longshots are expensive to trade — the FLB "avoid <10¢" rule is also a
  spread rule. Model executable depth (~15 shares many episodes).
- **[V] Convergence contamination**: exclude near-resolution phase (prices mechanically
  converge; MMs withdraw quotes). Entry-timing cutoff pre-specified, ≥ a few days out.
- **[V] Cluster-robust inference**: cluster SEs at event level (mutually-exclusive
  contracts negatively correlated) AND contract level (repeated daily obs); never
  double-count Yes/No sides. Enforce per-event exposure caps.
- **[V] Calibration regression**: use normalized probabilities when an overround
  exists (raw inverse-odds regression is biased against detecting FLB).
- **[V] Low power is severe**: even 14 seasons detects a real |β|=0.05 bias <50% of
  the time. Expect to need many bets; a null is not proof of no edge.
- **Model-vs-market threshold** (Kaunitz rule): bet only when model prob ≥ ~1.4×
  market implied — monotonically improves returns, though often not past breakeven.

---

## 4. METHODS (the gates — non-negotiable)
1. **PIT correctness**: features known on the date they appear. Value first visible
   the trading day *after* filed date. (Cycle-3 lesson: 10-Q vs 8-K timing.)
2. **Purged walk-forward** for model training (purge ≥ horizon).
3. **Walk-forward CONFIG selection**: pick τ/blend/threshold on trailing data only,
   measure forward. This is what took 0.28 → 0.05. The harshest, truest gate.
4. **Shuffled-label control**: real signal → shuffled ≈ 0. Always run it.
5. **PIT/survivorship measurement**: quote survivorship as a measured margin, not a
   disclaimer. Current-members panels are upper bounds.
6. **Trial counting / DSR**: every evaluated variant registers; quote plateaus not
   maxima. Selection tax measured at **98%** (max vs median of 50 variants).
7. **Efficient-market Monte-Carlo null** (betting): simulate histories where prices
   were exactly right; a record is real only if it beats that distribution.
8. **Data-artifact paranoia**: every artifact *flatters* (LUNA ticker-reuse gave a
   fake +17M% day hiding a negative strategy; convergence-contaminated trades gave a
   fake step-function). Cleaning always reveals something smaller and truer.

---

## 5. MASTERS' DOCTRINE (Thorp / Benter — verified)
- **Thorp loop**: idea → quantitative development → cheap real-world verification.
  (We reinvented this as the cycle loop.)
- **Benter**: 10 man-years to build the edge (5 model, 5 operation) — the effort
  *was* the moat. Published his model and still won: some moats survive disclosure.
- **Blend your estimate with the market's** (Benter's key technical insight): a raw
  model is biased vs public odds; combine them. Directly applies to bias-correcting
  market prices rather than forecasting independently.
- **Capacity-first pond selection**: Benter targeted the largest pools because
  edge capacity = 0.25–0.5% of pool turnover. Pick the pond by its capacity.
- **The ladder**: gambling→markets→scale. Niches are rocket fuel early, become
  rounding errors as wealth outgrows their capacity (our edge-factory sim reproduced
  this: niches 24% of profits early, 6% late). Buffett's confession: small sums earn
  the highest returns.

---

## 6. PREDICTION-MARKET OPERATIONS
- **Venues**: Polymarket (CLOB on Polygon, USDC, UMA oracle — 2h challenge window,
  $750 bonds, 50/50 "Unknown" settlement risk; US-person restricted). Kalshi
  (CFTC-regulated, US-legal, taker fee 0.07·p·(1−p)).
- **Free data**: Gamma (markets, no key), CLOB (order books), data-api
  (per-wallet positions/trades/leaderboard — the RIGHT tool for whale-following;
  the /trades endpoint is recency-first, causing convergence contamination).
- **Standable-on code**: `Polymarket/agents` (AI/RAG forecaster, MIT, 3.7k★),
  `warproxxx/poly-maker` & official `poly-market-maker` (LP-reward makers).
  **Scams flagged**: "guaranteed YES+NO<$1" bots; `Trum3it/polymarket-arbitrage-bot`
  = malware. Real code disclaims profit.
- **Institutions**: SIG desk 2023 / Kalshi MM Apr-2024 (NOT 2021 — corrected);
  DRW/Wintermute/IMC hiring 2026 = edge-death clock ticking. Liquid-sports
  single-market arb DEAD (7 episodes/mo, 3.6s lifespan). Capacity floor verified:
  combinatorial arb alive at 101bps but 77% of episodes can't fill $100.
- **Who loses**: partisan/emotional bettors, hedgers, attention traders. Markets
  ≤ polls on election eve since 1936 — not an oracle.

---

## 7. OPERATING RULES (the constitution)
- **Sizing**: portfolio vol target 10–12% (~⅕ Kelly of shrunk edge); per-niche
  positions ≤ ⅓ Kelly of estimated edge; theme-cluster caps (the Iran lesson: 3
  markets = 1 bet); STOP-file kill switch.
- **Niche selection** (rank order): structural loser > nameable barrier > event
  frequency > machine-testable > capacity fit > differential info. Anti-signals:
  needs latency, needs paid data, popular on FinTwit, loser is smart money.
- **Never**: trade what hasn't passed its gates; size past policy; touch a venue
  you're not eligible for; quote a max instead of a plateau; trust an artifact.
- **Always**: log every trial; measure survivorship; run the shuffled control;
  haircut published effects ~50%; treat a *worse* number on the second look as true.

---

## 8. OPEN / QUEUED
- [CLOSED 07-24] Storm gate: failed — scanner only. Anti-FLB harvest: dead
  (−21.7%/bet net; bias real at slope 0.87 but toll bigger). 2026 center is
  OVERCONFIDENT (reversed from 2021-25 lit). ALL tape roads → the maker.
- Prediction-market: TRUE tail calibration (gamma pagination blocks <$100k vol —
  needs per-day fetch); insider redo on OLDEST-first trades; wallet-follow
  (Desk shadow-book accruing, maker-noise filtered).
- THE DESK (moneymaker3000): arb-sim 30min / maker-sim + shadow 2x daily —
  verdicts: arb+maker ~2wks, shadow ~6-8wks.
- Forecast-vintage collector (NOAA) — the weather-error moat.
- Sept: WRDS/IBES announcement-dated earnings (the family falsified only for timing).
- The Jan–Jul 2026 prediction-market betting backtest (building on methodology research).

---
*Update this file when a cycle resolves. It is the model's memory and the operator's
manual. Honesty of this document = value of everything downstream.*
