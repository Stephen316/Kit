# Fusion read gaps

## Goal

Every tracked Fusion file in the repository reads. The sweep runs the readers over every tracked `.f3d`, `.f3z` and `.f2d` file.

## Tools

| Script | Purpose |
| --- | --- |
| `Sweep.py <label> [deep]` | Lists files with `git ls-files`. Runs `SweepOne.py` once per file in a subprocess under `/opt/homebrew/bin/python3.14 -I`, with a 900 s timeout. Writes `Sweep-<label>.json`. |
| `SweepOne.py <path> [deep]` | Runs `ReadDocument` on designs, `ReadBundle` on bundles and `ReadDrawing` on drawings. Routes bundle members by suffix. `deep` adds the `EmitParsed` round trip. Records the exception class, message and frames, or a SHA-256 digest of the read model. The digest walks the dataclasses and skips fields equal to their default, so a new defaulted field does not change it. |
| `Compare.py <before> <after>` | Lists documents that were fixed or broken, and read documents whose model, round trip or material projection changed. |
| `ExampleRecords.py`, `TrySchema.py` | Decode records of one class version from the unique example documents with candidate schemas. |

Each read document also runs two material projections:

- `NativeMaterial` on the model (`native`).
- `ReadMaterial` once for each `Body` node of the native graph (`graph`).

The model digest is stable across runs.

## Corpus

- 1,709 tracked files: 1,707 `.f3d`, 2 `.f3z`, no `.f2d`.
- The two bundles hold 9 `.f3d` members each, plus `Manifest.json` and `DesignDescription.json`. The members of `re/Fusion/examples/.f3z/example1.f3z` and `re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z` are byte-equal.
- 1,725 design documents in all. No drawing is tracked, so `ReadDrawing` has no corpus file. The sweep would route a `.f2d` file or member to it.

## Baseline (`Sweep-before.json`)

| Measure | Pass | Fail | Other |
| --- | --- | --- | --- |
| Files | 1,692 | 17 | |
| Documents, `ReadDocument` | 1,690 | 35 | |
| Round trip of read documents | 1,690 | 0 | |
| `NativeMaterial` | 1,371 | 284 | 35 body-free without material |
| `ReadMaterial` per body | 212 | 1,394 | 84 without a `Body` node |

The parent brief counted 1,145 of 1,159 F3D and F3Z files and 1,387 material passes against 292 failures. The corpus has grown since then. The counts above are the baseline for this work.

### Read failures

| Count | Error | Files |
| --- | --- | --- |
| 19 | `Unqualified Fusion native class or schema version` | `re/Fusion/examples/.f3d/example2.f3d`, 9 members of each bundle |
| 4 | `Converted Form BRep embeds a T-spline program absent from its parts` | `re/Fusion/LocalOracle/FormDocuments/Stale/{Box,Plane}{Brep,Member}Moved.f3d` |
| 4 | `Fusion primary offsets must increase in identity order` | `re/Fusion/Reconstruction/ContainerAuthoring/{Generated,StoredOnly,StoredFolders,StoredDirectories}/AuthoredParameter.f3d` |
| 1 | `Missing directories or unaccounted Fusion container members` | `re/Fusion/Reconstruction/ContainerAuthoring/OrderedAct/AuthoredParameter.f3d` |
| 2 | `Unsupported Fusion journal qualified field` | `re/Fusion/LocalOracle/FormDocuments/Cache/{Box,Plane}SurfNone.f3d` |
| 2 | `TSM record order or kind is unsupported: tol` | `re/Fusion/LocalOracle/FormDocuments/Intervals/Box/Single.f3d`, `.../Intervals/Plane4x4/Single.f3d` |
| 2 | `invalid literal for int() with base 10` | `re/Fusion/LocalOracle/FormDocuments/Intervals/Plane4x4/{ColumnRow,Half}.f3d` |
| 1 | `Only positive ring-torus carriers are qualified` | `re/Fusion/LocalOracle/FeatureAuthoring/Authored/vendor_RoundRimChain.f3d` |

### Material failures

| Count | Projection | Error |
| --- | --- | --- |
| 251 | `NativeMaterial` | `Unexpected material in a body-free Fusion profile` |
| 27 | `NativeMaterial` | `Unsupported Fusion physical material projection` |
| 6 | `NativeMaterial` | `Qualified Fusion solids require one material package` |
| 1,381 | `ReadMaterial` | `Unknown native Fusion entity class` from `BuildGraph` |
| 11 | `ReadMaterial` | `Native Fusion semantic link requires an entity reference` |
| 2 | `ReadMaterial` | `Native material projection requires shared package and asset appearance` |

