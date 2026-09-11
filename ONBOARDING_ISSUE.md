# Draft: [onboarding] paying_for_information v0.1.1

**Ready to request design and stage review once access is arranged. Open admission decisions are listed below; this draft has not been sent.**

## What is the competition?

Miners submit Python market-making strategies that choose whether to buy a noisy observation of fair value, choose its precision, and then quote. Raw score is mean conditional fill edge minus information expenditure, floored once at zero after all signed episode contributions. A fixed adaptive reference maker competes for retail flow. Success means buying information selectively and earning positive edge across changing conditions, with terminal marked profit checked separately.

This is the primary competition in a paired market-simulation project. We used the builder skill at commit `5a0be85a5975f0948a2d4878597a820c636656e2` and retained the hello-world example's repository history.

## HANDOFF.md

Attach [HANDOFF.md](https://github.com/sbloomberg1/paying-for-information/releases/download/v0.1.1/HANDOFF.md) and the [complete review package](https://github.com/sbloomberg1/paying-for-information/releases/download/v0.1.1/review-package.tar.gz). The private questionnaire is complete with explicit limitations and outstanding decisions. Use these finalized assets rather than the pre-build handoff at the source tag.

## Evaluation time budget vs. timeouts

Proposed worst-case planning budget: 17s startup/reset + 3,072 action calls × 0.1s + 240s scoring/record-write reserve = 564.2s. Referee and evaluation timeouts are both 1,200s; approximately 2.13× headroom. Local full-size reference run: 84.08s in the referee; signed released-image run on GitHub: 125.27s (126.72s full loop). Both used one CPU / 512 MiB. Stage hardware and dense-record write allowance still require verification; no unflagged over-budget claim is made.

## Release fields

| Form field | Value |
|---|---|
| Competition id | `paying_for_information` |
| Spec version | `0.1.1` private prerelease |
| Competition repo URL | https://github.com/sbloomberg1/paying-for-information (private) |
| Released git tag | [`v0.1.1`](https://github.com/sbloomberg1/paying-for-information/releases/tag/v0.1.1) |
| Player image ref | `ghcr.io/sbloomberg1/paying-for-information-player` |
| Player image digest | `sha256:2d1a5f65e767d80eb38520cc2bdfd040dc124543226d467e8bb01f17856f73d2` |
| Referee image ref | `ghcr.io/sbloomberg1/paying-for-information-referee` |
| Referee image digest | `sha256:4bc73897dd1d10354bc1bf4bd11f350722faa5b897e7834178af3f9395514250` |
| Target environment | Stage first |
| spec.yaml | [Final release asset](https://github.com/sbloomberg1/paying-for-information/releases/download/v0.1.1/spec.yaml), with [input schema](https://github.com/sbloomberg1/paying-for-information/releases/download/v0.1.1/input.schema.json) |

Signing identity: `https://github.com/sbloomberg1/paying-for-information/.github/workflows/release.yml@refs/tags/v0.1.1`; issuer: `https://token.actions.githubusercontent.com`. [Successful workflow](https://github.com/sbloomberg1/paying-for-information/actions/runs/34649869268); exact verification output and replay evidence are included in the release package.

## Pre-submission checks

- [x] `apex-dev preflight --spec ./spec.yaml --input fixtures/input.json` passes structural and input validation.
- [x] Custom local container harness produced a valid `result.json` and replay archive. The pinned toolkit's `apex-dev run` itself does not execute the match.
- [x] Both images keyless-signed and signatures verified on the released tag.
- [x] Both images pushed, pulled by registry digest and evaluated by the authenticated release workflow. Apex pull access still needs to be arranged.
- [x] Final spec passes toolkit onboarding triage as well as preflight.
- [ ] Apex admission decisions in `HANDOFF.md` resolved, with stage validation scheduled.

Local tests: 26 passed. Full replay accounting: 32,768 episodes verified. Ten adversarial submission fixtures exercised through the complete player/referee loop. The 20-seed variance target passes at N=32,768.

## Decisions requested from Apex

- Confirm baseline bootstrap/eligibility: a published positive reference can otherwise lead against a declared zero floor.
- Confirm referee-only, high-entropy seeds; network isolation; post-evaluation `history/` archiving and record-size allowance.
- Review trade-time conditional edge as the ranking score and terminal marked profit as a diagnostic.
- Review the 100 ms deadline for the whole batch, CPU allowance and the stage timeout budget.
