# Paying for Information — design candidate 0.1.0

Status: research and implementation candidate; not approved or released.

## Success

Produce a market-making policy that buys observations when their expected trading value exceeds their cost, adapts the purchase to uncertainty and inventory, and earns positive net edge across changing conditions under a fixed capital budget. Winning should reflect selective information use together with good quoting.

Check that adaptive purchases beat no-purchase, periodic-purchase and always-precise policies under matched quoting; inspect performance by cost and volatility regime; inspect inventory and terminal wealth as unranked diagnostics. Review the leading artifact against these checks after every round.

## Proposed game

A bounded latent probability evolves as a martingale. A binary claim is marked at terminal fair probability for diagnostics; ranking sums each fill’s conditional expected surplus at its trade-time fair value, removing later settlement noise. At each discrete tick the maker receives public noisy observations and its own market history, may purchase one of three signal-quality tiers, receives the signal, then replaces its bid and ask. The probability moves after quoting. An informed taker consumes stale quotes before price-sensitive retail arrives. One fixed adaptive reference maker competes for the same retail flow. Capital, inventory and quote size are bounded. All timing is simulated.

Players submit Python strategy code through the standard Apex gym_v1 interface. Batches contain independent episodes; information choice and quoting are separate calls. Code permits filtering, search and explicit policies as well as learned approximations. Models alone would unnecessarily restrict these methods.

The tentative raw score is max(0, mean(conditional fill edge minus information fees per episode)) in currency units. Signed episode results are aggregated before the single zero floor; no positive shift is added. Losses and information expenditure therefore count fully. Any invalid response or player failure forfeits the evaluation. Zero scores do not lead; a working positive reference is required. This deliberately rewards positive expected edge, not return on capital. Capital is identical for all entries. Final parameters depend on measured headroom and variance.

Round conditions vary along volatility, public-signal quality, information price and retail demand, within a fixed stratified mixture. All environment randomness derives from the private referee round seed. Player resets receive a constant public policy seed. Conditions and results are recorded after the round; generator seeds are excluded. Separate stress conditions are reserved for an out-of-band robustness audit.

## Evidence required

At least 20 seeds for the reference policies; evaluate the mean score's round standard deviation against 0.25% of its typical positive score; check rank consistency, an over-fitted policy, and the worst per-call timeout budget. Demonstrate deterministic replay, correct accounting, fault outcomes and score-neutral record failures. Exercise separate player and referee containers with internet disabled and resource limits.

## Initial operating proposal

CPU only, 1 CPU / 512 MiB per sandbox; one-day rounds; two-day reveal delay. Fee and emission weight remain Apex decisions. A shared engine also supports Competing Market Makers, whose ranking and release are separate.