## Findings

### Kit-authored containers that Fusion rejected

`re/Fusion/Reconstruction/ContainerAuthoring/ContainerModel.md` records the native outcome of each diagnostic container. These five files are Kit-authored, not Fusion saves.

| File | Fusion 2706.1.17 outcome | Reader error |
| --- | --- | --- |
| `Generated/AuthoredParameter.f3d` | Rejected: segment metadata stream initialization failed | Primary offsets out of identity order |
| `StoredOnly/AuthoredParameter.f3d` | Rejected: same failure | Primary offsets out of identity order |
| `StoredFolders/AuthoredParameter.f3d` | Rejected: bulk loading rejected a negative offset | Primary offsets out of identity order |
| `StoredDirectories/AuthoredParameter.f3d` | Never opened; exploratory output with the same ACT order | Primary offsets out of identity order |
| `OrderedAct/AuthoredParameter.f3d` | Rejected: `BRepHistorySerializer` found no `Breps.BlobParts/` directory | Missing directories |

The reader rejects the same defects that Fusion rejects. These files stay unread.

### Form cache rewrites that Fusion rejected

`re/Fusion/LocalOracle/FormDocuments/Cache/Probe.json` holds the native import of each rewrite. Fusion 2706.1.17 failed to import `PlaneSurfNone.f3d` and `BoxSurfNone.f3d` with `InternalValidationError : isSuccessfullyOpened && status.isOk()`. A research script rewrote their `t_spl_sur` caches with approximation level none. These files stay unread.

### Stale Form caches that Fusion opens

`re/Fusion/LocalOracle/FormDocuments/Stale/Probe.json` shows that Fusion 2706.1.17 opens `BrepMoved` and `MemberMoved` for both the plane and the box. The loaded body equals the control body. Fusion rejects `NoBrep`, which Kit reads. To be fixed.

### Spindle torus carriers

`vendor_RoundRimChain.f3d` holds a torus with major radius 0.2 cm and minor radius 0.3 cm. Fusion saved it after a 3 mm fillet on a 2 mm rim. `TorusCensus.py` reads every torus carrier in the corpus.

| Kind | Records | Files |
| --- | --- | --- |
| Ring, minor positive | 276 | 53 |
| Ring, minor negative | 98 | 10 |
| Apple, minor greater than major | 24 | 3 |

The three apple-torus files are `vendor_RoundRimChain.f3d`, `vendor_RoundHoleRim.f3d` and `vendor_RoundPostEdge.f3d` in `re/Fusion/LocalOracle/FeatureAuthoring/Authored`. The last two already read, because their tori sit in typed views that fell back to the exact journal. Rule: a torus carrier needs a positive major radius and a nonzero minor radius whose magnitude differs from the major radius. The horn torus, with equal magnitudes, has no corpus record and stays refused.

### TSM edge knot rows

`TsmCensus.py` lists the record order of all 253 TSM members. Two members hold a `106ek` block: `Intervals/Plane4x4/Single.f3d` and `Intervals/Box/Single.f3d` in `re/Fusion/LocalOracle/FormDocuments`. Fusion wrote them after it rewrote an inconsistent edge interval.

- The block has one row per `e` row, in edge order.
- Each row has one number. Its text equals the second field of its `e` row.
- The block sits after the `100edges` and `100verts` crease blocks, after any `105` symmetry block, and before `50000grip`. Extension blocks are in ascending order of their numeric prefix.

The TSM reader now reads the block into `KnotSurface.EdgeKnots`. These two files then stop in the converted patch program, as the next section says.

### Fractional patch programs

`PatchWords.py` shows the patch program words of the four interval files. Fusion writes each word as a double in `%.17g` form, for example `0.5`, `-2.9999999999999991` and `2.2204460492503131e-16`. `ReadPatchRow` in `src/convert/formats/Fusion/BrepCodec/Journal/Spline/Reading` parses every word with `int`. That folder belongs to the Form conversion writer, so this work does not change it. The four files stay unread:

- `Intervals/Plane4x4/Half.f3d`
- `Intervals/Plane4x4/ColumnRow.f3d`
- `Intervals/Plane4x4/Single.f3d`
- `Intervals/Box/Single.f3d`

### Stale Form bodies

`Documentation/Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md` shows that Fusion opens a Form document whose BRep cache disagrees with its TSM member. `ReadDocument` no longer runs `CheckFormBreps`. `EmitParsed` still runs it, so Kit never writes such a document. The four stale files read, and their round trip stops at `EmitParsed`.

### Example class versions

`InferVersions.py` decodes every record of each older class version with the next catalog version, minus 0, 1 or 2 members. `VersionLayouts.json` holds the result. A layout is adopted only when exactly one member set decodes every record.

| Class | Saved | Records | Layout |
| --- | --- | --- | --- |
| `ACTComponent` | 0 | 22 | Version 1 members, base `CommonBaseEntity` |
| `ACTComponentsRoot` | 0 | 10 | Version 1 members, base `CommonBaseRootCollection` |
| `ACTInstance` | 0 | 68 | Version 1 members, base `CommonBaseEntity` |
| `ACTInstances` | 0 | 22 | Version 1 members, base `CommonBaseGroupEntity` |
| `ACTInstancesRoot` | 1 | 10 | Version 2 members, base `CommonBaseRootCollection` |
| `DRMatrix` | 14 | 26 | Version 15 members |
| `Parameter` | 8 | 246 | Version 9 members without `actIdentifier` |
| `Joint` | 5 | 1 | Version 6 members without `useConstraintAlignment` |
| `DcGroupFeature` | 1 | 1 | Ambiguous: `insertedModel` or `suppressed` |
| `VisualAnalyses` | 9 | 10 | Ambiguous: any one of 11 `u32` creation indices |
| `CommonDataAssetSettings` | 17 | 10 | Ambiguous: `perspWithOrthoFaces`, `pmiSettings` or `rNamedLights` |
| `ParameterTable` | 3 | 1 | Ambiguous: `expandedNodeSet` or `groupOrder` |
| `Parameter` | 7 | 8 | Ambiguous: `actIdentifier` and one of six 1-byte members |
| `DRMatrix` | 12 | 3 | Ambiguous: `LinearOffsetOnPeriodicFace` and one of many members |

The ACT classes moved from the `CommonData` class space and its base classes to ACT bases. Their own members did not change. `BuildHistoric.py` writes the eight unique layouts to `src/convert/formats/Fusion/DocumentCodec/Vocabulary/HistoricClasses.json`.

### Opaque records

The metadata index bounds every bulk record. A record whose class version has no schema can therefore keep its bytes whole. The design reader and the ACT and Browser readers now give such a class an opaque schema:

- The schema takes its base from the metadata row and has no members.
- Its group holds the record bytes after the entity frame, in `EntityGroup.Opaque`.
- The group ends the lineage, because the bytes of the base groups follow the own members.
- A value object of an opaque class still raises, because no index bounds it.

The 34 classes absent from the catalog and the six ambiguous versions use this rule.

### Example record rules

`RecordFailures.py`, `AtomSpy.py`, `RefSpy.py`, `DumpClass.py` and `TryNamed.py` found four more record causes in the unique example documents. Each has a general rule.

**Flag bytes.** `DiameterDimensionInfo.needExtendArcForDim` is a `bool` member. In `example2.f3d` and its siblings it holds the bytes `0x02`, `0x0a` and `0x20` as well as 0. The value class and its base `C2C193F2` have metadata rows at versions 2 and 3, which equal the catalog. Every other member of the 417-byte records decodes, and the next member starts right after the byte. Rule: a saved `bool` member is one byte. 0 is false and any other byte is true. The reader keeps a byte above 1 as an integer, and the writer writes it back. Structural presence flags in frames and references stay 0 or 1.

**Secondary tag ids.** `profileEdgeTagData.secondaryTagId` in `SketchCurveRecipe` and `SketchRegionRecipe` holds odd values from `0x181` to `0x18f`. Rule: the field is a free `u64` identity, like `tagId`. `SketchFields.py` no longer limits it to 0.

**Cross-document references.** `JointOccurrence.rAssyConstr` holds a cross-document reference. Its type GUID `7F5A0426` is `Joint`, which derives from `AssyConstraint` `B96995C7`. The member type asks for `AssyConstraint`. `Joint` lives in the other document, so the referring document's profile has no schema for it. Rule: the reference check follows the target lineage only for classes that the profile defines. A cross-document target of a foreign class keeps its stated type GUID.

