# Deep research 2: per-family effect sizes & combination craft (verified)

*100 agents; 3-vote verification. Summary:*

The verified evidence gives a quantitatively grim but actionable answer for a solo large-cap US researcher: published anomaly premia must be haircut roughly 50-65% for post-publication arbitrage decay, and that decay is concentrated precisely in large, liquid, low-idiosyncratic-risk stocks — the S&P 500 universe is where the quant industry has most thoroughly eroded published signals, and the US is the only market where this decay reliably occurs. Most published cross-sectional families simply fail in large-cap-tilted (value-weighted, NYSE-breakpoint) tests — 64% at t>1.96 and 85% at t>3 — and classic single-quarter PEAD/SUE is essentially dead in large caps since ~2006, with costs consuming the paper profits in liquid stocks. The best-documented large-cap survivors are gross profitability (26 bp/mo in the largest quintile, incremental to book-to-market) combined with value: because the two are ~-0.58 correlated, a simple rank-average inside the 500 largest stocks earned 0.62%/mo with Sharpe 0.74 and only one-third annual turnover in-sample (1963-2010) — a concrete, replicable template for the researcher's XBRL fundamentals, though a realistic post-decay expectation is roughly half that. The most promising modern earnings signal is not last-quarter SUE but ML (elastic net) over 12 quarters of SUE history, which nearly doubles Sharpe (0.34 to 0.63) with gains strongest in large caps — directly buildable from EDGAR filed-date SUE plus Finnhub estimates (analyst-based surprises produce larger drift than time-series ones, and combining both is stronger still). Notably, the surviving evidence covers the effect-size and decay questions well but leaves the practitioner-craft questions (production IC ranges, Grinold-Kahn transfer coefficients, WorldQuant alpha statistics, weekly-horizon net results, short interest, insider Form 4) unverified — those remain open.

## Verified findings

### Published anomaly effect sizes decay substantially once public: returns are ~26% lower out-of-sample (74% persists in th...
Published anomaly effect sizes decay substantially once public: returns are ~26% lower out-of-sample (74% persists in the first ~3 post-sample years) and 58-65% lower post-publication in the US, with decay far from the original sample averaging ~50%; the decay is attributed to arbitrage capital (real changes in expected returns), not statistical bias, and the US is the only one of 39 markets showing reliable post-publication decline. A solo US researcher should therefore haircut any published per-family premium by roughly one-half to two-thirds.

**Confidence:** high | **Vote:** 3-0 across seven merged claims (0, 2, 14, 15, 16, 22, 23)

**Evidence:** McLean-Pontiff (97 predictors, JF 2016): 26% lower OOS, 58% lower post-publication; continuous Fama-MacBeth form retains 78% pre-publication (t=-1.40, insignificant) vs 51% post-publication (t=-4.91). Jacobs-Muller (241 anomalies, 39 markets, >2M anomaly country-months): 36% post-sample and 60% (EW) / 65% (VW) post-publication decline, US-only, with increased post-publication arbitrage trading in the US but not abroad. Chen-Zimmermann: ~50% decay far from sample, attributed to real expected-return changes since publication bias would appear immediately at sample end. All figures verified verbatim against primary texts.

**Sources:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623 (McLean & Pontiff, JF 2016); https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301618 (Jacobs & Muller, JFE 2020); https://arxiv.org/pdf/2209.13623 (Chen & Zimmermann, publication-bias meta-review 2023)

### The decay is concentrated exactly where this researcher operates: post-publication decline is greatest for anomalies hel...
The decay is concentrated exactly where this researcher operates: post-publication decline is greatest for anomalies held in large-cap, high-dollar-volume, low-idiosyncratic-risk, dividend-paying stocks, and the value-weighted (large-cap-tilted) decline (65%) exceeds the equal-weighted decline (60%). Published all-cap effect sizes therefore overstate what survives in an S&P-500-only universe, and the standard 58% haircut is a lower bound for large caps.

**Confidence:** high | **Vote:** 3-0 (claims 1, 14 merged)

**Evidence:** McLean-Pontiff Table 7: size, dollar volume, idiosyncratic risk, and dividend status each individually predict larger decay (in multivariate Table 8, idiosyncratic risk is the surviving driver — but S&P 500 stocks sit at the high-decay end under either attribution). Jacobs-Muller: VW post-publication coefficient -31.5 bp/mo (t=-2.82) against a 48.5 bp in-sample mean = 65% decline. Independently corroborated by Hou-Xue-Zhang showing most anomalies vanish outside microcaps even in-sample.

