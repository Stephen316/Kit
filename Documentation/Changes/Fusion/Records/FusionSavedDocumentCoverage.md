# Fusion-saved document coverage

## Purpose

This change lets the native Fusion reader read the documents that Fusion saves. `ReadDocument` reads each document and `EmitParsed` writes it again. A second `ReadDocument` must then give an equal model.

The change adds class schemas, a version rule, a matrix profile, graphics primitives and scene items, BRep entity ids, journal records and journal structure rules. It also changes typed view selection and the container directory rule. Each item has native registration evidence or a corpus census, and native acceptance.

## Draft feature version 6

The feature-authoring work needs this schema. The schema is in `src/convert/formats/Fusion/DocumentCodec/Vocabulary/SavedClasses.json`.

| Property | Value |
| --- | --- |
| Class | `DcDraftFeature` |
| Class GUID | `F4163A07-9E71-4C46-BD92-ACE5B5B40BED` |
| Base GUID | `666BFBBC-2150-4C5F-AAF7-09AB3C3D9E47` |
| Schema version | 6 |
| Class space | `Fusion` |
| Value class | No |

The fields are in ASCII order of their names. This order is the wire order.

| Field | Wire type | Saved value in the corpus |
| --- | --- | --- |
| `MovingPartingLineDraftAngleType` | `u32` | 3 |
| `draftType` | `u32` | 1 |
| `m_bFlipped` | `bool` | false |
| `m_bTangentPropagation` | `bool` | false |
| `m_directionType` | `u32` | 1 |
| `m_draftAngle1` | `ref` `D91D429C-1BB5-4640-B49F-69AF14F463E9` (`DcDoubleParameter`) | Local reference |
| `m_draftAngle2` | `ref` `D91D429C-1BB5-4640-B49F-69AF14F463E9` (`DcDoubleParameter`) | Local reference |
| `m_facePickPoint` | `struct` of `x` and `y`, each `f64` | `(-0.0, 0.0)` |
| `m_facesRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` (`ModelDataRef`) | Null |
| `m_fixedPlaneDraftAngleMode` | `u32` | 1 |
| `m_rFixedEdgesDataRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` | Null |
| `m_rRefPlaneDataRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` | Local reference |
| `rPartingLineToolDataRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` | Null |

Version 6 adds only `m_fixedPlaneDraftAngleMode`. Native registration index 12 holds it as `IntrinsicMetaTypeuint32` with option mask 51. The other twelve fields are the same as in version 5. The corpus holds seven version 6 records and 16 version 5 records. All seven version 6 records hold the saved values in the table.

`AuthorSchemas` does not read `SavedClasses.json`. To author a version 6 draft, add the same entry to the author vocabulary. `ReadDocSchemas` accepts one class in two vocabulary files only when the two entries are equal. Keep the field names, types and order unchanged. A version 5 schema remains in the packaged native catalog. When the segment metadata names version 5 or 6, the reader uses that exact version.

## Changed reader rules

All paths are relative to `src/convert/formats/Fusion`. Unsupported branches still raise `ValueError`.

### Document classes and containers

| Area | Rule | Location |
| --- | --- | --- |
| Saved-only classes | `TransientEntityHolder` version 0, with no own fields, and `DcDraftFeature` version 6 are read but not authored. | `DocumentCodec/Vocabulary/SavedClasses.json`, `DocumentCodec/Records/ReadDocSchemas.py` |
| Version selection | A class without a metadata row uses the newest catalog version. A version in the metadata must match exactly. | `EntityCodec/Vocabulary/PickSchema.py` |
| Matrix profile | `DRMatrix` version 16 `matrix3d` qualifies 16 row-major `f64` values. | `DocumentCodec/Vocabulary/DesignClasses.json` |
| Typed views | The exact `JournalModel` or `GeometryState` stays when a typed view rejects its stored tokens. | `DocumentCodec/Reading/ReadTypedBody.py`, `DocumentCodec/Auxiliary/Snapshots/ReadTypedSnap.py` |
| Directories | A directory entry can be stored with 0 bytes or deflated with 2 bytes. | `ContainerCodec/ReadContainer.py` |

### Graphics

| Area | Rule | Location |
| --- | --- | --- |
| Triangle strips | `OgsSimpleMesh` accepts primitive code 5, the triangle strip. | `GraphicsCodec/Geometry/XferMeshMut.py` |
| `Fusion_mesh` streams | Body LOD display items of types 0, 6 and 7 are read as `EnhancedEdge` and `EnhancedFace`. The `Fusion_mesh_NNN` family is written again from these items. | `GraphicsCodec/Nodes/XferLodMut.py`, `GraphicsCodec/Geometry/XferEdgeMut.py`, `GraphicsCodec/Geometry/XferFaceMut.py`, `ContainerCodec/IsGraphicPath.py` |
| Billboard version 1 | Scene globals accept `BillBoardAttribute` versions 1 and 2. Version 1 has no `FlipVisibility`. | `GraphicsCodec/Schema/VersionRules.py`, `GraphicsCodec/Fields/XferAttrMut.py` |