**Value class metatypes.** Named metadata on `DcExtrudeFeature`, `DcPCBBaseBody` and `DcPCBExtrude` records has the type name `EA46307F-1FD6-4B11-9C97-353B74F5E413`, the GUID of the value class `VisualMaterialValue`. The five values decode to the exact record end as value objects of that class. Rule: a named metadata type name is an intrinsic or reference metatype, `Vector`, or the GUID of a value class in the profile. A GUID type holds one value object of that class.

### ASM integer width

`AsmHeads.py` reads the header of every BRep member in the corpus.

| Member | Header | Scale | Members | Files |
| --- | --- | --- | --- | --- |
| `.smbh` | `ASM BinaryFile8` | 50 | 1,456 | 1,415 |
| `.smb` | `ASM BinaryFile8` | 10 | 1,375 | 1,334 |
| `.smb` | `ASM BinaryFile4` | 10 | 41 | 3 |
| `.smbh` | `ASM BinaryFile4` | 40 | 35 | 3 |
| `.smbh` | `ASM BinaryFile4` | 30 | 2 | 3 |

The three files are `re/Fusion/examples/.f3d/example2.f3d` and the two copies of `example1.f3z`. All members have ASM version 23200. `NarrowAsm.py` and `TryWidth.py` show the rule:

- The digit after `ASM BinaryFile` is the integer width, 4 or 8.
- The four header integers have that width.
- Tags 4, 12, 21 and 23 hold integers of that width. Tag 18 has a length of that width.
- Every other token is the same at both widths.
- The first header number of a history journal varies: 50, 40 or 30. Snapshots always hold 10.

`BrepHeader.IntWidth` now records the width. The token reader and the journal and snapshot writers use it. The history scale is any positive number, and the writers write the stored value.

The example journals also exceed Kit's size quotas. The largest member has 9,258,923 bytes, 5,139 entities and a `delta_state` record of 321,648 tokens. `JournalLimits.py` now holds the quotas: 32 MiB per member, 2^18 entities, 4,096 states, 2^16 roots, 2^14 boards per state, 2^18 board changes and 2^20 tokens per record.

### Browser stream tail

`example1.f3z` member 7 ends its Browser bulk stream with 5,372 bytes after the last indexed record. All 28 metadata owners have index entries, and object 28 decodes to its own end. `SlackSpy.py` shows that the tail holds 15 zero bytes and then record headers with type code `292` and object ids 21, 22 and 23. These are stale records of an earlier save, like the ACT tail in `Documentation/Gotchas/Conversion/Fusion/Records/FusionActBulkSlack.md`. Rule: the Browser stream may end with bytes after its final record, as the ACT stream does. The reader keeps them in `BulkSlack` and the writer writes them back.