**Sources:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623 (McLean & Pontiff); https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301618 (Jacobs & Muller)

### Most published cross-sectional anomalies fail outright in large-cap-tilted tests: with NYSE breakpoints and value-weight...
Most published cross-sectional anomalies fail outright in large-cap-tilted tests: with NYSE breakpoints and value-weighting, 64% of 447 anomalies (including 93% of liquidity/friction variables) are insignificant at 5%, rising to 85% at the Harvey-Liu-Zhu t>=3 multiple-testing hurdle; even the surviving families most relevant to this stack (SUE earnings momentum, analyst forecast revisions, accruals, asset growth) replicate at substantially smaller magnitudes than originally published. The gap is driven by microcaps (~60% of listed names but ~3% of market cap) whose profits are largely untradeable.

**Confidence:** high | **Vote:** 3-0 (claims 17, 18, 19, 20 merged)

**Evidence:** Abstract and text verified verbatim: 286/447 (64%) insignificant with microcaps controlled; 95/102 liquidity variables fail; t>=3 raises failures to 380 (85%); 'even for significant anomalies, their magnitudes are often much lower than originally reported,' explicitly naming Sloan accruals, CJL SUE/revisions earnings momentum, and Cooper-Gulen-Schill asset growth. Counter-literature (Jensen-Kelly-Pedersen JF 2023) disputes the p-hacking interpretation but not the statistics or the microcap facts.

**Sources:** https://www.nber.org/system/files/working_papers/w23394/w23394.pdf (Hou, Xue, Zhang, 'Replicating Anomalies', RFS 2020)

### Publication bias per se is small — bias-corrected shrinkage is only 10-15% of in-sample mean returns with false discover...
Publication bias per se is small — bias-corrected shrinkage is only 10-15% of in-sample mean returns with false discovery rate under 10% across three meta-studies — so published anomalies are mostly real discoveries that were subsequently arbitraged away, not artifacts. Separately, meta-studies document t-stat hurdles above 3.0 from multiple-testing algorithms and 30-50% weaker returns in alternative (value-weighted/liquid) implementations, though Chen-Zimmermann themselves argue t~2.3 suffices for FDR=5% and the 30-50% haircut is a liquidity effect, not bias.

**Confidence:** medium | **Vote:** 3-0 on claim 21 (verifier medium), 2-1 on claim 24

**Evidence:** Quotes verified verbatim; Section 4.3/Figure 10 shows value-weighting cuts mean returns ~35% and a NYSE-20th-percentile size screen ~25% across 207 predictors. Practical reading for this researcher: trust the SIGN of well-replicated published families, apply the arbitrage-decay haircut (finding 1) rather than a bias haircut, and demand t>=3-ish evidence before allocating — noting the threshold itself is contested (2.3-4.0 range across authors). Do not conflate the 10-15% bias shrinkage with the separate ~50-65% post-publication decay.

**Sources:** https://arxiv.org/pdf/2209.13623 (Chen & Zimmermann 2023, citing Harvey et al. 2016, Chen-Zimmermann 2020, Jensen et al. 2022)

### Gross profitability (Novy-Marx) is the best-documented factor that survives specifically in large caps: full-universe VW...
Gross profitability (Novy-Marx) is the best-documented factor that survives specifically in large caps: full-universe VW quintile spread 0.31%/mo (t=2.49) with FF3 alpha 0.52%/mo (t=4.49); within the largest size quintile (~Fortune 500, <350 stocks, ~75% of market cap) the spread is 26 bp/mo (t=1.88), exceeding the large-cap value spread of 14 bp/mo (t=0.95), and its incremental power beyond book-to-market is essentially undiminished by size. Buildable directly from XBRL fundamentals (gross profits / total assets).

**Confidence:** high | **Vote:** 3-0 (claims 3, 4 merged)

**Evidence:** All numbers verified verbatim against the primary PDF (NYSE breaks, ex-financials, VW). Caveats carried: large-cap t=1.88 is below 1.96 standalone; sample ends 2010 and is in-sample, so the finding-1 decay haircut applies (published 2013, so ~12 years of post-publication erosion) — a realistic modern large-cap expectation is perhaps 10-15 bp/mo standalone.

