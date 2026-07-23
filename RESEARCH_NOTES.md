# Research notes

Chronological record of decisions, findings and negative results. The point
of this file: every number in the README has a paper trail, and every choice
that could have been a degree of freedom is written down.

## Data quality findings (2026-07)

- **CL=F negative-price episode**: close of −$37.63 on 2020-04-20. A raw
  `pct_change` through zero produces sign-flipped garbage (−306%, then −127%
  the next day). Policy: spike/nonpositive prints are NaN'd (both return legs
  die) by `quark.data.quality.clean_panel` and documented here. We do not
  clip silently.
- **Holiday-NaN bug (caught mid-project, worth remembering)**: on a
  business-day calendar, US market holidays are all-NaN rows. With
  `min_periods = horizon`, any forward-return window containing a holiday was
  silently NaN — ~10% of 5-day windows and ~90% of 21-day windows discarded.
  Diagnosed because factor-IC sample counts collapsed (n=44 months where ~190
  expected). Fix: tolerate ≤2 missing bars inside the window (a closed market
  contributes zero return; the move lands in the next bar), and mask targets
  where the instrument itself did not trade. Lesson: **count your samples,
  not just your means.**
- Yahoo FX data has a shared gap Aug 2008 (11–17 business days across
  several pairs) — vendor artifact, left as NaN.
- **CNH=X removed from the universe**: Yahoo carries 1 observation.
- Equity panel: 341 stale runs (≥5 identical closes) across 503 names —
  mostly low-vol names at coarse price grids; left alone, flagged.
- The multi-asset DB previously stored prices adjusted as-of-2025 fetch
  dates. Refresh policy is full per-ticker replace to avoid mixed-vintage
  adjusted closes.

## Study 1 — multi-asset time series

(Numbers below updated 2026-07-15 to the committed post-audit artifacts —
the original 43-instrument run was superseded when the universe grew to 82
instruments (78 headline after excluding the 4 hindsight-picked mega-caps)
and the cross-gap returns fix landed; earlier vintages of this section
quoted tsmom_252/DSR 0.29/AUC 0.513/Sharpe −0.71 from the smaller universe.)

- 8 classic variants registered (3 tsmom lookbacks, 2 MA crosses, RSI
  reversion, MACD, Bollinger reversion). **Net of costs, none survive**:
  best is ma_cross_50_200 (net Sharpe 0.13 on the full window), and its
  **DSR is 0.193 with N=8 trials** — consistent with selecting the luckiest
  of 8 skill-less variants (reports/baselines.csv).
- Turnover of vol-targeted tsmom (~29x gross/yr per-instrument sum) is
  dominated by daily vol rescaling, not signal flips. Position buffering
  would cut it — future work, noted not implemented.
- **ML timing model: honest failure.** Pooled HGB classifier, purged
  walk-forward, annual folds: mean AUC 0.518, shuffled control ≈ 0.5.
  After causal signal calibration and costs: net Sharpe −0.44 on the
  model's own OOS window (−0.455 in the common-window comparison table —
  same failure, two windows), DSR ≈ 0. Conclusion: daily-horizon timing
  with standard price features does not clear ~2–10 bps costs on this
  universe. We report it and move on.
- Design decision: classifier probabilities cluster near 0.5, so raw 2p−1
  signals run far below the vol target while paying full turnover. Fixed by
  dividing each instrument's forecast by its *trailing* forecast std
  (252d, causal). One a-priori choice, not tuned.

## Study 2 — cross-sectional long-short equity (flagship)

- Universe: current S&P 500 members (503), eligibility per rebalance date:
  price > $5, 63d median dollar volume > $5M, ≥252 obs. **Survivorship bias
  is real and inflates the long side** — treat all results as upper bounds.
  Building a point-in-time universe from the Wikipedia constituent-change
  table is the top item in future work.
- Features: per-date cross-sectional ranks of momentum (5/21/63/126/252d,
  vol-normalized), vol ratios, RSI, 52w-high distance + calendar. Label:
  above/below cross-sectional median 5d forward return (relative, so the
  model predicts winners-vs-losers, not the market).
- **Trial accounting: exactly 2 configs run, both reported.**
  (h=5, weekly) was pre-declared primary; (h=21, monthly) secondary.
- Results (committed artifacts, post-returns-fix): weekly IC 0.0172
  (t=3.35, n=756 weekly obs; ~18% of adjacent forward windows overlap 1–2
  days on holiday weeks, but the IC series' lag-1 autocorrelation is −0.002
  so the Newey–West t is identical at 3.35) — genuine cross-sectional
  predictability. Decile spread near-monotonic, ~16 bps/week top-vs-bottom
  gross. Net economics modest: Sharpe 0.04 weekly (turnover eats the edge
  at 5 bps/side), 0.26 monthly. Shuffled control clean (AUC ≈ 0.5, IC ≈ 0,
  negative net Sharpe = pure costs).
- The spread is **long-side driven**: bottom deciles do not underperform the
  middle. Consistent with the post-2010 literature — shorting large caps on
  price signals doesn't pay.

## Vig top-3 selection review (2026-07-07)

The past-trades review surfaced that the top-3-by-|p−0.5| picks lost −117
bps/call (hit 37%) over the trailing 52 weeks, while the full decile book
stayed positive. Investigated on the full 156-week walk-forward record with
**four pre-declared selection rules, all reported, trial-counted**:

| Rule | avg bps/call | hit | t |
|---|---|---|---|
| Production: floating top-3 by \|p−0.5\| | −32.4 | 44.9% | −1.2 |
| A: fixed 2L+1S by prob | +27.8 | 51.5% | +0.99 |
| B: top-3 longs by prob | +9.1 | 48.7% | +0.34 |
| C: longs ranked 5–7 (off the tail) | +32.0 | 52.4% | +1.18 |
| D: random-3 in 90–97th pct band | +17.0 | 52.6% | +0.82 |