### BRep and journals

| Area | Rule | Location |
| --- | --- | --- |
| Entity ids | `EntityIds` holds face ids at ordinals 4, 5 and 6 and vertex ids at ordinals 20 and 21. `ReadIds` reads them, and `ApplyIds` writes them. | `BrepCodec/Models/EntityIds.py`, `BrepCodec/Reading/ReadIds.py`, `BrepCodec/Topology/ApplyIds.py` |
| Attribute records | `NameAttrib` and `NestedTag` decode saved generic and nested tag attributes. Tag 23 holds a signed 64-bit integer. `FeatureAttrib` and `NoMergeAttrib` decode thread and no-merge attributes. `FeatureAttrib` requires flags 2097152, the type code of its layout and a thread tail of 0 or 1. | `BrepCodec/Journal/Attributes`, `BrepCodec/Journal/Reading/Attributes`, `BrepCodec/Journal/Writing/Attributes` |
| Wire records | `WireNode` decodes a sketch tool wire and keeps its side logical in `Inside`. `ShellNode.FirstWire` holds the shell wire, and a wire can own a coedge. | `BrepCodec/Journal/Geometry/WireNode.py`, `BrepCodec/Journal/Geometry/ShellNode.py` |
| Working delta | `CheckWorking` accepts an open working delta state with `StateId` 0, one empty board and a next node. | `BrepCodec/Journal/Validation/CheckWorking.py` |
| Record size | One bulletin board holds at most 4,096 changes. Each journal record holds at most 16,384 tokens. | `Topology/AsmEdge/AsmTable.py`, `BrepCodec/Journal/Reading/ReadBoardMut.py` |
| Free roots | `CountRoots` counts bodies, faces without a shell and edges without a coedge. | `BrepCodec/Journal/Validation/CountRoots.py` |
| Apex edges | `IsApexEdge` accepts a live edge without a curve only when the edge closes a cone face at its apex. | `BrepCodec/Journal/Validation/IsApexEdge.py` |
| Torus sign | A torus carrier can have a negative minor radius with a magnitude less than the major radius. | `BrepCodec/Journal/Round/CheckRoundNode.py`, `BrepCodec/Journal/Snapshot/CheckGeometry.py` |
| Edge rings | An edge can have 1, 2, 3 or 4 coedge uses. For 3 or 4 uses, `CheckUseCycle` requires one partner ring and both coedge senses. | `BrepCodec/Journal/Validation/CheckUsePairs.py`, `BrepCodec/Journal/Validation/CheckUseCycle.py` |

`HistoryModel` and `FrustumHistory` have a new `Tracking` field. Its default holds `-1` in all five slots, so authored bodies do not change. `EmitHistory` and `EmitFrustumHist` take an optional `Tracking` argument.

The [complex geometry change](../Geometry/FusionComplexGeometry.md) found the thread, no-merge, wire, apex edge and record size rules independently. The two changes share one implementation of these rules. The [thread attribute](../../../Gotchas/Conversion/Fusion/Geometry/ThreadAttributeLayouts.md), [wire shell](../../../Gotchas/Conversion/Fusion/Geometry/WireShellSlots.md) and [degenerate edge](../../../Gotchas/Conversion/Fusion/Geometry/DegenerateHoleEdges.md) gotchas hold their evidence. The [records gotcha folder](../../../Gotchas/Conversion/Fusion/Records) holds the evidence for the other rules.

## Coverage

A file passes when `ReadDocument`, `EmitParsed` and a second `ReadDocument` give an equal model. A bundle passes when each member document passes. The counts use the 1,072 files that were in the repository before this change.

| Scope | Before | After |
| --- | --- | --- |
| `re/Fusion/LocalOracle/**/vendor_*.f3d` | 126 of 159 | 159 of 159 |
| All F3D and F3Z files under `re/` and `examples/` | 859 of 1,072 | 1,058 of 1,072 |

No file that passed before fails after the change. This change adds 78 files: 26 re-emitted documents and the 52 files that Fusion saved during native acceptance. All 78 pass, so the full census is 1,136 of 1,150 files and the vendor census is 211 of 211 files.

The complex geometry change adds 9 history archives, and all 9 pass. With these archives, the full census is 1,145 of 1,159 files. The 14 failures are the same files with the same errors.

