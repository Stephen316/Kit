# Author assemblies that reference other designs

`EmitAssembly` writes a new Fusion root assembly that references other cloud designs.
The targets can be Kit parts from `MakeFusionDoc` or Kit subassemblies from `EmitAssembly`.
The package is `convert.formats.Fusion.LinkAuthor`.
It is pure Python and has no Fusion dependency.

## API

| Name | Signature | Purpose |
| --- | --- | --- |
| `EmitAssembly` | `EmitAssembly(Request: AssemblySpec) -> bytes` | Check the request, make the base design and write the F3D archive |
| `LinkDocument` | `LinkDocument(BaseSpec: DocumentModel, Request: AssemblySpec) -> DocumentModel` | Add the references to an unlinked empty base model |
| `CheckAsmSpec` | `CheckAsmSpec(Value: object) -> AssemblySpec` | Validate a request and normalize its matrices |

| Model | Fields |
| --- | --- |
| `AssemblySpec` | `Base: DocumentSpec`, `Targets`, `Placements`, `Joint: RigidJoint \| None`, `SourcePath` |
| `LinkTarget` | `DisplayName`, `LineageUrn`, `VersionUrn`, `Target: DocumentModel` |
| `PlacedPart` | `TargetIndex`, `Matrix` with 16 values, `Grounded` |
| `RigidJoint` | `FirstIndex`, `SecondIndex`, two different placement indices |

The base must be a `parameter` document spec.
The request needs 1 to 64 targets with different asset GUIDs.
Each target must have exactly one placement.
The matrix is row-major in centimetres and must be a rigid transform that keeps orientation.
`CheckAsmSpec` raises `ValueError` for every other request.

## What the builder writes

The builder adds the records of each placement, each ground pin and the joint to the three segments.
It also changes the existing records that list instances, features, observers and tables.

| Item | Rule |
| --- | --- |
| Design object numbers | `XRefManager`, then the records of each placement, its ground pin and the joint, from `NextId` |
| ACT object numbers | Four for each placement: instance, data, `ACTRefdTable` and data copy |
| Browser object numbers | One browser entry for each placement |
| Feature numbers | From `operationSeedId`, in the order placement, its pin, next placement, joint |
| Instance numbers | From `nextInstanceId` of the ACT instance root |
| Link GUIDs, cache GUIDs and context tokens | New random values for each output |
| Context `RevisionId` | `DocumentId` of the target model |
| Asset link `PhysicalGuid` | Target `physicalChangeGuid` property, or the zero GUID |
| Identity placement | `MatrixValue(None)` |
| New classes | Appended to the segment class table with new type codes |

A nested subassembly target adds one occurrence record for each of its children.
The builder reads the child transforms from the target model.

## `ACTRefdTable` fields

The saved native controls carry five `ACTRefdTable` members for schema version 1.

| Member | Fusion type | Content in the native controls |
| --- | --- | --- |
| `ACTRefdTableEntries` | Map from text to a pair of a text set and an unsigned count | Target component identifier, tracked change types and reference count |
| `RevisionGuidForChangeType` | Map from text to GUID | Equal to `revisionGuidForChangeType` of the target ACT table |
| `CachedRevGuid` | GUID | Equal to `RevisionGuid` of the target ACT table |
| `RefdDocLinkName` | Text | Link GUID |
| `RefdAssetGuid` | GUID | Target asset GUID |

The map value is a plain pair without member names.
In the controls the second value is 1 for a single reference and 2 for Part A after the update.
Kit now calls this value `referenceCount` instead of `entryWord`.
How Fusion lowers or removes an entry is not confirmed by a black-box experiment.

| Controls | `referenceCount` values |
| --- | --- |
| `R1_part_a` to `R8_updated_saved`, `S0_inserted` and `S1_saved` | 1 in every `ACTRefdTable` |
| `R9_archive` | 1 for the subassembly, 2 for Part A after the update |

How Fusion uses `CachedRevGuid` to find a stale reference is not confirmed by a black-box experiment.

## Tests

`tests/convert/formats/FusionCodec/Links/AssemblyAuthorTests.py` contains the new cases.
The cases did not run locally.