Five variants examined, all reported. The production rule was the outlier:
by ranking on |p−0.5| it let the short tail dominate selection (83 shorts vs
70 longs in the trailing year) — precisely the side the original backtest
showed carries no alpha. **Adopted: fixed 2 longs + 1 short.** Justification
is twofold and ordered: (1) the pre-registered long-side-driven finding from
Study 2, (2) a PAIRED comparison on the same 156 weeks: +60.2 bps/week
improvement, t=+2.06. Rules B–D are not separable from A and were not
adopted. The review page contextualizes any display window against the full
record automatically, so a single bad year can't drive rule churn again.

## Multi-horizon desk (2026-07-08)

The desk gained a horizon setting: 1D / 1W / 3M / 6M / 2Y, each a separately
retrained cross-sectional model (same features, label = beat-the-median over
h days; training labels always end h days before today, so causality holds
at every horizon). **Trial accounting: the four new horizons are four new
trials.** Each was walk-forward validated once (scripts/validate_horizons.py)
with purge scaled to the horizon and scoring at a non-overlapping cadence
(h/5 weeks); results live in reports/xsec_horizons.csv and are quoted next
to each horizon's picks in the UI. 1W remains the desk default: it has the
longest validation, the live ledger history, and the graded record. Live
predictions for ALL horizons are recorded daily (ledger `horizon` column),
so per-horizon live ICs accrue with time — long horizons will take months
to score their first entries, which the UI should treat as "unproven", not
"clean".

## Adversarial math audit (2026-07-08)

Two independent review passes re-derived every formula. Confirmed correct:
PSR/DSR (exact Bailey–LdP forms, Monte-Carlo verified), expected-max-Sharpe,
CAGR/Sharpe/max-DD, vol targeting, cost timing, engine causality,
forward-return alignment, positional purge arithmetic, Spearman IC,
%B/MACD/VWAP, VaR z and time-scaling, blend-search vol targeting.

Found and fixed (all with regression tests):
1. **CRITICAL — cross-gap return deletion.** `pct_change(fill_method=None)`
   NaN'd the bar AFTER every gap, deleting each post-holiday move from
   labels AND backtest PnL (~9/instrument/yr, biases toward zero). Fixed:
   returns = ffilled-denominator pct_change masked to observed bars. All
   headline numbers recomputed under the fix.
2. Sortino used std of negative returns about their own mean; now standard
   target downside deviation (MAR=0, all obs).
3. `ann_turnover`/`cost_drag_ann` were per-instrument sums next to
   portfolio-unit stats (~n_alive x overstated); now divided consistently.
4. Half-Kelly growth mislabeled as S²/4; correct is 3S²/8 (2.5%/yr at
   S=0.26); full Kelly S²/2 (3.4%/yr).
5. "Compounding weekly" label on an arithmetic cumsum; relabeled.
6. Horizon-validation cadences were calendar weeks (~4.83 td): 2Y windows
   overlapped 100% (~19 td). Cadences re-sized (14/28/110 wks), re-run.
7. Missing-sleeve history in the portfolio replay was implicit 0%-return
   cash (aggressive was ~97% invested pre-2014); weights now renormalize
   over available sleeves, sleeves enter at inception; drawdowns now see a
   decline that starts on day one (baseline-1.0 peak).
8. Golden-cross NaN counted as bearish for short-history names; now skipped.
9. RSI labeled as Cutler's variant (differs from Wilder's by up to ~20 pts);
   flat-window RSI now 50, not 100. Missing cost rates now raise instead of
   trading free. Ledger logs unscoreable (delisted) names per scoring date —
   the backfilled IC history is survivorship-tilted and should be read as an
   upper bound (current-members universe; see Study 2 caveat).

## Turnover study — no-trade bands (2026-07-15)

Turnover was the binding constraint on Study 2 (67.9x/yr, 340 bps/yr cost
drag at weekly re-formation). Hysteresis variants: ENTER unchanged (extreme
decile), EXIT only once the name's rank decays past a gap. **Trial
accounting: 3 exit gaps (0.15 / 0.20 / 0.30) pre-registered before results;
all reported; nothing else tried.** All variants score the SAME stored
walk-forward predictions (one model fit), so differences are the weight
rule, not refit noise. Script: `scripts/run_turnover_study.py` →
`reports/turnover_study.csv`.

| variant | net Sharpe | ann turnover | cost drag | avg names |
|---|---|---|---|---|
| weekly re-formation (base) | 0.04 | 67.9x | 340 bps/yr | 93 |
| band, exit gap 0.15 | 0.13 | 47.1x | 236 bps/yr | 124 |
| band, exit gap 0.20 | 0.17 | 42.5x | 212 bps/yr | 134 |
| band, exit gap 0.30 | 0.18 | 34.6x | 173 bps/yr | 157 |

(Turnover/cost figures are annualized over the OOS window the strategy
actually trades in — an earlier vintage divided by the full 2005+ panel
length, understating both by ~1.48x; audit-found, fixed.)

Read: monotone improvement with band width — cost saved exceeds signal
staleness cost throughout the registered range, and max drawdown falls too
(−23% → −18%). The widest band converges toward the monthly-rebalance result
(Sharpe 0.26) by a different mechanism (hold longer vs trade less often).
Honest caveats: (1) still thin economics on a survivorship-biased universe —
a turnover result, not an alpha result; (2) the registration is not
git-verifiable — the gap list and the results entered the repo in the same
commit, so it rests on the author's word; treat the MONOTONE PATTERN across
all three gaps (0.13 / 0.17 / 0.18), not the best single number, as the
evidence. Quoting only the 0.18 would be selecting the max of 3 trials.

## Point-in-time universe — best-effort reconstruction (2026-07-15)

Built from Wikipedia's constituent-changes table walked backward from
today's 503 members (`scripts/build_pit_universe.py` →
`reports/pit_membership.csv`: month-end snapshots 2005+, 845 ever-member
names). Two stated gaps, direction of bias known:

1. Wikipedia's table is titled *"Selected changes"* — near-complete
   recently, sparser before ~2010 (407 events since 1976 vs a true rate of
   ~25/yr). Missing events leave the backward walk wrong for those names.
   Cross-check: after the rename clip (gap 3 below), reconstructed
   membership counts sit in [452, 504] — the early-year shortfall (~454 in
   2005 vs the true ~500) is renamed members' earlier stints lost under old
   symbols. Under-inclusion is the SAFE direction: a missing true member
   shrinks the panel; a falsely-included survivor (the pre-clip failure
   mode, e.g. META "in the index" 2005) manufactures survivorship alpha.
