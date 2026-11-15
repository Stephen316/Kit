# Refuse native and unknown record kinds in CLI conversion

`kit convert` requires recognized, nonnative kind values on component
definitions, assembly mates and mate entities, sketch entities, and sketch
constraints. The same rule applies to enum members and canonical string values.
`native` and unknown strings are refused with a `NativeRecord` error before
writing, including records within embedded component documents.

These records can be structurally valid without having portable semantics. A
native mate does not become a supported constraint because its entity links are
valid, and a native sketch-entity kind remains unsupported even when its geometry
object is a typed circle. Existing feature-definition and generator checks still
apply independently.

Use `kit decode` or the research tools to inspect unsupported records. Public SDK
model validation and inspection behavior are unchanged. Known enum members and
their canonical strings remain eligible for existing conversion and writer
checks; this guard does not establish target-application acceptance.

Actual CLI subprocess cases use typed Fusion parts and complete assemblies.
Native enum, native string, and unknown string cases cover mates, mate entities,
sketch entities, and sketch constraints; an unknown component-kind case covers
a linked leaf definition. Fixtures assert SDK model validity before conversion.
Root and nested cases verify source preservation, missing/existing destination
preservation, `NativeRecord` refusal, and continued decoding. Positive cases
preserve known enum/string records, including Coincident mates and their linked
typed component documents.

No local tests, SDK decoding, or test collection were executed. Pinned formatting,
typing, steering, path-policy and whitespace checks cover the new process files.
Actual execution evidence is required from remote CI on the accepted PR head.
See [the CLI procedure](../../Tasks/CommandLine.md) and
[the open-kind gotcha](../../Gotchas/Conversion/Commands/OpenRecordKindStrings.md).
