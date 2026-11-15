# Direct adapter write safeguards

The JSON, Fusion, CATIA, and FreeCAD adapters now apply the existing document write safeguards before output work.
Direct adapter calls reject unqualified research documents, unresolved SOLIDWORKS inch dimensions, and unresolved SOLIDWORKS equation references or targets.
The safeguards inspect embedded component documents as well as the root document.

The existing checks remain in the registry for registered third-party writers.
Concrete writers call those same checks directly. No second marker format or policy implementation is introduced.
The rejection applies when `WriteOptions(validate=False)` is selected.

Affected public entry points include `JsonAdapter.write`, `JsonAdapter.Write`, `JsonWriter.EmitTarget`, `FusionWriter.write`, and `FusionWriter.Write`.
They also include `CatiaAdapter.write`, `FreeCadAdapter.write`, and the existing FreeCAD convenience function that calls that adapter.
Research readers and inspection remain available.

## Rejection behavior

Each writer checks the document before it validates the model, encodes a payload, or examines destination output policy.
It raises the existing `ValueError` with the corresponding unresolved or unqualified diagnostic.
An existing destination file or stream remains unchanged. A missing destination directory is not created.
Callers must resolve the missing evidence or semantics before retrying a write.
Disabling structural validation does not remove these checks.

## Verification and limits

The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576561310) identified the direct adapter bypass.
Source inspection confirmed that the registry checked these conditions while the concrete adapter methods reached output code directly.

New integration cases read the bundled native SOLIDWORKS part, persist marked neutral documents, and reopen those exact files.
They cover root and nested component markers across seven direct method spellings.
They require preservation of existing files, binary streams, text streams, and absent destination directories with validation disabled.
A separate valid-document case requires direct JSON writing and reopening to preserve the original native-derived document.

Formatting and source checks provide local evidence only. No local tests, decoding, or CAD application runs verified this repair.
Remote integration results and current-head review remain required.
This repair does not qualify native conversion or resolve the recorded missing semantics.

See [the reader guide](../../Reference/Research/FusionResearchReader.md) and [the direct-write gotcha](../../Gotchas/Conversion/DirectAdapterWriteBypass.md).
