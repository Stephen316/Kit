# Fusion material schema tags do not determine the wire layout

A unit-bearing `Float` writes a signed 32-bit unit code followed immediately by a binary64 value.
This also applies to `unit="Unitless"`. No padding separates the two values on the wire.
Reading only a double shifts all subsequent properties and produces meaningless numbers.
Preserve the numeric unit code and apply the compact 12-byte representation.

A definition property tagged `Uuid` still uses counted UTF-8 text.
The observed `VersionGUID` value `PrismMaterial-018` is not a UUID.
Do not enforce UUID syntax or replace this value with 16 binary UUID bytes.

Instance headers contain three strings: schema, instance identity, and definition identity.
The following `AssetLibID` belongs to the schema's ordinary properties, even though its value resembles a UUID.

Instance definition identities and definition `VersionGUID` properties can differ.
For example, `PrismMaterial-018_physmat_aspects_1:PhysicalMetal_124` references a definition whose `VersionGUID` is `PhysicalMetal_124`.
Preserve both values independently.

The [material grammar](../../../../re/Fusion/Reconstruction/ProteinInstances/MaterialGrammar.md) links the decoded material values and accepted package rewrites.
