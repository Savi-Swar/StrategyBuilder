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
