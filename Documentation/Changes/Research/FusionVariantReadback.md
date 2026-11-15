# Fresh-process readback of captured Fusion variants

A02d's `--read-existing` capture preparation now pins every committed archive in each selected recipe's receipt.
Phase B reopens and recomputes each non-baseline variant in the restarted Fusion process.
Each observation binds the exact native hash, size and repository path.
The existing load diagnostics, timeline health checks and sketch binding collector apply to each readback.

Baseline A/B observations retain their existing fields and analytic baseline comparisons.
Other variants appear under `existing_variant_readbacks`, keyed by the recorded archive filename.
The collector does not apply baseline geometry expectations to dimension, direction, plane or termination variants.
Independent semantic comparison remains required.
The original native files, receipts and measurements remain unchanged.
P05 remains reserved and unavailable to this command.

Use the [fresh-process procedure](FusionFreshProcessEvidence.md) with `--read-existing` and selected P01–P04 recipes.
The plan also pins [observation-local bindings](FusionSketchBindingCapture.md).
Preparation rejects duplicate archive names, path traversal and mismatched receipt identities.

## Verification

Remote process coverage checks the exact P01 edit, plane and unit variant roster during preparation.
This revision's result is pending.
Static syntax, source review and whitespace checks cover the source change.
No local tests or native application ran.
The native Fusion bridge remains unavailable on the implementation host.
No new readback, source qualification or conversion acceptance is claimed.
