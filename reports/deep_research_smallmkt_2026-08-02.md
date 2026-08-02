# Arbitrage everywhere: the small-market cost-floor moat

*Deep research, 2026-08-02. Every substantive claim sourced in parens. Unconfirmed items marked. Read the "Refuted / overhyped" section before acting on anything.*

## Verdict

The moat is real but it is an **attention/fixed-cost moat, not a fee moat** — and it is a capped hourly-income floor, not a wealth engine. A professional firm builds a strategy only when expected annual profit clears its *marginal* cost, and that cost is dominated by fixed overhead that must be amortized (infra, a fully-loaded quant-dev headcount, risk capital clearing a hurdle, minimum-AUM economics), not by per-trade fees which are tiny for everyone (derived synthesis; supported by Shleifer & Vishny 1997, Journal of Finance — arbitrage is done by a small number of specialized intermediaries under capital/funding constraints, VERIFIED). The empirical persistence literature confirms the residual lives exactly where the thesis targets: McLean & Pontiff 2016 (JF) find predictor returns fall ~58% post-publication but *not to zero*, with the residual concentrated in high-idiosyncratic-risk, low-liquidity names (VERIFIED); AQR/Han et al. and Ma (Wharton Rodney White Center) find anomaly returns concentrate in small, illiquid, hard-to-short stocks (VERIFIED). So the band below the pro floor and above the $0-operator's own-labor floor exists and is durable. The fatal caveat: the same smallness that keeps firms out hard-caps total dollars. Realistic solo aggregate is order $10k–$100k/yr bounded by labor hours (my estimate, UNCONFIRMED), and scaling by hiring re-imports a cost floor that pushes you back into the pro-competed zone.

**Ranked arb forms genuinely reachable by a $0-then-small operator, net of fees:**

1. **On-chain complete-set mint/merge (Gnosis CTF)** — structurally fee-free primitive (no protocol fee, only gas; VERIFIED core mechanics). Best pure fit for the thesis on small-cap outcome markets.
2. **SX Bet single-bet lines** — genuinely 0% both sides, sports/event exchange (VERIFIED). Cleanest fee-free venue found; F-1 gambling caveat (see compliance).
3. **Funding-rate / basis carry (crypto, delta-neutral)** — patient, periodic scan not a latency race, near-zero net fee via maker/promo (PARTLY verified). Fits the existing desk cleanly.
4. **CEF/ETF NAV-gap and dual-listing arb via zero-commission brokers** — fee-light, sub-$50 mispricings economically fine for a $0 operator, irrational for a salaried desk (thesis VERIFIED; specific residual-fee rates STALE, see below).
5. **Sports middles / +EV vs soft books** — patient and cheap to detect, but gated by feed cost (free Odds API exposes only 2 recreational books, no sharp anchor; VERIFIED) and by F-1 gambling risk.
6. **TCG / collectibles / graded-card spreads** — genuine below-institutional-floor corner, free-tier price feeds, but manual/physical execution and — critically — an unauthorized-employment problem for an F-1 holder.

Deprioritized entirely: DEX MEV / flashloan arb, single-market liquid CEX and sports arb (fast corners firms already own), and physical retail/online arbitrage (paid tooling, ToS/scraping risk, F-1 employment problem).

## Dimension 1 — Does the fee floor even bind? (fee-free structures)

Fee-free/fee-light structures do still exist in 2026 but cluster narrowly, and most "zero-fee" claims collapse into near-zero residual or time-limited promos.

