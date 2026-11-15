# Require active model history and qualified datum geometry

A nonempty timeline with no active features now fails CLI conversion with
`IncompleteFeature`. Global suppression, feature configuration state, configuration
suppression IDs, and inactive dependencies cannot supply model history.

SDK geometry qualification also includes standalone support planes. An active
reference datum with cached geometry needs a matching regeneration contract;
typed labels alone do not qualify its frame. Unsupported standalone datum models
remain inspection-only. Qualified constrained sketches and solids retain their
existing contract checks.

Sixteen remote subprocess cases cover globally/configuration-suppressed and active
plane-only documents at root/nested levels and absent/existing outputs. They
require source/output preservation and successful decoding. No local tests or
decoding ran. Static validation and exact-head CI evidence are recorded in PR #119.

See [suppressed timelines](../../Gotchas/Conversion/Commands/SuppressedTimelinesAreNotHistory.md).
The [Feature-path formatter gotcha](../../Gotchas/Ci/Commands/BlackExcludesFeaturePaths.md)
records the explicit formatting workaround used for these process files.