The [census script](../../../../re/Fusion/Reconstruction/ReaderCoverage/Census.py) and the [comparison script](../../../../re/Fusion/Reconstruction/ReaderCoverage/CompareCensus.py) produce these counts.

Fourteen files still fail.

| Files | Error | Cause |
| --- | --- | --- |
| `re/Fusion/examples/.f3d/example2.f3d`, `re/Fusion/examples/.f3z/example1.f3z`, `re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z` | `Unqualified Fusion native class or schema version` | An older Fusion saved these 19 documents. They declare 14 class versions older than the catalog and 34 classes that the catalog does not hold. |
| 4 files in `re/Fusion/LocalOracle/FormDocuments/Stale` | `Converted Form BRep embeds a T-spline program absent from its parts` | A research script rewrote these members. Each moves a grip in the Form member or in the BRep cache, but not in both. |
| 2 files in `re/Fusion/LocalOracle/FormDocuments/Cache` | `Unsupported Fusion journal qualified field` | A research script rewrote the `t_spl_sur` cache with approximation level none. The reader does not qualify that value. |
| 4 `AuthoredParameter.f3d` files in `re/Fusion/Reconstruction/ContainerAuthoring` | `Fusion primary offsets must increase in identity order` | Kit authored these diagnostic containers. They are not Fusion saves. |
| `re/Fusion/Reconstruction/ContainerAuthoring/OrderedAct/AuthoredParameter.f3d` | `Missing directories or unaccounted Fusion container members` | Kit authored this ACT record order diagnostic. It is not a Fusion save. |

The [example gap evidence](../../../../re/Fusion/Reconstruction/ReaderCoverage/ExampleGaps.json) lists each missing class version.

## Native acceptance

The [preparation script](../../../../re/Fusion/Reconstruction/ReaderCoverage/PrepareAcceptance.py) re-emits 26 representative documents. Each case covers one or more of the changed rules. The [preparation record](../../../../re/Fusion/LocalOracle/ReaderCoverage/Preparation.json) holds the SHA-256 value of each source and output.

The [acceptance script](../../../../re/Fusion/LocalOracle/AcceptReaderCoverage.py) opens each source and each re-emitted document in Fusion 2706.1.17. It rebuilds the design. When the design has a timeline, it rolls back to marker 0, restores the marker and rebuilds. Then it saves the design and opens the saved file. The observations of each pair must agree.

Fusion 2706.1.17 accepted all 26 cases. In each case, the control and the re-emitted document gave equal observations at every stage. The run closed every document that it opened, so `documents_after` is 0. Fusion saved 52 files during the run. Each saved file reads, re-emits and reads again to an equal model.

| Item | Value |
| --- | --- |
| Report | [`NativeAcceptance.json`](../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json) |
| Report SHA-256 | `503fdfc703b07842c25e0295b201ceb9754da6cd5338dfee68e840a4c09bcc43` |
| Status | `accepted` |
| Cases | 26 |
| Files that Fusion saved | 52 |

Fusion copied account residue into 35 of the 52 saved files. These files were rewritten with same-length placeholders before publication. The [scrub ledger](../../../../re/Fusion/LocalOracle/ScrubLedger.json) records the digest of each file before and after the rewrite. The [fixture scrub](../Privacy/FusionFixtureScrub.md) also rewrote four control sources of this change. The report and the preparation record hold the digests of the rewritten files. The re-emitted documents of the four sources did not change.

Source paths in this table are relative to `re/Fusion`.

