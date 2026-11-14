# Fusion material property codec

## Behavior and usage

`convert.formats.Fusion.MaterialCodec` reads and writes the three binary members of the nested Protein material package without a CAD runtime or donor payloads.

`DecodeMaterials(Streams, Schemas)` accepts a `MaterialData` value containing table-of-contents, definition-store, and instance-store bytes, plus explicit `MaterialSchema` declarations. It returns immutable `MaterialAsset` values.
`EncodeMaterials(Assets, Schemas)` accepts those semantic values and returns newly allocated binary stores. It does not accept original payloads, padding, source paths, or residual byte strings.

The caller supplies schema names, base names, property names and kinds, definition/read-only/multiple flags, unit metadata, and connection modes. The codec resolves inheritance, selects persisted fields, and writes the native sorted property order.
Typed properties distinguish strings, signed integers, booleans, doubles, four-channel colors, unit-code/magnitude pairs, and explicit asset connections. Definition identifiers are independent of the `VersionGUID` property.

The store writer allocates new 136-byte blocks and clears unused capacity. The reader validates linked chains, allocation roots, block flags, lengths, identities, schema membership, and connection targets. It rejects cycles, shared blocks, unreachable blocks, partial blocks, duplicate identifiers, and unsupported property kinds. Limits bound store sizes, string lengths, item counts, and schema inheritance depth.

See the [detailed material grammar](../../../../re/Fusion/Reconstruction/ProteinInstances/MaterialGrammar.md), [property type gotcha](../../../Gotchas/Conversion/Fusion/FusionMaterialPropertyTypes.md), and [padding gotcha](../../../Gotchas/Conversion/Fusion/FusionMaterialStorePadding.md).

## Verification

The [production rewrite](../../../../re/Fusion/LocalOracle/Features/ProductionMaterialRewrite.json) contains six instances, 168 instance properties, 48 definition properties, and eleven schemas. The surrounding source document had already received independently authored geometry from the production embedded BRep codec.

[Native Fusion acceptance](../../../../re/Fusion/LocalOracle/Features/ProductionMaterialAcceptance.json) verifies structural and thermal density changed from 7850 to 6300 and appearance color changed to RGBA `(51, 102, 153, 255)`. These changes survive a dependent extrusion parameter edit to 23 mm, rebuild, native save, and reopen in Fusion 2706.1.17. The input digest is `104d3aeb906eba7e59f568e039e5c796b8a4fa1f11bfcc10a4108123b2b4451b`; the native saved result is `b1cb8eddd9ada07db6e1511c949f5da418e12649519a798c0da92dc9ec1b9069`.

PR compatibility coverage reads the native material package, edits typed values through a disk ZIP boundary, and verifies regenerated allocation. The coverage also rejects malformed complete stores and missing connection targets. Padding mutation verifies that unused capacity is excluded from logical semantics. Automated tests run only in PR CI; no local test execution occurred. Static formatting, lint, and both configured type checkers passed before this addition was pushed.

## Limits

This API handles the binary material stores. The [typed package codec](FusionMaterialPackages.md) now provides qualified XML schema, metadata and relationship packaging. The measured archive in this entry is a same-source edit; the later package entry records independently authored complete-document acceptance separately. External texture resources, arbitrary legacy libraries, and unobserved property kinds are not established. The binary codec requires explicit schema input and does not silently guess a material layout.
