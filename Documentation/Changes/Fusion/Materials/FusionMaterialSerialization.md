# Fusion material serialization

## Behavior

The research reader decodes all logical material data in the empty and extrusion controls.
Ten instances contain 273 named properties. Ten definitions contain 80 named properties. No logical bytes remain unexplained.
The [material grammar](../../../../re/Fusion/Reconstruction/ProteinInstances/MaterialGrammar.md) describes schema inheritance, property selection, ordering, types, connections, and block allocation.

`encode_material_data(materials, schemas)` writes the binary property stores and table of contents from semantic values.
`encode_package(materials, schemas, package_id, asset_id, timestamp)` creates the complete nested Protein ZIP.
The input schemas are structured XML trees. Property inputs include explicit units and connection identities.
The writers generate metadata, resource relationships, property records, and allocation indexes. They zero unused block capacity.
They accept no opaque record suffix or source archive path.

## Verification

The [rewrite report](../../../../re/Fusion/LocalOracle/Features/MaterialRewrite.json) identifies the generated archive and its source.
It reconstructs six instances, 168 instance properties, 48 definition properties, and 11 schemas.
[Fusion acceptance](../../../../re/Fusion/LocalOracle/Features/MaterialAcceptance.json) confirms equality of 68 native material properties and 18 appearance properties.
Those values survive a parameter edit to 23 mm, rebuild, native save, and reopen.

A [second native acceptance](../../../../re/Fusion/LocalOracle/Features/ChangedMaterialAcceptance.json) verifies deliberately changed values.
Structural and thermal density change from 7850 to 6300. Native appearance color changes to RGBA `(51, 102, 153, 255)`.
Fusion exposes these values immediately and preserves them after save and reopen.
Both acceptance runs leave zero open documents.

These experiments use the explicitly authorized local application. General automated tests remain PR-only.

## Limits

These are same-source package rewrites. The surrounding document remains derived from its own source archive.
The writer is research code and is not yet registered as a production material adapter.
External textures, additional property kinds, legacy library categories, and arbitrary material schemas require separate evidence.
Whole-document independent generation remains separate from the measured material acceptance.

See the [unit and identifier gotcha](../../../Gotchas/Conversion/Fusion/FusionMaterialPropertyTypes.md) and [padding gotcha](../../../Gotchas/Conversion/Fusion/FusionMaterialStorePadding.md).
