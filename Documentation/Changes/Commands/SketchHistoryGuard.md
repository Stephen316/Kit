# Require sketch feature history for CLI conversion

`kit convert` refuses sketches without a feature timeline, even when independent
parameters make the document valid for SDK serialization. Each sketch must also
have its own active sketch-reference step; an unrelated timeline or a partial set of references
does not qualify the remaining sketches. Nested assembly documents follow the
same rule. Globally or configuration-suppressed steps, inactive dependencies,
and suppressed sketches do not qualify. Parameter-only documents without sketches remain supported.

Refusal happens before writing output. `kit decode` remains available for
inspection. Valid circle and rectangle sketch histories retain their existing
conversion coverage, including inactive references and logical feature ordering.

Process cases cover missing, unrelated, partial, and suppressed sketch history at the root
and inside assemblies, preserving source bytes and existing or missing output
files while checking continued decoding. Tests and decoding were not run locally.
Static formatting, typing, steering and path checks validate the repair; exact-head
process execution and review evidence are recorded in PR #119.

See [the sketch-history gotcha](../../Gotchas/Conversion/Commands/SketchParametersAreNotHistory.md)
and [command usage](../../Tasks/CommandLine.md).
