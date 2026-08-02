# Arbitrage across all forms and venues

Date: 2026-08-02. Scope: every arbitrage form the desk can name, across every real-money-priced venue it can reach, ranked by what is actually wireable for a patient $0, US-connected (F-1) operator. Supersedes the Polymarket-only framing in deep_research_arb_2026-07-31.md and deep_research_impl_2026-08-01.md. House style: every claim sourced in parens; unconfirmed marked; refuted claims quarantined at the end.

## Verdict

The executable universe is five venues — Polymarket, Kalshi, Limitless, SX Bet, Manifold — but they split cleanly by role. Only two are real-money-executable legs for this operator, and only one of those without a compliance problem. Ranked by what is worth wiring:

1. **Same-venue rebalancing on Polymarket (TRUE LOCK, largest measured dollars).** Single-condition YES+NO priced away from $1 ($10.58M realized Apr2024-Apr2025) and neg-risk set rebalancing (~$29.0M) are the only genuine locks and hold essentially all the historically measured money (arXiv:2508.03474, confirmed against full text). Maker-reachable at $0, depth-capped to tens of shares per episode. This stays the desk's spine.

2. **Cross-venue crypto Limitless↔Polymarket (BTC/ETH Up/Down) — first genuine cross-venue LOCK CANDIDATE.** Both venues now resolve short-dated crypto up/down via Chainlink Data Streams (theblock.co/post/370444; docs.limitless.exchange llms.txt; verify CONFIRMED). If a market-pair references the identical stream/round/strike-reference/window/tie-rule, YES-cheap + NO-other for combined <$1 is oracle-identical with no settlement-divergence risk. Maker-reachable, no measured history — the desk must measure it. Binding risks: per-pair spec-identity verification, capital split across Base+Polygon, non-atomic legging.

3. **Cross-venue sports (SX Bet as the fee-free leg) — reachable, but a SPREAD, not a lock.** SX Bet's 0% single-bet commission (help.sx.bet, docs.sx.bet; CONFIRMED) removes the fee wall that made single-venue Polymarket sports arb fee-negative. But the three venues settle on different mechanisms (SX creator-report Outcome1/Outcome2/Void; Polymarket UMA; Kalshi rulebook 6.3(c)), so the spread is compensation for settlement divergence, not free money (Cardi B precedent: $0.26/$0.74 Kalshi vs $1.00 YES Polymarket; CONFIRMED). Small risk-scored book at most.

4. **Resolution-dependent cross-market forms** (deadline/containment, combinatorial/logical, calendar/temporal, dutch-book) — all patient, all economically tiny (~$95.2K/yr venue-wide, top pair $60,237; arXiv:2508.03474 CONFIRMED), all split-risk-bearing. Small caps only.

5. **Excluded:** single-market taker sniping on live crypto/sports (3.6s lifetimes, unwinnable speed race at $0; arXiv:2605.00864); Kalshi and SX Bet and Limitless real-money **execution** for this operator (see compliance below); Manifold (play-money).

**Honest verdict on cross-venue sports:** it is real and structurally the opposite of the single-venue Polymarket form that measured fee-negative — but for THIS desk it is a measurement layer, not an execution layer. Execution needs funded capital on ≥2 venues simultaneously, and the two on-chain sports venues (SX Bet, Limitless) both prohibit US persons from transacting, while Kalshi requires a US-person account an F-1 holder cannot open. So the sports cross-venue collector is worth building *as a basis monitor*, and only as a basis monitor, unless/until the compliance picture changes. No credible public figure for realized cross-venue sports P&L exists; every "2-8% spread = profit" number traces to marketing guides (unverifiable).

## Dimension 1: Arbitrage forms (taxonomy)

**True locks (payoff offsets regardless of resolution):**
- *Single-condition rebalancing* — YES+NO on one oracle away from $1; buy both <$1 or sell both >$1, atomic split/merge to $1. $10.58M realized on Polymarket ($5.90M buying below + $4.68M selling above; arXiv:2508.03474 confirmed against 2025aft-arbitrage.pdf). Same mechanism on Limitless (every YES+NO pair fully collateralized by $1.00 USDC; docs.limitless.exchange merge-split, CONFIRMED). Maker legs pay zero fee on both. Depth-capped.
- *Neg-risk set rebalancing* — mutually-exclusive winner-take-all set; buy all legs when ask-sum<$1 or sell all when bid-sum>$1, NegRiskAdapter caps collateral at $1. Largest measured bucket, ~$29.0M (arXiv:2508.03474). Hazards that break it: augmented events with "Other" placeholder legs, second-YES oracle freeze, 50/50 $0.50 resolution. Polymarket only among executable venues; Limitless documents no neg-risk multi-outcome adapter (verify per-event).

