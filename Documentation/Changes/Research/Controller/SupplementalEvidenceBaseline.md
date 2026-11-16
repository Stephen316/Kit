# Supplemental evidence baseline reservation

## Decision and scope

The A02 owner, `jdharcourt`, reserved `f8a4dc7686dece8d44719b12721105a63864a365` at 2026-11-16 19:06:32 UTC for supplemental preflight and subsequent frozen-rule adjudication.
The [coordination record](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6926240900) records the explicit reservation and the private evidence custody split.
This is a new reservation after existing discovery observations.
It does not assert that those observations had an earlier frozen baseline.

Use this exact commit as `frozen_rules_revision` when the owning operator seals the coordinated [supplemental manifest](PairedEvidenceManifest.md).
Select `target_revision` separately to match the actual clean checkout used for that run.
Select `capture_revision` separately to retain the original measured archives.
Record the independently supplied input, verifier and normalized-report pins.
The manifest must retain both applications for each selected P01–P04 recipe.

Later reader changes do not silently move this baseline.
A replacement baseline requires a new explicit owner decision before its evaluation.
Record a failed or incomplete evaluation against its actual baseline instead of changing the pin to accept its result.

## Limits and verification evidence

The accepted GitHub head and local commit identity were verified before reservation.
No coordinated manifest was sealed and no qualification evaluation was executed by this decision.
The public principal and five-record P02 receipt chains remain supporting same-format observations.
The original source preparer retains custody of private originals.
Fusion and original P04 verifier contracts still require their owning source handoffs.

The preflight retains `qualification: not_evaluated` and `qualified_pairs: 0`.
This reservation neither admits a pair nor ratifies a complete qualification protocol.
It does not authorize consuming P05, change family splits, qualify A06, or establish portable conversion or native application acceptance.
The [step register](../../../Reference/Research/AutomationSteps.md) retains those dependencies.
