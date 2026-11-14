# Typed Protein material serialization

## Result and scope

All logical material bytes in the two controlled documents now decode into named schema properties. There are no remaining material instance tails in this profile. The reader consumes 10 instance records with 273 properties and 10 definition records with 80 properties. Every logical record ends exactly at its block-chain boundary. The decode counts describe the read-only interpretation. Native writer acceptance is recorded separately below.

`TypedMaterials.json.xz`, indexed by `EvidenceIndex.json`, records every value, byte range, instance/definition identity, schema, connection and unit code. `DecodeInstances.py` reads the original archives and reconstructs material block chains without reading unused allocation bytes. No production code or native CAD functions are executed by it.

`EncodeMaterials.py` implements the inverse grammar from semantic values. `EncodePackage.py` constructs a complete nested Protein ZIP from those values and schema XML trees, with fresh supplied identities and timestamps. The parent generated a new package from the six controlled extrusion material records and accepted it in the installed Fusion application. Independent full-F3D acceptance remains separate.

| Control | Schema | Instance properties | Logical instance bytes | Logical definition bytes |
| --- | --- | ---: | ---: | ---: |
| empty | PhysMatSchema | 18 | 365 | 521 |
| empty | StructuralMetalSchema | 43 | 708 | 160 |
| empty | PrismMetalSchema | 23 | 314 | 185 |
| empty | ThermalSolidSchema | 21 | 338 | 145 |
| extrude | StructuralMetalSchema | 43 | 708 | 160 |
| extrude | PrismMetalSchema | 23 | 314 | 185 |
| extrude | PhysMatSchema | 18 | 365 | 521 |
| extrude | ThermalSolidSchema | 21 | 338 | 145 |
| extrude | GenericSchema | 40 | 434 | 153 |
| extrude | PrismMetalSchema, Post2015 instance | 23 | 323 | 185 |

These records use five concrete schemas and their supplied base schemas. A corpus-wide arbitrary material reader is not claimed. Binary properties, vector/matrix properties, additional connection/resource forms, texture resource embedding and legacy library categories require their own evidence before support is extended.

## Schema groups and ordering

Each `Schemas/<name>.xml` describes an `AssetSchema`. Its `UID/@val` gives its name. `Base/@val` names its parent schema. Resolve base schemas recursively, then apply the concrete schema's member declarations by `id`. A schema declaration is a tag such as `String`, `Float`, `Choice`, `Boolean`, `Color`, `Reference` or `Uuid` with properties on its XML attributes. Nested bounds, choice labels, defaults and localization metadata remain part of the typed schema tree; they are not additional serialized instance values.

The observed property traversal is lexical order by property identifier. Definitions select properties whose `definitionIteratorData` attribute is `true`. Instance values select the other properties and omit those declared `readonly=true`. The readers and writers also skip `texture_MapChannel` and `unifiedbitmap_MapChannel`. Neither appears in the current controls. That exclusion came from earlier binary inspection and is not confirmed by a black-box experiment.

Definition payloads have no separate fixed header. Their eight sorted properties are:

| Name | Wire type |
| --- | --- |
| BaseSchema | Counted UTF-8 string |
| Hidden | Boolean byte |
| UIName | Counted UTF-8 string |
| VersionGUID | Counted UTF-8 string, despite its `Uuid` schema tag |
| category | Counted list of counted UTF-8 strings |
| description | Counted UTF-8 string |
| keyword | Counted list of counted UTF-8 strings |
| thumbnail | Counted list of counted UTF-8 strings |

The control values of `VersionGUID`, such as `PrismMaterial-018`, are not UUID-shaped. Treating this property as 16 raw UUID bytes corrupts the record. Earlier positional labels for the third and fourth definition strings were corrected in `DocumentEnvelope/ReadProtein.py` and its report; this schema-driven decoder is the authoritative semantic interpretation.

An instance payload starts with three counted UTF-8 strings: schema name, instance ID, and referenced definition ID. After these, the ordered instance properties begin. `AssetLibID` is the first property in all observed schemas. Its GUID-like string is a library reference, not a fourth fixed header field. `ExchangeGUID` follows and is an empty string in these controls.

The header shape is observed for the instance library category in these controls. Other library categories cannot be assumed to have the same header.

## Value wire types

All scalar bytes are little endian. Strings are `u32 byte_count` followed by UTF-8 bytes, with no NUL terminator. `allowmultiplevalues=true` introduces a `u32 count` followed by repeated element encodings. The currently observed multiple-value definition properties contain strings.

| Schema type | Encoding |
| --- | --- |
| String, URL, Uuid | Counted UTF-8 string |
| Boolean | One byte, 0 or 1 |
| Integer | Signed `i32` |
| Choice | Signed `i32` numeric choice value; labels and IDs remain in XML |
| Float without a `unit` attribute | IEEE 754 `f64` |
| Float with a `unit` attribute | Signed `i32` unit code, immediately followed by `f64` |
| Color | Four `f64` values in RGBA order |
| Reference | No primitive value bytes; its connections follow |