**Locks only under oracle-identity (candidate):**
- *Cross-venue same-event crypto* — Limitless↔Polymarket BTC/ETH Up/Down, both Chainlink Data Streams. A lock only if stream/round/strike-reference (open vs prior-close)/end-timestamp/tie-rule match per pair; otherwise the two can resolve oppositely and both legs lose. No measured history (probable; verify CONFIRMED as candidate, not demonstrated lock).

**Spreads, not locks (resolution-dependent):**
- *Cross-venue sports* — settlement-mechanism divergence across SX/PM/Kalshi (probable/CONFIRMED). ~2x notional, no cross-margin.
- *Cross-venue same-event non-crypto* (PM vs Kalshi politics/econ/Fed) — ~6% of events cross-listed, execution-adjusted deviations 2-4%, ~$0.07 half-life over minutes; persists because rulebook vs UMA can resolve near-identical contracts oppositely plus semantic non-fungibility (arXiv:2601.01706 Gebele & Matthes, CONFIRMED). No credible realized P&L.
- *Deadline/containment* ("X by earlier" nested in "X by later") — lock direction is buy cheap superset/short expensive subset; in NO-space the implication reverses (desk derivation, unconfirmed — no primary literature). Not a lock: separate UMA questions split by wording drift (MSTR "sold BTC by May 31" resolved NO despite a June-1 8-K, sibling resolved YES; CONFIRMED via CoinDesk/Benzinga).
- *Combinatorial/logical* — real but negligible: $95.2K realized across ~4-5 dependent pairs vs $39.6M total (~0.24%); leaks because arbitrage-free logical pricing is #P-hard (Kroer et al. EC'16 arXiv:1606.02825, verified). Non-atomic separate questions.
- *Calendar/temporal* (semifinal→final bracket nesting) — special case of containment; no dedicated measured size; folds into the $95K bucket (unconfirmed derivation). Cleaner same-venue (one oracle) than cross-venue.
- *Dutch-book across correlated non-identical markets* — general case of combinatorial; correlation is not identity, so payoffs don't perfectly offset. Collapses into either a formal neg-risk lock or the $95K resolution-dependent bucket (probable synthesis).

**Sports grids** (correct-score/bracket/mutually-exclusive grids) are structurally neg-risk partitions: within-grid rebalancing is a same-venue lock. NBA measurement (arXiv:2605.00864, 173 games, 75M snapshots): only 7 executable single-market episodes (median 3.6s lifetime, unwinnable speed race) but 290 combinatorial episodes at median 101bps, 76.9% depth-capped to ~14.8 shares, concentrated in final live minutes. Detection is not the constraint; depth is (CONFIRMED).

## Dimension 2: Venues and execution mechanics

**Polymarket** — Polygon, pUSD/USDC, CTF split/merge via gasless relayer; batch endpoint posts 1-15 signed orders but processes them with independent per-order results (explicitly NOT all-or-nothing; docs.polymarket.com, CONFIRMED). Only atomic repair is the on-chain NegRiskAdapter convert within one event. 2026 sports taker fee: θ=0.03 (Mar) → 0.05 (Jul), max $1.25/100 shares at 50%; makers pay 0 + 15% sports-fee rebate; politics/geopolitics fee-free (marketmath.io/igamingbusiness.com/startpolymarket.com; CONFIRMED, secondary but concordant).

**Limitless** — Base (Coinbase L2), USDC native collateral, YES+NO pair = $1.00, shares $0.01-$0.99 (docs.limitless.exchange, CONFIRMED). CLOB+AMM; short-dated crypto resolves via Chainlink Data Streams. Three wallet paths: smart-wallet gas fully sponsored (~$0, USDC only), EOA/embedded pay a few cents ETH/tx (approve+trade may be two txs first use; CONFIRMED). Maker/resting orders pay ZERO fee; taker buy 0.40-3.00% / sell 0.42-1.50%, AMM flat 0.40%. Placement not anonymous-keyless: Privy Bearer-token auth + EIP-712 signing, but no KYC/manual-key gate (CONFIRMED). **ToS explicitly prohibits US persons from trading** (operated from Panama; docs.limitless.exchange ToS, CONFIRMED).

**SX Bet** — P2P on-chain betting exchange, chain ID 4162 (SX Rollup, an Arbitrum Orbit chain, ~250ms blocks), USDC, also live on Arbitrum (docs.sx.technology, CONFIRMED). **0% commission on single bets for both maker and taker; 5% only on winning-parlay profit; native chain covers all gas** — a bet costs the user ~$0 (help.sx.bet/docs.sx.bet, CONFIRMED). Reads fully keyless ("No API key or account is required to fetch market data"; full order book + Centrifugo WS, CONFIRMED). Writes: EIP-712-signed maker (POST /orders/new) and taker (POST /orders/fill/v2), settle on-chain in USDC (CONFIRMED). Mid-migration: sunsetting the SX token for a fully-gasless architecture, snapshot 15 May 2026, activation deadline 15 Aug 2026, destination chain unannounced — execution surface unstable through late 2026 (blog.sx.bet, CONFIRMED). **Not available to US persons** (SX T&Cs, CONFIRMED).