- **SX Bet: 0% commission on single bets, both sides.** A 5% fee applies only to the *net profit* of a *winning parlay* — not stake, not single bets, not losing bets (SX Bet docs, docs.sx.bet overview; corroborated by help center — VERIFIED). This is the cleanest genuinely fee-free arb venue found: a P2P sports/event exchange where two-line arbs clear at zero transaction cost on the SX legs. (Note: the docs.sx.bet/trading/fees deep link 404s currently; the overview page carries the numbers.)
- **Gnosis Conditional Tokens Framework (CTF) mint/merge: no protocol fee.** 1 USDC of collateral mints one full outcome set (YES+NO=$1); merge/redeem burns a set back to $1; only cost is gas (conditional-tokens.readthedocs.io; gnosis/conditional-tokens-contracts — core mechanics VERIFIED). Structurally fee-free: whenever a complete set assembles for < $1, merging locks risk-free profit. Caveat: the *primitive* is fee-free, but the BUY legs that assemble the set now carry taker fees on the major venue — the surviving fee-free edge is on smaller CTF venues without taker fees, or via minting (providing liquidity) rather than buying.
- **Zero-commission US equity/ETF brokers (Alpaca, Robinhood): $0 commission**, residual fees trivial and sell-side only (thesis VERIFIED). **CORRECTION — the specific rates in the source are stale.** SEC Section 31 fee for FY2026 (effective 2026-04-04) is **$20.60 per $1,000,000** principal, not $23.10; FINRA TAF effective 2026-01-01 is **$0.000195/share, per-trade cap $9.79**, not $0.000119/share cap $5.95 (VERIFY note; the older figures are from prior years). The directional conclusion — near-zero, a few cents to a few dollars per round trip — still holds; the quoted numbers do not. Use the corrected rates.
- **dYdX v4 negative maker fee — real but not a standing retail edge.** A genuine negative maker rebate exists, max -0.011%, and Surge Season promotions rebate 100% of front-end perp fees in DYDX tokens (dydx.xyz Surge Season 7 blog — VERIFIED). **CORRECTION:** the -0.011% requires the top tier (~$200M 30-day volume); negative fees historically start ~Tier 6 / $125M+. A $0/retail maker gets zero net fee only *during a Surge holiday*, not a persistent negative fee (VERIFY: PARTLY). Treat as a promo channel, not a structural rebate.

## Dimension 2 — Why the moat persists (theory)

Formalization: a firm trades an opportunity-stream only when expected annual profit exceeds *marginal* cost, and marginal cost is dominated by fixed costs that must be amortized (derived; UNCONFIRMED as a specific model, but each input below is sourced). Estimated per-tier "worth-building" floors (my order-of-magnitude model, UNCONFIRMED):

