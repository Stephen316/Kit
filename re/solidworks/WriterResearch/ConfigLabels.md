# Config-0 saved label definitions

`WriteSavedLabels` follows the [table definitions](ConfigTables.md) and reconstructs the generation-19000 `moLabelDefs_c` record. Its five label objects share an inline base, with separate text formats and per-type defaults. The caller supplies fonts for the detail and section labels, auxiliary, orthographic and miscellaneous, component text and the separate shared font. The supported slots within each of those groups carry the same format.

## Native field owners

Addresses are virtual addresses for the installed 34.4.1.1011 [pinned DLL](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Parent | `moDetailDefs_c::Serialize` calls its +0x2750 label member at `0x3c86a448`. Constructor `0x3c857480` identifies detail, section, auxiliary, orthographic and miscellaneous at +0x18, +0xe8, +0x1e8, +0x2b8 and +0x388 and stores the separate font at +0x458. Serializer `0x3c86e7d0` first writes the section and detail switches, then both owners and the auxiliary owner. It files the common font before orthographic and miscellaneous. |
| Common base and fonts | `moDrViewLabelData_c::Serialize` at `0x3c87d8c0` sends label names and syntax, delimiter options, position, styles and the unused layer at `0x3c87d900`–`0x3c87d9f2`. Its +0x5c clockwise option comes from bit 2 in `setClockwise` at `0x3c87f860`. The serializer files the view label and entity fonts, entity and view border widths, then the label, scale, delimiter and angle fonts at `0x3c87dbeb`–`0x3c87dcb5`. Native constructor `0x3c87c0c0` and standard defaults `0x3c87dfd0` establish the shape. |
| Detail and section | Detail serializer `0x3c87d7e0` files its options and drawing style after the base. The dimension and cosmetic thread inheritance setters at `0x3c87f8b0` and `0x3c87f830` control bits 3 and 4. Section serializer `0x3c87de00` files arrow width, height and length, text-height scaling, alternate treatment, arrow style, half-section arrow and shoulder visibility. Section defaults follow constructor `0x3c87c640` and standard-specific `getDefaults` at `0x3c87e2f0`. |
| Auxiliary and orthographic | Auxiliary `0x3c87d760` files its simplified-view option. Orthographic and miscellaneous use the common serializer at `0x3c87dd50` and file their label visibility and creation settings. Constructors `0x3c87bc10`, `0x3c87c550` and `0x3c87c4b0` establish the three defaults. |

## Pinned comparison

The six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` contain the same 3,570-byte label interval, from +9441 to +13011 relative to the relation return. Its SHA-256 is `72ba8a71eb8f14338d591bd4ea623511b275b4d726f2592a41b52c17d76907f6`. The archive next slot remains 66 or 70. The independent finish helper continues to +13333. [Hosted comparison](VerifyConfigLabels.py)

The replay SHA-256 is `ec01b43a07347fac6f8e851b419a03da1a6cd70bab391a3ba90a0d392e9443d1` over source receipt hashes, the label and finish boundaries, inherited slot and rendered interval hash.
