# Creation definitions can reject a fixture before the CLI runs

A neutral fixture with a typed definition still has to satisfy the SDK's definition-specific validation before it can test a CLI guard.
`DistanceExtrude` validation calls `GetDistValues`, which requires extrusion kind and create intent.
Relabeling that definition as native, imported, or unknown fails `Document.AssertValid` before the process integration reaches the installed command.

Remote [CLI job 132657682013](https://github.com/TryUniCAD/Kit/actions/runs/43663480845/job/132657682013) at `3bcfe9fd` reported 12 such fixture failures and 341 passing cases.
The affected negative cases now use `CombineFeature`, whose generic SDK representation permits those labels, so the CLI can exercise its own kind refusal.
This preserves the neutral validation boundary rather than weakening it.
The repaired process cases still require remote execution; no local tests ran.

See [the feature guard change](../../../Changes/Commands/FeatureDefinitionGuard.md).