| Case | Check |
| --- | --- |
| `TestReplay` | Builds `R4_joint` from `R0_empty`, `P_A1_saved` and `S1_saved`, and compares every record with the native control |
| `TestKitNested` | Builds two Kit parts, a Kit subassembly and a Kit root, and checks links, contexts, matrices and a model round trip |
| `TestSpecReject` | Eight invalid requests raise `ValueError` |
| `TestZeroChange` | The asset header keeps a zero `PhysicalGuid` and rejects a zero link GUID |
| `TestSlots` | The next observer indices of `P_A1_saved` are 2, 3 and 1 |

`TestReplay` masks new GUIDs, link names, time stamps, hashes and compute caches.
All other fields of every new and changed record must equal the native values.

`tests/convert/formats/FusionCodec/Links/SavedRootTests.py` reads a Fusion export of the saved Kit root.
`tests/convert/formats/FusionCodec/Documents/Act/ActSlackTests.py` covers the Design tail limit.
These cases did not run locally either.

| Case | Check |
| --- | --- |
| `TestSavedRoot` | Reads `KitAsmRootSaved.f3d`, keeps 10 Design tail bytes, re-emits every stream byte-equal and round-trips the model |
| `TestSlackBound` | A Design tail of 17 bytes raises `ValueError` on read and on emit |
| `TestSlackGate` | A Design tail of 2 bytes is written back, and a Browser tail raises `ValueError` |
| `TestOtherTrail` | A Design tail of 17 bytes and a Browser tail of 2 bytes raise `ValueError` on read |

## Native acceptance

The acceptance ran in Fusion 2706.1.17 inside the acceptance project.
Each script closed every document that it opened, and each run ended with 0 open documents.

### Uploaded files

`AuthorParts.py` made the two parts with `MakeFusionDoc` and `EncodeDocument`.
`AuthorAssembly.py` made the subassembly and the root with `EmitAssembly`.

| File | Content | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `KitAsmPartA.f3d` | Cylinder, radius 10 mm, `heightA` 5 mm | 97,709 | `c8784c623d0b36aa8af552d73e59c1649b7735a87ba1d4a004cb4bcd73117b9f` |
| `KitAsmPartB.f3d` | Cylinder, radius 4 mm, `lengthB` 12 mm | 97,711 | `4a2b0ac06e8a06ad268c920b563d2e3760e56223d3d51b9518399f0158703609` |
| `KitAsmSub.f3d` | Part B, rotated 90° about Z, translation (2, 0, 1) cm | 57,799 | `ecfb252f4891e44d07a63c855352c44146c66eebb03114c0d13481f59bbe53ec` |
| `KitAsmRoot.f3d` | Part A grounded, the subassembly, and a rigid joint between them | 70,234 | `f6c389ffa898b7f2439aac9d795a80c875bb4ebbccb228e7f738ae30aa27b86c` |

Kit built the subassembly and the root only after Fusion had inserted their targets.
The scripts read the lineage and version URNs from these inserts.

| Placement in the root | Matrix (row-major, cm) |
| --- | --- |
| Part A | Rotation with cosine 0.6 and sine 0.8 about Z, translation (5, 2, 1) |
| Subassembly | 90° about X, translation (−3, 4, 0.5) |
| Part B inside the subassembly | 90° about Z, translation (2, 0, 1) |

### Native inserts of the Kit files

`ProbeAsmTargets.py` inserted each uploaded Kit file into a new Fusion design at the origin and exported it.

| Native export | Bytes | SHA-256 | Context `RevisionId` equals the Kit `DocumentId` | `PhysicalGuid` | Empty matrix fields |
| --- | --- | --- | --- | --- | --- |
| `ProbeKitAsmPartA.f3d` | 60,456 | `0164048f7926ca328743d4336ddffc5c3e5f1086f07d2bbc089acc1669a1ef28` | Yes | Zero | 6 of 6 |
| `ProbeKitAsmPartB.f3d` | 57,148 | `9fc8ccdd7525641b7fac88da404e73da2be60dc1d302150403a8c6bf168e950d` | Yes | Zero | 6 of 6 |
| `ProbeKitAsmSub.f3d` | 56,924 | `580ef05413157a45b5820dbc5f96c6af835bbb7968c25da3e8769b3260025f56` | Yes | Zero | 6 of 7 |

The seventh matrix of `ProbeKitAsmSub` is the nested Part B occurrence.
For Part A and the subassembly, Kit also built the same insert with `EmitAssembly`.
Each Kit output had the same new records and fields as the native insert.
Only new GUIDs, link names, revision GUIDs, time stamps, hashes, compute caches and identifiers made from object numbers differed.