2. Yahoo drops most delisted tickers: recovery of ever-member names absent
   from the DB was **153/342 (45%)** (`reports/pit_recovery_report.csv`).
   The unrecovered 189 skew toward the worst outcomes (bankruptcy,
   distressed acquisition) — exactly the names survivorship bias deletes —
   so even the PIT run remains optimistic. It bounds the bias; it does not
   eliminate it.
3. Ticker renames (audit-found): the changes table records events under
   historical symbols, so a rename like FB→META produces no event under the
   current symbol and the backward walk kept META "in the index" back to
   2005 — a survivor eligible before it existed. Defense: any current
   symbol the changes table never touches is clipped at its "Date added"
   from the members table. Cost of the defense: a leave-and-rejoin name
   with no recorded events loses its earlier stint (over-conservative).
   Ticker reuse across different companies (e.g. CEG 2005/2022) is
   self-limiting — the old company has no Yahoo data, so it can't become
   eligible.
4. Engine delisting convention: a held name whose price series ends earns
   exactly zero afterward and pays a normal exit cost at the next
   rebalance. Real delistings pay the terminal move (often ≈−100% for
   longs, a gain for shorts). This adds optimism to the PIT run on top of
   the recovery gap; both push the same direction — the measured bias is a
   floor.
5. Month-end snapshot granularity: a name removed on the 3rd stays
   "a member" until the next month-end (and additions enter late). Removals
   correlate with distress, so this too is mildly optimistic.

Comparison run (`scripts/run_pit_study.py`, identical pipeline, membership
mask ANDed into eligibility; results in `reports/pit_study.csv`):

| | IC | IC t | D10−D1 gross | net Sharpe (weekly) | names/wk |
|---|---|---|---|---|---|
| current members (shipped) | +0.0164 | 3.19 | 16 bps | +0.04 | 471 |
| point-in-time (best-effort) | +0.0127 | 2.38 | 10 bps | −0.19 | 438 |

(Vintage note: the current-members baseline here — IC +0.0164, t=3.19,
n=757 — differs slightly from the headline +0.0172/t=3.35/n=756 because the
DB gained a week of data between runs; same code, same config. Deltas
between rows of the same run are the meaningful comparison.)

**Read: the signal survives point-in-time treatment — the bias does not.**
Cross-sectional predictability remains statistically real (t=2.38 on 757
weeks) but ~23% weaker, the decile spread drops ~40%,
and the weekly-rebalance net economics go negative: survivorship was
carrying them. The honest claim after this study is "genuine but modest
cross-sectional predictive power; net profitability requires the turnover
discipline above AND is still overstated by residual survivorship in the
45%-recovered PIT panel." Headline IC in the README keeps the shipped
config for continuity with the live ledger, with this study linked as the
bias measurement.

## Future work (ordered by expected value)

1. Ratio-back-adjusted continuous futures for Study 1.
2. Meta-labeling: use the Study 2 model to size a momentum base signal
   instead of generating positions directly.
3. Revive the legacy cointegration pairs idea inside the tested engine
   (needs two-leg position semantics).
4. A true PIT universe (CRSP/Norgate) if this ever gets a data budget —
   the free reconstruction above is at its ceiling.

## 2026-07-22 — Cycles 1-2: Garleanu-Pedersen partial rebalancing, PIT-gated

Motivated by a verified literature review (reports/deep_research_net_alpha_
2026-07-22.md): cost-aware construction — trading a fraction tau toward the
target book each rebalance instead of full re-formation — is the documented
net-of-cost lever (+~0.2 net Sharpe, GP 2013); ex-post band overlays alone
documented NOT to rescue ML signals. `partial_rebalance_weights()` added to
quark/ml/xsec.py.

**Cycle 1** (scripts/run_partial_rebal.py, current-members panel,
pre-registered tau grid, all reported):

| tau | 1.00 | 0.50 | 0.25 | 0.15 | 0.10 | 0.05 |
|---|---|---|---|---|---|---|
| net Sharpe | 0.06 | 0.23 | 0.37 | 0.45 | 0.48 | 0.50 |
| turnover x/yr | 68 | 36 | 18 | 11 | 7 | 3.4 |

Monotone in tau — mechanism real on this panel.

**Cycle 2** (scripts/run_cycle2_pit_partial.py, best-effort PIT panel,
656 recovered names, pre-registered: weekly taus {1, .25, .10, .05},
monthly h21 taus {1, .5, .25}):

| config | net Sharpe |
|---|---|
| weekly tau=1.00 | −0.13 |
| weekly tau=0.25 | **+0.10** (peak; hump-shaped, decays at slower tau) |
| weekly tau=0.05 | −0.03 |
| monthly h21, any tau | ~0.01, **IC −0.0000 (t=−0.00, n=188)** |

**Read:** (1) The GP lever delivers almost exactly the literature's promised
+0.2 Sharpe on the honest panel (−0.13 → +0.10) — but the honest starting
point is negative, so the ceiling is ~0.1, not cycle 1's 0.50. Survivorship
was carrying most of the cycle-1 miracle (consistent with the 2026-07-15 PIT
study). (2) The monthly h=21 signal is ENTIRELY survivorship on the PIT
panel: IC exactly ~0. The shipped monthly net Sharpe 0.26 should be read as
bias, not edge. (3) Slow tau dilutes a fast-decaying thin signal — the
tau optimum shifts from 0.05 (biased panel) to ~0.25 (honest panel), which
is itself evidence the persistent signal component is weaker than the
biased panel suggested. Conclusion: cost side is now optimized; the binding
constraint is GROSS signal on the honest universe (9.5 bps/wk spread).
Next lever must be new information: earnings-family features (PEAD,
revisions) via Finnhub now, IBES/Compustat when WRDS clears. Trial count
this session: 6 (cycle 1) + 7 (cycle 2), all reported here.

## 2026-07-22 — Cycle 3: EDGAR SUE/PEAD features — NEGATIVE result

