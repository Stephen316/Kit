# Independent F3D Container Authoring

`AuthorContainer.py` constructs a one-asset, three-segment F3D container from an independently authored Design graph. It writes ACT and Browser entity graphs, metadata indexes, root and asset manifests, empty document properties, and two newly generated PNG previews. It never reads a vendor archive or a captured entity graph at runtime.

The complete independently authored circle-extrusion document is now accepted by Fusion 2706.1.17. Its existing solid is correct before compute, its two timeline features remain healthy through rollback and restoration, and editing the driving parameter changes the solid and survives native save/reopen. This acceptance applies to the described single-component circular-extrusion profile; it does not establish arbitrary Fusion feature or document support.

The corrected parameter writer has passed native Fusion 2706.1.17 import, read, edit, compute, save, close, and reopen. The complete fresh generation is `FreshParameter/AuthoredParameter.f3d`, SHA-256 `126dc166545a8c9156d6492d4b0913c675c7bf56aaa2fe33493dde03c05ae970`; the authority is `LocalOracle/Authored/ParameterAcceptance.json`. The incremental diagnostic candidate `BrowserBindings/AuthoredParameter.f3d` also passed, recorded separately in `LocalOracle/Authored/ParameterBrowserAccepted.json`. Both runs read `authoredLength = 17.25 mm`, preserved its comment, accepted an edit to `31.5 mm`, and reopened the saved value. Creating a native circle and extrusion afterward also succeeded, producing two healthy timeline features and one three-face solid. That last step verifies editability of the authored document; those extra features were created by Fusion, not by this writer.

The initial candidate is `Generated/AuthoredParameter.f3d`, SHA-256 `91fda6a666e843a525a2fb7b6cee3aedf34cd0dff92040a091dc41d4f6391487`. It contains 11 generated members. Fusion rejected it before reading segment metadata. The controlled revisions below distinguish archive hierarchy from entity ordering. Successful artifact generation is not evidence that Fusion accepts the document.

## Inputs and provenance

The complete generation entry point accepts a semantic Design specification:

```sh
python3 re/Fusion/Reconstruction/ContainerAuthoring/AuthorContainer.py --specification re/Fusion/Reconstruction/DocumentAuthoring/Specification.json --output re/Fusion/Reconstruction/ContainerAuthoring/Fresh
```

This calls the independent `DocumentAuthoring/AuthorDesign.py` writer directly. Its runtime data dependencies are the semantic specification, the reflected type vocabulary in `LocalOracle/Reflection/Versions.json`, and the class vocabulary in `BinaryClasses.json`. Neither vocabulary contains source entity payloads. Runtime type knowledge still comes from the recovered reflection schema; this is a research author, not a standalone production module.

The frozen candidate instead uses `--generated-design re/Fusion/Reconstruction/DocumentAuthoring/Generated`. These are intermediate outputs of the same independent writer, not a vendor template. Its Design metadata SHA-256 is `4b9c11144cab53fe802558b04d4647186480344aa8effe40a7f967324b252d10`; its Design bulk SHA-256 is `603948ccc9087ba1f285f8e79466f1fa7cc7a9e2ecf5eaa79ecd23ee80e00659`.

The intermediate mode deliberately trusts that the supplied metadata, bulk stream, and authored role model are coherent outputs from the independent Design writer. It is not a public arbitrary-file ingestion interface. `Generation.json` records every member digest and the selected input mode. `EnvelopeModel.json`, `ActModel.json`, and `BrowserModel.json` expose the complete generated semantic data.

`FreshParameter/AuthoredParameter.f3d` was generated through the complete semantic-specification entry point after incorporating the discovered constraints. Unlike the incremental diagnostic artifacts, this execution read no prior Design streams, authored-model intermediate, or archive. Its accepted native save has SHA-256 `40f99790a141f2b8538aa46f44f56f7ebe74c3b8e30ec850937d01fd401af506`; the native feature-creation output has SHA-256 `faea60100a4a5f6614177eedbb7edc40c5c6c41592acc94db030ed010463d8d6`. The oracle closed all documents after acceptance.

