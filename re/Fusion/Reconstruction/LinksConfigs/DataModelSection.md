# Draft section: external references and configurations

This draft is for the lead to merge into `Documentation/Reference/Research/FusionDataModel.md`.

## External references

A Fusion design that inserts another cloud design keeps the link in five places.
Kit reads and writes all five places through `ReadDocument` and `EmitParsed`.

| Layer | Member | Typed model | Join key |
| --- | --- | --- | --- |
| Root link table | Root `Manifest.dat` | `RootManifest.Links` | Link GUID |
| Asset link rows | Asset `Manifest.dat` | `AssetHeader.Links` | Link GUID |
| Version contexts | Each `MetaStream.dat` | `MetaSegment.Contexts` | Link GUID and token |
| Cross-document references | Entity payloads | `CrossRef` | Token |
| Bundle graph | `RedirectionsStream.dat`, `DesignDescription.json` | `DocRedirects`, `BundleModel` | `neutronRole` equals link GUID |

### Root manifest

The root manifest has an ordered ancestry GUID list after the version table.
The link table follows the ancestry list.
The asset GUID and the terminal follow the link table.

| Link field | Wire type | Content |
| --- | --- | --- |
| `LinkId` | GUID | Link GUID |
| `SourcePath` | UTF-16 text | Export target path |
| `CachePath` | UTF-16 text | Local cache file of the referenced design |
| `XrefPath` | UTF-16 text | Local `_XRef_` cache file with an `_LV<version>` suffix |
| Words | Four `u32` | `2, 4, 1, 0` in all observed links |
| `Properties` | Count and UTF-16 pairs | Named text values |

| Property | Content |
| --- | --- |
| `LineageId` | Lineage URN of the referenced design |
| `LineageUrn` | Same value as `LineageId` in all 18 fixture links |
| `toDocDisplayName` | Name of the referenced design |
| `URL` | Version URN, `urn:adsk.wipprod:fs.file:vf.<key>?version=<n>` |
| `linkedAssetGUID` | Asset GUID of the referenced design |
| `linkClassification` | `OriginalDesign`, present after a cloud save |

The terminal is an export label for API exports.
It is a display name and a lineage URN for cloud bundle members.

### Asset manifest

The asset manifest stores its kind and subtype as one text, separated by a zero character.
Each asset link row has the fields in the table.

| Field | Content |
| --- | --- |
| `LinkId` | Root manifest link GUID |
| `AssetId` | Asset GUID of the referenced design, equal to `linkedAssetGUID` |
| `SnapshotId` | Snapshot GUID of the referenced design |
| `LinkWord` | 1 in all observed rows |
| Marker | 2 in all observed rows |
| `PhysicalGuid` | `physicalChangeGuid` asset property of the referenced design, or the zero GUID when that property is absent |

### Version contexts

The `u32` after `NextId` in `MetaStream.dat` is the context count.
The previous model called this field `Reserved`.
The contexts come before the property list.

| Field | Wire type | Content |
| --- | --- | --- |
| `Token` | `u64` | Key for `CrossRef` values in this segment |
| `LinkId` | UTF-16 text | Root manifest link GUID |
| `RevisionId` | UTF-16 text | Document GUID of the referenced cloud design, the same for every version |
| `VersionUrn` | UTF-16 text | Version URN, equal to the link `URL` in all 54 fixture contexts |
| `AssetId` | UTF-16 text | Equal to `linkedAssetGUID` in all 54 fixture contexts |
| `SegmentId` | `u32` | 0 for Design and Browser, 1 for ACT |

Each segment has one context for each link.
The Design and Browser contexts of a link share one token.
The ACT context of the same link has a different token.

cadmpeg `docs/formats/f3d.md` describes the context as a token, an asset GUID and optional revision fields.
The cadmpeg documents use the CC-BY-4.0 licence.
In the Kit controls, the second field always equals a root manifest link GUID.

### Cross-document references

The observed cross-document reference has 60 bytes.

```text
u8        present = 1
u64       target object number
u8        cross_document = 1
u64       version context token
u8        0
LP-ASCII  target class GUID, 36 characters
u8        0
```

Each token equals a context token of the same segment.
The target object number addresses a record in the referenced design.
The class GUID names the class of the target record.

