# Mesh document integration contract

The initial component native preparation uses `adjacent_pair.f3d` and `closed_thickness_point_one.f3d`. The independent graph reader consumes all 295 and 269 Design physical records respectively. Both original archives have a fully consumed 14,552-byte ordinary OGS world. No custom mesh world occurs in these two original controls. [DocumentLinks.json](DocumentLinks.json) binds the compressed named-value evidence and source hashes.

## Identity and ownership joins

| Native class | GUID | Relevant persisted fields |
| --- | --- | --- |
| ParaMeshGeometry | `A8338A26-5436-433C-8BAC-C3CF024AD595` | `pMeshUuid`, `rSerializerTrigger`, `identityVolume`, `isClosed`, `isOriented`, `needsUpdate`, `textureIdToUuidMap` |
| ParaMeshSerializerTrigger | `A1BAA3F6-4B67-4A0D-BACC-75F38A2230F3` | `rMeshGeometry` |
| BlobSerializerTrigger base | `130A0711-4E92-4FCD-AADE-B9C82238BB27` | `partName` |
| ParaMeshBody | `EA90DA22-556C-4C61-89BB-20C2681B7A9D` | `rMeshGeometry`, `rDcFeature`, `rGroupParent`, `mtxTransform`, `mtxBakedTransform`, material references, display state |
| ParaMeshBodies | `443807AD-8025-41A3-8A50-5157579C3D78` | `textureStore`, creation and visibility fields |
| ParaMeshTextureStore | `6FC173DC-C7E3-402C-A8C0-891A26DADF8D` | `uuidToTextureInfoMap`, `uuidToTextureMap` |

For each geometry, follow `rSerializerTrigger` to its primary trigger entity and require the trigger's `rMeshGeometry` to point back to that geometry. The trigger's inherited `partName` selects `ParaMeshGeometry.BlobParts/<partName>`. The selected component registry's `fusion_uuid` must equal the geometry's `pMeshUuid`. Neither the container's `mesh_uuid` nor the UUID embedded in the filename substitutes for this join.

In the adjacent-pair archive, current body 213 points to geometry 512, whose `pMeshUuid` is `126bca4a-adb9-4907-b66a-2269ee51903b`; trigger 513 selects `ParaMeshGeometry.cdbebe0a-783e-441a-a371-05cc935b4730.paramesh`. The component's separate `mesh_uuid` is `c981ad4f-fc46-4bc3-aaac-39f829b04b52`. Historical geometry 211 has trigger 212 and its own source component; geometry 509 has trigger 510 and an intermediate generated-face-group component. The active body alone therefore does not enumerate every component required for rollback and recomputation.

The feature chain explains those historical objects: `DcParaMeshModifyBase.beforeMeshGeomRef` and `afterMeshGeomRef` connect successive geometries; `meshBodyRef` connects through `ParaMeshBodyModelDataRef`, `ParaMeshBodyDataRef.meshBody` and their typed recipe. Preserve those ordinary entity fields through the existing metadata-selected entity codec. The mesh component codec must not collapse history to the currently displayed mesh.

The shell archive similarly has source geometry 211 and current geometry 274, with `DcParaMeshHollow` thickness bound through its ordinary numeric parameter. Its current component contains 2,745 vertices and 5,482 triangles. This is useful native evidence for rebuilding a mesh feature rather than only reopening an imported static object.

Both controls have empty texture maps and no `.smbh` or `.smb` part. Their other nonsegment members are the already qualified configuration table/rule, material package and OGS world/mesh. Material validation already visits `physicalMaterial` and `visualMaterial` fields across all entity groups, including ParaMeshBody. A new permissive material special case is unnecessary.

## Proposed typed document routing

Add an immutable document mesh part with a relative member name and `ParaMesh` value. Route only the exact `ParaMeshGeometry.BlobParts/ParaMeshGeometry.<UUID>.paramesh` member profile. Read every member through `ReadParaMesh`; emit every member through `EmitParaMesh`. Validate trigger class, local reference domain, reciprocity, member path, `fusion_uuid`, uniqueness and exhaustive part ownership. Reject nonempty unsupported texture mappings rather than retaining untyped textures.

Keep body transforms in the typed Design graph. The original controls store both `mtxTransform` and `mtxBakedTransform`, including a scale of `1.0000000149011612`; their coexistence does not justify applying both transforms to a position. No additional coordinate-unit conversion is claimed by the component model. Model-space placement and projection require their own precise transform semantics.

## Saved graphics branch

The custom mesh-world layout is not known from saved documents. Earlier binary inspection suggested its field list; that evidence was removed and is not confirmed by a black-box experiment. It must be qualified against a saved visible native mesh.

The component-native acceptance should save and reopen its imported results and retain that native save as the next graphics control. Full original-document reconstruction can first target the already decoded ordinary-world branch; saved mesh-world support must remain an explicit boundary until its callback is completely modeled.