The control captures in `DocumentEnvelope/EnvelopeEvidence.tar.xz` informed the grammar and relationships during research. They are not opened by this writer. No source block, opaque tail, image payload, identifier instance, or class code assignment is copied. Class GUIDs and root identifiers are type vocabulary. New classes receive local codes starting at 256, entity IDs are allocated from semantic roles, offsets and indexes are calculated from emitted records, and document/asset UUIDs are newly generated.

## Archive and manifests

The initial ZIP used standard Deflate with no explicit directory entries. The current writer uses Stored entries with explicit directory entries. Native probing established that explicit directory entries are required for this generated archive to reach segment metadata. Changing compression alone did not resolve the initial failure; this does not prove Deflate unsupported. The active asset folder is `FusionAssetName[Active]/`. Segment directories are the segment user name followed by its one-based occurrence count among the asset's segments; the suffix is not the numeric segment ID. Thus Browser segment ID 2 is stored in `FusionBrowserSegmentType1/`.

The root manifest writes format `3-2-0-0`, document type `FusionDocType`, extension `.f3d`, document type name and description, two new UUIDs, marker 1234, format version 20, and a packed software version. The software value is `(2706 << 50) | (1 << 38) | 17`; it is one 64-bit number, not two independent header words. See `HeaderGrammar/HeaderModel.md`. The initial candidate incorrectly used the authored title and description in the document-type name/description positions. The fresh candidates write `Fusion Document` and `A Fusion Document` there, and Fusion accepted them. This does not explain the observed missing-stream error, which occurs later.

The root's seven extension versions and the asset's four extension versions are explicit format-version vocabulary for this observed writer profile. The root points to the asset UUID, declares a single active `FusionAssetName` asset, and writes export label `NA_EXPORT`. `Properties.dat` is a counted empty ASCII string.

The asset manifest writes the same asset UUID, a fresh snapshot UUID, `FusionAssetType`, `Neutron3DAssetType`, no properties, and the three segment declarations: Design 0, ACT 1, Browser 2. The segment preamble's observed value 5 sits where the fresh writer stores one more than the highest segment ID. The fresh three-segment candidates write 3, and Fusion accepted them. Earlier binary inspection named this field the next available segment ID. It also named the first two root UUIDs the document identifier and the current version. The fresh candidates write new random UUIDs in both, and Fusion accepted them. These names are not confirmed by a black-box experiment. The initial `EnvelopeModel.json` label `documentLineageId` is historical; this model calls that field the current version. Diagnostic revisions retain the initial values to isolate the stream-lookup and record-order failures.

Previews are valid newly encoded RGBA PNGs containing a uniform light background. They describe the candidate's empty geometric scene, with dimensions 256×256 and 64×64. They are stored at the observed asset-relative names `Previews/big.png` and `Previews/small.png`.

## ACT graph

ACT is segment 1, neutron type 5, with eight entities and no continuation records. Its extension versions are Application 1 and Server 1. The entity allocator ends at 108.

| Role | ACT ID | Relationship |
| --- | ---: | --- |
| Component | 100 | Design component 1002; parent ACT root instance 102 |
| Instances collection | 101 | Design component-instances 1017; parent ACT component 100 |
| Root instance | 102 | Design root instance 1004; target ACT component 100 |
| Change table | 103 | Root `ACTTable`; two change-data entries |
| Components root | 104 | Root `ACTComponentsRoot`; roots component 100 |
| Instances root | 105 | Root `ACTInstancesRoot`; maps instance ID 0 to entity 102 |
| Component change data | 106 | Identified by `1_100` |
| Instance change data | 107 | Identified by `1_102` |

The table's `AssetRevGuid` equals the asset manifest's snapshot UUID. The fresh Design revision UUID supplies table and component revision tokens; a separate fresh token supplies instance revision data. These revision tokens are authored states, not histories reconstructed from an existing document.

Every revision map contains Appearance, Geometry, PhysicalMaterial, Properties, StructureChange, and Transform. The root instance's `ACTRefValue` observes those six change types, owns itself, and refers to the ACT component. It is local to this asset, with no referenced table or external asset. Four additional-root index entries identify the table, component root manager, instance root manager, and root instance.

## Browser graph

Browser is segment 2, neutron type 6, with 32 entities at IDs 200–231 and 33 physical records. Its extension versions are Application 2 and Server 2. It authors the component entry and the empty semantic folders relevant to the generated Design. No VisualAnalyses folder is created because that Design does not contain a VisualAnalyses entity.

