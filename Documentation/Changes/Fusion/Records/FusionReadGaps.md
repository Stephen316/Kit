# Fusion read gaps

## Purpose

This change closes read failures of the native Fusion reader across the tracked corpus. Each fix is a general format rule found in the corpus. No rule names a file, and no saved byte ships in `src/`.

The sweep scripts in `re/Fusion/Reconstruction/ReadGaps` read each tracked F3D, F3Z and F2D file in its own process. `ReadGapNotes.md` there records each cause, its evidence and each sweep.

## Corpus

The corpus has 1,709 tracked files: 1,707 F3D files and 2 F3Z bundles. The bundles hold 9 design documents each, so the sweep reads 1,725 documents. No F2D drawing is tracked.

## Results

| Measure | Before | After |
| --- | --- | --- |
| Files that read | 1,692 of 1,709 | 1,698 of 1,709 |
| Documents that `ReadDocument` reads | 1,690 of 1,725 | 1,704 of 1,725 |
| Read documents that round-trip | 1,690 of 1,690 | 1,698 of 1,704 |
| `NativeMaterial` passes | 1,371 | 1,656 |
| `NativeMaterial` failures | 284 | 13 |
| `NativeMaterial` documents with no body and no material | 35 | 35 |

The patch word rule came after this sweep. The four interval files that stopped in the patch program now read and round-trip, and the counts above do not include them.

No document that read before fails now, and no model of such a document changed. Only the projections of the 11 documents with an undefined body material changed, from the default material to an error.

## Rules

| Rule | Documents fixed | Gotcha |
| --- | --- | --- |
| Older saves declare class versions that the catalog lacks. Eight versions have unique layouts. The rest get opaque schemas, bounded by the offset index. | Older example files reach later rules | [Historic class versions](../../../Gotchas/Conversion/Fusion/Records/FusionHistoricClassVersions.md) |
| A torus carrier can be an apple torus. | 1 | [Apple torus](../../../Gotchas/Conversion/Fusion/Geometry/FusionAppleTorus.md) |
| A TSM member can hold a `106ek` edge knot block. | 2, with the patch word rule | [Edge knot rows](../../../Gotchas/Conversion/Fusion/TSpline/FusionEdgeKnotRows.md) |
| A converted patch program word can be a double in `%.17g` form. | 4 interval files, the two edge knot files among them | [Knot interval conversion](../../../Gotchas/Conversion/Fusion/TSpline/KnotIntervalConversion.md) |
| `ReadDocument` reads a Form document whose BRep cache is stale. `EmitParsed` still refuses it. | 4 | [Stored Form BRep authority](../../../Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md) |
| A saved `bool` member can hold any byte. | Older example files reach later rules | [Flag bytes](../../../Gotchas/Conversion/Fusion/Records/FusionFlagBytes.md) |
| A sketch `secondaryTagId` is a free `u64`. | Older example files reach later rules | [Read gap notes](../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#example-record-rules) |
| A cross-document reference can name a class outside the profile. | Older example files reach later rules | [Foreign targets](../../../Gotchas/Conversion/Fusion/Records/FusionForeignTargets.md) |
| Named metadata can be typed by a value class GUID. | Older example files reach later rules | [Value metatypes](../../../Gotchas/Conversion/Fusion/Records/FusionValueMetatypes.md) |
| `ASM BinaryFile4` members use 4-byte integers. Older journals exceed the old quotas. | 7 | [ASM integer width](../../../Gotchas/Conversion/Fusion/History/FusionAsmIntegerWidth.md) |
| The Browser bulk stream can end with stale records. | Member 7 reaches later rules | [ACT bulk slack](../../../Gotchas/Conversion/Fusion/Records/FusionActBulkSlack.md) |
| A material package can hold a `Resources` folder tree. Assets that share a definition id keep their own definitions. | Member 7 reaches later rules | [Package resources](../../../Gotchas/Conversion/Fusion/Materials/FusionPackageResources.md) |
| `ImageSerializer` records name PNG image parts. | 2 | [Image parts](../../../Gotchas/Conversion/Fusion/Records/FusionImageParts.md) |
| The document material comes from the bodies, then the component default. An empty body reference is an undefined material. | 284 projections, 11 of them now refused | [Document material](../../../Gotchas/Conversion/Fusion/Materials/FusionDocumentMaterial.md) |

## Remaining failures

| Documents | Error | Reason |
| --- | --- | --- |
| `re/Fusion/Reconstruction/ContainerAuthoring/{Generated,StoredOnly,StoredFolders,StoredDirectories,OrderedAct}/AuthoredParameter.f3d` | Primary offsets out of order, or missing directories | Kit research files that Fusion rejected. See `ContainerModel.md` there. |
| `re/Fusion/LocalOracle/FormDocuments/Cache/{Box,Plane}SurfNone.f3d` | `Unsupported Fusion journal qualified field` | Rewritten caches that Fusion failed to import. See `Probe.json` there. |
| `re/Fusion/LocalOracle/FormDocuments/Intervals/{Plane4x4/Half,Plane4x4/ColumnRow,Plane4x4/Single,Box/Single}.f3d` | `invalid literal for int()` | Patch program words are doubles. The fix belongs in `BrepCodec/Journal/Spline`. |
| `example1.f3z` members 0, 3, 5, 6 and 8, in both copies | Graphics cache errors | Fixed by the [cache and package gaps](FusionCacheGaps.md) change. |

## Remaining round trips and projections

- The four stale Form files read, and `EmitParsed` refuses them.
- `example1.f3z` member 7 reads in both copies. Its round trip is fixed by the [cache and package gaps](FusionCacheGaps.md) change.
- Eleven documents have bodies with an undefined material, and `NativeMaterial` raises for them.
- `example1.f3z` member 7 gives three physical assets to its bodies. `NativeMaterial` returns one material, so it raises.

## Writer changes outside this change

- `MaterialCodec/Package/Envelope/PackageEntries.py` now writes `Resources`. See the [cache and package gaps](FusionCacheGaps.md) change.
- `ReadPatchRow`, `PatchCell` and `WritePatches` in `BrepCodec/Journal/Spline` should read and write patch words as `%.17g` doubles.