Added sue_recent (Bernard-Thomas seasonal SUE, live 75 trading days) +
ann_age from EDGAR XBRL 10-Q/10-K vintages (quark/data/edgar.py; PIT-strict:
value first visible the trading day AFTER `filed`; leak unit-checked).
Coverage: 605/656 PIT names, 28.7k announcements, 71% of names live 2012+.
Pre-registered: weekly h5 PIT, taus {1.00, 0.25}. Result vs cycle-2 baseline:

| | IC | t | net Sharpe tau=1.00 | tau=0.25 |
|---|---|---|---|---|
| baseline (no earnings) | +0.0125 | 2.35 | −0.13 | +0.10 |
| + SUE/ann_age | +0.0107 | 2.14 | −0.25 | +0.03 |

**Read: the features SUBTRACT.** Best diagnosis (not yet tested): XBRL
`filed` dates are 10-Q/10-K submissions, typically 2–4 weeks AFTER the 8-K
press release that actually moves the price. PEAD's drift is front-loaded;
entering at the 10-Q date buys the stale tail while the price-momentum
features already encode the announcement jump — so the SUE columns add
noise, and HGB spends splits on them. Implication for the family, not the
thesis: announcement-date-precise surprise data (IBES via WRDS, which
carries announcement dates) remains the right test; XBRL-vintage SUE at
weekly horizon is the wrong instrument. Staleness-TOLERANT fundamental
families (value/profitability/asset growth/issuance — slow signals where a
3-week lag is immaterial) are unaffected by this failure mode and are the
next test (fundamentals prefetch running). Trials this cycle: 2, reported.

## 2026-07-23 — Cycle 4: EDGAR fundamental families (PIT panel)

Five slow families added as ranked features (quark/data/edgar.py
fundamental_feature_panels): value_bm, profit_roa, asset_growth,
net_issuance, accruals. Coverage 63-86% of names 2012+. Pre-registered:
ML arm taus {1.00, 0.25, 0.10} + Novy-Marx-style rank-combo reference arm.

| config | net Sharpe (cycle 2 same-tau baseline) |
|---|---|
| nm_rank_combo (value+profit, annual, no ML) | **−0.00** |
| fund tau=1.00 | −0.06 (−0.13) |
| fund tau=0.25 | +0.13 (+0.10) |
| fund tau=0.10 | **+0.19** (+0.07) |

Weekly IC dipped (0.0125 → 0.0105, t=2.22): fundamentals do NOT predict
next-week winners. But net Sharpe improved at EVERY tau and the tau-curve
now rises toward slower trading — the fundamentals strengthen the
PERSISTENT component of the composite signal, which is exactly what the
GP aim-portfolio math rewards (slow signals earn more weight in the EWMA
book). Weekly IC is the wrong metric for slow features; the economics are
the metric. Also instructive: the famous standalone value+profitability
rank combo (Novy-Marx OSoV, Sharpe 0.74 in-sample pre-2011) is DEAD on our
2012+ PIT large-cap panel (Sharpe −0.00) — consistent with McLean-Pontiff
decay being worst in large caps — yet the same information adds ~+0.1
Sharpe as features inside cost-aware ML construction. Published effect
sizes are epitaphs; combinations inside honest construction still pay.
Trials: 4, reported. PIT trajectory so far: −0.13 → +0.10 (GP) → +0.19
(GP + fundamentals).

## 2026-07-23 — Cycle 5: tau-curve peak + monthly revival (PIT, fundamentals)

Pre-registered follow-ups to cycle 4. (A) Weekly tau completion: 0.15→0.181,
0.05→0.161, 0.03→0.153 — peak confirmed at tau≈0.10 (0.192), and tau=0.05 no
longer collapses (price-only: −0.035; composite: +0.161): the fundamentals
made the signal genuinely more persistent, the interpretation test passed.
(B) Monthly h=21 revival: price-only PIT IC was EXACTLY 0.0000 (cycle 2);
with fundamentals IC +0.0120 (t=1.68, n=188), net Sharpe 0.177 (tau=1.00) /
0.211 (tau=0.50) — the monthly horizon's entire signal is attributable to
the fundamental families. Best honest configs now: monthly+fund tau=0.50
(0.21) and weekly+fund tau=0.10 (0.19). Trials: 5, reported. Predictions
cached to reports/preds_{weekly,monthly}_fund_pit.parquet.

## 2026-07-23 — Cycle 6: book blending (PIT, cached predictions)

Weekly(tau=0.10) and monthly(tau=0.50) book returns correlate only +0.39
OOS — partially independent information. Pre-registered trials (3):
blend_50_50 → 0.246; monthly_tau0.25 → 0.273; blend(wk 0.10 + mo 0.25) →
**0.276**, turnover 5.2x, cost drag 26bps. PIT trajectory: −0.13 → +0.10
(GP) → +0.19 (fundamentals) → +0.28 (two-horizon blend).

**Multiple-testing caveat (standing):** ~27 registered trials now touch
this panel family. The tau/blend grids are 1-D monotone structures (cost
mechanics, low mining risk) but "extend until it stops improving" is still
selection along a curve — quote the plateau (~0.2-0.28), never the single
max. The PRIMARY statistical claims remain the model-level ICs computed
once per configuration (weekly +0.0105 t=2.22; monthly +0.0120 t=1.68,
horizon-distinct), not any particular Sharpe cell. A final shipped config
must be chosen by walk-forward selection (choose tau/blend on data through
year Y, measure on Y+1) before any number is quoted externally — TODO.
Residual PIT optimism (45% delisted recovery) still applies to everything.

## 2026-07-23 — Cycle 7: SUE-history + gross profitability — NEGATIVE