Root 200 uses `FusionComponentBrowserRoot`, `ComponentBrowserRoot`, and `PersistBrowserRoot` in its primary record. Its `ManagedEntity` base occupies a continuation record. This differs from splitting at every add-in boundary: the Browser add-in bases remain in the primary record even though the concrete class belongs to Fusion. All other Browser entries fit in primary records.

The root's passive map connects Design entities to Browser entries. Its string map distinguishes the five relationship folders observing the same Design AssyConstraints entity 1022 and the document-structure entry whose entity reference is null. This is not the separate Design Relationships entity 1034. Child and parent vectors are derived from semantic folder hierarchy. The Units entry refers to the UnitSystems root 1007, not the active UnitSystem child 1008.

Observer indexes are allocated from the generated Design's existing subject records. The Design root instance already occupies component 1002's observer slot 0. Browser's component entry therefore uses slot 1. The five relationship entries receive successive slots, as do the settings and component-instances observers. No source observer index is copied.

## Omissions and acceptance boundary

The parameter-only candidate has one user parameter, no body, no sketch, and no timeline feature. Its Protein manager references no materials and has an empty part name; therefore no `.protein` member is written. Its OGS serializer has an empty part name; therefore no OGS members are written. Its Design has no configuration triggers and no BRep bodies; therefore configuration and BRep payloads are absent. The empty `Breps.BlobParts/` directory is nevertheless required by BRepHistorySerializer's post-load behavior. The accepted circle and extrusion candidates retain empty material references and omit OGS/configuration payloads; the extrusion adds its independently generated BRep history part.

The writer currently targets a single local component and root instance. Assemblies, external assets, configuration semantics, named geometry, historical ACT transitions, and arbitrary Browser nodes need additional authoring models. The independent Protein package author is a separate component; attaching it requires coherent material references and part names in the Design graph.

The native parameter acceptance is bounded to this graph profile. Each new feature graph needs its own native import, semantic inspection, edit, save, close, reopen, and inspection of the saved result. No native application calls or local tests were run by this authoring task. The parent task owns all native acceptance.

## Feature and generated-part integration

`AuthorFeatureContainer.py` calls the semantic circle or extrusion author directly, allocates a fresh asset UUID before building PassiveScope values, and passes that same UUID to the envelope builder. Its circle CLI requires only a semantic specification:

```sh
python3 re/Fusion/Reconstruction/ContainerAuthoring/AuthorFeatureContainer.py --specification re/Fusion/Reconstruction/DocumentAuthoring/Variants/CircleSpecification.json --output re/Fusion/Reconstruction/ContainerAuthoring/FreshCircle
```

The fresh circle artifact is `FreshCircle/AuthoredCircle.f3d`, SHA-256 `da4771d9c1dfe7c31737a2f8846b8e19fbd93189421a2a25babba1d3c80c6f37`. It contains 112 Design entities in 135 records, one authored circle of radius 12.5 mm, and the 17.25 mm user parameter. Its asset UUID is `28caa5a4-7731-4861-93ad-abef0bb87ac5`. `LocalOracle/Authored/CircleAcceptance.json` records native acceptance: one healthy timeline entry, one sketch, one circle, one profile, unchanged radius after compute, direct radius edit to 18 mm, and save/reopen preserving that edit. Fusion subsequently created a healthy dependent extrusion using `authoredLength`, with volume `17.55836134091411 cm³`. The circle was independently authored; that subsequent extrusion was created by Fusion and is separate from the fresh extrusion candidate below. The oracle closed every document. Complete authored models are stored as XZ-compressed JSON.

For extrusion, `prepare_feature('extrude', specification)` returns the freshly authored Design and its `model.brepContract`. `package_feature(design, brep_encoder=callback)` passes that contract to an independent encoder returning SMBH bytes, then attaches the generated part at the exact `partName` referenced by the Design serializer. A missing encoder is an error; it does not emit a container with an unresolved BRep dependency. `write_result` records the final candidate and per-member hashes.

