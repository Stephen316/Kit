# Read and write external component references

`ReadDocument` and `EmitParsed` now read and write Fusion designs that contain external component references.
The typed model keeps every link structure that Fusion writes into an F3D archive.
The writer emits these structures again from the typed values.

## Typed link structures

| Structure | Location | Typed model | Content |
| --- | --- | --- | --- |
| Root link table | Root `Manifest.dat` | `RootManifest.Links`, `ManifestLink` | Link GUID, three local paths and named text properties |
| Root ancestry | Root `Manifest.dat` | `RootManifest.Ancestry` | Ordered GUID list before the link table |
| Root lineage | Root `Manifest.dat` | `RootManifest.Lineage` | Display name and lineage URN, or `None` for an export terminal |
| Asset link rows | Asset `Manifest.dat` | `AssetHeader.Links`, `AssetLink` | Link GUID, target asset, target snapshot, link word and physical GUID |
| Version contexts | Each `MetaStream.dat` | `MetaSegment.Contexts`, `MetaContext` | Token, link GUID, revision, version URN, asset and segment number |
| Cross-document reference | Entity payloads | `CrossRef` | Object number, context token and target class GUID |

The root link properties are `LineageId`, `LineageUrn`, `toDocDisplayName`, `URL` and `linkedAssetGUID`.
A link that existed at a cloud save also has `linkClassification` with the value `OriginalDesign`.
`linkedAssetGUID` equals the `AssetId` of the asset link row with the same link GUID.

Each segment has one version context for each link.
The Design and Browser segments use the same token for a link, with segment number 0.
The ACT segment uses a different token for the same link, with segment number 1.
Each `CrossRef` token in a segment equals one context token of that segment.

## Cross-document references

The observed reference form has 60 bytes.
The reader also accepts a 37-character class text, which gives 61 bytes.

| Offset (bytes) | Size (bytes) | Value |
| --- | --- | --- |
| 0 | 1 | Presence flag `01` |
| 1 | 8 | Object number in the target segment |
| 9 | 1 | Cross-document flag `01` |
| 10 | 8 | Version context token |
| 18 | 1 | Separator `00` |
| 19 | 4 | ASCII length, 36 |
| 23 | 36 | Target class GUID text |
| 59 | 1 | Terminator `00` |

cadmpeg describes a second inline-typed form of 51 bytes.
Kit did not find this form in 15 native controls, 1,004 study F3D files or the example1 bundle members.
`ReadRefMut` raises `ValueError` for that form.

## New native classes

| Class | Segment | Schema version | Source |
| --- | --- | --- | --- |
| `XRefManager` | Design | 2 | Fusion schema dump |
| `DcXRefPCIFeature` | Design | 3 | Fusion schema dump |
| `DcPlaceComponentInstance` | Design | 2 | Native catalog base chain |
| `DcAssemblyFeature` | Design | 0 | Native catalog base chain |
| `ACTRefdTable` | ACT | 1 | Fusion schema dump and ACT payload replay |

The graphics frame of an external instance has a third link flag, `RenderFrame.HasEmptyLink`.
`SelectabilityAttribute` links an `AlphaImageSelectionQualifier` that holds one optional image path.
A set link flag that a callback payload follows raises `ValueError`.

## Evidence

The [link control script](../../../../re/Fusion/LocalOracle/LinksConfigs/CreateLinkControls.py) made two parts, one subassembly and one root assembly in Fusion 2706.1.17.
The script exported each state, saved each design to the acceptance project and closed every document.

| Control | State | Links | Contexts in each segment | `CrossRef` count (Design, ACT, Browser) |
| --- | --- | --- | --- | --- |
| `R0_empty` | Empty root | 0 | 0 | 0, 0, 0 |
| `R1_part_a` | Part A at 30° about Z, translation (5, 2, 1) cm | 1 | 1 | 2, 2, 6 |
| `R2_grounded` | Part A grounded | 1 | 1 | 3, 2, 6 |
| `R3_nested` | Subassembly at 90° about X, translation (0, 6, 0) cm | 2 | 2 | 5, 4, 12 |
| `R4_joint` | Rigid as-built joint | 2 | 2 | 5, 4, 12 |
| `R5_saved` | Root after cloud save | 2 | 2 | 5, 4, 12 |
| `R6_out_of_date` | Part A version 2 exists | 2 | 2 | 5, 4, 12 |
| `R7_updated` | After `updateAllReferences` | 2 | 2 | 5, 4, 12 |
| `R8_updated_saved` | Root version 2 | 2 | 2 | 5, 4, 12 |
| `R9_archive` | Archive export of the saved root | 2 | 2 | 5, 4, 12 |
| `S0_inserted` | Part B at translation (1, 2, 0) cm | 1 | 1 | 2, 2, 6 |
| `S1_saved` | Subassembly after cloud save | 1 | 1 | 2, 2, 6 |