The unit field is present even for `unit="Unitless"`. Omitting it causes apparently tiny or enormous float values and misaligns every subsequent field. For the controls, density uses unit code 69633 with value 7850, Poisson ratio uses 4097 with value 0.3, Young modulus uses 135176 with value 210000000, and thermal conductivity uses 282625 with value 56. The report also records the schema's declared unit string. The actual numeric unit code must remain data; it is not replaced merely because a schema supplies a default unit name.

The compact unit representation is a four-byte code followed by an eight-byte double, with no padding. A Color4 value is 32 bytes, four doubles. Both shapes follow from the complete decode of the controls and from accepted rewrites.

## Connections

After a property value, `allowconnectedassets="single"` or `"multiple"` adds a connection encoding:

1. One boolean byte `present`
2. If present, one boolean byte `enabled`
3. If present, `u32 count`, then that many counted instance-ID strings

An absent connection is only one zero byte. It has neither an enabled byte nor a count. A Reference contributes no other primitive bytes before this sequence. A Color or scalar property keeps its primitive value and then emits the connection sequence.

The empty physical material's `physmat_aspects` has three enabled targets: its appearance, structural and thermal material instances. Its deleted-aspects connection is absent. The appearance properties have explicit absent-connection bytes even when their ordinary value is present.

A present connection writes a presence byte, an enabled byte, a count and each target ID. Only local package material connections are represented by the current writer, which rejects missing target instance IDs.

## Independent generation interface

`encode_material_data(materials, schemas)` returns the three binary members. Each material is a typed mapping with `schema`, `instance_id`, `definition_id`, `role`, `definition_properties`, and `properties`. Property rows contain `name`, `value`, and, where applicable, `connections`. A unit value is `{unit_code, value}`. Definitions use the eight exact property names above. Additional diagnostic fields on reader report rows are ignored by the encoder; the set of property names must exactly match the schema group, and duplicates are rejected.

`encode_package(materials, schemas, package_id, asset_id, timestamp)` produces the complete nested ZIP. The supplied schemas are `xml.etree.ElementTree` AssetSchema nodes, reconstructed from the application's material schema model. The writer validates schema UIDs and base references. It serializes schema trees, resource links, core metadata, content types and the Autodesk design-package declaration from structured values, then builds ZIP entries through the standard library.

The package directory is the supplied `asset_id`. The top-level `cnx.xml` links it. Its connection document links `AssetData` and `Schemas`. Each subfolder's connection document names the generated resource files, their MIME types and creation timestamp. `core.xml` files carry the supplied identities and timestamp; root metadata and the two folder metadata records share `package_id`, while the asset directory's core record uses `asset_id`. The asset record retains the observed embed-option value 49. This arrangement is observed, not yet verified as a minimal package.

The three binary members use newly allocated consecutive 136-byte blocks. Each block has next-index, used-length and first-block flag fields; unused storage is zeroed. TOC root indexes are derived from the allocation, not copied. The writer does not accept raw instance tails, raw definition records, source archive paths or opaque package members. The format-version table is generated from the observed schema versions. XML is regenerated and ZIP compression is new; byte identity of allocation padding, XML formatting or compressed bytes is neither expected nor a semantic requirement.

The [native rewrite acceptance](../../LocalOracle/Features/MaterialAcceptance.json) compares all 68 native material properties and 18 native appearance properties before and after package reconstruction. Values remain equal after a 23 mm parameter edit, native save and reopen. The [changed-property acceptance](../../LocalOracle/Features/ChangedMaterialAcceptance.json) independently changes structural and thermal density from 7850 to 6300 and material color from gray to RGBA 51/102/153/255. Fusion exposes those changed values immediately and preserves them through save/reopen. These experiments regenerate six instances, 168 instance properties, 48 definition properties, 11 schemas, all package metadata and block allocations. They retain the same source document outside the Protein member. They do not establish source-free F3D generation or arbitrary material support.

## Reproducibility and limits

The reader and static extractor can reproduce their evidence from the controlled inputs and installed binaries. The static extractor does not load the libraries. The decoder never invokes Fusion and never runs the writer as a comparison. The two failed exploratory decode reports were removed after the correct unit representation was established; `TypedMaterials.json` is the complete, current interpretation.

The controlled package rewrite and changed-property acceptance are complete. Remaining work includes production promotion, independently authored whole-document relationships, and additional schema and resource families. External textures and unsupported property types must fail explicitly until their resource and value grammars are implemented. No general arbitrary-Protein, legacy-library, or full-F3D production readiness is implied by this bounded result.