The lower-level `build_container` accepts `generated_parts`, a mapping from asset-relative member names to in-memory bytes returned by independent encoders. Names must be one file below `Breps.BlobParts`, `ProteinAssets.BlobParts`, or `Images.BlobParts`; traversal, backslashes, NULs, and other folders are rejected. This is an integration seam for freshly generated SMBH or the independently authored material package from `ProteinInstances/EncodePackage.py`. It does not read source archives. The caller must provide coherent serializer part names and references in the Design graph and retain semantic provenance for those generated bytes; the container layer cannot infer their origin from byte content. The feature variants currently reuse a uniform preview raster and do not claim a rendered geometry preview.

### Complete independent extrusion generation

`PrepareExtrusion.py` prepares a fresh semantic extrusion Design, passes its `brepContract` into production `convert.formats.Fusion.BrepCodec.EmitHistory`, and packages the result through `package_feature`. It reads the semantic specification, type vocabulary, and implementation modules. It does not open an existing F3D, an authored-model snapshot, geometry payload, or history payload.

```sh
.venv/bin/python re/Fusion/Reconstruction/ContainerAuthoring/PrepareExtrusion.py
```

The accepted output is `FreshExtrusion/AuthoredExtrusion.f3d`, SHA-256 `7c3dbb1a213d9a3ef5fa609a721fba2de5a5870d0249d64c7c77f07968456523`. It contains 139 Design entities in 172 physical records and a 5299-byte independently emitted SMBH part, SHA-256 `86fe6f7e07ecd30917e718887f64ec90deab0ec09e22c7340fd8461bd4f1952c`. Native acceptance of this complete independently authored extrusion is recorded in `LocalOracle/Authored/ExtrusionAcceptance.json`.

The authored cylinder has radius 12.5 mm, height 17.25 mm, and origin `(0,0,0)`. The fresh asset UUID is `73242b24-ae39-46b4-bc84-9513878acde8`; body entity 1125 has UUID `231ee6f9-fbaa-4f31-a9bc-5d3b54c8e7ff`. The BRep serializer references `BREP.5a9f5d15-eff0-4ae4-93eb-90c743638620.smbh`, exactly matching the emitted archive member.

The contract maps body key 0, operation 301, and generation reference 4 into `BodyIdentity`. It maps current/initial history states 4/2, generation 4, allocation 1, and board 2 into `HistoryState`. Face selectors are 1 with labels side `3`, top `2`, and bottom `1`; top-edge selector 2 carries label `-1`, and bottom-edge selector 4 carries label `-102`. Every feature tag refers to operation 301. `SketchLink` uses primary 102, secondary 0, sense 0, and enumerations 1/1. These are semantic inputs for the canonical circle extrusion profile, not copied attribute bytes. A fresh authoring time supplies the timestamp attribute. The body UUID links the Design-side body and compute node; the binary body's map key is the contract's body key.

`FreshExtrusion/BrepEncoding.json` records all production model inputs and the generated history digest. `Generation.json` records the new asset UUID, complete contract, member digests, and absence of source archive or runtime vendor template. `AuthoredHistory.smbh` is the standalone newly generated member; compressed JSON models preserve the complete semantic Design, ACT, Browser, and envelope for inspection.

Fusion opened the authored archive with two healthy named timeline entries, `Authored Circle` and `Authored Extrusion`. Before compute, it exposed one body with height 17.25 mm, volume `8.467573949129104 cm³`, three faces, two edges, and two vertices. Its feature distance parameter `d2` retained expression `authoredLength`; taper `d3` retained `0 deg`.

Rolling the timeline back to the sketch removed the body. Restoring the timeline brought back the original body with the same measurements. A subsequent full compute preserved its geometry and healthy feature states. Editing `authoredLength` to 23 mm updated both the driving and bound feature parameters, producing height 23 mm and volume `11.290098598838801 cm³`. Native save, close, and reopen retained those parameters, both healthy features, and the same topology and measurements. The saved artifact SHA-256 is `81c5f35d8bdda4f2cee8721299cc2757e496f2f386a9c26741c6d46ece000199`. The oracle ended with zero open documents. Unlike the earlier native feature-creation checks, this run began with the sketch, extrusion feature, topology, and BRep history all independently authored.

## Controlled native failures and revisions