Added 6 SUE-history panels (lags 1-4, mean4, mean12 — Kaczmarek-Zaremba-
style) + gp_assets (GrossProfit TTM/assets, 324/656 tickers = 38% coverage,
sector-biased: financials don't report GrossProfit). Result: everything
degraded vs cycle 5/6 baselines — weekly tau0.10 0.192→0.005; monthly IC
+0.0120(t=1.68)→+0.0053(t=0.83), tau0.25 0.273→0.082; blend 0.276→0.053.

**Design error acknowledged: two feature blocks changed at once — cannot
attribute.** Suspects: (a) gp_assets missingness is sector-correlated
noise; (b) SUE lag-1 panel reintroduces the cycle-3 stale-timing failure
x4 lags; (c) monthly model (188 obs) is most feature-count-sensitive.
Cycle 8 = pre-registered one-variable ablation on the monthly config:
(A) fundamentals+SUE-history only; (B) fundamentals+gp_assets only.
Recovery bar: monthly IC >= +0.0120. If neither recovers, cycle-6 config
stands as champion and both families are logged dead on this panel.
Trials: 4, reported.

## 2026-07-23 — Cycle 8: ablation verdict

Control (fund-only) reproduced cycle 5 exactly (IC +0.0120 t=1.68, 0.273)
— comparisons valid. SUE-history block is the cycle-7 killer (IC → +0.0076,
Sharpe → 0.096): XBRL-vintage SUE now falsified at BOTH horizons; family
suspended pending announcement-dated surprises (IBES/WRDS or 8-K parsing).
gp_assets mild drag (38% sector-biased coverage) — dropped. Champion
remains cycle-6 blend (0.276). Trials: 3, reported. Next: walk-forward
config selection (the standing honesty TODO) — all selection so far used
the full OOS window; the shipped number must come from configs chosen only
on trailing data.

## 2026-07-23 — Cycle 9: walk-forward config selection — THE HONEST NUMBER

Protocol: for each year Y in 2015-2026, pick the config (27 candidates:
weekly/monthly tau grids + all 50/50 blends) by net Sharpe on 2012..Y-1
only; apply to year Y; chain. Predictions were always walk-forward; this
closes the last selection leak (config choice).

**Walk-forward-selected 2015-2026: net Sharpe 0.05** (CAGR 0.1%, vol 3.3%,
maxDD -11%). In-sample-selected champion (b_w0.10_m0.25), same window:
0.29. The 0.28 "plateau" was ~80% config-selection bias.

Structure worth recording: from 2017 on, the selector stably picks m0.25
(the trailing-Sharpe ranking is not chaotic); the damage concentrates in
2015-2016 (short trailing windows chose configs that then cratered:
-0.36, -2.27) and in the wide year-to-year dispersion of realized Sharpe
(-1.0 to +1.7) — with 12 annual observations, se(Sharpe) ≈ 0.29, so 0.05
vs 0.29 is not even statistically distinguishable. That is the deepest
honest statement: **the economic edge of this system cannot be
distinguished from zero at this sample size, even though the predictive
signal is statistically real (IC t=2.2-2.4).** Thin real signals produce
exactly this signature. No post-hoc window slicing to rescue the number —
that would be the exact sin this protocol exists to catch.

Implication (consistent with verified fundamental-law math): config
polishing is exhausted; only additional independent signal families can
raise composite IC enough for the economics to clear the selection tax.
Families queued: announcement-dated earnings surprises + analyst revisions
(WRDS pending), FINRA short interest. Trials: measurement protocol, not a
search — champion unchanged.

## 2026-07-23 — Crypto branch, cycles 1-2: the LUNA artifact

New domain: Binance daily panel (414 coins, 2019+, current-listing bias
documented up front). Cycle 1 (pre-registered h=7 weekly xsec, $10M screen,
10bps, taus {1,.25,.10}): IC +0.0165 (t=1.52, n=341) but ann_vol ~300 —
GARBAGE. Postmortem: Binance reused the LUNA ticker post-Terra-collapse;
compute_returns' gap-bridging (correct for equity holidays) glued old-LUNA
$0.0001 to LUNA2 $8.87 across a 2-week delisting gap = +17,739,900% in one
untradeable bar inside the backtest. Real tails (DOGE +392% Jan-2021)
verified as genuine and KEPT. Cleaning rule (from the diagnostic, not tuned
on results): 24/7 market ⇒ any >3-day gap = halt/redenomination ⇒ break
series, keep latest contiguous segment; drop 14 stablecoins/fiat proxies.
Cycle 2 = identical configs on cleaned panel. Lesson filed under "most of
the real work is data": the engine was fine; the CALENDAR ASSUMPTION
(gaps = holidays) was an equity convention that became a bug in a 24/7
market. Domain expansion means auditing every convention, not just adding
data.

## 2026-07-23 — Crypto cycle 2 verdict (cleaned panel)

IC sharpened on clean data (+0.0223, t=1.99, n=341 — the artifact was
DILUTING the measured signal) but net Sharpe negative at every tau
(−0.64/−0.56/−0.39, sane vol 10-28%). Cycle-1's +0.32 was entirely the
LUNA artifact. Structure: positive weekly rank-IC + negative decile-book
returns even at 74bps drag ⇒ the extreme deciles mean-revert (pumped coins
crash) while mid-ranks carry the correlation — the tradeable ends of the
signal don't pay. Price-momentum crypto xsec: DEAD as implemented, and
this is still the optimistic listing-biased panel. Remaining crypto
hypothesis with documented support: funding-rate carry (orthogonal,
unbuilt). Trials: 3, reported.

## 2026-07-23 — Cycle 10a: broad universe (5,594 names), price-only

Pond change delivered on the SIGNAL side: IC +0.0173 (t=3.11, n=654,
1,562 names/wk) vs S&P panel +0.0125 (t=2.35) — more breadth, stronger
statistics, exactly as the decay literature predicts. But net Sharpe still
negative at all taus (−0.52/−0.10/−0.07, tiered 5/10/20bps costs), and the
diagnostic explains why: decile curve is monotone D1→D8 (16→28.7bps/wk)
then REVERSES at D10 (23.6) — gross D10−D1 spread only 7.5bps/wk (~2%/yr
gross on the book), LOWER than the S&P panel's 16bps despite higher IC.
Rank correlation up, dollar spread down: small-cap returns are noisier, and
the prediction extremes are systematically the flattest/reversing part of
the curve. THIRD universe with the same fingerprint (S&P, crypto, broad):
**weekly price-only ML produces real rank-IC everywhere and extreme-decile
economics nowhere.** Hypothesis logged, NOT traded (would be post-hoc):
interior-rank constructions (long D8-ish, rank-linear weights) may harvest
the monotone region; a proper test must be pre-registered on new data or
justified structurally first. Upper-bound caveat applies (listing bias).
Trials: 3 + 1 diagnostic, reported.

## 2026-07-23 — Cycle 12: construction overhaul (cached predictions)

Pre-registered arms A(decile)/B(rank-linear)/C(B+inv-vol)/D(C+beta-neutral)
on two cached prediction sets. Broad weekly: A −0.07 → D −0.19 — no gross
edge to transfer (TC × 0 = 0); construction cannot rescue the broad
price-only book. S&P monthly (fund): A 0.273 → B 0.361 → **C 0.367**
(vol 3.0%→1.8%, turnover 4.5→2.8x) → D 0.311 (beta hedge added noise —
dropped). The decile-diagnostic prediction held: interior-rank harvesting
+ risk-weighting lifts Sharpe ~34% where gross edge exists. Champion
candidate sp_m_C is FULL-WINDOW-measured — walk-forward gate rerun with
construction arms in the candidate set is the required next measurement.
Trials: 8, reported.

## 2026-07-23 — Cycle 13: cross-sectional multi-asset — THE POND

Study 1 traded these instruments time-series and died; ranking them
AGAINST each other weekly (77 instruments, 7 asset classes, ex
hindsight_picked, per-class costs) delivers the campaign's best number:
**decile tau=0.25 net Sharpe 0.71** (IC +0.0169 t=2.66 n=758; CAGR 4.4%,
vol 6.3%); armC 0.545 at vol 2.6%. Only 3 pre-registered trials.
VERIFICATION: shuffled-label control −0.59 (clean); 12/15 years positive,
losers = documented trend-graveyard years (2012/14/18); corr to equity WF
stream +0.08 (orthogonal). Structural advantages vs equities: instruments
don't delist at zero (minimal survivorship), and the family (cross-asset
relative momentum) has persisted publicly for decades at CTA scale.
CAVEATS: Yahoo continuous-proxy data quality; per-class cost model is
optimistic for retail ETF implementation; family is published → decay
haircut applies; walk-forward config selection still to run (3-config
burn is small). Next: FX carry via FRED differentials (documented
orthogonal family, key already held), more markets, blend with equity
book. The verified thesis lands: the edge wasn't in the most-arbitraged
universe; it's in cross-asset relative value at retail-inaccessible-to-
institutions scale. Trials: 3 + verification, reported.

