# Read and write the F3Z dependency graph

The container codec now reads and writes the members that connect the designs of an F3Z bundle.
`FusionContainer` and `DocumentModel` have two new fields, `Properties` and `Redirects`.

## Container members

| Member | Typed model | Content |
| --- | --- | --- |
| `Properties.dat` | `DocProps`, `DocStruct` | Length-prefixed JSON with an optional `docstruct` object |
| `RedirectionsStream.dat` | `DocRedirects`, `RedirectDesign`, `RedirectRef` | JSON list of designs and references |
| `ComponentReferenceData.json` | Fixed content | The two bytes `{}`, present with the redirection stream |

`Properties.dat` has four zero bytes when no properties exist.
`EmitDocProps(None)` writes these four bytes.
`DocProps(None)` is the JSON object `{}`, which the PCB member of example1 contains.

`DocStruct` holds `version`, `type`, `subtype` and Boolean `attributes`.
The observed `type` values are `part-design` and `assembly-design`.

## Redirection stream

| JSON key | Typed field | Content |
| --- | --- | --- |
| `designs[].file-version` | `RedirectDesign.FileVersion` | Version number of the design |
| `designs[].targetFileName` | `RedirectDesign.TargetName` | Member file name in the bundle |
| `designs[].displayName` | `RedirectDesign.DisplayName` | Design name |
| `designs[].lineageUrn` | `RedirectDesign.LineageUrn` | Lineage URN |
| `designs[].versionUrn` | `RedirectDesign.VersionUrn` | Version URN |
| `references{}.from` | `RedirectRef.SourceName` | Member that holds the link |
| `references{}.relativePath` | `RedirectRef.TargetName` | Referenced member |
| `references{}.properties` | `RedirectRef.Properties` | Named text values, for example `neutronRole` |

The writer emits `"references":{}` when no references exist.
A reference `type` other than `XREF` raises `ValueError`.
A stream without designs raises `ValueError`.

## Graph relations

`BundleGraph.py` checked the example1 F3Z bundle with the production readers.
All nine members satisfied the relations in the table.

| Relation | Result |
| --- | --- |
| `DesignDescription.json` edges of a member equal the redirection references of that member | Equal for 9 of 9 members |
| `neutronRole` of each reference equals a root manifest link GUID of the member | Equal for 9 of 9 members |
| The redirection designs list the member itself and each referenced design | True for 9 of 9 members |

The root assembly lists 9 designs and 8 references.
Each part member lists 1 design and 0 references.

## Limits

`ReadDocument` does not read the example1 members yet.
Eight members fail on the `Fusion_mesh_000` member name.
The PCB member fails on unqualified native classes.
The [cloud member gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionCloudMembers.md) gives the details.

The Fusion archive export of a saved root wrote one F3D, not an F3Z bundle.
That export contains no redirection stream.

## Related information

- [External references change](FusionExternalReferences.md)
- [Archive extension gotcha](../../../Gotchas/Conversion/Fusion/Assembly/FusionArchiveExtension.md)
- [Bundle codec change](../FusionBundleCodec.md)
