# Refuse retained source bytes in CLI metadata

`kit convert` checks every field of the complete `CadDocument` model before invoking a writer, including embedded assembly documents.
The retained-source key `solidworks_source_bytes` is refused whenever present, including with empty or nonbinary values.
Raw `bytes`, `bytearray`, and `memoryview` values are refused through nested mappings, lists, tuples, sets, and frozen sets.
The scan traverses dataclass record fields as well as containers, including
feature, sketch, assembly, source and provenance attributes. No source record
fields are skipped. It protects against cycles and shared record graphs and
does not trust aliases, wrapper names, or placement outside document metadata.

This closes a source-retention route that can exist even when a document has typed feature history and linked geometry.
Public SDK source-retention behavior and developer inspection remain unchanged.
Ordinary provenance text, hashes, and paths remain eligible, and the existing strict Fusion round trips remain required.
Metadata eligibility does not establish native or parametric acceptance.

Process cases start with a real typed Fusion cylinder and retain the actual committed SOLIDWORKS fixture archive in metadata.
They cover the original key, an alias, nested mappings and JSON-supported collection forms, plus empty or null retained-source markers.
Root and nested cases validate source documents and verify source preservation, missing or existing destination preservation, and successful `kit decode` inspection.
Additional process cases place actual archive bytes in typed feature, sketch,
and assembly attributes, feature provenance attributes, and source attributes.
They exercise aliases, nested mappings and tuples, and nested retained-source
markers at each location. Root and nested documents retain the same publication
and inspection checks. Positive cases preserve digest and text provenance at
all of these locations without removing the typed feature history.
The existing Fusion compatibility job executes this test subdirectory.

The JSON wire serializer supports binary `bytes` records but rejects `bytearray` and `memoryview`; cycles are not serializable.
Those broader scan branches have source-inspection evidence, not JSON process-fixture evidence.
No tests, SDK decoding, or CAD applications ran locally.
Pinned Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for the changed Python process coverage.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; remote process evidence remains required.

See [command usage](../../Tasks/CommandLine.md) and [the retained-source metadata gotcha](../../Gotchas/Conversion/Commands/RetainedSourceMetadata.md).