| Target | Class GUID |
| --- | --- |
| Design component | `E03784ED-5E19-4E14-B9F2-3B07017018CD` |
| ACT component | `D956D02C-2806-4E57-8B2E-EFA323A5C2B8` |

cadmpeg documents a different cross-document grammar with a segment number, an asset GUID, a link name and an optional version URN.
It also documents a 51-byte inline-typed local form with length byte `0x24` after the object number.
Kit did not find either form in 15 native controls, 1,004 study F3D files or the example1 members.
`ReadRefMut` raises `Unsupported inline-typed Fusion entity reference` for the `0x24` byte.

### Records of one external instance

The difference between `R0_empty` and `R1_part_a` gives the records of one external instance.

| Segment | New record | Function |
| --- | --- | --- |
| Design | `XRefManager` | Owner of the external references of the component |
| Design | `ComponentInstance` | Occurrence with `initialTransform`, `transform` and `rTargetComponent` as `CrossRef` |
| Design | `DcComponentInstance` | Compute node of the occurrence, primary and continued records |
| Design | `DynamicUpdateData`, two records | `timeStamp` and `xRefPredecessorsHash` |
| Design | `DcXRefPCIFeature` | Timeline feature "Component Insert" with the placement transform |
| Design | `DcStatus` | Compute status of the feature |
| Design | `ProgenitorTable` | Progenitor table of the feature, primary and continued records |
| Design | `DcOccurrence` | Occurrence path and transform state |
| ACT | `ACTInstance` | Instance with `ACTRef` and `targetComponent` as `CrossRef` |
| ACT | `RevGUIDACTDataMany`, two records | Revision GUID for each tracked change type |
| ACT | `ACTRefdTable` | Referenced table with tracked change types, reference count, link name and revision map |
| Browser | `FusionComponentInstanceBrowserEntry` | Browser node with `CrossRef` subjects into the target |

Existing records also change.
Examples are the ACT table, the instance roots, the component, the design fragment and the compute and dependency managers.

The occurrence matrix is stored in four Design fields of `R1_part_a`.
These are `ComponentInstance.initialTransform`, `ComponentInstance.transform`, the `DcXRefPCIFeature` placement and the `DcOccurrence` state.
The matrix is row-major with the translation in the fourth column, in centimetres.
No graphics value of `R1_part_a` equals this matrix.
A typed change of these four fields moves the occurrence in Fusion.

### `ACTRefdTable`

`ACTRefdTable` has six members for schema version 1.
The member names and types came from earlier binary inspection, which was removed.
The Saved and Content columns come from the controls.

| Member | Fusion type | Saved | Content in the controls |
| --- | --- | --- | --- |
| `ACTRefdTableEntries` | `map<wstring, pair<set<string>, unsigned int>>` | Yes | Target component identifier, tracked change types, reference count |
| `RevisionGuidForChangeType` | `map<string, uuid>` | Yes | `revisionGuidForChangeType` of the target ACT table |
| `CachedRevGuid` | `uuid` | Yes | `RevisionGuid` of the target ACT table |
| `RefdAsset` | `int64` runtime pointer | No | Not written |
| `RefdDocLinkName` | `wstring` | Yes | Link GUID |
| `RefdAssetGuid` | `uuid` | Yes | Target asset GUID |

The pair has no registered member names.
Kit calls the count `referenceCount`.
Earlier binary inspection described how Fusion adds, removes and counts entries, and how it detects an out-of-date link.
Those rules are not confirmed by a black-box experiment.

### Authoring rules

`EmitAssembly` writes a new root that references other designs.
These rules match `R4_joint` and a native insert of a Kit part.

| Item | Rule |
| --- | --- |
| Design object numbers | `XRefManager`, then per placement: instance, compute node, update data, placement feature, update data, status, progenitor table, occurrence, nested occurrences |
| Ground pin | Directly after its placement: override, feature, data reference, recipe, external recipe, update data, status, progenitor table |
| Joint | Joint, feature, nine occurrence references, update data, status, progenitor table, compute occurrence, joint occurrence |
| ACT object numbers | Instance, data, `ACTRefdTable` and data copy for each placement |
| Feature numbers | From `operationSeedId`, in timeline order |
| Record order | Primary records by object number, each followed by its continuation |
| Observer index of a target object | One more than the largest index on that object in the target design |
| Identity placement | Empty matrix value |

