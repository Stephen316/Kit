# Direct adapter write safeguards

The JSON, Fusion, CATIA, and FreeCAD adapters now apply the existing document write safeguards before output work.
Direct adapter calls reject unqualified research documents, unresolved SOLIDWORKS inch dimensions, and unresolved SOLIDWORKS equation references or targets.
The safeguards inspect embedded component documents as well as the root document.
They also reject history containing `NativeFeatureDefinition`, including suppressed steps and reference-kind nodes.
Native-only definitions retain format-specific data without establishing editable portable semantics.

The existing checks remain in the registry for registered third-party writers.
Concrete writers call those same checks directly. No second marker format or policy implementation is introduced.
The rejection applies when `WriteOptions(validate=False)` is selected.
The native-definition check follows the existing research, inch, equation, and support checks to preserve their diagnostic priority.
It applies to every source format and survives interchange serialization.

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
A separate valid-document case requires direct JSON writing and reopening to preserve an independently authored Fusion document.
The bundled SOLIDWORKS example is a refusal case because its support references remain unqualified.
See [the fixture evidence](../../Gotchas/Conversion/SolidWorksBundledExampleSupports.md).

The [native-definition review](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576647550) identified a separate history qualification gap.
The new boundary cases read an actual SOLIDWORKS definition with retained native record bytes.
They place that unchanged definition in an independent typed graph to isolate its refusal from unrelated native sketch support gaps.
The saved interchange input must reopen for inspection and then fail every registry and direct writer boundary without output mutation.
Root, nested, active, and suppressed histories receive the same refusal.
This negative fixture does not qualify the retained definition or relabel its source semantics.

CATIA native feature graphs and unsupported FreeCAD feature types also use `NativeFeatureDefinition`.
Public writes that previously selected exact replay or carriers for these graphs now fail at this shared boundary.
Copying retained native bytes does not qualify an editable portable graph.
Native reading and explicit model serialization remain available for inspection.
The low-level native replay helpers are unchanged.
Further [native semantic qualification](Readers/NativeSemanticWriteQualification.md) covers bare native kinds, unknown operations, explicit unresolved assembly markers, and FreeCAD required-feature expressibility before output work.
Existing generic API exact-copy cases now require refusal and destination preservation when the decoded history contains native-only definitions.
Their original exact-result assertions remain for fully typed inputs.

The concrete CATIA and FreeCAD caller suites now reflect this restriction.
Native CATPart graphs and loaded CATProduct components retain their source declaration, payload, structure, and mutation inspection checks, then require an exact native-definition refusal with existing file and stream preservation.
The former public-writer claims for native CATIA exact replay, native-base edit overlays, and native CATIA assembly component export are withdrawn while those graphs remain opaque.
FreeCAD Revolution and Hole definitions retain model inspection and explicit JSON serialization checks, then require refusal rather than output object serialization.
The bundled SOLIDWORKS source retains its payload digests and decoded feature names, with the earlier unqualified-support diagnostic taking precedence over native-definition rejection.

Generic CATIA carrier, foreign payload, tamper, configuration, replay-binding, reader-kind, and JSON bridge cases use an independently authored Fusion rectangle and retain their output assertions.
FreeCAD deterministic-output and stream-probe cases use that same typed input.
Independently constructed neutral FreeCAD geometry cases retain their source identity instead of claiming a SOLIDWORKS origin.
Wrong CATIA part and assembly destinations remain rejected before replacement using typed part and assembly inputs.
These positive cases verify their stated boundary behavior and do not establish target-application acceptance.

Formatting and source checks provide local evidence only. No local tests, decoding, or CAD application runs verified this repair.
Remote integration results and current-head review remain required.
This repair does not qualify native conversion or resolve the recorded missing semantics.

See [the reader guide](../../Reference/Research/FusionResearchReader.md) and [the direct-write gotcha](../../Gotchas/Conversion/DirectAdapterWriteBypass.md).
