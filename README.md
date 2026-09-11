# Paying for Information

Research candidate 0.1.1. Local implementation and evidence are available; this is not an activated Apex competition. See `HANDOFF.md` for the admission status.

Decide when an observation is worth buying, how precise it should be, and how to quote after seeing it. You compete for flow against a fixed maker that adapts to public news and its inventory.

## The market

There is one binary claim. Quotes and balances use integer ticks: 10,000 ticks equal one currency unit. Each account starts with 100 currency units, no position, a position limit of ±20 claims, and at most four claims quoted on each side. Both terminal outcomes must remain fully collateralized. A fill that would exceed account limits is unavailable. Quotes expire every tick.

The hidden fair probability starts between 3,500 and 6,500 ticks and follows a bounded symmetric random walk. A step's magnitude is reduced symmetrically near a boundary, keeping the process a martingale. The usual step size varies by episode; 8% of steps are four times as large. Public news updates every fourth tick with uniform bounded noise. The episode publishes its usual volatility and public-noise bound.

1. Receive public news, your account, prior fills and prior quotes.
2. Choose one information tier for each episode.
3. Pay the quoted fee and receive the purchased observation.
4. Replace your bid and ask.
5. Fair value moves; an informed taker trades first, followed by retail.
6. Repeat for 24 ticks.

This is a discrete quote-driven market. Makers only supply liquidity to external takers; they do not trade directly with one another. Informed takers know the current fair value and take stale quotes with at least five ticks of edge. Each episode has three to five retail orders per tick, each for one claim, with equally likely buy/sell direction and a reservation price 250–1,100 ticks above/below fair value. Retail trades only if an eligible quote meets that price. Better prices receive flow first; equal prices use priority rotating by tick and episode, balanced within each condition stratum. These simplified order-flow rules are part of the game.

## Score

For a maker purchase at price `q`, fill edge is `fair_at_fill − q`; for a maker sale, it is `q − fair_at_fill`. Sum this edge over all fills, then subtract information fees. This is conditional expected trading surplus. It removes subsequent price-path and binary-settlement luck from ranking.

The raw score is `max(0, total signed edge / (N × 10000))`. Apply the floor once, after summing every episode. Buying an observation subtracts its fee from edge and cash. Any unavailable or invalid player response forfeits the evaluation, for a raw score of zero.

The report separately gives cash plus inventory valued at terminal fair probability, less initial capital. This terminal marked profit is a diagnostic, not the ranking score. No terminal Bernoulli draw is used. All balances, fees and edge are calculated in integer ticks before aggregation. Clock time affects request deadlines only.

## Submission contract

Submit a single Python file, at most 1 MiB, with `reset(config)` and `act(observation)`. The runtime provides Python 3.12 and its standard library. The example is `player/submission.py`. The server invokes `reset` once per evaluation. State can be maintained by episode ID and discarded after the last tick. Training takes place outside the evaluation.

The gym_v1 observation has `phase` and `episodes`. The response is a list of exactly the same length, in the same order. An episode includes:

| Fields | Meaning |
|---|---|
| `id`, `tick`, `remaining` | Episode identity and simulated time |
| `public`, `public_age`, `public_noise`, `volatility` | Public observation, its age, its uniform error bound, usual process step |
| `signal`, `tier`, `costs`, `signal_noise` | Purchased observation or null, its tier, current prices and noise bounds |
| `cash`, `inventory`, `position_limit`, `max_size` | Account state and limits |
| `fills` | Your prior tick's fills: side +1 for buying, −1 for selling, price, quantity |
| `book` | Prior quotes and remaining quantities, by seat |

For `phase="buy"`, return integers from 0 to 3. Tier 0 costs nothing and returns no observation. Tiers 1, 2 and 3 have uniform error bounds 300, 100 and 25 ticks. Their base fees are 20, 65 and 210 ticks, multiplied by the episode's published cost multiplier (1 or 6). A signal observes fair value before the subsequent market move. Only one observation is available per tick. The duel does not send buy-phase requests.

For `phase="quote"`, return either null (sit out this tick) or an object such as:

```json
{"bid": 4700, "ask": 5300, "bid_size": 4, "ask_size": 4}
```

Prices and sizes must be integers. `0 ≤ bid < ask ≤ 10000`; each size is between 0 and 4. A zero size disables that side. Responses must use these four keys and no additional keys. Returning a valid null quote differs from a missing or malformed response. An unaffordable information purchase is an invalid action.

The proposed evaluation uses **32,768 episodes**, batches of up to **512**, and a **100 ms deadline for the entire batch response**. All episodes have 24 ticks. The platform-owned input can select a 256-episode smoke test; miners do not choose evaluation size. One CPU and 512 MiB are allocated per sandbox.

## Try it locally

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
docker build --platform linux/amd64 -f player/Dockerfile -t pfi-player:dev .
docker build --platform linux/amd64 -f referee/Dockerfile -t pfi-referee:dev .
python3 scripts/docker_match.py --submission player/submission.py --episodes 256 --output evidence/my-run
python3 scripts/read_records.py evidence/my-run/history/episodes.jsonl.gz
```

Choose a new output directory for each run. The local harness uses separate player containers, a referee container and internal networks. Its behavior supplements `apex-dev preflight`; the current toolkit’s `apex-dev run` prints a plan but does not execute the match. The replay reader checks each episode’s accounting and the aggregate score.

`input.schema.json` is generated from `referee/config.py` using Pydantic. The scoring containers have no pip dependencies. The vendored `gym_v1` is unchanged from the Apex hello-world template; see `PROVENANCE.json` for its source and the shared engine hash.
