# Fusion native feature record codec

## Behavior

Kit now reads and writes complete qualified sketch, extrusion, and managed-entity continuation payloads from typed semantic values.
The declarative vocabulary contains 13 classes and 80 field declarations, including explicitly excluded transient members.
There is no native application dependency, research-file lookup, subprocess, or retained payload argument in the production codec.

The reader requires the full class lineage from the archive metadata registry and checks every owning and inherited class version.
The supported current profiles include `DcSketch` version 5, `DcExtrudeFeature` version 8, and `ManagedEntity` continuation version 1 through `Entity` version 0.
The writer derives the complete payload from typed frames, member groups, and field values, applying the recovered lexical persistence order.

## Usage

Import `ReadFeature` and `EmitFeature` from `convert.formats.Fusion.SegmentCodec.Features`' corresponding modules.
Construct a tuple of `ClassStamp(ClassGuid, BaseGuid, SchemaVersion)` entries from the record's owning class through all bases to the entity root.
`ReadFeature(Payload, Lineage)` returns a `FeatureRecord` containing its frame and ordered member groups.
`EmitFeature(Record)` encodes that semantic record without access to the original bytes.

The model distinguishes local references, vectors, booleans, numeric fields, strings, UUID values, and reference collections.
`FeatureFrame.Subjects` preserves absent versus present subject storage, and `HasNamedMeta` preserves absent versus present empty metadata.
Unsupported class versions, nonlocal references, nonempty named metadata, unknown fields, transient fields in persisted groups, malformed values, missing groups, and trailing bytes are rejected.
The [data model](../../Reference/Research/FusionDataModel.md) links the field-level evidence and explains the separate continuation boundary.

## Verification and limits

The independent research decoder explained 1,734 bytes across ten records and matched 238 native field observations.
The production codec then generated a same-source archive with fully reconstructed sketch, extrusion, and managed continuation records.
The archive also had an edited extrusion name and 19 mm parameter/binding values.
[Fusion accepted that archive](../../../re/Fusion/LocalOracle/Features/GraphAcceptance.json), retained both timeline entries and rebuilt the 19 mm cylinder.
Fusion also accepted a further 23 mm edit and retained the extrusion name and geometry after native save and reopen.
The [rewrite record](../../../re/Fusion/LocalOracle/Features/GraphRewrite.json) lists the reconstructed records and fields.

The first naming experiment expected the sketch's design-capture label to control its visible timeline name; it did not.
The corrected experiment preserves that label and edits the extrusion label only.
See [sketch naming ownership](../../Gotchas/Conversion/Fusion/FusionSketchLabels.md).

Archive compatibility cases exercise parameter and full feature re-encoding together in PR CI.
Additional cases reconstruct valid archive and segment framing around unsupported inherited class versions and trailing feature bytes, then require the semantic reader to reject them.
Static formatting and typing checks ran locally; no local automated tests were run.
The native acceptance archive preserves its own other source records and requires native recomputation of stale geometry caches.
This does not establish independent complete F3D/F3Z generation or enable production adapter discovery.
