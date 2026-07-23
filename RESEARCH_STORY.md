# How this went

Three days in July 2026. The trial-by-trial log is RESEARCH_NOTES.md, the
condensed findings are in KNOWLEDGE_BASE.md, and the literature reviews live
under reports/deep_research_*.md. This file is the short version, told in
order.

## The equity work

I started with a cross-sectional S&P signal I'd built earlier: rank ~500
stocks weekly with a gradient-boosted model, hold the extreme deciles. The
IC had a t-stat of 3.35, which sounds like a finished project. It wasn't.

Cost-aware rebalancing (trade partway toward the target book instead of
rebuilding it weekly, an idea from Garleanu and Pedersen) added about 0.2
Sharpe, right where the literature said it would. Then I rebuilt the index
membership point-in-time and watched part of the edge turn out to be
survivorship. The harshest test came last: pick the configuration using
trailing data only, then measure forward. Sharpe 0.28 became 0.05. Signal
real, money gone. I wrote that down and moved on.

Along the way I built new features from primary sources instead of vendors:
EDGAR XBRL fundamentals, Form 4 insider filings, overnight versus intraday
returns. Composite IC reached t=3.9 on a 5,594-name panel, the best
statistic in the repo, and large-cap economics stayed thin anyway. Costs and
crowding beat statistics.

One strategy survived every test I could throw at it. Take the 77-instrument
multi-asset universe and, instead of timing each instrument, rank them
against each other and trade the cross-section. Walk-forward Sharpe 0.85,
clean shuffled-label control, positive in 12 of 15 years, and it passed the
same config-selection gate that killed the flagship.

## What I learned about edges

I replicated eight published anomalies on my own panel. Six were dead or had
flipped sign. Momentum limps along. The only one still fully alive is the
turn-of-month effect, published in 1968, which persists because the buying
it exploits comes from payroll calendars, and payroll calendars don't read
papers.

Other tests from this stretch: realized weather doesn't predict natural gas
(the market trades forecasts days earlier, so whatever edge exists is in
forecast errors, not outcomes). WallStreetBets attention stopped predicting
anything in early 2021, which matches the academic record. Post-earnings
drift in small caps is gone at every size tier I could measure, most likely
because software reads every filing now.

## Prediction markets

I picked prediction markets as the focus and did the homework first:
microstructure, fee models, who the institutional players are (Susquehanna
has been Kalshi's market maker since 2024; DRW and Wintermute were hiring
prediction-market traders in 2026), and what the academic record claims.

The famous claim is the favorite-longshot bias: favorites underpriced,
longshots overpriced. I ran a betting backtest with a two-month development
window and a five-month frozen out-of-sample vault, 55 registered trials in
total. The frozen strategy scored below an efficient-market Monte Carlo
null, at the 2.4th percentile. Worse than random betting at the same
prices.

So I measured the calibration myself on 3,341 resolved markets. The bias has
reversed since the 2021-25 study window: the market is now mildly
overconfident, slope 0.87. And the reverse trade loses too, 21.7% per bet
after spreads, because the spread is wider than the mispricing in both
directions. Every directional strategy on this venue pays a toll larger
than the edge. The one participant who nets positive is the market maker
collecting that toll.

## The Desk

That conclusion set the current phase. Three mechanisms make documented
money in this venue and none of them can be backtested, because they live
in order books, reward programs, and other people's positions rather than
in price history. So they run live, on paper, and grade themselves:

1. An arbitrage detector that checks mutually-exclusive outcome sets
   against real order-book depth every 30 minutes.
2. A market-maker simulation that quotes both sides on paper and tracks how
   often informed flow runs over the quotes, against the reward income.
3. A tracker that photographs the public on-chain positions of the top 30
   wallets twice a day and paper-copies their new directional entries.
   The current #1 wallet made $8.5M last month, and its book shows both
   sides of the same matches. It's a maker. That observation alone was
   worth building the tracker.

A scheduled job checks the ledgers daily and writes a digest. Nothing goes
live with real money until a mechanism clears the same gates everything
else faced.

## What this produced

About 70 registered experiments, 15 dead strategies, one survivor, a
calibration result that contradicts the published record, and a set of
instruments that keep collecting data whether or not anyone is watching.
Also a habit that mattered more than any single result: when a metric and
a profit number disagree, believe the metric.