## 2026-07-23 — Gates: cycle-13 WF PASS; insider x arm-C fail

Cycle-13 walk-forward config selection (3 candidates, yearly, 2015-2026):
**0.852 — no selection tax** (equities paid 80%). Config ranking stable;
full-window 0.711 was dragged by 2012-14, not inflated by hindsight. The
multi-asset book is the first Quark result to pass every local gate:
shuffled control, yearly stability, orthogonality, walk-forward selection.
Remaining before external quoting: futures-proxy data audit + retail cost
stress. Insider x arm-C on broad panel: −0.045 (decile +0.047) — arm-C
construction is S&P/monthly-specific, NOT universal; broad book stays
decile. corr(equity book, multiasset book) = −0.16: natural hedge pair.

## 2026-07-23 — Cycle 14 + trimmed-book test (broad panel)

Overnight/intraday decomposition (opens fetched, on/id momentum 21/63 +
clientele gap) joins price+insider: **IC +0.0212 (t=3.93, n=654)** — third
confirmed family, composite tracking quadrature (0.0173→0.0194→0.0212).
Net Sharpe still ~0.076 (decile, tau .25): the broad book's signal is now
overwhelming and its monetization unchanged — gross spread is spread
thin across the curve and 20bps small-cap costs eat it. Trimmed-interior
book (pre-registered bands long [.7,.9) short [.1,.3), one trial):
**−0.184 — FALSIFIED**; the D8 peak was noise. Broad-book constructions
now exhausted: decile stands at ~0.08. Honest read: broad equity caps
near ~0.1-0.3 until more IC lands (fundamentals fetch + 8-K dates
pending). Trials: 2+1, reported. WSB attention data fetching (Arctic
Shift, top-100/day 2019-2026) — attention-reversal test next; documented
prior says FADE hype, small caps, small capacity.

## 2026-07-23 — Information-edge test: realized weather → natural gas

