# Release procedure

Local candidate only. The images have not been signed or pushed, and no onboarding issue has been sent. Private publishing under `sbloomberg1` is authorized. Resolve admission questions in HANDOFF.md before requesting activation.

1. Publish this repository while retaining the template Git history. Add the chosen remote as `origin`; keep `template-upstream` for provenance. Keep the private threat-model review within its agreed audience.
2. Confirm source/evidence pins in PROVENANCE.json, rerun pytest and toolkit preflight, and test the full-size fixture on the target hardware. Review economic and tournament issues; do not treat a structural preflight as admission approval.
3. Create the intended version tag and push it. `.github/workflows/release.yml` builds linux/amd64 player/referee images from the pinned Python base, pushes them to `ghcr.io/<owner>/<repository>-player` and `-referee`, signs by digest using GitHub OIDC, verifies signatures, and emits `signed-release-spec`.
4. Download that workflow artifact. Its `spec.yaml` and `input.schema.json` contain the actual registry digests and exact signing identity. Replace the development spec, rerun preflight and onboarding triage, and keep signature verification output with the handoff. No local build ID should be described as a signed registry release.
5. With authorization to contact Macrocosmos, submit the draft ONBOARDING_ISSUE.md with the filled HANDOFF.md and released artifacts. The registry is private; activation goes through Macrocosmos's onboarding issue, security review and stage round.

The workflow is prepared but has not yet run in GitHub Actions. Registry permissions, package visibility and access for Macrocosmos must be checked on the chosen owner. All future changes need a new immutable competition version and signed images.
