# Fusion embedded geometry writers

## Behavior

Kit now includes independent serializers for the controlled circular-extrusion snapshot and solved BRep history.
`EmitSnapshot(Model, TagSet, Stamp)` writes three bodies: the cylinder, a double-sided planar region, and a single-sided profile body.
`EmitHistory(Model, Identity, TagSet, History, Stamp)` writes the solved cylinder and its insertion journal.
Both serializers construct every geometry, topology, attribute, and journal record from typed inputs.
They read no research artifact, fixture, vendor payload, or CAD runtime.

The [snapshot writer](../../../src/convert/formats/Fusion/BrepCodec/EmitSnapshot.py) emits 59 records.
The [history writer](../../../src/convert/formats/Fusion/BrepCodec/EmitHistory.py) emits 35 records and two history states.
The existing `CylinderBody` model supplies positive radius and height, plus base position, in millimeters.
The writers convert positional values to the native centimeter representation.

## Inputs and identities

`TopologyTags` supplies five feature tags and a sketch link.
Each `FeatureTag` contains its primary identifier, ordered operation identities, secondary identity, and approach identity. The primary byte count is derived from the identifier.
`SketchLink` retains two source identities, direction, and the two observed enumeration values.
The secondary sketch identity supports the full unsigned 64-bit range.

`BodyIdentity` supplies the persistent body key, operation identity, explicit secondary identity, and authoring timestamp.
`HistoryState` supplies insertion and initial delta IDs, stream current/maximum state IDs, the next entity tag and the board status. [Native history semantics](FusionHistoryStates.md) supersede the original generation/allocation/board-number labels.
The body secondary identity remains explicit and is independent of the current history state. In the canonical authored document it matches the Design-side body progenitor tag. [Native tag semantics](FusionGenericTagSemantics.md) supersede the earlier generation-reference and selector interpretation.
The [identity model](../../../re/Fusion/Reconstruction/BrepHistory/HistoryAuthoring.md) records the observed relationships and remaining semantic limits.

The surrounding Design graph must bind body keys, passive IDs, feature identities, and history states consistently.
These serializers do not synthesize that entire graph or independently qualify a complete F3D document.

## Verification

The [production generation report](../../../re/Fusion/LocalOracle/Features/ProductionBrepRewrite.json) identifies both generated members and the containing archive.
The [native acceptance report](../../../re/Fusion/LocalOracle/Features/ProductionBrepAcceptance.json) records the actual Fusion result.
Fusion accepted correct initial 19 mm geometry, healthy features, sketch-only rollback, restoration, and a 23 mm edit through save and reopen.
The run left zero open documents.
The surrounding archive uses its own reconstructed source document and regenerated material package.

New PR compatibility checks exercise emitted files through the existing independent ASM reader.
They inspect body roots, reciprocal topology, circular geometry, ownership attributes, and full-width sketch references.
These automated checks were not executed locally.
[PR run 43210865752](https://github.com/TryUniCAD/Kit/actions/runs/43210865752) passed all 36 compatibility cases on `77fa7e9b37aaba0ebae6f5b03d2c10930b74447e`.
That result includes four new embedded geometry cases. It does not establish deferred merge-group acceptance.

## Limits

Support is restricted to the evidenced circular-extrusion profile and insertion-only history.
Arbitrary boolean journals, changing topology, other primitive families, and general assembly histories remain unsupported.
The observed snapshot and history header scale values are 10 and 50, respectively.
This profile does not establish a universal relationship between those header values and coordinates.
Production adapter discovery remains disabled until whole-document acceptance requirements are satisfied.