| Candidate | SHA-256 | Change | Native result |
| --- | --- | --- | --- |
| `Generated/AuthoredParameter.f3d` | `91fda6a666e843a525a2fb7b6cee3aedf34cd0dff92040a091dc41d4f6391487` | Initial independently authored file | Segment metadata stream initialization failed |
| `StoredOnly/AuthoredParameter.f3d` | `0c7658b3962a49d57e18fb7c6e5409aee958c526191c93fd3e64c695480324de` | Compression changed to Stored for all 11 members; payloads identical | Same failure; compression alone does not explain rejection |
| `StoredFolders/AuthoredParameter.f3d` | `2bee9d409dbdc8f651a08bb035213d6491edd15da3ddb47068f3e5c1e162b11e` | Added five explicit directories; all 11 payloads unchanged | Metadata initialization succeeded; bulk loading rejected a negative offset |
| `OrderedAct/AuthoredParameter.f3d` | `cda56e7247dcfdbb2271063c1498d324a6000f8186058d921cb45b0981565db0` | Re-emitted only ACT metadata and bulk with numeric entity order; all semantic values and UUIDs unchanged | Negative-offset error resolved; BRepHistorySerializer rejected missing blob directory |
| `BrepFolder/AuthoredParameter.f3d` | `e2b94c7e74a8206fc0027ed3a830f0c5f8d40f421820b98b524a9d32d77037e4` | Added empty `Breps.BlobParts/`; all previous entries unchanged | Asset fully initialized, then native Browser activation crashed |
| `BrowserBindings/AuthoredParameter.f3d` | `f6e92a059e3e9db0c914f93b17191d6019fc34b5cd321e97ee83a3c75ab813c6` | Corrected five relationship folder bindings from Relationships to AssyConstraints | Accepted: read, edit, save/reopen, subsequent native feature creation |
| `FreshParameter/AuthoredParameter.f3d` | `126dc166545a8c9156d6492d4b0913c675c7bf56aaa2fe33493dde03c05ae970` | Fresh complete generation from semantic specification; all UUIDs newly authored; corrected manifest fields and allocator | Accepted independently through the same full native sequence |
| `FreshCircle/AuthoredCircle.f3d` | `da4771d9c1dfe7c31737a2f8846b8e19fbd93189421a2a25babba1d3c80c6f37` | Fresh semantic circle sketch with coherent asset scopes | Accepted: initial profile, compute, radius edit, save/reopen, later native dependent extrusion |
| `FreshExtrusion/AuthoredExtrusion.f3d` | `7c3dbb1a213d9a3ef5fa609a721fba2de5a5870d0249d64c7c77f07968456523` | Fresh semantic extrusion and production-generated binary BRep history | Accepted: correct body before compute, healthy timeline, rollback/restore, driving edit, save/reopen |

`StoredVariant.py` and `OrderedActVariant.py` are isolated diagnostic packagers. They accept only the exact digest of the prior independently authored candidate. They are not the semantic writer and cannot accept an arbitrary vendor archive. `StoredDirectories/` was an unused exploratory generation with additional changed revision tokens; it provides no controlled native evidence.

A candidate without explicit directory entries failed with the observed error. Explicit entries are the demonstrated workaround. No claim is made that every ZIP consumer or every Fusion archive requires them.

The ACT author initially emitted IDs in semantic construction order, `103,104,100,106,101,105,102,107`. The revised stream emits `100,101,102,103,104,105,106,107`, preserving every entity's semantic value and identifier. Fusion rejected the first order. Changing only ACT physical order resolved this failure. Continuations remain inside the primary entity's bounded chunk. Earlier binary inspection explained the failure as a rule that increasing entity identities need strictly increasing primary offsets. That general rule is not confirmed by a black-box experiment beyond this case.

The Browser crash followed a typed-reference mismatch. The original authored Browser bound the relationship folders to a Relationships object. The control's Design entity 12 is `AssyConstraintsMetaType`, GUID `596C8B98-D176-4E40-B294-6404BAD566BC`; its separate Relationships entity is 45. The corrective Browser model binds the five folders, their observer subjects, and their root string-map group to authored AssyConstraints 1022. Fusion accepted this corrected model. It retains the folder class names because those names describe the UI role, not the required target entity type. Earlier binary inspection traced the crash to a typed call through the wrong target; that trace is not part of the black-box evidence.
