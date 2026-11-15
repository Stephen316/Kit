# Exercise material and output-policy refusals independently

The CLI CATIA refusal process case now uses a qualified, dimension-driven
rectangle without material records when checking `output_not_application_usable`.
Its previous constrained cuboid includes a physical material, so the SDK's
material-support guard rejects it before the writer can return usability evidence.

The same process case also covers the cuboid's intended typed-material refusal.
Both paths require a nonzero exit, machine-readable diagnostics, unchanged source
and destination bytes, and no companion outputs. The material-free path retains
the exact structured usability-error assertion. Production conversion and its
material guard are unchanged.

Remote run `43703354275`, attempt 2, reported 765 passed and one failure because
the material error has no usability `details` field. Static formatting, typing,
steering, rationale, path, and whitespace checks validate this repair locally;
process execution remains remote only. Exact-head results are recorded in PR #119.

See [material guard ordering](../../Gotchas/Conversion/Commands/MaterialGuardsPrecedeWriterPolicy.md).
