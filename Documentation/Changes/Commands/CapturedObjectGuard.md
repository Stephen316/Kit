# Refuse captured FreeCAD object replay in CLI conversion

The CLI refuses nonempty `metadata.freecad.objects` with `CapturedObjects` before
calling any writer, including when the owning document is nested. Text-only XML
properties can be replay records even when they contain no binary payload.
An independently qualified geometry contract does not qualify that saved graph.

JSON and FCStd destinations are both refused. Source and existing output files
remain unchanged, and no companion files are published. `kit decode` and the
deterministic research tools remain available. The SDK writer's replay behavior
and research document contracts are unchanged.

Eight remote process cases cover root/nested sources, absent/existing outputs,
and both destinations using a material-free constrained sketch with textual
object metadata. Static formatting, typing, steering, rationale, path, and
whitespace checks validate the repair locally; no local tests or decoding ran.
Exact-head CI and configured review evidence are recorded in PR #119.

See [text replay metadata](../../Gotchas/Conversion/Commands/TextObjectsCanReplayVendorGraphs.md).
