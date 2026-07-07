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

- 8 classic variants registered (3 tsmom lookbacks, 2 MA crosses, RSI
  reversion, MACD, Bollinger reversion). **Net of costs, none survive**:
  best is tsmom_252 (net CAGR ~1%, Sharpe 0.37 on the 2012+ window), and its
  **DSR is 0.29 with N=8 trials** — consistent with selecting the luckiest of
  8 skill-less variants. The 2004–2011 in-sample-free period doesn't rescue
  it either.
- Turnover of vol-targeted tsmom (~11x gross/yr) is dominated by daily vol
  rescaling, not signal flips. Position buffering would cut it — future work,
  noted not implemented.
- **ML timing model: honest failure.** Pooled HGB classifier, 17 features,
  purged walk-forward, 15 annual folds: mean AUC 0.513 (best fold 2020 at
  0.556 — vol-regime predictability, interesting), shuffled control 0.503.
  After causal signal calibration and costs: net Sharpe −0.71, DSR ≈ 0.
  Conclusion: daily-horizon timing with standard price features does not
  clear ~2–10 bps costs on this universe. We report it and move on.
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
- Results: weekly IC 0.0165 (t=3.22, n=756) — genuine cross-sectional
  predictability. Decile spread near-monotonic, ~16 bps/week top-vs-bottom
  gross. Net economics modest: Sharpe 0.05 weekly (turnover eats the edge at
  5 bps/side), 0.26 monthly. Shuffled control clean (AUC 0.498, IC −0.004,
  Sharpe −1.5 = pure costs).
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

## Future work (ordered by expected value)

1. Point-in-time S&P universe from Wikipedia change history (kills the main
   bias qualifier on Study 2).
2. Position buffering / no-trade bands (turnover is the binding constraint in
   both studies).
3. Ratio-back-adjusted continuous futures for Study 1.
4. Meta-labeling: use the Study 2 model to size a momentum base signal
   instead of generating positions directly.
5. Revive the legacy cointegration pairs idea inside the tested engine
   (needs two-leg position semantics).
