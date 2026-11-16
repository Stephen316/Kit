# Generation-19000 standalone part storage and configuration index

The active configuration uses one native configuration ID across the [CMgr opening and aliases](../../WriterResearch/CmgrComposition.md), the light configuration index and the configuration storage names. The scoped writer covers the first configuration ID 0 and the default rebuilt part with one configuration. There are six P01 sketch saves and eight P03 single-boss saves in the checked corpus. [Pinned captures and build](../../WriterResearch/CmgrVisual.md#inputs-and-reproduction)

## Version and main stream dispatch

On installed SOLIDWORKS `34.4.1.1011`, the ordinary `suFileStorage::loadVersion` branch at `sldmfcu.dll+0x19ce9f` passes the root prefix `_MO_VERSION_` through virtual slot `+0x250`. The ZIP storage vtable at `0x3cc8d610` gives `0x3c8cb620` for that slot. Its node walk filters to type 1, parses the matching suffix with `_wtoi` at `0x3c8cb7a3` and returns the greatest parsed generation, with zero when none is present. `writeVersion` uses slot `+0x258` at `0x3c8ce8c9`. That ZIP branch renders the supplied version in base ten and reaches `ZipStorage::createZipNode` at `0x3c8ca2e7` when the target folder is absent. Both saved children, `_MO_VERSION_19000/History` and `_MO_VERSION_19000/Biography`, occur in all fourteen saves.

The [container codec](../../../../src/convert/adapters/solidworks/Container/Container.py) builds local and central entries from leaf streams and derives CRCs, sizes and offsets. The version folder has no separate data stream in the measured manifests. The loader has independent `LoadVersionHistory` and `LoadBiography` entry points in `doccplu.dll`. Their first-document branches determine the [generated leaf records](ContainerFraming.md#version-storage).

| Role | Native observation and saved route |
| --- | --- |
| Configuration identity | `SolidStorage_c::LoadConfigMgr` calls `dmConfigMgrHeader_c::loadFromStorage` at `doccplu.dll+0x3968b`. The reader opens `Contents` at `sldarchiveu.dll+0x9678` and the modern `CMgrHdr2` child at `+0x96d6`. The serialized CMgr holds the active part and its aliases. |
| Configuration data | `moBaseConfiguration_c::getStorageName` at `sldmodu.dll` `0x4bdd9887..0x4bdd98b9` concatenates `Config-` and the actual native configuration ID rendered in base ten. The part loader calls this at `doccplu.dll+0x3c7b0` and `+0x3c822`. The saved first part route is `Contents/Config-0`. |
| Resolved features | `moModel_c::loadResolvedFeatures` appends `-ResolvedFeatures` at `sldmodu.dll+0x4487e0` and takes the completed configuration allocation map. The typed root count and map handoff still belong to the configuration and resolved writers. [Loader map handoff](../../records/P04ArchiveWalk.md#map-handoff-in-the-loader) |
| Headers | The saved configuration header is `Contents/Config-0-ModelHeader`; `Header2` is the document header returned by the separate path at `sldmodu.dll` `0x4be8cbe5`. The decompressed payloads agree in all fourteen archives. |
| Definition and auxiliary streams | `Contents/Definition` and `Contents/CMgr` take the existing owning writers. The ordinary `Contents/CnfgObjs`, `ModelStamps` and display update stamp have the [typed empty bookkeeping profile](../PartBookkeeping.md). |

The older [measured stream ablations](../../archive/Multistream.md#4-which-streams-are-load-critical) establish the need for the Definition, CMgr, configuration, ModelHeader and resolved shape records on their measured route. The newer controls include caches, previews, document properties, interchange summaries, and version-history children. No omission probe on generation 19000 has established a minimal loadable roster.

The existing bookkeeping constructors reproduced all three of their streams in each pinned archive. This gives 18 exact stream matches across P01 and 24 across P03.

The fourteen format-4 directories all validated through the existing codec. The 32-bit local record header word exposed by `TemplateFields` as `TypeId` was `0xfff7ffdf` for `Config-0` and `Config-0-ResolvedFeatures`. It was `0xff67dd74` on the two model headers, Definition, CMgr, CMgrHdr2, CnfgObjs, ModelStamps, display update and both version children. The native reader identifies this standard [ZIP date word](ContainerFraming.md#zip-date-word). The dated research wrapper derives it from the document's supplied modification time.

## Active configuration index

`SolidStorage_c::SaveConfigMgr` populates the root from its manager at `doccplu.dll+0x3f4b6..0x3fa02`. Its call at `+0x3f8af` constructs one `dmConfigHeader_c` per configured item. The active selector compares that item with the manager configuration at `+0x3f69a..0x3f6a5`. The `dmConfigMgrHeader_c::Serialize` virtual entry at `sldarchiveu.dll` `0x31a07270` writes the inline list through the member's list virtual at `0x31a0729b`. It then writes the manager save time and sort order at `0x31a073ac` and `0x31a073e6`.

| Saved span | Fields and native source |
| --- | --- |
| 0–49 | Schema-1 manager definition, compact count 1, schema-1 configuration header definition. |
| 49–79 | Active signed 1, native name `Default`, configuration ID 0 and session update. The active bit comes from the identity comparison. The ID comes from virtual slot `+0x188` at `doccplu.dll+0x3f7cb`. The session word comes from configuration member `+0x860` at `+0x3f621`. |
| 79–113 | The native display description `Default`, absent parent sentinel `-1`, clean rebuild word 0, empty comment and alternate name. The save call obtains the parent and clean state through named accessors at `+0x3f784..0x3f7c5` and reads comment and alternate name separately at `+0x3f75c` and `+0x3f774`. |
| 113–129 | CMgr standalone flags from configuration `+0x4c4`, absent LDR mark, geometry-change stamp and transform stamp. The opened part virtual slots `+0x19d8` and `+0x19d0` give `moModel_c::getGeometryChangeStamp` at `0x4b55fdb0` and `moFeature_c::getTransformStamp` at `0x4b55fa00`. The first reads `+0x1300`; the second returns 101. The geometry stamp is caller state. It matches 101 on P01 and ranges 103–111 on the P03 saves, independently of the P03 body stamp 105–121. |
| 129–137 | `moConfigurationMgr_c::getLastSavedTimeStamp` reads `+0x570` and supplies the independent saved time at `doccplu.dll+0x3f4e5..0x3f4f5`. It agrees with the separate ModelHeader self modification-time field. The manager sort order member `+0x75c` is initialized to 2 in the native ordinary manager constructor at `0x4b87fbd6`. |

[`EncodeCmgrIndex`](../../WriterResearch/CmgrIndex.py) writes the isolated 137-byte index. It takes the standalone configuration name and ID, current session stamp, model geometry-change stamp and manager save time. The [read-only replay](../../WriterResearch/VerifyCmgrIndex.py) joined CMgr, ModelHeader, ModelStamps and the selected stream names, then re-emitted exact bytes in six P01 and eight P03 archives. The sorted compact JSON map from receipt file SHA-256 to decompressed index SHA-256 has SHA-256 `37e968f489f54f33265f1927e3b4d17b8f5a3b4679aa9bcecef297d7b173c04a`. The hosted verifier includes this comparison. Hosted execution, independent full part assembly and licensed editable acceptance remain pending.