| Case | Source | Covers |
| --- | --- | --- |
| `DraftV6` | `LocalOracle/JournalStates/vendor_DraftControlEdited.f3d` | `DcDraftFeature` version 6 and `DRMatrix` version 16 in a parametric timeline |
| `TransientHolder` | `LocalOracle/Brep/vendor_binary_temporary.f3d` | `TransientEntityHolder` version 0 and the newest version for classes without a metadata row |
| `DecodedSphere` | `LocalOracle/RoundBodies/vendor_DecodedSphere.f3d` | `TransientEntityHolder` version 0 in a round body document |
| `RoundFillets` | `LocalOracle/RoundBodies/vendor_RoundFilletsControl.f3d` | `DRMatrix` version 16 `matrix3d` rows that are not identity |
| `StripCuboid` | `LocalOracle/PublicAdapter/vendor_cuboidEdited.f3d` | `OgsSimpleMesh` triangle strips in mesh streams |
| `StripRectangle` | `LocalOracle/DimensionAuthoring/vendor_DimensionedRectangleEdited.f3d` | Triangle strips for dimension arrowheads |
| `CylinderIds` | `LocalOracle/RotationalDocuments/vendor_NativeCylinderControl.f3d` | Face and vertex entity ids in a typed cylinder history |
| `FrustumIds` | `LocalOracle/RotationalDocuments/vendor_NativeFrustumControl.f3d` | Face and vertex entity ids in a typed frustum history |
| `JournalFallback` | `Study/extents-f0f33a9a605f/offset_negative.f3d` | The exact journal model when the typed body view disagrees |
| `SnapshotFallback` | `Study/namedbodies-3c7c11fc2924/namedbodies.f3d` | The exact geometry state when the typed snapshot view disagrees |
| `PrismFallback` | `Study/thinextrudes-f758eff14202/open_line_side1.f3d` | The exact journal model when prism records are outside the typed view |
| `AssemblyIds` | `Study/assembly-acc48a9dc05d/assembly.f3d` | BRep entity ids in a document with more than one component |
| `DeflatedFolders` | `LocalOracle/JournalStates/DraftTypedHistory.f3d` | Deflated empty directory entries |
| `WireShell` | `Study/splitfacemodes-4fc4adf2a868/along_vector.f3d` | A journal shell with a wire and no face, and coedges that a wire owns |
| `NestedTag` | `Study/moretools-88a2cd6cad0b/MoveRotate.f3d` | Journal generic tags that own a nested tag with an empty identifier |
| `ThreadFace` | `Study/threadmodes-d51d2ae60564/modeled_full.f3d` | Journal thread face attributes with two payloads |
| `EdgeRing` | `Study/thinextrudes-c1632bcb5efe/closed_two_sides_mixed.f3d` | Four-use edge rings with alternating senses in the geometry and the journal |
| `FillRing` | `Study/boundaryfills-a0953038318b/plane_first.f3d` | Four-use edge rings with mixed senses and 64-bit sculpt name attributes in a journal |
| `FillCells` | `Study/boundaryfills-a0953038318b/component_middle.f3d` | Three-use edge rings and 64-bit sculpt name attributes in a journal |
| `ApexEdge` | `Study/holes-926347c1eaa8/simple.f3d` | Journal cone apex edges without a curve |
| `TorusSign` | `Study/specialfillets-d50f7a4f04e0/rule_all_both.f3d` | Journal torus carriers with a negative minor radius |
| `FreeRoots` | `Study/extents-f0f33a9a605f/from_plane.f3d` | A journal root count that includes free faces and free edges |
| `WorkingDelta` | `Study/pathpatterns-de9857f6a1bc/arc_along.f3d` | A journal with an open working delta state |
| `BoardSize` | `Study/patterns-35e49809a812/symmetric_one.f3d` | A journal bulletin board with more than 1,000 changes |
| `SceneMesh` | `Study/timeline-5867579925b5/grouped.f3d` | `Fusion_mesh` edge and face display items in graphics scenes |
| `RolledScene` | `Study/timeline-5867579925b5/rolled_back.f3d` | `Fusion_mesh` scenes in a timeline that is rolled back |

## Tests

No test ran locally. The tests need Python 3.14 for ZIP method 93.

| File | Content |
| --- | --- |
| `tests/convert/formats/FusionCodec/SavedCorpus/SavedReadTests.py` | Round trips of Fusion-saved files, the draft schema, version selection, the transient holder, matrix rows, strips, entity ids, typed fallback and directories |
| `tests/convert/formats/FusionCodec/SavedCorpus/SavedAcceptTests.py` | Preparation hashes, the native acceptance report and reads of the files that Fusion saved |
| `tests/convert/formats/FusionCodec/SavedCorpus/JournalAttributeTests.py` | Journal attribute and wire record replay |
| `tests/convert/formats/FusionCodec/SavedCorpus/JournalStructureTests.py` | Journal structure rules and boundary fill round trips |
| `tests/convert/formats/FusionCodec/SavedCorpus/SceneStreamTests.py` | `Fusion_mesh` scenes and billboard version 1 |

CI does not run this folder yet. Add `tests/convert/formats/FusionCodec/SavedCorpus` to the `Exercise native document, entity, material, and geometry archives` step in `.github/workflows/FusionCompatibility.yml`. That step uses Python 3.14.

## Remaining boundaries

- The typed views put records in a canonical order. They re-emit equal models, but not always equal bytes. ParaMesh and `.protein` members are also re-encoded.
- The example documents need 48 more class schemas. For the 14 older versions, Fusion 2706.1.17 registers and saves a newer version, so a controlled save cannot produce them. The local registration census holds no field list for the 34 absent classes. These classes come from PCB, assembly constraint, appearance override and browser features. This change did not make controlled saves for them.
- Billboard version 1 occurs only in the example documents. Kit cannot read these documents yet, so native acceptance has no re-emitted copy of them.
