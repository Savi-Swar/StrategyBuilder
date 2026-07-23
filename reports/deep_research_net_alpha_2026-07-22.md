# Deep research: from IC 0.017 / net Sharpe 0 to net-of-cost performance
*2026-07-22. 104-agent research run: 22 sources, 102 claims extracted, 25 verified by 3-vote adversarial panels → 20 confirmed, 5 refuted. Confidence labels per finding.*

## Diagnosis (high confidence — top-journal sources, unanimous votes)

1. **Quark's outcome is the textbook outcome, not a Quark bug.** ML equity alpha
   concentrates in hard-to-arbitrage stocks (microcaps, distressed, high-vol states).
   Liquid S&P 500 large caps are structurally the low-gross-alpha segment:
   excluding microcaps kills most of it (Avramov-Cheng-Metzker, Mgmt Sci 2023);
   96% of trading-friction anomalies fail |t|=1.96 with NYSE breakpoints +
   value weighting (Hou-Xue-Zhang, RFS 2020).
2. **The cost-agnostic two-step workflow (predict gross returns → form portfolios)
   generically fails net of costs** — training loads on fleeting reversal-type
   features, turnover eats the spread (Jensen-Kelly-Malamud-Pedersen, RFS).
   Canonical example: momentum 0.64%/mo gross, 63bps/mo cost, 0.01%/mo net.
   Quark's 68x/yr turnover vs 16bps/wk spread is a direct instance.

## The remedy, ranked by verified effect size

**The surprise: cost-awareness in CONSTRUCTION, not new data, is the documented lever.**

1. **Garleanu-Pedersen partial rebalancing (JF 2013).** Trade partially toward an
   "aim portfolio"; weight persistent (slow-decay) signals more. ~+20% net Sharpe
   vs best static policy. Closed form under quadratic costs; under proportional
   costs → no-trade bands. [3-0 x3, verified against author PDF]
2. **TCA factors (Baldi-Lanfranchi 2024 WP).** Factor-specific optimal rebalance
   speed → net max squared Sharpe up to 2.5x; momentum costs 63→30bps/mo,
   +0.19 net Sharpe, same signal. [3-0; unrefereed magnitudes]
3. **Cost term inside the training objective.** TC-penalized conditional
   autoencoder: OOS R² 0.03%→0.27% ex-microcaps (Jo-Kim-Shin 2025 WP).
   Full Portfolio-ML (learn weights directly under cost-aware objective):
   ~+20% net Sharpe over even a cost-aware two-stage (JKMP, RFS). [3-0 x6]
4. **WARNING — ex-post overlays mostly don't work on ML signals.**
   Azevedo-Hoegner-Velikov: holding-period extension to 2 months was the ONLY
   overlay improving net performance across all 9 ML strategies tested, and only
   +5bps. Buy/hold bands, quintiles, size filters: turnover falls, gross falls
   with it. Implication: Quark's no-trade-band study (0.13→0.18) is directionally
   consistent but bands alone won't reach the target; the cost logic must enter
   the objective/rebalancing rule. [3-0, single strong source → medium]

## Realistic ceiling (medium confidence, single source AHV)

Post-2005 liquid US equities, monthly ML combinations of 320 published anomalies:
OOS monthly R² 0.05–0.76%; gross VW decile Sharpe 0.32–1.11; costs 19–26bps/mo
at 120–140% monthly turnover (HF effective spreads, value-weighted); only best
sequence models (LSTM) survive net: 1.42%/mo (t=3.99).
**Net Sharpe ~1 is roughly the documented frontier. IC 0.04+/net Sharpe >1 on
S&P-500-only is AT or BEYOND anything published.** Live scholarly dispute:
Avramov et al. say costs kill ML strategies; AHV say good spread estimates
rescue the best ones. Truth depends on execution quality.

## Refuted in verification (do NOT rely on these)

- "Value/quality features become top-importance under cost-aware training →
  fundamentals are the highest-value data add" — REFUTED 0-3.
- AQR "real-world costs are many times smaller than academic estimates" — 1-2.
- AQR "size/value/momentum survive costs at very large scale" — 0-3.
- "Short-term reversal can't be rescued by optimization" — 0-3.
- "Cost-adjusted model Sharpe 1.071 vs 0.758 ex-microcaps" — 0-3.

## Open questions (research needed — we generate our own evidence)

1. Incremental IC per data family (fundamentals, IBES revisions, short interest,
   NLP) — NO claim survived verification. Unverified leads from fetch stage worth
   testing in-house once WRDS clears: PEAD (rank-SUE coeff 0.070, t=7.16,
   1983-2001), post-announcement analyst revisions (3.43% 90-day CAR spread vs
   2.18% for SUE, 1995-2019), short-interest surprise (SUSIR, JFM 2023),
   earnings-call NLP (IC ~0.017 standalone, S&P Global 2018).
2. Can GP-style rebalancing alone lift a 16bps/wk gross spread to net Sharpe ~1,
   or is new data strictly necessary? (Both levers likely needed.)
3. Does Quark's t=3.35 deflate under proper trial counting? (Trial registry
   exists; apply DSR to the xsec family.)

## Prioritized action plan for Quark

| # | Intervention | Documented gain | Effort | Data needed |
|---|---|---|---|---|
| 1 | GP-style partial rebalancing toward aim portfolio (tune speed τ OOS); slow-signal tilt | ~halve costs, +~0.2 net Sharpe | days | none (have it) |
| 2 | Retarget to longer horizon / slower components (2-mo class; Quark's own 3M IC 0.0291 > 1W 0.0172) | +5bps (only overlay that survives) + slower decay | days | none |
| 3 | Cost term in training loss (TC-penalized objective), then Portfolio-ML-style direct weight learning | R² 0.03→0.27% ex-microcaps; +20% net Sharpe | weeks | none |
| 4 | New data families via WRDS: IBES revisions, PEAD, short interest, fundamentals | unquantified (open question) — test in-house | weeks | WRDS |
| 5 | Recalibrate target: net Sharpe 0.5–0.8 on S&P-only would already be publication-grade | honesty | — | — |

*Full verification transcript: task output wkpy1he1v; journal at subagents/workflows/wf_a00ff121-685.*