**Sources:** https://mysimon.rochester.edu/novy-marx/research/OSoV.pdf (Novy-Marx, JFE 2013, sample 1963-2010)

### Combining negatively correlated signals delivers documented, large Sharpe gains in large caps — the clearest verified em...
Combining negatively correlated signals delivers documented, large Sharpe gains in large caps — the clearest verified empirics on combination in this evidence set: profitability and value correlate -0.57 (all-cap) / -0.58 (large-cap), so a 50/50 mix roughly doubles return at unchanged risk (all-cap Sharpe 0.85 vs 0.27/0.14 standalone large-cap legs combining to 0.44). A simple rank-average (sum of profitability rank + B/M rank) inside the 500 largest non-financial stocks, long top 150 / short bottom 150, rebalanced annually, earned 0.62%/mo with Sharpe 0.74 and only one-third of each side turning over per year — a net-of-cost-plausible large-cap-only template.

**Confidence:** high | **Vote:** 3-0 (claims 5, 6 merged)

**Evidence:** All statistics verified verbatim. This is the concrete answer to the combination question that survived verification: rank-averaging two weakly/negatively correlated families works, and the gain comes almost entirely from the correlation structure, not the standalone strength (the individual large-cap legs are statistically weak at t=1.88 and t=0.95 — the combination carries the significance). Caveats: in-sample 1963-2010 gross returns; the 'doubled return' holds per unit of risk, with double the gross book of either leg; value performed poorly 2010-2020.

**Sources:** https://mysimon.rochester.edu/novy-marx/research/OSoV.pdf (Novy-Marx, JFE 2013)

### Classic single-quarter PEAD is effectively dead in large caps: the historical 4%/quarter (~18% annualized) Bernard-Thoma...
Classic single-quarter PEAD is effectively dead in large caps: the historical 4%/quarter (~18% annualized) Bernard-Thomas hedge return has declined markedly post-2000, drift strength is inversely related to firm size, transaction costs consume most or all profits in liquid stocks (SUE long-short earns ~0.04%/mo VW in the most liquid quintile vs ~2.4%/mo in the least liquid), and Martineau (2021) finds PEAD essentially zero in large caps since ~2006. Signal-construction recipe that still matters: analyst-forecast-based SUE (IBES/Finnhub-style) produces larger drift than time-series SUE, and a two-way sort combining both surprise definitions is stronger than either — though the LEVEL on a modern S&P 500 universe is likely near zero.

**Confidence:** high | **Vote:** 3-0 (claims 7, 8, 9, 10 merged)

**Evidence:** Peer-reviewed review article quotes verified verbatim; verifiers independently corroborated Martineau (drift near zero in non-microcaps since ~2001-2006, price discovery moved to announcement day) and Chordia et al. (costs consume 63-100% of paper profits). Implication for the stack: do not expect standalone IC from last-quarter SUE on the S&P 500; use the surprise definitions as inputs to richer constructions (finding 8).

**Sources:** https://www.sciencedirect.com/science/article/pii/S2214635020303750 (Fink, PEAD review, JBEF 2021); https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607 (Martineau, 'Rest in Peace PEAD', CFR 2021, verifier corroboration); Chordia et al. 2009/2014; Livnat & Mendenhall 2006 (via review, verifier-corroborated)

### The most promising modern earnings signal for large caps is ML over the full SUE history rather than the last surprise: ...
The most promising modern earnings signal for large caps is ML over the full SUE history rather than the last surprise: elastic net models using 12 quarters of SUE lags nearly double the strategy Sharpe (0.34 to 0.63, +0.4%/mo alpha, surviving controls for one-quarter SUE and streaks), and the incremental gains are strongest among large-cap stocks precisely because the most recent surprise is priced in quickly there. Directly buildable from EDGAR filed-date SUE histories plus Finnhub estimates.

**Confidence:** medium | **Vote:** 3-0 (claims 11, 12, 13 merged; one verifier medium)

**Evidence:** Abstract statistics verified via multiple retrievals. Confidence capped at medium because this is a single unreplicated 2025 paper in a short-format letters journal, results are almost certainly gross of transaction costs, full-text size-subsample tables were paywalled (so read 'strongest in large caps' as incremental gain, not absolute signal level), and no post-publication decay has yet occurred — but it will.