### Root acceptance

`AcceptAsmRoot.py` opened the uploaded root, changed Part A, updated the references, saved the root and opened it again.

| Check | Root as uploaded | After the Part A edit | After `updateAllReferences` | After save and reopen |
| --- | --- | --- | --- | --- |
| References | Part A v1, subassembly v1 | Part A v1 out of date | Part A v2, subassembly v1 | Part A v2, subassembly v1 |
| References out of date | 0 | 1 | 0 | 0 |
| Occurrence paths equal to the expected paths | 3 of 3 | 3 of 3 | 3 of 3 | 3 of 3 |
| Bit-exact `transform2` matrices | 3 of 3 | 3 of 3 | 3 of 3 | 3 of 3 |
| Largest transform error | 0.0 | 0.0 | 0.0 | 0.0 |
| Grounded occurrences | Part A | Part A | Part A | Part A |
| As-built joint | `Rigid 1`, rigid, Part A to subassembly, healthy | Same | Same | Same |
| Timeline items, unhealthy items | 4, 0 | 4, 0 | 4, 0 | 4, 0 |
| Part A body height | 0.5 cm | 0.5 cm | 0.8 cm | 0.8 cm |
| Part B body height | 1.2 cm | 1.2 cm | 1.2 cm | 1.2 cm |

The three expected paths are `KitAsmPartA:1`, `KitAsmSub:1` and `KitAsmSub:1+KitAsmPartB:1`.
The expected matrix of the nested path is the product of the two Kit matrices.
The edit set `heightA` from 5.0 mm to 8 mm and saved Part A as version 2.
The root save made version 2 of the root.

The first acceptance run stopped at the first check, because the script read `AsBuiltJoint.healthState`.
This property does not exist.
The second run read the health from the joint timeline object.

### Fusion exports of the saved root

The Design `BulkStream.dat` of each Fusion export ends with 10 bytes after the last record.
These bytes differed between exports.
The [stream padding gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionStreamPadding.md) gives the details.
Kit now keeps such a tail as `ParsedSegment.BulkSlack`, up to 16 bytes, and writes it back unchanged.
All three exports now read in Kit, with 2 links and 2 contexts in each segment.

| Export | Bytes | SHA-256 | Kit read |
| --- | --- | --- | --- |
| `AcceptedKitAsmRoot.f3d` | 24,786 | `9addebfb2bc3621fad7fa87addecaf7aedf299d857f403ef149c0fe571288d27` | Yes |
| `ReexportFirstKitAsmRoot.f3d` | 24,794 | `c477e0657f2668775b5865d9c6a466628314c22619fcfb958b0b5d92a710f9eb` | Yes |
| `ReexportSecondKitAsmRoot.f3d` | 24,804 | `eab25cb1ad2b67dfd57e87f8050f435d654f8628ffa14775327304e3d08fd5c7` | Yes |

[`KitAsmRootSaved.f3d`](../../../../re/Fusion/LocalOracle/LinksConfigs/Fixtures/KitAsmRootSaved.f3d) is a sanitized copy of `AcceptedKitAsmRoot.f3d`.
It has 24,439 bytes and SHA-256 `59dee7b0ff21f3085c7d90dcbe80e80b84ddc2e509d4378a05abfbeedc509b07`.
[`Sanitize.py`](../../../../re/Fusion/Reconstruction/LinksConfigs/Sanitize.py) replaced cloud lineage keys and the home path with placeholders.
[`AsmAcceptance.json`](../../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json) records all values without cloud identifiers.

## Limits

- The joint is a rigid as-built joint. Kit has no native control for a revolute joint, so the builder does not write one.
- A subassembly target can have direct children only. Deeper nesting raises `ValueError`.
- Each child of a subassembly target needs an explicit matrix. A child at the identity raises `ValueError`.
- The target model must be the exact uploaded file, as the [context revision gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionContextRevision.md) explains.
- The base must be an empty Kit `parameter` design without links.
- `ReadDocument` rejects a Design tail longer than 16 bytes.

## Related information

- [External references change](FusionExternalReferences.md)
- [Context revision gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionContextRevision.md)
- [Zero physical GUID gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionZeroPhysical.md)
- [Observer index gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionObserverSlots.md)
- [Identity matrix gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionIdentityMatrix.md)
- [Kit revision gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionKitRevisions.md)
- [Stream padding gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionStreamPadding.md)
