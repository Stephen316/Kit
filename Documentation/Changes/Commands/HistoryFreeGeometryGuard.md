# Refuse geometry without feature history in CLI conversion

`kit convert` refuses a document with local B-rep, meshes, or bodies and no feature timeline before invoking a writer.
The check includes nested assembly documents and assemblies whose parts use local mesh representations.
Parameters without a feature timeline do not establish that geometry has editable history.

Parameter-only documents remain eligible when they contain no geometry.
Assembly roots without local geometry do not need a local feature timeline; their embedded documents are checked separately.
The guard leaves public SDK serialization and `kit decode` inspection available.
History presence does not establish completeness, parametric behavior, vendor loadability, or application acceptance.

The process integration cases use a typed cylinder B-rep and a triangle mesh with and without parameters, at the root and inside an assembly.
They also cover local assembly mesh references. Parameter-only documents are now
refused under [the complete model guard](ParametricModelGuard.md).
Refusal cases validate the input model, preserve source bytes and existing destinations, leave missing destinations absent, and retain successful inspection.
The Fusion compatibility job already executes the command test directory, so no workflow change is required.

No tests or decoding ran locally.
Pinned Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for the three new Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; process results remain pending remote CI.

See [command usage](../../Tasks/CommandLine.md) and [the history-free geometry gotcha](../../Gotchas/Conversion/Commands/GeometryWithoutFeatureHistory.md).
