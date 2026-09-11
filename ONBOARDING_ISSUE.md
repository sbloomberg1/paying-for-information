# Draft: [onboarding] paying_for_information v0.1.0

**Prepared for review; do not file as an activation request until release fields and open decisions are resolved.**

## What is the competition?

Miners submit Python market-making strategies that choose whether to buy a noisy observation of fair value, choose its precision, and then quote. Raw score is mean conditional fill edge minus information expenditure, floored once at zero after all signed episode contributions. A fixed adaptive reference maker competes for retail flow. Success means buying information selectively and earning positive edge across changing conditions, with terminal marked profit checked separately.

This is the primary competition in a paired market-simulation project. We used the builder skill at commit `5a0be85a5975f0948a2d4878597a820c636656e2` and retained the hello-world example's repository history.

## HANDOFF.md

Attach `HANDOFF.md` and `evidence/REPORT.md`, or link them at the released tag when available. The private questionnaire is complete with explicit limitations and outstanding decisions.

## Evaluation time budget vs. timeouts

Proposed worst-case planning budget: 17s startup/reset + 3,072 action calls × 0.1s + 240s scoring/record-write reserve = 564.2s. Referee and evaluation timeouts are both 1,200s; approximately 2.13× headroom. Local full-size reference run: 83.54s in the referee at one CPU / 512 MiB. Stage hardware and dense-record write allowance still require verification; no unflagged over-budget claim is made.

## Release fields

| Form field | Value |
|---|---|
| Competition id | `paying_for_information` |
| Spec version | `0.1.0` candidate |
| Competition repo URL | https://github.com/sbloomberg1/paying-for-information (private) |
| Released git tag | Pending; intended `v0.1.0` after design review |
| Player image ref | `ghcr.io/sbloomberg1/paying-for-information-player` |
| Player image digest | Pending signed registry release; local build metadata supplied separately |
| Referee image digest | Pending signed registry release; local build metadata supplied separately |
| Target environment | Stage first |
| spec.yaml | Attach generated final spec from release workflow; current `spec.yaml` is a development draft |

## Pre-submission checks

- [x] `apex-dev preflight --spec ./spec.yaml --input fixtures/input.json` passes structural and input validation.
- [x] Custom local container harness produced a valid `result.json` and replay archive. The pinned toolkit's `apex-dev run` itself does not execute the match.
- [ ] Image keyless-signed by the release workflow on the released tag.
- [ ] Image pushed and pullable by its registry digest.
- [ ] Apex admission decisions in `HANDOFF.md` resolved, with stage validation scheduled.

Local tests: 26 passed. Full replay accounting: 32,768 episodes verified. Ten adversarial submission fixtures exercised through the complete player/referee loop. The 20-seed variance target passes at N=32,768.

## Decisions requested from Apex

- Confirm baseline bootstrap/eligibility: a published positive reference can otherwise lead against a declared zero floor.
- Confirm referee-only, high-entropy seeds; network isolation; post-evaluation `history/` archiving and record-size allowance.
- Review trade-time conditional edge as the ranking score and terminal marked profit as a diagnostic.
- Review the 100 ms deadline for the whole batch, CPU allowance and the stage timeout budget.