- **HFT firm ~$500k–$1M/yr net per new strategy** — must amortize ~$600k–$850k/yr infra (colocation, cross-connects, direct feeds, DMA) plus a $300–500k fully-loaded quant dev plus a risk-capital hurdle (infra figures PARTLY verified — Equinix cabinets ~$1.5–3k/mo and direct feeds thousands/mo each are corroborated; the $50–72k/mo and $200–400k capex *totals* come only from content farms, treat as illustrative).
- **Mid quant fund / prop desk ~$100k–$500k/yr per strategy** — breakeven AUM averages ~$86M (a third break even at ≤$50M; global macro highest ~$132M, alt credit lowest ~$77M; sub-$100M funds spend 4–8% of AUM on ops) (AIMA/GPP survey via Wealth Professional — VERIFIED). A strategy that can deploy only ~$50k of capital, even at 30%/yr, yields ~$15k — below the accounting noise of a fund with $2–3M opex, so no researcher is ever assigned (operator's arithmetic, sound).
- **Sophisticated retail ~$5k–$50k/yr aggregate**, or must beat a few hundred $/hr of the operator's own time.
- **$0 student ~a few dollars per instance** if low-effort/automatable, because fixed cost ≈ own labor + free infra.

**The exploitable band:** roughly $2–$50 expected profit per instance with per-niche annual capacity of order <$100k/yr — too small to amortize any professional headcount, large enough to beat a near-zero marginal cost (derived; UNCONFIRMED). Theoretical backbone: Shleifer & Vishny 1997 (specialized, capital-constrained arbitrage — VERIFIED); capacity is formally the AUM at which marginal alpha no longer clears execution cost (Bonelli, Landier, Simon & Thesmar, "The Capacity of Trading Strategies," SSRN 2585399 — paper exists and models capacity via alpha-vs-cost, but the exact definition wording is UNVERIFIED against the compressed PDF, and its own nuance is that dynamic optimization keeps net performance from going negative even at large size — verify before quoting).

**Durability against other small operators (PARTLY verified):** the firm-side half rests on rigorous literature; the "stable self-limiting equilibrium, operator's own time is the binding scarce resource" half rests on practitioner anecdote (elitetrader forum, retail-arb guides — low rigor). Directionally reasonable: no solo operator can saturate thousands of fragmented micro-markets, and as entrants crowd a niche, per-instance profit falls below their own-hour value and they exit.

**Capacity ceiling (the fatal limit, UNCONFIRMED band):** aggregate solo take is bounded by labor hours, realistically order $10k–$100k/yr, and does not compound. Honest framing: capped hourly income, not a scalable fund.

## Dimension 3 — Tooling and the detection-vs-execution axis

The open-source tooling splits cleanly by detection vs execution, and that axis *is* the moat line.

- **FAST corners (firms win — speed is capital):** DEX MEV / flashloan arb has abundant free code but needs paid execution infra. solidquant/mev-templates (577★, Python/JS/Rust, triangular Uniswap-V2) requires WSS/HTTPS nodes, a *paid* Blocknative gas key, and a deployed bot contract (VERIFIED). **CORRECTION:** the "README says profitable only on less-competitive chains" caveat is misattributed — that framing is in the author's blog/tutorial, not the repo README (VERIFY: PARTLY). CEX price arb via CCXT (MIT, 100+ exchanges, unified order books/funding/WS — VERIFIED) is the best free feed layer but the naive cross-exchange arb it enables is competitive.
- **PATIENT corners (retail cost floor wins — detection = free cron, execution = manual/slow):**
  - *Sports middles/+EV vs soft books:* edge-scanner, SportsArbFinder, ArbitrageFinder etc. are batch/manual, not streaming (VERIFIED). The binding gate is the *feed*, not the code: The Odds API free tier is 500 req/day, no card, indefinite, but exposes only 2 recreational bookmakers — sharp books, exchanges, prediction markets are paid, so you can see line gaps but not the sharp anchor genuine +EV needs (VERIFIED).
  - *Funding-rate / basis carry:* delta-neutral (long spot, short perp), earns funding regardless of direction, periodic scan (VERIFIED as a patient corner). aoki-h-jp/funding-rate-arbitrage exists as a detection framework (VERIFIED); kir1l, hamood1337, kiprella repos named but not individually confirmed (PARTLY). Quark memory's "crypto basis 7–8% ann" cross-ref is internal, not externally verified.
  - *TCG / collectibles / graded-card spreads:* free-tier price feeds (TCGPlayer, JustTCG, Cardmarket); arb forms are geographic cross-marketplace, buylist-vs-market, and raw→PSA/BGS grading (PARTLY verified). No repo demonstrates a closed-loop profitable system — these are feeds, not graded strategies.

**Reusable insight:** the existing desk (moneymaker3000/Quark) is already architected *more disciplined than the public bots* — its files exist and were confirmed locally (arb_executor_sim.py with real order-book fillability, whale_shadow.py, maker_sim.py, shadow_grader.py, plus collectors — VERIFIED existence). Nearly every OSS repo conflates detection and execution and computes spreads on top-of-book/summary feeds, not on fillable depth net of fees/slippage/transfers; the desk's fillability + paper-first grading gate is the antidote and already proved that summary-feed prediction-market edges did not survive real books (VERIFIED). Keep that gate on everything.

## Dimension 4 — F-1 compliance (I am not a lawyer; confirm with UPenn ISSS / an immigration attorney)

This dimension gates the ranking hard and is not in the source research — reasoning below is general, marked UNCONFIRMED as legal advice.

- **Passive investment income is generally permissible for F-1 students.** Trading your own equities/ETFs/crypto for your own account is typically treated as passive investing, not "employment." CEF/ETF NAV-gap arb, dual-listing arb, and personal crypto carry/CTF positions plausibly sit here — *if* passive and self-directed (UNCONFIRMED; confirm with ISSS).
- **Anything that looks like an active business or self-employment is unauthorized work.** Retail/online arbitrage (buy-resell as a business), and running a monetized service/bot for others, plausibly count as unauthorized employment — a serious status risk. Deprioritize regardless of economics.
- **Sports betting / prediction markets carry two separate problems:** (1) state-by-state legality of the activity itself, and (2) whether systematic betting reads as a "business." SX Bet and sports +EV score worst here despite good fee economics. Prediction-market CTF arb is ambiguous — treat cautiously.
- **The cleanest F-1 fit is passive, self-account financial arb** (equity NAV gaps, delta-neutral crypto carry), which is also where the desk already operates.

## Arb-form scorecard

| Arb form | Fee-reachable? | Speed or patient? | Measured size | F-1 compliant? |
|---|---|---|---|---|
| CTF complete-set mint/merge | Yes — no protocol fee, gas only (VERIFIED); buy legs may carry taker fees | Patient (mostly) | Small-cap outcome mkts; $2–50/instance (thesis) | Ambiguous — prediction-mkt/legal gray; confirm |
| SX Bet single-bet lines | Yes — 0% both sides (VERIFIED) | Patient | Low-volume event lines, small size | Poor — gambling + business risk |
| Funding/basis carry (crypto) | Near-zero (maker/promo; PARTLY) | Patient, periodic scan | Delta-neutral; Quark memo "7–8% ann" (unverified) | Plausible if passive/self-account (UNCONFIRMED) |
| CEF/ETF NAV-gap, dual-listing | Fee-light — $0 commission, tiny sell-side residuals (VERIFIED; rates corrected) | Patient | Sub-$50 mispricings | Best fit — passive investment (UNCONFIRMED) |
| Sports middles / +EV vs soft books | Cheap to detect, but sharp feed is paid (VERIFIED gate) | Patient | $2–50/line | Poor — gambling + business risk |
| TCG / graded-card spreads | Free-tier feeds; manual/physical (PARTLY) | Patient | $2–50/item | Poor — active resale = employment |
| DEX MEV / flashloan | No — needs paid RPC/gas key (VERIFIED) | Fast/atomic (firms win) | Competed away for retail | N/A — deprioritized |
| Single-market CEX/liquid sports arb | Fee-light but competitive | Fast (firms win) | Quark memo: 3.6s lifespan (unverified) | N/A — deprioritized |
| Retail/online goods arb | No — paid tooling (Keepa etc.) | Patient | Real capacity but ToS risk | No — active business |

## The one new lane worth adding to the desk

**Add a CCXT funding-rate / basis-carry collector.** It is the single extension that scores well on every dimension the desk actually controls: (1) fee-reachable — delta-neutral carry clears at near-zero net fee via maker posting or promo windows (PARTLY verified); (2) patient — a periodic scan on a cron, not a latency race, so it slots directly into the existing collector cadence with no new infra (VERIFIED as a patient corner); (3) free feed layer already standardized — CCXT normalizes funding rates across 100+ venues under the MIT license (VERIFIED); (4) it is the most defensible F-1 fit among the crypto lanes if run passive and self-account, unlike the sports/gambling and physical-resale lanes (UNCONFIRMED legal — confirm with ISSS). Critically, it reuses the desk's existing discipline: run every flagged carry spread through arb_executor_sim.py's real-order-book fillability check and shadow_grader before any capital, because the OSS funding scanners uniformly compute spreads on summary feeds and none publish audited live PnL (VERIFIED universal caveat).

Do **not** add sports/SX (F-1 gambling + business risk, and the free feed lacks a sharp anchor), and do **not** add TCG/retail goods (active-resale employment problem for an F-1 holder, plus paid or ToS-restricted tooling). The CTF mint/merge primitive is the most thesis-pure structure but is a heavier build and legally ambiguous — worth a later spike, not the next lane.

## Refuted / overhyped — read this before believing any of the above

This domain is saturated with get-rich-quick noise. What does not survive scrutiny:

- **"DEXes are fee-free."** REFUTED. Uniswap in 2026 keeps LP fee tiers *and* activated protocol fees across V2/V3/V4 via the "UNIfication" governance proposal executed ~2026-07-27 (~1/6 of the swap fee, routed to UNI burn); only the Uniswap Labs interface fee is 0% (blog.uniswap.org/unification — VERIFIED). An on-chain swap arb pays LP fee + protocol fee + gas.
- **"Solana base gas is the arbitrage cost floor."** REFUTED / MISATTRIBUTED. The real floor is the priority-fee + Jito tip auction, which pro bots already saturate (Jito tips ran 5–7x priority fees and exceeded ~60% of priority-fee value by early 2025; one bot paid ~7,980 SOL in tips over 30 days — directionally CONFIRMED via 99bitcoins/Jito stats). **But the cited arXiv 2507.13023 does NOT support this** — that paper is about *Ethereum* CEX-DEX extracted value and never mentions Solana, Jito, or the tip auction (VERIFY: PARTLY). Drop that citation.
- **"Maker rebates on NYSE/Nasdaq are harvestable retail income."** REFUTED. Rebates (~$0.0015–0.003/share) accrue only to exchange members / DMA participants; a $0 retail order routed through a zero-commission broker is sold via PFOF and the wholesaler/broker captures the economics (SEC EMSAC memo; NYSE/Nasdaq price lists — VERIFIED). These are a reason retail fills are *free*, not a rebate you can collect.
- **"Polymarket now charges a fee on winning positions."** REFUTED as stated. Polymarket's Fee Structure V2 (~2026-03-30) charges *taker* fees at trade execution (category-tiered; makers pay zero and get rebates) and explicitly charges **zero** on winnings/resolution (VERIFY: PARTLY). It is a taker trade fee, not a settlement fee — though the practical consequence (buy legs into a CTF set now cost more on the major venue) still stands.
- **"dYdX gives everyone a -0.011% maker rebate."** OVERHYPED. That rate is top-tier only (~$200M 30-day volume); retail gets zero net fee only during a Surge promo (VERIFIED).
- **Every "profitable" arb repo on GitHub.** UNIVERSAL CAVEAT (VERIFIED): all compute spreads on top-of-book/summary feeds, unfilled, unbacktested, net of nothing — no taker fees, slippage, transfer times, or shipping. None publish audited live PnL. This mirrors the desk's own finding that summary-feed edges vanish on real books. Treat all as detection scaffolding, never as evidence of profit.
- **Kalshi as a "0% maker venue."** UNCONFIRMED / contested. Taker fee ~0.07·C·(1−C) per contract (max ~1.75c at 50c); sources disagree on whether makers get a true rebate or simply pay 25% of the taker fee with no rebate. Cheap near price extremes, not a dependable true-zero venue.
- **Retail/online goods arbitrage as a "$0 lane."** OVERHYPED for this operator. Real capacity, but the tooling is paid (Keepa ~$19/mo, Tactical Arbitrage, etc.), Amazon actively blocks scraping (ToS risk), 2026 FBA fee rises and the end of de-minimis squeezed margins, and for an F-1 holder it reads as an unauthorized business. Fails the $0 constraint and the compliance constraint simultaneously.
- **The whole thesis as a "wealth engine."** The honest verdict: the moat is real but self-capping. The smallness that keeps firms out also caps your total dollars at a labor-bounded income floor (order $10k–$100k/yr, my estimate, UNCONFIRMED). Anyone selling small-market arb as scalable passive wealth is selling the hype, not the edge.

*Placeholder note: the crypto_dex, sports_books, retail_goods, and defi_fixed research keys in the input were test/placeholder stubs with no real findings and were excluded; only the substantive keys (fee_free_structures, why_persists, tooling) and the verification pass informed this report.*