**Kalshi** — CFTC-regulated, USD. Keyless for DATA (real prices, good for basis measurement). Taker fee = 0.07·contracts·P·(1-P), peak ~1.75% at P=0.5, ~0 at extremes; maker rebate; ~0.25% flat maker fee on marquee events (kalshi.com fee schedule, CONFIRMED). Real-money trading needs a US-person brokerage account this operator (F-1, no SSN) cannot open — measurement/pricing venue only.

**Manifold** — keyless but play-money (mana); zero real-capital value; sandbox for detection/execution logic only (CONFIRMED).

**Compliance conclusion:** both on-chain sports/crypto venues (Limitless, SX Bet) bar US persons from transacting; Kalshi is account-gated for this operator. Keyless reads from all are fine. There is currently **no compliant real-money execution leg** for the operator on any cross-venue form — the desk's cross-venue work is measurement-first by necessity, not just by caution (CONFIRMED synthesis).

## Dimension 3: Atomicity and legging

Multi-leg atomicity does not exist cross-venue and only partially within one. Polymarket batch is per-order independent, not atomic; the sole atomic op is NegRiskAdapter convert scoped to one event (CONFIRMED). Cross-venue (Base/Polygon/Arbitrum, no shared collateral) is inherently non-atomic — every cross-venue form is a maker-patient play (rest a quote on one venue, hedge on fill) requiring ~2x capital held simultaneously (CONFIRMED). Limitless↔Polymarket rebalancing between chains uses Circle CCTP (burn-and-mint, low fee, ~minutes latency) — bridging latency, not gas, is the binding cross-venue execution cost (probable). MEV/frontrunning risk is low on both L2s (Base single Coinbase sequencer; SX single-sequencer Orbit + off-chain order book; no contestable public mempool), sequencer reordering a theoretical residual (probable).

## Dimension 4: External reference / offline validation

the-odds-api free tier = 500 credits/month, cost = markets × regions (1×1 = 1 credit), historical 10× — ceiling ~16 calls/day (the-odds-api.com, CONFIRMED). Too slow to be a live arb scanner (arbs close in seconds; Gebele & Matthes measured ~2-7s cross-venue windows). Its role is a **sharp-reference anchor**: use Pinnacle consensus fair odds to detect whether PM/SX/Kalshi are stale, then confirm on the keyless venue feeds (probable derivation, sound).

## Build spec for THIS desk

### A. Limitless cross-venue crypto collector (BTC/ETH Up/Down) — BUILD, priority 1 of the new work

Purpose: measure the rank-2 lock candidate. Read-only, $0, no compliance issue (reads are unrestricted).

- **Feeds:** Limitless keyless market reads on Base (CLOB depth + AMM); Polymarket keyless crypto up/down reads on Polygon. Both keyless.
- **Core requirement — spec-identity resolver:** per candidate market-pair, extract and match Chainlink stream ID, round/window boundaries, strike-reference convention (open vs prior-close), end-timestamp, and tie-rule. Emit a boolean `oracle_identical` per pair. This is the load-bearing component — the lock exists ONLY when it is true. Mismatched window/reference is not a smaller edge, it is a two-legged loss.
- **Signal:** for oracle-identical pairs, compute min-cost YES-here + NO-there; flag combined ask-sum < $1 (maker-achievable) net of zero maker fees.
- **Needs:** the two keyless read feeds; a Chainlink stream-spec parser; clock-sync across chains; a depth model (how many shares fillable as maker on each side). No keys, no capital to measure. Execution would need USDC pre-positioned on both Base and Polygon and would violate Limitless US ToS — so ship the monitor, not the executor.
- **Output:** per-pair `oracle_identical`, gross edge, maker-fillable depth, and a running distribution — the desk has NO historical P&L for this pair and must generate it.

### B. SX Bet / sports cross-venue collector — BUILD as a basis monitor only; justified but bounded

Justification: SX Bet's 0% single-bet fee is the specific fact that reopens sports cross-venue vs the fee-negative single-venue Polymarket result. The same major-league games are priced concurrently on PM, Kalshi, and SX (CONFIRMED). So the *measurement* is worth building. Execution is NOT justified for this operator: SX and sportsbooks bar/limit US arbers, Kalshi is account-gated, and settlement divergence means the spread is risk compensation, not a lock.

