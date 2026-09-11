# Competition onboarding manifest: paying_for_information

**Private review candidate 0.1.1 — not released or activated.** This manifest is filled with measured results and explicit outstanding decisions. Send it with the draft in `ONBOARDING_ISSUE.md` after completing the authorized private release. Do not describe placeholder refs as released images.

## 1. Goal statement and alignment plan

A maker buys observations when their trading value exceeds their price, varies information quality with uncertainty and exposure, and earns positive expected trading surplus across market conditions under fixed capital and position limits.

Alignment checks:

- Compare adaptive buying against never, periodic and always-precise buying with matched quoting; inspect purchases by price, uncertainty, inventory and remaining time.
- Inspect signed conditional edge, terminal marked profit, fees, volume, inventory and each condition stratum. Investigate sustained disagreement between ranking and terminal marked profit.
- Run the out-of-band stress audit and inspect top artifacts after each reveal. Review every round's top three entries and rerun the sizing/rank audit whenever a materially stronger policy appears. No inference of live-market deployability follows from this simulation alone.

The ranking score uses trade-time conditional expected surplus; terminal marked profit is unranked. This removes later price-path and Bernoulli noise while retaining adverse selection and information costs. The claim is marked at terminal probability; no random binary payout is added. This is a design choice requiring economic review with Apex.

## 2. Deliverables

