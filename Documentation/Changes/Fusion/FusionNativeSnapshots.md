# Typed native snapshots and empty configurations

Fusion document models can contain typed snapshot and configuration parts through `DocumentModel.Snapshots` and `DocumentModel.Configurations`. `ReadDocument` routes qualified `.smb` snapshots and the two configuration sidecars to their semantic readers. `EmitParsed` regenerates these parts from the models.

The snapshot wrapper supports the existing 59-record circular profile and a new 168-record cuboid profile. `ReadPrismSnap` and `EmitPrismSnap` preserve the solved solid, double-sided planar profile, single-sided sketch sheet, all carrier frames, vertex ownership, generic face identities and sketch links. The cuboid model includes explicit typed topology orders and curve parameterization. The reader validates every field and reference against independently regenerated records, consumes the complete payload, and rejects unsupported topology or trailing data. The writer does not retain source bytes, native object graphs or raw record arrays.

Configuration support is deliberately limited to empty table and rule JSON objects. Canonical UUID-bearing filenames identify their roles. Document validation requires exact agreement with the corresponding Design serializer triggers. Nonempty configurations remain unsupported.

## Usage

Import `ReadSnapPart` and `EmitSnapPart` from `convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots`. The reader accepts a `ContainerPart` with its logical `Breps.BlobParts/BREP.<UUID>.smb` name and returns a `DocumentSnap`. Its `Snapshot` is either the existing `SnapshotModel` or the new `PrismSnapshot`. The emitter returns a regenerated `ContainerPart`.

Direct cuboid APIs are under `DocumentCodec.Auxiliary.PrismSnapshot`: `ReadPrismSnap(Payload)` and `EmitPrismSnap(Value)`. `PrismSnapshot` contains millimeter dimensions, centimeter carrier frames, header/provenance, six solid face tags, four paired source-coedge identities and two explicit rectangular region models. Mutations must keep geometry, carrier endpoints, topology and parameter ranges consistent; validation rejects inconsistent edits.

## Limits

The cuboid profile contains one untransformed axis-aligned solid, two ordinary rectangular bottom regions and the qualified attribute structure. The region faces have +Z plane normal, forward coedges and a single four-edge loop. Other snapshot families, extra attributes, transformed topology and populated configuration tables are rejected. Payload size is bounded at 2 MiB.

This addition does not yet decode nested OGS world or mesh streams. Complete native archives containing those streams still fail the container's unaccounted-member check. It does not copy unknown graphics or omit them. See [the native auxiliary boundary](../../Gotchas/Conversion/Fusion/FusionNativeAuxiliaryParts.md) and [snapshot body roles](../../Gotchas/Conversion/Fusion/Geometry/FusionSnapshotBodies.md).

## Verification

Source inspection covers the ordinary rectangle control, Fusion-saved independently authored cuboid and native cylinder control. Reproducible inventories, compressed token evidence and the complete field model are in [NativeAuxiliary](../../../re/Fusion/Reconstruction/NativeAuxiliary/SnapshotModel.md).

Remote compatibility cases cover native ZIP member decoding, snapshot reserialization through a new ZIP boundary, three-root-body inventory and geometric dimensions. The cases also cover profile/sketch corners, semantic face-tag editing, nonincident owner rejection, trailing bytes, empty configuration roles and nonempty configuration rejection. No tests were run locally.

Authorized native-acceptance artifact generation produced two complete source-specific archives, replacing only their `.smb` members with production typed serialization. [Preparation evidence](../../../re/Fusion/LocalOracle/PrismSnapshot/Preparation.json) records source/output hashes, all typed frames and expected 25 → 37 mm and 37 → 43 mm height edits. The preparation script performs no native application calls. Fusion 2706.1.17 then accepted both archives with the correct initial solid and profile, healthy features and rollback to zero bodies. The acceptance also covered restored/rebuilt geometry, parameter editing, save and reopen. The ordinary rectangle passed 25 → 37 mm with volume 30 → 44.4 cm³; the saved cuboid passed 37 → 43 mm with volume 14.467 → 16.813 cm³. All stages retained six faces, 12 edges and eight vertices. The application returned to zero open documents. [Native acceptance](../../../re/Fusion/LocalOracle/PrismSnapshot/NativeAcceptance.json), SHA-256 `2b1407635e513c354356e2497086a5ae3d93b7e9faf495705f35c2cf268ba993`, qualifies replacement of the complete snapshot in each source's own surrounding archive; it does not qualify undecoded graphics.

Black, repository steering checks, Ruff, mypy and strict Pyright passed for the new codecs, wrappers and compatibility cases. Existing full-document material and history semantics remain unchanged.