- **Feeds:** SX Bet keyless REST (get-sports/leagues/markets/odds/full order book) + Centrifugo WS; Polymarket keyless sports reads; Kalshi keyless data; the-odds-api free tier + Pinnacle as sharp anchor (~16 calls/day, batch to marquee games only).
- **Core requirement — settlement-diff engine:** per game-pair, diff the resolution rules (OT inclusion, DNP/void, postponement/tie) across SX (Outcome1/Outcome2/Void creator-report), PM (UMA), Kalshi (rulebook 6.3(c)). Any divergence downgrades a "locked" spread to a directional bet — tag it, don't count it as arb.
- **Signal:** per game, post-fee implied-price divergence (SX 0% leg vs PM taker/maker vs Kalshi P(1-P) curve), with fee routing baked in (place taker on SX, maker on PM/Kalshi). Cross-check against Pinnacle staleness.
- **Needs:** the four read feeds; the settlement-diff engine; a fee-routing model per venue; the-odds-api key (free tier). No capital, no writes.
- **Bound:** ship as monitor. Do not wire execution — no compliant funded leg exists, and SX's 15-Aug-2026 migration makes its write surface unstable regardless.

### C. N-venue normalized market model — BUILD, the shared substrate under A and B

Both collectors need the same abstraction: a venue-agnostic market object so PM, Kalshi, Limitless, SX (and Manifold as sandbox) are comparable.

- **Schema per market:** canonical event id; venue; chain; outcome legs with live bid/ask + depth; oracle/resolution source (Chainlink stream id | UMA | Kalshi rulebook | SX creator-report); resolution rule digest (for the settlement-diff engine); fee function (maker/taker, category-specific — PM sports θ, Kalshi P(1-P), SX 0%, Limitless taker curve); collateral/chain and bridging path; keyless-read vs execution-gated flag; US-compliance flag.
- **Matching layer:** cross-venue event linker (crypto: Chainlink spec-identity; sports: league/team/start-time + rule digest). Emit `same_underlying` and `oracle_identical` separately — they are not the same predicate and conflating them is how a spread gets mislabeled a lock.
- **Fee/depth normalizer:** every price reported net of the correct fee function and capped by fillable depth, so cross-venue sums are apples-to-apples.
- **Needs:** the per-venue read adapters (all keyless); a resolution-rule digester; a chain/bridging cost table (CCTP latency for Base↔Polygon). This is the piece to build first — A and B are thin signal layers on top of it.

## Refuted / dropped

- **REFUTED — SX Bet ~$200m lifetime volume.** Primary/press states over $500M in bets from 10,000+ users; the ~$200m figure is understated/stale (verify REFUTED). Use $500M+ if a volume figure is needed; it is not load-bearing.
- **DROPPED — placeholder/test research entries.** The `crossvenue_crypto` finding ("a", source "b"), and the `stat_arb` and `aggregation` summaries ("test claim", source "test source") are content-free test stubs (verify UNVERIFIABLE). No signal; excluded from all sections above. Note: the *substance* of cross-venue crypto is carried by the `taxonomy_complete` and `onchain_mechanics` findings, which are real and verified — only the stub entry is dropped.
- **FLAGGED weak — "SX covers 40+ soccer leagues + Olympics."** SX is a genuine multi-sport exchange covering major US/tennis/soccer, but the specific 40+/Olympics counts rest on secondary review sites, not primary docs (verify PARTLY). Treat the coverage gradient (deep marquee, thin niche) as sound; the exact counts as unconfirmed.
- **FLAGGED weak — "Kalshi is the sharp leg / most US-sports volume / tightest NFL-NBA-MLB pricing."** Directionally consistent with 2026 reporting but sourced to comparison/opinion articles, not hard primary metrics (verify PARTLY). Analytically reasonable, not proven; do not hard-code Kalshi as the sharp anchor — use Pinnacle for that.
- **FLAGGED — sportsbook arb edge "~0.5-2% after fees."** Mechanism (not risk-free; line can move before the second leg fills) CONFIRMED; the specific 0.5-2% band is a rule-of-thumb, not pinned to a primary quote (verify PARTLY). Treat as typical range.
- **FLAGGED — "cross-venue sign flips positive."** Component premises (SX 0% singles, PM/Kalshi maker rebates, independent-book divergence) all CONFIRMED, but the positive-edge conclusion is a valid analytical argument, not a measured result (verify PARTLY). No primary source demonstrates realized positive cross-venue sports edge — hence the measure-first build spec.
- **NUANCE — "exchanges do NOT limit winners."** True for stake caps on SX; Betfair does not limit but applies a Premium Charge to sustained winners (verify note). Not load-bearing.
