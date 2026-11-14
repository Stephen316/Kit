# Fusion class identifiers are not uniformly UUIDs

Fusion's class registry uses identifier strings that often resemble UUIDs.
Normalizing all of them through a UUID parser loses valid native class identities.

The runtime reflection capture of Fusion 2706.1.17 lists these exact examples:

- `CommonBaseGroupEntityMetaType`: `A7AEA631-985B-4DD1-8CE2-DE2C-14B54081`
- `DcBooleanParameterMetaType`: `fe4edba5-5680-4ce8-bebd-1e21809130442`
- `BRepSerializerMetaType`: `40DCC3F41D-E94F-B3B1-3E95-9B6ABE572C`

Preserve the original identifier spelling and length in the metadata registry.
Treat these as opaque class identifiers, even when existing code calls the field a GUID.
Do not rewrite them into canonical UUID spelling or assume their separators imply a fixed-width binary layout.

The [reflection capture](../../../../re/Fusion/LocalOracle/Reflection/Versions.json) and the [class catalogue](../../../../re/Fusion/Reconstruction/BinaryClasses.json) keep the exact spellings.
