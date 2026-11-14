# Fusion persistence schema recovery

## Behavior

Local Fusion 2706.1.17 supplied controlled parameter-allocation captures and a native schema dump.
The [class catalogue](../../../re/Fusion/Reconstruction/BinaryClasses.json) maps 1,218 class identifiers to class names.
Every identifier also appears in the runtime reflection capture.
It names all 403 Design classes present in the 712-archive corpus.
The [schema dump](../../../re/Fusion/LocalOracle/Allocation/ParameterSchema.xml) lists the registered parameter member names.
The [wire observations](../../../re/Fusion/LocalOracle/Allocation/WireObservations.json) record the controlled allocation captures.

The recovered model corrects several earlier interpretations.
The deletion and reallocation captures confirm the allocation item.
The other field meanings first came from binary inspection, which was removed at the tip.
They are not separately confirmed by a black-box experiment.

- The initial zero word is an empty root-identity string count, not a class version.
- Class versions live in the metadata registry.
- Parameter creation indexes and the table high-water mark survive deletion.
- Schema 10 inserts `isExternal` before the favorite flag.
- Binding subject indexes are signed observer-vector positions.
- `DcParameter.rparamId` is a 64-bit member, not a 32-bit rank followed by padding.

The native parameter codec now supports the captured schema-10 user-parameter metadata, preserves explicit table allocation state, and reads and writes the full binding identifier width.
Archive integration coverage includes the new deletion and reallocation captures.

## Usage and limitations

See the [data model](../../Reference/Research/FusionDataModel.md), [oracle command reference](../../Reference/Research/FusionOracleCommands.md), and [allocation watermark gotcha](../../Gotchas/Conversion/Fusion/FusionParameterWatermark.md).
The research command bridge runs scripts inside the installed application; production codecs remain independent of that application.
Class-name coverage is not complete field-schema coverage or proof of a complete native document writer.
Runtime schemas apply to the recorded application build.

## Verification

Fusion exported four controlled archives and reopened the post-deletion archive with both saved parameters intact.
`computeAll()` returned true on that vendor-authored control.
The schema dump contains 155 native types and 404 member names.
Fusion also accepted [a Kit-edited parameter archive](../../../re/Fusion/LocalOracle/Rewritten/Acceptance.json) and read both new numeric values and comments.
Fusion rebuilt a newly edited dependency, saved it, and reopened it with the same expression and value.
The output retains the same source document's non-parameter records and has no modeled bodies or feature timeline.
This proves the measured parameter-edit path only.
General automated tests remain in PR CI.

The later [feature experiment](FusionFeatureOracle.md) extends native acceptance to a same-source extrusion control rewrite and full rebuild, with measured geometry and two retained timeline entries.
It also records that the saved BRep cache stays stale until rebuild; neither experiment establishes independent document generation.

The experimental XML stream dump entered Fusion's crash handler before a completion record was written.
See [Fusion XML stream dump failure](../../Gotchas/Conversion/Fusion/FusionXmlDumpFailure.md).
It supplies no successful XML or writer-acceptance evidence.
The application was restarted and its [binary-persistence setting was verified on](../../../re/Fusion/LocalOracle/Restore.json), with zero documents open.
