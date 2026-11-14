# Draft section for the Fusion data model reference

This draft is for the maintainer of `Documentation/Reference/Research/FusionDataModel.md`. Add it as one section after "General current geometry and document history dispatch". Links are relative to that reference page.

## Fusion-saved document coverage

`ReadDocument` followed by `EmitParsed` must read and re-emit each document that Fusion saves. The re-emitted document must read to an equal model. Gaps in classes, graphics, BRep ids, journal records and journal structure blocked Fusion saves. Each fix uses native registration evidence or a corpus census, and native acceptance.

### Saved-only classes

`SavedClasses.json` holds classes that Fusion saves but Kit does not author. `ReadDocSchemas` reads it. `AuthorSchemas` does not read it, so authored class tables do not change.

| Class | Version | Base | Own members |
| --- | --- | --- | --- |
| `TransientEntityHolder` `D87EC2D8-35C1-4AA2-A308-09AF07C490FF` | 0 | `98542EB9-A4F2-4137-A808-DBB5B3CD6159` | None |
| `DcDraftFeature` `F4163A07-9E71-4C46-BD92-ACE5B5B40BED` | 6 | `666BFBBC-2150-4C5F-AAF7-09AB3C3D9E47` | 13 |

`DcDraftFeature` version 6 adds `m_fixedPlaneDraftAngleMode`, a `u32` at native registration index 12. The other twelve members are the same as in version 5. Fields are in ASCII order of their names:

| Field | Wire type |
| --- | --- |
| `MovingPartingLineDraftAngleType` | `u32` |
| `draftType` | `u32` |
| `m_bFlipped` | `bool` |
| `m_bTangentPropagation` | `bool` |
| `m_directionType` | `u32` |
| `m_draftAngle1` | `ref` `D91D429C-1BB5-4640-B49F-69AF14F463E9` |
| `m_draftAngle2` | `ref` `D91D429C-1BB5-4640-B49F-69AF14F463E9` |
| `m_facePickPoint` | `struct` of `x` and `y` as `f64` |
| `m_facesRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` |
| `m_fixedPlaneDraftAngleMode` | `u32` |
| `m_rFixedEdgesDataRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` |
| `m_rRefPlaneDataRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` |
| `rPartingLineToolDataRef` | `ref` `2CA5A1CD-C99B-4C9B-91AF-57989148E841` |

The seven version 6 records in the corpus have `m_fixedPlaneDraftAngleMode` 1, `draftType` 1, `m_directionType` 1 and `MovingPartingLineDraftAngleType` 3.

### Version selection for classes without records

Segment metadata lists only classes that have records. A class that the type closure reaches only through a reference, a value type or a base has no metadata row. `PickSchema` then selects the newest catalog version. For each of the six classes with two catalog versions, the newest version is the current Fusion 2706.1.17 registration. A version that the metadata states must still match exactly.

### Matrix rows

`DRMatrix` version 16 `matrix3d` qualifies 16 row-major `f64` values. Version 16 changed only `arcLengthForPeriodicFace`, from a double to a strong reference. Saved offset and fillet documents store translations in `matrix3d`.

### Triangle-strip graphics

`OgsSimpleMesh` primitive code 5 is a triangle strip. Sketch dimensions use four-vertex strips without an index buffer. `XferMeshMut` accepts codes 2 to 5. `XferRenderMut` accepts codes 2 to 4.

### Body entity ids

Token 1 of an ASM face or vertex record holds an entity id or `-1`. Saved cylinder and frustum histories can store ids on faces 4, 5 and 6 and on vertices 20 and 21. `EntityIds` keeps these five values in `HistoryModel.Tracking` and `FrustumHistory.Tracking`.

### Typed view selection

`ReadBodyPart` and `ReadSnapPart` decode the exact journal or geometry model first. Then they try the typed view. When the typed view rejects the stored tokens, the exact model stays. A journal or geometry parse error still rejects the document. Typed views put records in a canonical order. Journal and geometry models re-emit their stored bytes.

### Container directories

Fusion writes stored, zero-byte directory entries. Fusion also opens deflated directory entries that hold the 2-byte empty Deflate stream. `ReadContainer` accepts both forms and rejects all other directory entries.

### Scene display items

Body LODs can hold display items of types 0, 6 and 7. `EnhancedEdge` and `EnhancedFace` hold the edge and face items. Fusion writes their geometry in the `Fusion_mesh_NNN` stream family, separate from `stream_mesh_NNN`. Scene globals declare `BillBoardAttribute` version 1 in older saves. Version 1 has no `FlipVisibility`.

### Journal records

Saved journals hold these records in addition to the records that Kit authors:

| Record | Kit model | Saved content |
| --- | --- | --- |
| `name_attrib-gen-attrib` and `int64_attrib-name_attrib-gen-attrib` | `NameAttrib` | A name and an optional signed 64-bit integer with tag 23 |
| `no_merge_attribute-st-attrib` | `NoMergeAttrib` | A system attribute with links and no payload |
| Nested `generic_tag_attrib_def` | `NestedTag` | A child tag with an empty identifier, its owner and an operation number |
| `FDM_feature_attrib_def` | `FeatureAttrib` | A `feature_data` layout, or a `thread_face_data` layout with three points and a tail of 0 or 1 |
| `wire` | `WireNode` | A sketch tool wire that a shell owns and that owns a coedge, with an `Inside` side logical |

### Journal structure

| Shape | Rule |
| --- | --- |
| Open working delta | `WorkingNode` equals `ActiveNode`, with `StateId` 0, one empty board and a next node |
| Record size | One board holds at most 4,096 changes, and one journal record holds at most 16,384 tokens |
| Free roots | The root count includes faces without a shell and edges without a coedge |
| Apex edge | A live edge without a curve closes a cone face at its apex |
| Torus sign | A torus carrier can have a negative minor radius with a smaller magnitude than the major radius |
| Edge rings | An edge has 1 to 4 coedge uses. Three or four uses form one partner ring with both senses. |

Thin extrudes write 4-use rings with alternating senses. Boundary fill journals keep cell bodies in older states. These states hold 3-use rings and 4-use rings with equal senses next to each other.

### Coverage and acceptance

| Corpus scope | Before | After |
| --- | --- | --- |
| `re/Fusion/LocalOracle/**/vendor_*.f3d` | 126 of 159 | 159 of 159 |
| All F3D and F3Z files under `re/` and `examples/` | 859 of 1,072 | 1,058 of 1,072 |

Each passing file reads, re-emits and reads again to an equal model. The [change entry](../../../../Documentation/Changes/Fusion/Records/FusionSavedDocumentCoverage.md) lists the remaining failures by cause. Three example files from an older Fusion declare 48 class versions that the catalog does not hold. The other 11 failures are research files that Kit made. The [native acceptance report](../../LocalOracle/ReaderCoverage/NativeAcceptance.json) compares Fusion observations of each control and re-emitted document for 26 cases. The stages are open, rebuild, rollback, restore, save and reopen. Fusion 2706.1.17 accepted all 26 cases.