Fusion accepted a root that `EmitAssembly` wrote.
`AsmAcceptance.json` in `re/Fusion/LocalOracle/LinksConfigs` records the run.

### Reference update

`updateAllReferences` after a new version of Part A replaced the Part A link.

| Item | Before | After |
| --- | --- | --- |
| Link GUID | Old | New |
| `URL` | `?version=1` | `?version=2` |
| Design, Browser and ACT tokens | Old | New |
| `ACTRefdTable` record | Object 10 | Object 16 |
| `linkClassification` | `OriginalDesign` | Absent until the next save |

The subassembly link kept its GUID, tokens and version.

### Graphics of saved assemblies

Saved roots with an as-built joint have two more graphics structures.
A render frame has a third link flag, `RenderFrame.HasEmptyLink`.
`SelectabilityAttribute` links an `AlphaImageSelectionQualifier` with one optional image path.

## F3Z dependency graph

| Member | Typed model | Content |
| --- | --- | --- |
| `Properties.dat` | `DocProps` | Four zero bytes, or a length-prefixed JSON object with an optional `docstruct` |
| `RedirectionsStream.dat` | `DocRedirects` | Designs and `XREF` references |
| `ComponentReferenceData.json` | Fixed | `{}` |
| `DesignDescription.json` | `BundleModel` | Bundle graph |

The `docstruct` object has `version`, `type`, `subtype` and Boolean `attributes`.
The observed types are `part-design` and `assembly-design`.

The redirection designs of a member list the member itself and each design that it references.
Each reference has the properties `neutronRole` and `neutronData`.
`neutronRole` equals a root manifest link GUID of the member.
The `DesignDescription.json` edges of a member equal its redirection references.
All nine members of example1 satisfy these relations.

## Configurations

A design has `DesignConfigurationTable.<GUID>.dsgcfg` and `DesignConfigurationRule.<GUID>.dsgcfgrule` sidecars.
A Design serializer trigger names each sidecar.
All observed sidecars contain `{}`.
No observed file has a sidecar larger than 2 bytes.
The configuration table, rule, row and cell layouts are not known.
`Design.createConfiguredDesign` failed with an account restriction, so no configured control exists.

A second search found no other source of a configured design.
The Fusion app bundle has 232 design files and 21 nested designs, and none has a configuration sidecar.
`AppConfigScan.json` records the bundle scan.

## Verification

| Check | Result |
| --- | --- |
| Native controls read and written | 14 of 14, typed model equal after a second read |
| Byte-identical members | All except `.protein`, part `.smb` and part `.smbh` |
| Context count equals link count | 14 of 14 controls, all segments |
| `CrossRef` tokens in the context set | 14 of 14 controls |
| example1 graph relations | 9 of 9 members |
| Inline-typed references found | 0 |
| Nonempty configuration sidecars found | 0 in 1,063 files |
| Fusion opens uploaded Kit outputs with resolved references | 2 of 2, largest transform error 0.0 |
| Kit-written occurrence matrix shown by Fusion | Equal, largest error 0.0 |
| `updateAllReferences` on Kit outputs | Part A v1 to v2, body height 0.5 cm to 0.8 cm |
| Save as version 2 and reopen | 2 of 2, references and transforms kept |
| Kit-authored root with two Kit parts, a Kit subassembly, a ground pin and a rigid joint | Opened with resolved references, 3 of 3 transforms bit-exact |
| Part A edit through `updateAllReferences` on the Kit-authored root | Part A v1 to v2, body height 0.5 cm to 0.8 cm |
| Kit-authored root saved as version 2 and opened again | References, transforms, ground pin and joint kept, 0 unhealthy items |
| Kit read of the Fusion exports of the saved Kit root | 3 of 3, 10 Design tail bytes kept and written back byte-equal |

## Boundaries

- Kit authors rigid as-built joints only. No native revolute control exists.
- `ReadDocument` keeps at most 16 bytes after the last Design record. A longer Design tail raises `ValueError`.
- Kit does not author configured designs.
- `ReadDocument` does not read the example1 members, because of mesh stream members and unqualified PCB classes.
- The inline-typed reference form and the cadmpeg cross-document grammar are not qualified.
