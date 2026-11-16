# Config-0 saved table definitions

`WriteSavedTables` follows the [annotation definitions](ConfigAnnotations.md). The generation-19000 table owner saves nine inline settings objects, a separate shared font and two cell padding values. The caller supplies the member and shared fonts separately. All nine member fonts use the same format in the supported profile.

## Native field owners

Addresses are virtual addresses in the installed 34.4.1.1011 [pinned DLL](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Order | `moDetailDefs_c::Serialize` calls its +0x2410 table member at `0x3c86a434`. `moTableDefs_c::Serialize` at `0x3c8702e0) files the standard, then the general, revision, BOM and hole tables. Its shared font is called at `0x3c87037e`. The title block, weld, bend, punch and family tables follow. Constructor `0x3c8e33f0` identifies these embedded objects and initializes the separate shared format. |
| Common base | `moGeneralTableDefs_c::Serialize` at `0x3c86d640` stores the standard, leading and trailing zero settings, the current layer and dual-dimension position. The -1 layer skips its optional data at `0x3c86d6b1`. The inherited line widths serialize at `0x3c86d767` and `0x3c86d779`, then the inline character format follows. The constructor at `0x3c8e31b0` and standard initialization at `0x3c8e48b0` supply the shared fields. |
| Revision and BOM | Revision constructor `0x3c8e33a0` and serializer `0x3c86fc00` own the symbol, change and additional-sheet settings, row count and placeholder. BOM constructor `0x3c8e3120` and serializer `0x3c865f60` own the zero-quantity fields and the three empty custom texts. |
| Hole and punch | The hole table starts at serializer `0x3c86e5c0` and constructor `0x3c8e32b0`. The punch table starts at `0x3c86f9a0` and `0x3c8e3330`. Each serializes its own table axes, alphanumeric style, offset, angle and display options. Their field orders differ. The punch constructor clears the extra +0x50 member at `0x3c8e3357` before the serializer writes it at `0x3c86fa2b`. |
| Weld, bend and family | Weld serializer `0x3c870d90` appends the two-sided quantity tag. Bend serializer `0x3c866c80` stores length precision, angle precision, alphanumeric style and bend allowance precision in that order. Family serializer `0x3c86cad0` files its option flags after the base. The title block has no separate suffix in this profile. |
| Cell padding | Constructor `0x3c8e3487`–`0x3c8e34a2` assigns the 0.0005 horizontal and 0.001 vertical values. `moTableDefs_c::Serialize` writes them in that order at `0x3c87043e` and `0x3c87044f`. |

## Pinned comparison

All six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` carry the same 1,466-byte interval, from +7975 to +9441 relative to the relation return. Its SHA-256 is `4aa2e94dc16559c8b41290e025e7784e22ec929f412a1e2013289d83e9f9f727`. It consumes no class or object slots. The independent label reader then reaches +13011. [Hosted comparison](VerifyConfigTables.py)

The replay SHA-256 is `b3d0a77dc2f93a84c3509b254d954090b96968c8db4232cbab350e8fbc6339a3` over the archive receipt hashes, native boundaries, incoming slot and generated interval hash. The saved label definitions follow.