| Item | Location | Status |
|---|---|---|
| Repository and release tag | [https://github.com/sbloomberg1/paying-for-information](https://github.com/sbloomberg1/paying-for-information); template Git history preserved | Private repository created; released tag pending workflow |
| Competition spec | `spec.yaml` | Schema/input preflight passes; refs and digests remain explicit placeholders |
| Player image | `evidence/player-build.json`, `evidence/docker-full/run.json` | Built locally; unsigned, not published |
| Referee image | `evidence/referee-build.json`, `evidence/docker-full/run.json` | Built locally; unsigned, not published |
| Layer 2 screen | None proposed | Rationale in §5.15; Apex review required |
| Round generation | Platform seed plus referee-owned configuration | No separate `generate_round` needed |
| Overfit control | `benchmarks/overfit.py`; solo `evidence/solo-20-seeds.json` in sibling primary repo | Implemented; memorizes public training seed 0 |
| Signing workflow | `.github/workflows/release.yml` | Prepared, immutable action pins; not executed |
| Input schema and fixtures | `referee/config.py`, `input.schema.json`, `fixtures/` | Generated and validated |
| Positive reference | `player/submission.py` | Full-container score: 1.280184 |
| Adversarial set | `adversarial/`, `evidence/adversarial-results.json` | Ten fixtures exercised through containers |
| Records and reader | `/data/history/episodes.jsonl.gz`, `scripts/read_records.py` | 32,768 full-run episodes reconstructed; 83.90 MB compressed |
| Miner README | `README.md` | Complete for candidate rules |
| End-to-end evidence | `evidence/docker-full/`, `evidence/REPORT.md` | Local run complete; stage pending |

Pins: `PROVENANCE.json` lists template/builder commits, every Python source hash, and the shared market-engine hash. Python base: `python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`, built for linux/amd64. No pip dependencies in either runtime image. Model revisions and dataset hashes: n/a, no external model/data; scenarios are generated procedurally. Development dependencies are exact versions in `requirements-dev.txt`. The final spec must use the pushed image digests and verified signing identity from the release workflow, not local IDs or zeros.

## 3. Proposed operations

| Parameter | Proposal and reason |
|---|---|
| process_type | cpu; simulator and batched policies need no GPU |
| kind | solo; absolute edge supports the platform’s takeover rule |
| duel | n/a |
| round_length_in_days | 1; frequent adaptation without changing the evaluation distribution |
| submission_reveal_days | 2; permit iteration while delaying direct copying |
| lower_is_better | false |
| baseline_raw_score / baseline_score | 0 / 0; no arbitrary positive score offset |
| resources per sandbox | 1 CPU, 512 MiB, 0 GPUs; full local run completed at these limits |
| evaluate.timeout_s / referee.timeout_s | 1200 / 1200; derived budget and headroom below |
| per-request deadline | 100 ms for the whole batch of up to 512; below toolkit's usual per-move norm, justified by batching and measured runtime; sophisticated policy headroom needs stage review |
| submission fee | Propose approximately USD 1; Macrocosmos decides |
| incentive weight | Propose 0.03 for the primary research competition; Macrocosmos decides |

Declared floor is zero. The positive reference is a test artifact, not a declared nonzero floor. The builder's simultaneous “positive published baseline” and “baseline copy cannot lead” requirements need a bootstrap policy decision; see §5.4. Do not silently substitute a hidden score offset or contradictory floor.

## 4. Round variation and sizing

Every episode belongs to one of eight equally sized strata: usual volatility (55 or 170 ticks, with ±10 jitter), public-noise bound (180 or 650, with ±25 jitter), and information fee multiplier (1 or 6). Retail arrival count varies from three to five per episode. A private per-episode RNG is derived from the platform master seed and episode index with SHA-256. Initial fair value, path, jump signs, signal errors, retail directions/markups and the jittered parameters change with the seed. A fixed eight-stratum mixture keeps difficulty approximately stationary. Choosing only new price paths without changing condition parameters is not the entire rotation mechanism.

The usual live ranges exclude the stress audit's doubled volatility, public noise and information prices. The audit has no input-schema switch available to a submission. Published historical seeds are practice data, never live seeds. No external round generator is required, provided Apex keeps a sufficiently unpredictable master seed private to the referee.

Measured N: **32,768** episodes, 24 ticks each, batch 512. Twenty master seeds, with live condition generation. Reference mean **1.280819034**; sample σ_round **0.002668041**. A 1% margin at that mean is 0.012808190; one quarter is 0.003202048.

**Measured quarter-margin rule: PASS.** The smaller N=8,192 study failed this rule, and the candidate was increased to N=32,768. The first 20-seed study ranks adaptive > periodic > never > always-precise in every seed (the separate overfit control wins only its memorized seed). The overfit control scores 1.491166 on training seed 0 and zero on all 19 unseen seeds. Stress means: adaptive 0.879605, periodic 0.566663, never 0.216842, always-precise 0. Reference round values and per-stratum diagnostics are in the JSON evidence.

The baseline never buys the highest precision tier. Verify whether a stronger policy uses it profitably; this is a useful tuning question, not evidence that all three paid tiers are equally valuable. The seed study estimates variance for these policies, not every possible future champion. Paired challenger/incumbent studies and fresh-seed confirmation remain part of stage qualification.

Full-size reference evaluation: **84.08 seconds** in the referee; **84.91 seconds** including local harness lifecycle. One local full-size run and 20 trusted-policy simulations are supplied; these are not twenty separate stage rounds.

Timeout budget:

- 64 batches × 24 ticks × 2 phases × 1 player = **3,072 action calls**.
- At 0.1 seconds each: **307.2 seconds**. A player that actually exceeds a deadline forfeits and receives no further calls; this budget covers one that stays just inside every deadline.
- Readiness and reset allowance: **17 seconds** (one player).
- CPU scoring, JSON processing and record-write reserve: **240 seconds**, approximately 2.9 times the entire measured referee runtime. This is a conservative planning allowance, not a measured maximum on Apex storage/hardware; verify it with a dense-response run on stage.
- Planning worst case: **17 + 307.2 + 240 = 564.2 seconds**.
- Proposed timeout: **1,200 seconds**, headroom **2.13×**. Fits the skill's 20-minute ceiling. Remaining margin: 635.8 seconds.

The cardinality and per-response size are bounded. Host outages and blocked filesystem I/O are operational failures outside this planning bound. No score uses wall time. Records are best effort and a record-write failure does not change arithmetic, as tested.

## 5. Threat-model questionnaire — private review

1. **Miner-visible surface.** Round input schema: `episodes`, `batch_size`, `deadline_ms`, all platform-controlled. Reset wrapper passes constant match ID `market`, player index 0 and seed 0, plus mode, horizon, price scale, batch size and deadline. Observations contain ID/time, public signal/age/noise, usual volatility, signal/tier/cost schedule, account limits/cash/inventory, own previous fills and previous quotes. Purchased signals are the intentionally bought information. No future prices, terminal probability, master/per-task seed or event tape enters the player. The referee-only seed env is not copied into the player container.
2. **Seed leverage.** The public engine plus the true master seed would regenerate all scenarios. Privacy and entropy of the platform seed are therefore essential. SHA-256 does not increase the entropy of a weak seed. Apex must confirm the live seed is private and impractical to enumerate (prefer at least 128 unpredictable bits), and that neither logs nor job metadata expose it before/during a run. Do not reuse the published test seeds in production.
3. **Degenerate submissions.** Constant narrow quotes, random legal quotes, all-zero/wrong-shaped responses, empty results and no trading were exercised. All ten fixtures score zero after signed aggregation or whole-evaluation forfeit. No ad hoc gate excludes a legitimate simple profitable strategy. An idle policy ties other zero scores and cannot take a positive incumbent.
4. **Baseline resubmission.** An exact copy earns the same positive raw score as the reference. It cannot beat an identical rescored incumbent by 1%, but it could become the first leader against the declared zero floor. That is an unresolved contradiction in the builder's written requirements, not something this code conceals. Apex should specify reference seeding/eligibility or an explicit initial qualification policy. Do not mark this check passed without that decision.
5. **Metric gaming.** Probes covered narrow constant quotes, random prices, never trading, excessive information spending, late failure after profitable ticks, message abuse and inventory/cash accounting. Signed episode values are summed before the solo floor; negative tasks cannot be dropped. Marked profit is compared with conditional edge to expose directional-risk divergence. This was a bounded engineering probe, not a completed independent day-long red-team review. Economic strategies, cross-episode learning, simulator specialization and coordinated entries remain review areas.
6. **Malicious responses.** `transport.py` accepts one bounded UTF-8 JSON object, rejects duplicate keys, nonfinite JSON constants and excessive nesting, and imposes a total response deadline. `validate_action` checks exact batch length, action structure, key set, integer types excluding booleans, price order and ranges. A bad response forfeits the entire evaluation/game for that player. Invalid raw payloads are not reflected in metadata.
7. **Profitable failure.** Missing, unhealthy, exception, timeout and late-invalid fixtures forfeit the entire player result. No accrued positive credit survives; the result is zero, equal to the zero floor rather than strictly less than every honest losing strategy. Unexpected referee bugs are not converted into successful scored results; they propagate for platform attribution. There is no retry that chooses a more favorable market path. Remaining valid duel players continue with the failed player inactive, which can still affect their field and is part of the coordinated-entry risk.
8. **Aggregation integrity.** N is platform-controlled and fixed; denominator never shrinks. The solo floor applies once after summing all signed episode edges. No per-episode clipping or arbitrary positive offset. Quote inventory/capital/size bounds limit a valid tick to at most eight fills per maker; edge magnitude is at most eight currency units per tick before fees. A 24-tick episode is bounded well above −1000 even under the stress fee schedule. Early forfeits never retain partial eligibility. Per-stratum diagnostics reveal concentration.
9. **Adversarial loop results.** All ten fixtures were evaluated as real mounted submissions in isolated containers at 256 episodes. See table below and machine-readable results; these fixtures are shared between the competitions. Full-size reference runs separately demonstrate scale.
10. **Defense hygiene.** Detailed threat rationale is confined to this private manifest. Miner documentation states ordinary market and response rules, not attack explanations. Production error strings are generic; result metadata contains scoring/account diagnostics. Test fixtures and this manifest should be reviewed before choosing public repository visibility. This is a source review, not a claim of an external information-flow audit.
11. **Copy plus epsilon.** The platform’s 1% improvement rule is expected to reject trivial score changes when incumbent and challenger share the current evaluation; it does not prove independent work. Verify the exact platform bootstrap and incumbent-rescoring contract.
12. **Cross-round leakage.** A prior task record reveals that task, not the private seeds. Seeds and condition jitter change; the overfit control collapses on unseen worlds. Parameter distributions are intentionally learnable. The record archive must be released after evaluation; exposing it live would reveal current truth. A miner can retain its own public/paid observations as part of legitimate policy state.
13. **Error-message hygiene.** Normal terminal reasons are `completed` or `forfeit`; transport/action failures use generic unavailability/invalid-action text. No secret seed, URL, source exception or hidden state is echoed to a player by the scorer. Player-generated logs live in that player's sandbox and are not trusted scoring inputs.
14. **Referee state.** New episode state is allocated per evaluation. No cross-game cache or submission-controlled pathname. Conditions derive deterministically from the seed and index. All scored terms use integer prices, quantities, costs and simulated ticks. Elapsed seconds are an unranked diagnostic; deadlines alone depend on a clock. Native and container accounting are deterministic for a fixed input and policy.
15. **Code execution.** Python permits filtering, dynamic inventory rules, search and learned approximations; ONNX/TorchScript alone would exclude useful methods. The spec adds `socket` and `subprocess` to generic AST screening. No Layer 2 image is proposed because there is no untrusted model parser or data deserializer beyond the constrained JSON interface. Generic screening is not a security boundary; container separation, no egress and CPU/memory/PID limits remain required. Apex decides whether another screen is needed.
16. **Player-image hygiene.** Only `launch.py` and unchanged vendored gym_v1 enter the player image. Submission code is mounted at runtime. Engine, conditions, future paths, seed and scorer are absent. No Docker socket or referee filesystem is mounted in a player. The local duel harness uses a separate internal network for each player, with the referee attached to all; it prevents player-to-player traffic. Apex must confirm equivalent network isolation on stage.
17. **Diagnostics payload.** Result metadata contains signed edge, marked profit, information expenditure, volume, purchase counts, stratum aggregates, active flags and elapsed time. Post-evaluation records intentionally include per-tick fair values to make fill-edge arithmetic reconstructible. They therefore correlate with that completed task’s hidden truth, by design. This conflicts with a literal reading of “no diagnostics correlate with hidden ground truth”; the safe distinction is completed-task disclosure versus future/live leakage. No seed is disclosed. Do not stream these records during play.
18. **Evaluation records.** Versioned gzip JSONL in `/data/history/episodes.jsonl.gz`, one record per episode plus a summary. Each episode includes realized conditions, buy/quote observations, chosen actions, account fills, charged fees, eligibility, terminal state and arithmetic. Summary includes phase/tick of faults and fixed-denominator aggregation. Malformed raw payloads are omitted; their failure location is recorded. Neither master nor per-task RNG seeds are present. Records hold only one batch in memory and write failures leave scores unchanged. `read_records.py` reconstructed all 32,768 full-run episodes, 83.90 MB compressed. Confirm Apex archives `history/` and that this volume fits its artifact policy. As with any task transcript, realized conditions are present, not RNG state or seeds.

| Submission | Candidate player's score | Outcome |
|---|---:|---|
| constant.py | 0.000000 | completed |
| empty.py | 0.000000 | forfeit |
| exception.py | 0.000000 | forfeit |
| late_failure.py | 0.000000 | forfeit |
| nan.py | 0.000000 | forfeit |
| no_trade.py | 0.000000 | completed |
| oversized.py | 0.000000 | forfeit |
| random.py | 0.000000 | completed |
| timeout.py | 0.000000 | forfeit |
| zero.py | 0.000000 | forfeit |

## 6. GPU justification

Not applicable: both images are CPU-only. No GPU access is requested.

## 7. Admission sequence and outstanding decisions

1. Owner is `sbloomberg1`; private repositories and their release publishing are authorized. No Apex onboarding issue or message has been sent. The signed release workflow is the next step.
2. Apex reviews score/goal alignment, the baseline-copy/bootstrap contradiction, private seed entropy, network isolation, record archiving/size and the 100 ms batch budget. The duel additionally needs four-player advancement, signed-score/forfeit handling, close-match rules and coordinated-entry review.
3. Resolve those decisions; run fresh-seed and stage-hardware checks. The supplied results are sufficient for a concrete design review, not a claim that security/admission review has already occurred.
4. Push an authorized version tag; the prepared release workflow builds, pushes, signs and verifies real image digests, then creates the final spec artifact. This workflow has not yet been exercised in GitHub Actions. Replace the development spec with the generated release spec and rerun toolkit preflight/triage.
5. Submit `ONBOARDING_ISSUE.md` plus this manifest and evidence with explicit authorization. Macrocosmos reviews, copies the final spec to its private registry, runs the baseline on stage and determines fee, incentive weight and activation timing. Updates use a new version and signatures.