`Sweep-slack.json` applies the rule. `Compare.py width slack` shows no fixed, broken or changed document. Member 7 then stops in its material package. See [Material resource folders](#material-resource-folders).

### Graphics caches

After these rules, five unique example documents stop in the OGS graphics cache. Member numbers follow the bundle order of `ReadBundle`, as in the sweep. `MemberOrder.py` maps them to the sorted ZIP order that `ExampleRecords.py` uses. `GraphicsSpy.py`, `AttrSpy.py` and `MeshTail.py` show three causes:

| Document | Cause |
| --- | --- |
| `example1.f3z` members 5 and 3 | Attribute classes `FProteinEffectAttribute` and `OverrideTransformAttribute` have no field rules. `OverrideTransformAttribute` holds 16 `f32`, a flag and a linked `PersistentPassiveNodePath` object. |
| `example1.f3z` member 0 | The serializer header lists `F360InstanceNode` version 0 and lacks `GraphicsBlobFeatures`. Only version 1 has a layout. |
| `example1.f3z` members 6 and 8 | The world names only part of `stream_mesh_000`: 64,048 of 128,096 bytes, and 35,460 of 91,620 bytes. |

Fusion opens a document without its graphics cache, as `Documentation/Gotchas/Conversion/Fusion/FusionGraphicsCacheOmission.md` shows. These layouts still need their own study.

### Document material

`MaterialCensus.py` reads every document and lists each reference to a material asset by the class that holds it. `MaterialCensus.json` keeps one row per document.

| Holder | Field | Documents |
| --- | --- | --- |
| `Body` | `physicalMaterial` | 1,427 with an asset, 11 empty |
| Mesh body `EA90DA22` | `physicalMaterial` | 84 |
| Form body `FA1F0081` | `physicalMaterial` | 247 |
| `ComponentBase` | `defaultPhysicalMaterial` | 1,266 with an asset, 429 empty |

In every read document the body records name at most one physical asset, and the components name at most one default asset. In 20 documents the body asset differs from the component default, and the package holds both. The old projection failed on these shapes:

| Count | Shape | Old error |
| --- | --- | --- |
| 163 | No body, component default only | `Unexpected material in a body-free Fusion profile` |
| 59 | Mesh bodies only | `Unexpected material in a body-free Fusion profile` |
| 29 | `Body` records without a BRep part | `Unexpected material in a body-free Fusion profile` |
| 22 | Package with two physical assets | `Unsupported Fusion physical material projection` |
| 5 | Bodies with no physical reference, package with only an appearance | `Unsupported Fusion physical material projection` |
| 6 | Bodies with no physical reference and no package | `Qualified Fusion solids require one material package` |

Rule: the document material is the physical asset that the body records name through `physicalMaterial`. Brep, mesh and Form bodies all count. Without one, it is the asset that `ComponentBase.defaultPhysicalMaterial` names. Without either, the document states no material, and the projection returns the default `MaterialSpec`. Two different assets at the same level stay an error. No corpus document has them.

A body whose `physicalMaterial` reference is empty has an undefined material. Fusion reports zero density for such a body, and its material getter fails. `Documentation/Gotchas/Conversion/Fusion/Materials/UndefinedBodyMaterial.md` and `re/Fusion/LocalOracle/RectangleAuthoring/MassProbe.json` hold the proof. So the projection raises `Fusion body has an undefined physical material` for these documents. It does not return the default.

`Sweep-material.json` shows all 284 failures pass, and the other 1,376 projections keep their digest. Eleven of the 284 have bodies with an empty physical reference. `Sweep-material.json` still shows them with the default. Since the undefined body rule they raise:

- `re/Fusion/LocalOracle/Authored/{ProductionEdited,ProductionExtrusion,ProductionReemitted,kit_production_container}.f3d`
- `re/Fusion/LocalOracle/Authored/vendor_{independent_extrusion,production_container,production_document,production_edited}23mm.f3d`
- `re/Fusion/LocalOracle/RectangleAuthoring/Initial/{ProductionCuboid,vendor_ProductionCuboid37mm}.f3d`
- `re/Fusion/Reconstruction/ContainerAuthoring/FreshExtrusion/AuthoredExtrusion.f3d`

The graph projection `ReadMaterial` runs only where `BuildGraph` builds. `BuildGraph` serves the narrow vendor profile and refuses every class outside the authored vocabulary. That guard is not a read failure, so this work leaves it. Past the graph, the same eleven documents fail because the body names no physical material. `mass_probe_ProductionCuboid.f3d` and `mass_probe_ProductionExtrusion.f3d` in `re/Fusion/LocalOracle/RectangleAuthoring` use a customized appearance color, which `ReadMaterial` refuses.

### Material resource folders

After the Browser tail rule, `example1.f3z` member 7 stops at `Unsupported material asset folders`. It is the only corpus document that does. Its single material package holds 37 assets.

`PackageSpy.py`, `ResourceSpy.py` and `CoreSpy.py` show the layout. The asset folder links `AssetData`, `Resources` and `Schemas`, in that order. Every other package links only `AssetData` and `Schemas`. `Resources` is a tree of folders. Each folder holds a `core.xml` asset node whose name is the folder name, and a `cnx.xml`. A `cnx.xml` either links child folders by name, or lists resources with the same metadata as the `AssetData` and `Schemas` resources. A resource file lies next to the `cnx.xml` that lists it. Here the tree is `Resources/<asset>/thumbnail/0/<resource>`, six times, and each resource is a PNG thumbnail.

Rule: an asset folder links either `AssetData` and `Schemas`, or `AssetData`, `Resources` and `Schemas`. The reader reads the `Resources` tree into `MaterialPackage.Resources`. A folder holds either child folders or resources, never both and never neither. Folder and file names are single path segments.

The package then stops at `Conflicting Fusion material definition identity`. `DefinitionSpy.py` shows that each asset has its own definition root in `DefinitionIteratorProperties.bin`. Several appearance assets share one definition id but differ in `UIName` and `thumbnail`. A `thumbnail` names a file in `Resources`. `DefinitionCensus.py` reads all 1,679 corpus packages and 9,530 assets. 1,372 definition ids are shared by more than one asset. In 1,368 the definitions are equal. The other 4 are in this document and its copy, and only `UIName` and `thumbnail` differ. Every shared id keeps one schema. Rule: assets that share a definition id share its schema. Their definition values are their own. The encoder already writes one definition per asset, so the rule loses nothing.

The package writer does not write `Resources` yet. The material writers are outside this task, so `EmitMatPart` refuses a package with resources. The change it needs is in [Writer changes](#writer-changes).

### Image parts

With the package read, member 7 stops at `Unsupported Fusion document part`. `PartSpy.py` shows two files `Images.BlobParts/Image.<uuid>.png`. `ImageCensus.py` finds image parts only in this document and its copy. Both are PNG files. The Design bulk stream names each one as a UTF-16 string.

`ImageRefs.py` shows that each name is the `partName` of one primary `ImageSerializer` record (`830A2A2B`). Members 1, 2 and 4 hold `ImageSerializer` records with an empty `partName` and no image part.

Rule: an image part is a PNG file named `Images.BlobParts/Image.<uuid>.png`. Every nonempty `ImageSerializer.partName` names one image part, and every image part is named. The reader keeps the parts in `DocumentModel.Images`, and `EmitParsed` writes them back unchanged.

Member 7 then reads. Its round trip stops at the `EmitMatPart` guard for resource folders. `BodyMats.py` shows that its bodies name three physical assets and its components two defaults. `NativeMaterial` raises `Fusion document uses more than one physical material`. Its `DocumentSpec` holds one material for one body, so this stays an error.

## Sweep after the first rules (`Sweep-current.json`)

Rules applied: spindle tori, TSM edge knots, stale Form bodies, historic class versions and opaque records.

| Measure | Pass | Fail | Other |
| --- | --- | --- | --- |
| Files | 1,697 | 12 | |
| Documents, `ReadDocument` | 1,695 | 30 | |
| Round trip of read documents | 1,691 | 4 | The four stale Form files, refused by `EmitParsed` |
| `NativeMaterial` | 1,376 | 284 | 35 body-free without material |

`Compare.py before current` shows 5 fixed documents, no broken document, and no changed model, round trip or material result.

The example documents now stop later:

| Count | Error | Cause |
| --- | --- | --- |
| 9 | `Invalid Fusion feature scalar` | Nonzero sketch secondary tag ids |
| 6 | `Unsupported Fusion geometry signature` | `ASM BinaryFile4` BRep members |
| 2 | `Fusion entity reference target class is incompatible` | `JointOccurrence.rAssyConstr` |
| 2 | `Unsupported Fusion entity named metadata metatype` | Named metadata typed by a value class GUID |

## Sweep after the record and width rules (`Sweep-flags.json`, `Sweep-width.json`)

`Sweep-flags.json` adds flag bytes, free secondary tag ids and foreign cross-document targets. `Compare.py material flags` shows no fixed, broken or changed document. The examples then stop at the BRep header.

`Sweep-width.json` adds value class metatypes, the ASM integer width and the journal quotas. `Compare.py flags width` shows 7 fixed documents, no broken document and no changed model, round trip or material result. All 7 round-trip.

| Measure | Pass | Fail | Other |
| --- | --- | --- | --- |
| Files | 1,698 | 11 | |
| Documents, `ReadDocument` | 1,702 | 23 | |
| Round trip of read documents | 1,698 | 4 | The four stale Form files |
| `NativeMaterial` | 1,667 | 0 | 35 body-free without material |

## Sweep after the Browser tail rule (`Sweep-slack.json`)

`Compare.py width slack` shows no fixed, broken or changed document. The counts equal `Sweep-width.json`.

## Final sweep (`Sweep-after.json`)

`Sweep-after.json` adds the material resource folders, shared definition ids, image parts and the undefined body material. `Compare.py slack after` shows 2 fixed documents, both copies of `example1.f3z` member 7. No document broke, and no model or round trip changed. The 11 documents with an undefined body material changed their `NativeMaterial` result from the default to an error.

## Before and after

`Compare.py before after` shows 14 fixed documents, no broken document and no changed model or round trip. 273 `NativeMaterial` results changed from failure to a pass. The other 11 of the 284 old failures now fail for the undefined body material.

| Measure | Before | After |
| --- | --- | --- |
| Files that read | 1,692 of 1,709 | 1,698 of 1,709 |
| Documents, `ReadDocument` | 1,690 of 1,725 | 1,704 of 1,725 |
| Round trip of read documents | 1,690 of 1,690 | 1,698 of 1,704 |
| `NativeMaterial` pass, fail, no material | 1,371, 284, 35 | 1,656, 13, 35 |
| `ReadMaterial` pass, fail, no `Body` | 212, 1,394, 84 | 212, 1,408, 84 |

Documents that still fail:

| Count | Error | Documents | Reason |
| --- | --- | --- | --- |
| 4 | Primary offsets out of order | `ContainerAuthoring/{Generated,StoredOnly,StoredFolders,StoredDirectories}/AuthoredParameter.f3d` | Kit research files that Fusion rejected |
| 1 | Missing directories | `ContainerAuthoring/OrderedAct/AuthoredParameter.f3d` | Kit research file that Fusion rejected |
| 2 | `Unsupported Fusion journal qualified field` | `FormDocuments/Cache/{Box,Plane}SurfNone.f3d` | Rewrites that Fusion failed to import |
| 4 | `invalid literal for int()` | `FormDocuments/Intervals/...` | Patch words are doubles; the fix is in the Spline folder |
| 2 | Graphics serializer versions | `example1.f3z` member 0, both copies | `F360InstanceNode` version 0 |
| 2 | `OverrideTransformAttribute` | `example1.f3z` member 3, both copies | No field rules |
| 2 | `FProteinEffectAttribute` | `example1.f3z` member 5, both copies | No field rules |
| 4 | Trailing graphics mesh bytes | `example1.f3z` members 6 and 8, both copies | Mesh stream partly referenced |

Round trips that still fail: the four stale Form files, which `EmitParsed` refuses, and both copies of member 7, which `EmitMatPart` refuses.

`NativeMaterial` failures: the 11 undefined body materials and both copies of member 7, whose bodies name three physical assets.

## Writer changes

These changes lie outside this task:

- `MaterialCodec/Package/Envelope/PackageEntries.py` should link `AssetData`, `Resources` and `Schemas` when `MaterialPackage.Resources` is set, and write each folder's `core.xml`, `cnx.xml` and resource files. `EmitMatPart` can then drop its guard.
- The patch program words of `Intervals/` need `ReadPatchRow`, `PatchCell` and `WritePatches` in `BrepCodec/Journal/Spline/`.

## CI fixes on the merged branch

The squash merge `cf93062c3` failed 16 Fusion compatibility tests.

- `TsmArchiveTests.py::TestTsmArchive`, 12 cases. The new `EdgeKnots` field of `TsplineSurface` added an empty key to every semantic hash. The code was wrong, not the digests. A surface with a `106ek` block is now a `KnotSurface`, a subclass that adds `EdgeKnots`. `TsplineSurface` equals its form before the merge. `TsmEncode.py` reads all 253 corpus TSM members with the old and new reader. The 251 members that read before keep the same semantic hash and their byte round trip. The two members with the block now read.
- `DocumentArchiveTests.py::TestUnknownPart` writes a member `Images.BlobParts/Unknown.bin` and expects `Unsupported Fusion document part`. The image rule covers only `Image.<uuid>.png`. The reader now sends only such names to the image reader. Other members of the folder stay unsupported document parts.
- `ReadGapRuleTests.py::TestDefaultMat`, 2 cases. `DefaultMatSpy.py` shows that Fusion stores an empty `physmat_Label` in both files. The default asset is library steel with density 7,850. The material projection now reads the name from `physmat_Label`, so the name is empty. The test expectation was wrong. It now expects the empty label and the density.
- `SavedReadTests.py::TestNewestPick`. The historic layouts add `DRMatrix` version 14 and `Parameter` version 8 to the catalog. The test expected two versions per class. It now lists the exact versions of each class and still checks that an unversioned pick takes the newest.

## Status

Done for this pass. The graphics cache layouts of `example1.f3z` need their own study.