NOAA CPC daily population-weighted HDD (2012-2026, free) vs NG=F. PIT
seasonal norms (prior-years day-of-year), declustered top-quintile shocks.
Cold shocks d+1..+5: +0.67% (t=0.44, n=100) vs random-winter-day control
+0.82% — INDISTINGUISHABLE. Warm shocks: −0.40% (t=−0.50). **Realized
weather is fully priced.** The informational frontier is UPSTREAM: the
market trades forecasts 5-10 days ahead of realization, so the only
tradeable seam is forecast ERROR (the acquaintance's actual edge) —
requires archiving forecast vintages vs realizations. NOAA GFS forecasts
are free → forecast-error collector is buildable; history accrues from
day one (moat-by-patience). Also instructive: the test itself took ~1 hr
end-to-end — the machine can price-check an information hypothesis same-
day, which is the actual edge-hunting capability. HDD series cached:
data/noaa_hdd_daily.csv.

## 2026-07-23 — WSB study PRE-REGISTRATION (before data completes)

Dataset: first-100-posts-per-day chronological (NOT score-sorted), titles +
final scores + timestamps, r/wallstreetbets 2019-2026 (Arctic Shift).
KNOWN TRAPS DISARMED IN ADVANCE:
1. Final-score lookahead: archived scores are END-STATE (upvotes accrue
   after posting) — scores may NOT be used as PIT weights. Post COUNTS are
   PIT-safe. Scores usable only for descriptive analysis, flagged.
2. Ticker extraction: cashtags ($XXX) + uppercase tokens matched to panel
   symbols MINUS blocklist of ambiguous symbols (A, DD, IT, CEO, ON, ALL,
   ARE, FOR, GO, NOW, OPEN, REAL, SO, OUT, EAT, BIG, CAN, HAS, ANY, RH,
   YOLO-adjacent). Blocklist fixed BEFORE results.
3. Chronological first-100 sampling = attention proxy via daily post
   VOLUME share, not popularity — biased toward early-UTC hours; accepted
   and documented (uniform across sample).
4. Regime nonstationarity: 2021 mania vs after — results reported for
   full sample AND 2022+ separately (pre-declared split).
PRE-REGISTERED HYPOTHESES (directional priors from literature):
H1: abnormal mention spike (count z>2 vs trailing 63d) in sub-$2B names →
    REVERSAL d+5..+20 (fade the hype). Primary.
H2: same-day/next-day momentum d+1..+3 (attention chase) — secondary.
Universe: broad panel ∩ eligibility. Event decluster: 5 trading days.
Controls: random matched-size events. All trials reported.

## 2026-07-23 — WSB prior UPDATE (methodology research, unverified leads)

Before running the pre-registered WSB study, documented priors (multi-source
academic, NOT adversarially verified — usage limit): (1) WSB DD edge died
post-Jan-2021 — predicted +2.3%/mo ex-GME/AMC pre-GME, decayed to ~zero/
negative after the 500k→10.7M member explosion; our pre-declared 2022+ split
is the honest-but-likely-dead window. (2) ADVERSARIAL DATA: WSB users
deliberately post wrong tickers to poison scrapers; academics manually
reviewed all 5,050 posts. Our blocklist stops common-word tickers, NOT
intentional poisoning — extraction noise is a documented confound.
EXPECTATION SET: null or corpse likely; run anyway (clean null on famous
edge validates machine + is honest). Do NOT p-hack a live result out of a
dead edge. Masters doctrine banked (reports/deep_research_masters):
Benter fractional Kelly (½-⅓, because 2x edge-overestimate → negative
growth), blend-with-market-odds insight, capacity=0.25-0.5% of pool →
pick pond by capacity; Thorp idea→quant→cheap-verify loop = our cycle loop.

## 2026-07-23 — WSB study: CLEAN NULL (as pre-registered expectation)

274,415 posts, 2,847 tickers extracted (top: GME/TSLA/AMC/BBBY — sane;
AI-token contamination 2-3%, reported not hidden). First pass showed
−22/−38% "fade" — entirely zero-price data errors (clip −95%/+500% +
zero-cleaning removed it; LUNA lesson recurs: artifacts flatter). CLEAN:
H1 fade d5-20: +0.3% (t=0.15) full / −0.4% (t=−0.20) 2022+; H2 momentum:
−0.8% (t=−0.64); control −0.5%. NULL everywhere. The WSB attention edge
is dead post-2021, replicating Bradley et al. independently. Study closed;
no further trials on this family without NEW construction justification.

## 2026-07-23 — SIZING POLICY (Benter/Thorp doctrine applied)

Multi-asset book WF Sharpe 0.85 (se≈0.27). Doctrine: shrink edge before
sizing (Benter: 2x overestimate → negative growth at full Kelly). Shrunk
live expectation S≈0.5. Kelly-optimal vol = S = 50%; half-Kelly 25%;
POLICY ADOPTED: vol target 10-12% (~⅕ Kelly of shrunk edge) for any
deployment, paper first, revisit after 26 weeks of live ledger. Per-edge
niche positions: ⅓-Kelly ceiling on estimated edge, hard per-position
caps, kill-switch discipline unchanged. Rationale logged: backtest-derived
edges carry estimation error ABOVE Benter's in-vivo betting edges.

## 2026-07-23 — PRIMARY NICHE STUDY: 8-K drift by size — THESIS FALSIFIED

Preliminary (data through 2023-06; 98,360 on-panel events, 60,606 after
30d declustering; |reaction|>5% filter; signed drift d+2..d+21 vs market).
PREDICTION was: drift ~0 in LARGE, growing down the size ladder. REALITY:

           2013-2019              2019-2026
  LARGE   +0.40% (t=2.68)        +0.06% (t=0.27)
  MID     −0.03% (t=−0.19)       +0.25% (t=1.19)
  SMALL   −0.18% (t=−1.05)       +0.07% (t=0.26)

The gradient runs BACKWARDS: the only significant drift was in LARGE names
pre-2019 (+0.40%/event — modest, and now decayed to zero), and the SMALL
tier — the thesis's home — is a tightly-bounded null (n≈8k, se≈0.13%/event)
in BOTH eras. Post-earnings drift in small caps does not exist on this
panel. Best explanation: "nobody is paid to read the filing" was true in
1989; today MACHINES read every 8-K within seconds regardless of market
cap — filing-reading was commoditized exactly like parking-lot satellites.
Honest caveats: d0-d1 reaction window may mis-time some after-close
press-release sequences; EFTS display_names may under-cover tiny/OTC
filers (selection toward better-covered names). Neither plausibly
manufactures a null this flat across 8k events. Study closes when full
fetch lands (2023-2026 tail); thesis not expected to revive. Trials: 9
cells, all reported.

## 2026-07-23 — 8-K drift study FINAL (full dataset)

Complete: 168,071 Item-2.02 announcements, 4,604 tickers, 2012-2026;
84,576 declustered events. Preliminary verdict CONFIRMED: SMALL tier
full-sample −0.05% (t=−0.40, n=11,852) — a precise null; LARGE pre-2019
+0.40% (t=2.68) decayed to +0.09% (t=0.64) after. No size gradient in
the predicted direction. Post-earnings drift is extinct at all sizes on
this panel; the barrier ("nobody reads small filings") was commoditized
by machine filing-readers. Study CLOSED. The announcement-date dataset
itself (data/ann_dates_8k.csv) remains an asset: PIT earnings-event
timing for 4,604 names, reusable for any future event study.

## 2026-07-23 — EDGE ONTOGENY: the vital signs of alive vs dying edges

Rolling vitality curves on our own panels (reports/study script
run_edge_ontogeny.py). THE FINDING — an alive edge's calm phase looks like:
**sign persistence at LOW annual t, never loud.** 8-K LARGE drift alive
phase (2012-2019): eight consecutive positive years at +0.2..+0.8%/event,
per-year t only 0.3-2.2 — no single year significant; the accumulation
was the signal. DEATH SIGNATURE #1: sign coherence breaks BEFORE the mean
dies (2020+: +0.58,−0.50,+0.75,+0.46,−0.23,−0.10 — alternating chaos, mean
still ~0.1). DEATH SIGNATURE #2 (crowding inversion): rolling Sharpe
crosses zero and TRENDS (reversal_1990: −1.1,−1.4,−1.4 deepening 2024-26 —
the corpse became an anti-edge). UNDEAD state (momentum): wild ±1.5
oscillation around small positive mean — harvestable only inside
diversified books. IMMORTAL (turn-of-month): modest, persistent, mean-
reverting after bad years (2024 −1.3 → 2026 +1.5).
IMPLICATIONS: (1) edge detectors should scan for MULTI-YEAR SIGN
PERSISTENCE AT LOW t — anyone demanding annual t>3 only ever finds loud
dead things; (2) decay monitoring for OUR live book = watch sign
coherence, not mean (our multi-asset book: 12/15 positive years = the
alive signature, currently in its calm); (3) the 2015 lesson: an alive
edge's best year (t=2.2) looks like noise to everyone not tracking the
cumulative record — which is WHY it stayed alive seven more years.

## 2026-07-23 — Decade-game training study (50 variants, 2016-2026)

Mechanical regime-riders on hindsight menu {SPX,IXIC,NVDA,BTC,GC,CL}:
MAX $6.4B (W63/top1/no-filter/1.5x, maxDD 64%); MEDIAN $134M; MIN $15.5M.
**Selection tax max→median = 98%** — the DSR lesson in dollars. Even MIN
beat S&P buy-hold 4x: menu bias dwarfs all parameter choices (universe
selection = the deadliest lookahead, quantified). Kelly inverted-U visible
empirically: median by leverage 1.0x $77M < 1.25x $232M > 1.5x $138M —
over-Kelly costs real money even in a winning decade. Crash filters HURT
at median (V-bounce re-entry misses). Median maxDD 50-67%: statistically
optimal paths are behaviorally unholdable. Learnings transferred to
doctrine; none of these numbers are forward expectations.

## 2026-07-23 — THE CALM DETECTOR: storms are learnable, 11/11 OOS years

Storm = fwd 126d > +50%. Purged walk-forward by year, broad panel, texture-
only features. **Mean OOS AUC 0.761, top-decile lift 2.6x, positive lift
11/11 years** incl 2018/2020/2022 regime breaks. THE LEARNED CALM (top-5%
states vs population): vol63 0.86 vs 0.32 (HIGH-vol, not quiet); dd_from_
high −49% vs −13%; mom252 −34% vs +11%; mom21/63 ≈ 0. The model's pre-storm
state is NOT serene compression — it is a small violent name down ~half
whose decline has finally flattened: crashed-and-stabilized, base-forming.
"Calm before the storm" = EXHAUSTION, not serenity. Matches verified
literature (alpha concentrates in hard-to-arbitrage distressed/high-vol
names) — model rediscovered it blind. CAVEAT (standing): storm-classifier
≠ strategy — the other 90% of that decile includes names that keep dying;
tradability requires the full return distribution net of costs/borrow in
exactly the universe where costs bite hardest. Next gate before any use:
expected-return study of top-decile states. Detector saved as screening
instrument: scripts/run_storm_detector.py.

## 2026-07-24 — Polymarket betting backtest: 50-variant campaign — FAMILY FALSIFIED

Framework: Jan-Feb steering (4 configs), Mar-Jul scored. Frozen v7 vault
run first: **−$2,111 on 181 bets, MC percentile 2.4%** — significantly
WORSE than the efficient-market null. Then (vault reopened as development,
honestly labeled) 50-variant sweep across stretch-strength k, thresholds,
category sets, horizons, cluster modes. RESULTS: best of 50 = +$50 (zero,
after 50 looks); median −$1,750. MARGINALS (the real deliverable):
- FLB stretch k: monotone WORSE with strength (−0.5→+$16, 1.5→−$2,302);
  every positive-k cell significantly below null (MC 0.03-0.17). **The
  published FLB (2021-25 window) does not exist as a harvestable edge in
  our Mar-Jul 2026 tail markets — consistent with the documented 2026
  institutional entry (SIG/DRW/Wintermute) compressing exactly this bias,
  and with our own KB warning ("FLB frequently does not survive costs").**
- Politics = the poison category (adding it: −$1,426 median); "other"
  worse (−$3,032). geo+tech alone ≈ null (−$146).
- **Cluster caps robustly save money in EVERY configuration** (none
  −$2,693 → theme −$590): risk rails are permanent doctrine, confirmed.
- CLV was negative-to-flat from January — the gold-standard metric called
  the verdict months before P&L did. Believe CLV over P&L, always.
NOT TESTED by this sweep (still-live hypotheses for live-forward paper):
the telegraph/slope signal (momentum in probability space — our own
discovered pattern, absent from this static-entry sweep), pure arbitrage
(monitor logs 9-10 live mispricings/snapshot), maker/LP-reward quoting,
whale-following (collector accruing since 7/23). Next clean test = August
forward, live paper, via monitors — the only untainted data there is.
Trials: 4 dev + 1 vault + 50 sweep = 55, all logged. $0 real lost;
family killed for ~$0.15 of compute. The machine works.

## 2026-07-24 overnight — calibration convergence: ALL tape roads lead to the maker

Center calibration (3,341 liquid resolved markets, 5d-out): slope 0.87 —
the 2026 market is mildly OVERCONFIDENT (longshots 7.4% real vs 5.3%
implied **; favorites 87.5% vs 94.4% **) — REVERSED from the 2021-25
literature. But the reverse harvest is also dead: buying the cheap side
<25c nets −21.7%/bet (t=−4.6, n=1,855) — the longshot spread wall
(750bps half) exceeds the bias. Combined with the 55-trial favorite-side
falsification: the tape pays NOTHING net in either direction; the only
structural winner is the spread-charger. THE MAKER MECHANISM IS THE POND'S
ANSWER — now proven by convergence (sweep marginals + vault + calibration
+ live shadow-book observation of the #1 wallet quoting both sides).
NOTE: true tail (<$100k vol) still unfetched (gamma pagination depth
blocks it) — tail calibration remains open. Desk built and running:
arb-sim 30min, shadow-book (maker-noise filtered) + maker-sim + grader
2x daily, DESK_REPORT.md auto-writes.