**Sources:** https://www.sciencedirect.com/science/article/abs/pii/S1544612325020057 (Kaczmarek & Zaremba, Finance Research Letters 2025)

### Synthesis for the action plan: the three data families to build first, ranked by verified large-cap evidence, are (1) XB...
Synthesis for the action plan: the three data families to build first, ranked by verified large-cap evidence, are (1) XBRL gross profitability rank-combined with book-to-market value (strongest verified large-cap survivor; in-sample combined Sharpe 0.44-0.74, realistically ~half that after the 50-65% decay haircut), (2) historical-SUE ML features (12-quarter elastic-net-style lags from EDGAR filed dates — the only earnings-based construction with verified large-cap-specific incremental evidence), and (3) analyst-forecast-based surprise/revisions from Finnhub combined with time-series SUE in a two-way construction (verified to dominate either alone, though level is decayed). Every published effect size should be multiplied by roughly 0.35-0.5 for a modern large-cap implementation, and the combination arithmetic — not any single family — is where the achievable IC gain lives.

**Confidence:** medium | **Vote:** Derived synthesis across all 25 verified claims (not independently voted)

**Evidence:** This ranking uses only families with verified large-cap-specific evidence. The verified record supports a sober IC ceiling: with the researcher's current honest IC of 0.0125 and each well-built additional weakly-correlated family plausibly contributing a post-decay standalone IC of order 0.005-0.01 on large caps (inferred from the haircut arithmetic applied to the verified premia, not directly measured — no verified claim reports production IC levels), a combined honest IC in the 0.02-0.03 range appears attainable; claims about 0.04-0.05 production ICs did not survive verification and remain unconfirmed.

**Sources:** All primary sources above (McLean-Pontiff; Jacobs-Muller; Hou-Xue-Zhang; Novy-Marx; Chen-Zimmermann; Fink review; Kaczmarek-Zaremba)

## Caveats

Coverage caveat (most important): only sub-questions (1) partially and the decay/replication literature comprehensively survived the 3-vote verification. The surviving claims contain NO verified evidence on: production IC ranges at AQR/WorldQuant/Two Sigma, Grinold-Kahn fundamental-law/transfer-coefficient empirics, AQR Craftsmanship Alpha implementation increments, WorldQuant 101 Alphas statistics, Lopez de Prado deflated-Sharpe thresholds, weekly-horizon strategy results, short interest, insider Form 4, or net share issuance effect sizes. Statements about those topics in the final report must be flagged as unverified or researched separately. Evidence-quality caveats: Novy-Marx numbers are in-sample 1963-2010, gross of costs, with statistically weak standalone large-cap legs (t=1.88, t=0.95) — the combination result carries the significance, and value's poor 2010-2020 decade postdates the sample. The Kaczmarek-Zaremba ML-PEAD paper is a single unreplicated 2025 letters-journal result, gross of costs. Jacobs-Muller's 60-65% decline estimates carry the authors' own qualifier that a general time trend partly explains them (though post-publication dummies survive time-trend controls). The Harvey-Liu-Zhu t>=3 threshold is contested (Chen-Zimmermann argue t~2.3 suffices; Chordia et al. propose 4.0). Some McLean-Pontiff figures cited are from the working-paper draft (82 characteristics, ~35% decay) vs the published JF version (97 predictors, 26%/58%) — the published figures should be treated as canonical. Time-sensitivity: all decay estimates compound — a factor published in 2013 has had 12+ years of arbitrage erosion, so even 'post-publication' academic estimates from mid-2010s samples may overstate 2026 premia.

## Open questions

- What honest IC do real production large-cap signals achieve at established quant firms — is the hypothesized 0.02-0.05 range documented anywhere citable (Grinold-Kahn, Qian-Hua-Sorensen, AQR publications), and what transfer coefficients do they realize after constraints and costs?
- Does anything work at a WEEKLY horizon on large caps net of costs — industry-relative short-term reversal, news momentum, or weekly earnings drift — with published gross AND net numbers? No claim on this survived verification.
- What are the verified large-cap effect sizes for the untested data families in this stack — FINRA short interest (days-to-cover), insider Form 4 net buying, and net share issuance/buybacks — and how much did each decay post-publication?
- Does the Kaczmarek-Zaremba historical-SUE elastic-net result replicate on an independent implementation (e.g., the researcher's own EDGAR-based PIT SUE panel), and does it survive realistic S&P 500 transaction costs at its implied turnover?