[`LinkEvidence.json`](../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json) records the native and sanitized SHA-256 values of all 14 fixtures.
For each fixture, the model read again from the Kit output equals the original model.
All members are byte-identical except `.protein` members and the part `.smb` and `.smbh` members.
The existing codecs regenerate these three member kinds.

## Native acceptance

`PrepareReplay.py` made two Kit outputs from the unsanitized controls.

| Output | Source | Kit operation | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| `KitLinkReplayR5.f3d` | `R5_saved` | `ReadDocument`, then `EmitParsed` | 140,057 | `f89b39397f705117b85592be15c0c146b1e25f289d2a5fef427830962b66cda9` |
| `KitLinkMovedR1.f3d` | `R1_part_a` | New Part A matrix in the typed model, then `EmitParsed` | 135,024 | `feb364e1f0b8a23415f01b6326e983c8d7a9259893badc0dc9d78562ddffa297` |

The new matrix is a rotation of 45° about Z with the translation (7, −3, 2) cm.
Kit replaced the matrix in four Design fields.
Only the Design `BulkStream.dat` and the `.protein` member differ from the source control.

`ImportManager.importToNewDocument` refused both outputs, as the [local reference gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionLocalReferences.md) describes.
`BeginLinkUpload.py` uploaded both outputs to the acceptance project with `DataFolder.uploadFile`.
`AcceptLinkUploads.py` then opened the native cloud root and both uploaded outputs in Fusion 2706.1.17.

| Check | Native root `KitLinkRoot` | `KitLinkReplayR5` | `KitLinkMovedR1` |
| --- | --- | --- | --- |
| Open documents after open | 4 | 4 | 2 |
| Occurrence paths equal to the expected paths | Yes | Yes | Yes |
| Largest transform error after open | 0.0 | 0.0 | 0.0 |
| References after open | Part A v2, subassembly v1 | Part A v1 out of date, subassembly v1 | Part A v1 out of date |
| Part A body height after open | 0.8 cm | 0.5 cm | 0.5 cm |
| `updateAllReferences` | Not run | `True`, Part A v2 | `True`, Part A v2 |
| Part A body height after update | Not run | 0.8 cm | 0.8 cm |
| Largest transform error after update | Not run | 0.0 | 0.0 |
| Unhealthy timeline items | 0 | 0 | 0 |
| Open documents at the end | 0 | 0 | 0 |

The expected transforms of `KitLinkReplayR5` are the native `R5_saved` occurrence matrices.
The expected transform of `KitLinkMovedR1` is the matrix that Kit wrote.
Fusion showed this matrix for Part A without a difference.

The first save attempt in `AcceptLinkUploads.py` closed each document after 300 s and made no new version.
The later runs kept the document open until a new folder lookup showed the new version.
The [save completion gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionSaveCompletion.md) gives the details.
`ProbeLinkSave.py` and `AcceptLinkSaves.py` then saved each updated output as cloud version 2 and opened that version again.

| Check after save and reopen | `KitLinkReplayR5` | `KitLinkMovedR1` |
| --- | --- | --- |
| Cloud version | 2 | 2 |
| References | Part A v2, subassembly v1, none out of date | Part A v2, not out of date |
| Part A body height | 0.8 cm | 0.8 cm |
| Largest transform error | 0.0 | 0.0 |
| Unhealthy timeline items | 0 | 0 |
| Open documents at the end | 0 | 0 |

The [native acceptance report](../../../../re/Fusion/LocalOracle/LinksConfigs/LinkAcceptance.json) records all values.

## Tests

`tests/convert/formats/FusionCodec/Links` contains the new cases.
`LinkArchiveTests.py` replays the 14 fixtures and checks the link, context and token relations.
Its case `TestPlacement` writes a new Part A matrix into the typed model of `R1_part_a` and reads it back.
`LinkWireTests.py` checks synthetic root links, contexts, references, `Properties.dat` and `RedirectionsStream`.
The cases did not run locally.
`LinkArchiveTests.py` requires Python 3.14 for ZIP method 93.

## Limits

The [assembly authoring change](FusionAssemblyAuthoring.md) adds new assemblies that reference other designs.
It also confirms the `ACTRefdTable` field split from the Fusion binary.

## Related information

- [Assembly authoring change](FusionAssemblyAuthoring.md)
- [Dependency graph change](FusionDependencyGraph.md)
- [Configuration boundary](../Configuration/FusionConfigurationBoundary.md)
- [Link renewal gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionLinkRenewal.md)
