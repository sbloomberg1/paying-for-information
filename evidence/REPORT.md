# Evaluation evidence — paying-for-information

Candidate 0.1.0, measured locally on 11 September 2026. This is a research qualification report, not a stage or production approval.

| Check | Result |
|---|---|
| Full configured evaluation | 32,768 episodes, 84.08 seconds in referee |
| Isolated containers | Two containers; one CPU / 512 MiB each; linux/amd64; internal referee-to-player links |
| Reference raw score(s) | 1.280184 |
| Tests | 26 passed |
| Replay accounting | 32,768 episodes reconstructed exactly |
| Full replay size | 83.90 MB compressed |
| Master seeds | 20 |
| Reference mean | 1.280819034 |
| Sample standard deviation | 0.002668041 |
| Quarter of a 1% margin | 0.003202048 |
| Release / stage approval | Pending |

The larger evaluation passes the builder’s measured variance rule: sample standard deviation is below one quarter of the 1% takeover margin. This is an estimate from 20 seeds, not a guarantee about future champions. Recheck stronger candidates and paired challenger/incumbent differences before activation. At N=8,192 the same test failed (SD 0.004329 versus target 0.003195), motivating the larger batch.

## Information-use ablation

Twenty identical master seeds, N=8,192 per policy, the first four policies share quoting code and differ only in information choice. The overfit row is a separate memorization control. Scores are currency units per episode.

| Policy | Mean raw score | Mean signed edge | Mean fees |
|---|---:|---:|---:|
| adaptive | 1.277990 | 1.277990 | 0.129439 |
| never | 0.842587 | 0.842587 | 0.000000 |
| periodic | 1.034284 | 1.034284 | 0.136500 |
| always | 0.000000 | -0.218552 | 1.764000 |
| overfit | 0.074558 | -1.315509 | 0.000000 |

Adaptive information use beats never and periodic buying in all 20 measured seeds. The always-precise policy has negative signed edge and is floored to zero. The adaptive reference chooses no purchase, coarse, or medium precision; it never chooses the highest tier. That leaves an open design question: is the highest tier useful to a stronger policy, or should its price be retuned? No claim of optimality is made.

The overfit reference memorizes the latent paths from test seed 0: 1.491166 on that seed, and raw score zero on all 19 unseen test seeds. This is a deliberate memorization control, not a candidate winner. `benchmarks/overfit.py` reconstructs only that public training world.

Stress audit (five seeds, N=8,192, double usual volatility, public noise and information fees): adaptive 0.879605, never 0.216842, periodic 0.566663, always-precise 0. The public-regime mixture is held constant for ranking; these condition ranges are excluded from live evaluation inputs and used only for the robustness audit.

## Files and reproduction

- `summary.json`: machine-readable qualification summary.
- `docker-full/run.json`: images, resource limits, timing and full result. Image IDs/build digests are local evidence, not signed registry releases.
- `record-verification.json` and `docker-full/history/episodes.jsonl.gz`: accounting verification and records.
- `tests.txt`, `preflight.txt`, `adversarial-results.json`: test and fixture outcomes.
- `../scripts/experiment.py`: trusted-reference experiment runner. Untrusted submissions belong in `docker_match.py`.
- `../scripts/read_records.py`: replay and score arithmetic verifier.

The numerical reference experiments run trusted strategies in the host process; isolated full-size container runs separately confirm the runtime. Only the recorded configurations and reference policies were timed. The worst-case budget is derived in HANDOFF.md; it has not been validated on Apex stage hardware.
