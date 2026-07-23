# Deep research: WSB signal methodology (UNVERIFIED — panels rate-limited)

*Verification failed (usage limit). Claims are single-source extractions, NOT adversarially confirmed. Treat as leads, not facts.*

- Before the January 2021 GameStop short squeeze, due-diligence (DD) recommendations posted on r/wallstreetbets were statistically significant predictors of both stock returns and subsequent cash-flow news (i.e., the posts contained genuine fundamental information, not just price pressure).
  [https://academic.oup.com/rfs/advance-article-abstract/doi/10.1093/rfs/hhad098/7486572]

- The return predictability of WSB due-diligence posts is eliminated in the period after the GameStop event — a documented structural break/decay point that any study pooling 2019-2026 data must model as a regime change rather than a stable signal.
  [https://academic.oup.com/rfs/advance-article-abstract/doi/10.1093/rfs/hhad098/7486572]

- Post-GME, the composition of DD reports shifted dramatically toward price-pressure and attention-grabbing stocks, and the loss of informativeness is concentrated in exactly those report types — implying content/topic filtering matters for signal construction.
  [https://academic.oup.com/rfs/advance-article-abstract/doi/10.1093/rfs/hhad098/7486572]

- In the pre-GameStop period (July 2018–December 2020), WSB due-diligence buy recommendations significantly predicted returns: +0.92% one-week and +2.32% one-month ahead per incremental buy DD report, even after excluding GME and AMC (+6.04% one-month including them).
  [https://russelljame.com/wsb_3_15_2022.pdf]

- DD report predictive value fully decayed to statistical zero in the post-GME period (Jan–Jun 2021): the one-month estimate falls by 5.21% to 0.83% in the full sample and by 3.83% to -1.51% excluding GME/AMC, with neither post-period estimate distinguishable from zero; quarterly estimates show the break at Q1 2021 (-0.71%) worsening in Q2 2021 (-1.42%).
  [https://russelljame.com/wsb_3_15_2022.pdf]

- The mechanism of decay is a regime shift in post content: the share of DD reports emphasizing price-pressure/squeeze strategies rather than fundamentals quadrupled after the GME squeeze, and the loss of informativeness is concentrated in those price-pressure reports — a documented case of signal nonstationarity tied to the Jan 2021 subscriber explosion.
  [https://russelljame.com/wsb_3_15_2022.pdf]

- Automated ticker extraction from WSB is unreliable enough that the authors manually reviewed every report, in part because WSB users deliberately post wrong tickers to poison algorithmic scrapers — direct documentation of an adversarial ticker-extraction contamination channel beyond ordinary common-word false positives.
  [https://russelljame.com/wsb_3_15_2022.pdf]

- WSB due-diligence (DD) reports in the pre-GameStop period (2018-2020) significantly predicted one-month-ahead returns: an incremental DD buy recommendation was associated with a 6.04% one-month return increase in the full sample and 2.32% after excluding GME and AMC, and this predictability fully reversed in the post-GME period (Jan-Jun 2021).
  [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3806065]

- Pre-GME DD reports positively forecast fundamental cash-flow news (media sentiment, earnings surprises, analyst forecast revisions), indicating genuine information rather than pure price pressure; these effects reverse to zero or turn significantly negative in 2021, consistent with the post-GME user influx degrading research quality.
  [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3806065]

- Ticker extraction from WSB posts cannot be done reliably by automated string matching: the authors manually reviewed every one of the 5,050 DD reports (July 2018-June 2021) to identify ticker and recommendation, because users add special characters around tickers and sometimes intentionally post wrong tickers to mislead algorithmic monitors.
  [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3806065]

- WSB coverage concentrates in speculative names and the forum underwent an order-of-magnitude regime change: DD reports tilt toward young, volatile stocks with low institutional ownership and high short interest; the forum grew from roughly 500,000 users in July 2018 to roughly 10.7 million by June 2021 with the spike at the January 2021 GME squeeze, and GME+AMC alone represent close to 25% of the 2021 DD sample.
  [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3806065]

- A daily long-short portfolio built from WSB buy/sell recommendations produces no risk-adjusted alpha at any holding period from one day to one year, after controlling for Fama-French factors.
  [https://link.springer.com/article/10.1007/s11408-022-00415-w]

- WSB submission activity is positively associated with abnormal trading volume in the mentioned stocks, i.e., the attention signal moves volume even though it does not generate alpha.
  [https://link.springer.com/article/10.1007/s11408-022-00415-w]

- The null-alpha result is robust to removing GameStop from the post-2021 sample, and the weakest predictive results occur for sell recommendations in the post-2021 subsample — consistent with post-meme-era signal decay.
  [https://link.springer.com/article/10.1007/s11408-022-00415-w]

- Requiring a '$' prefix for ticker extraction on WSB has very low recall: only about 13% of GameStop mentions and 12% of Microsoft mentions used the dollar sign, so the authors instead match uppercase 2-5 character tokens against a known NASDAQ ticker list plus a manually curated stopword blocklist of common-word tickers, and exclude single-character tokens without '$' entirely as mostly false positives.
  [https://arxiv.org/pdf/2105.02728]

- WSB buy signals show a documented momentum-horizon structure: they are no better than random or equally-distributed buying at 1-day to 1-week horizons, but become discernibly better at 1-3 months — success rate 51.75% after 1 day rising to 69.94% after 3 months, versus 60-62% for random/equal baselines at 3 months (up to 15.6% higher).
  [https://arxiv.org/pdf/2105.02728]

- The short-term average-return advantage of WSB buy signals (32.03% 3-month growth vs 16.65% buying every day) was mostly driven by a handful of meme stocks (GME, AMC, BB) rather than broad signal quality — following buy signals led to consistently better outcomes for only about 7 of 20 portfolio tickers, and sell signals were outright unsuccessful (prices rose more after sell signals than average).
  [https://arxiv.org/pdf/2105.02728]

- Separating 'proactive' from 'reactive' buy signals matters: only 46.5% of WSB buy signals preceded the price move (proactive); reactive signals — posts appearing after a price run-up — performed significantly worse, and a simple PIT-computable filter (price change over the preceding day below its 30-day moving average) yielded approximately 83% higher growth after one day and 17% higher after three months versus all buy signals.
  [https://arxiv.org/pdf/2105.02728]

- Pushshift-archived upvote scores are unreliable (incomplete and often substantially below true values) and the authors excluded all author/moderator-deleted posts from the dataset — directly documenting both the score-integrity problem and a deliberate survivorship filter; they also confirm regime nonstationarity, with pre-2021 (Jan 2019-Dec 2020) buy-signal effects much weaker though directionally similar (3-month buy-signal return 12.57% vs 32.03% in the full sample).
  [https://arxiv.org/pdf/2105.02728]

- The paper's first-stage attention-spike detector is a PIT-safe counts-vs-trailing-baseline construction: a day is flagged when ticker-related submission/user counts exceed the trailing 10-day mean plus one mean absolute deviation (for level variables) or double day-over-day (for change variables), with at least 4 of 6 indicators required to fire.
  [https://arxiv.org/pdf/2203.13790]

- Applied to r/WallStreetBets Oct 2020–Jun 2021, the alert system fires almost exclusively on meme stocks — 21 suspicious days for GME and 4 for AMC versus 2 for AAPL and 1 for MSFT (consolidating to 8/4/2/1 independent events with a 10-day separation rule) — and significant positive abnormal returns follow alerts only for the meme stocks.
  [https://arxiv.org/pdf/2203.13790]

- The horizon structure is momentum-after-attention with a multi-day lag: for the GME event dated Jan 14, 2021, cumulative abnormal return over a [-10,+10] market-model event window reaches 3.883 (388%) by day +10, with the largest daily abnormal return (+1.349, significant at 5%) on day +8 and peak abnormal volume (20.3x baseline) on day +7 — significance concentrated after, not before, the social-network alert.
  [https://arxiv.org/pdf/2203.13790]

- Barber-Odean attention theory posits an asymmetry: attention drives individual investors' BUYING but not their selling, because buyers face a search problem over thousands of stocks while sellers choose only from the few stocks they already own — so retail attention signals should predict net buying pressure, not balanced flow.
  [http://www.econ.yale.edu/~shiller/behfin/2001-05-11/barber-odean.pdf]

- The paper operationalizes attention with three concrete, measurable proxies — daily abnormal trading volume (stock's daily volume relative to its own baseline), extreme one-day returns (buying on the day AFTER the extreme move), and presence in the news — establishing the abnormal-attention-vs-trailing-baseline construction that a WSB mention-count signal should replicate.
  [http://www.econ.yale.edu/~shiller/behfin/2001-05-11/barber-odean.pdf]

- Documented effect size for attention-driven retail buying: self-directed discount-brokerage investors make roughly 2x as many purchases as sales of stocks in the top 5% of abnormal volume, and are nearly 2x as likely to buy as sell the previous day's worst performers (bottom 5% one-day return) — retail herds into BOTH big winners and big losers.
  [http://www.econ.yale.edu/~shiller/behfin/2001-05-11/barber-odean.pdf]

