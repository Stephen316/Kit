# Config-0 surface finish and note helpers

`WriteSavedFinishNote` follows the [drawing label definitions](ConfigLabels.md). It writes the generation-19000 `moSFDataHelper_c` and `moNoteDataHelper_c` intervals. Their two embedded annotation objects share one constructor and serialization layout. The caller supplies the four font faces. Each font uses the native unset-height constructor.

## Native field owners

Addresses are virtual addresses in the installed 34.4.1.1011 [pinned DLL](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Parent | `moDetailDefs_c::Serialize` calls the embedded +0x2e8 finish, +0x4d8 note and +0x730 weld helpers at `0x3c86a489`, `0x3c86a499` and `0x3c86a4a9`. Constructor `0x3c7e0fd0` initializes the same members in that order. |
| Unset character height | `utCharFormat_c` default constructor at `0x3c7cf4e0` passes the -1.0 height at `0x3c7cf55c` from `0x3cb32400`, default line spacing 0.001 at `0x3c7cf541` and font weight 400 at `0x3c7cf517`. It resolves the default typeface separately. Its modern serializer is the [same character format](ConfigDetailOpening.md) used throughout saved detail. |
| Shared annotation | Constructor `0x3c7e0d40` sets its unset-layer and leader settings and constructs the embedded font. `moAnnotationDataHelper_c::Serialize` at `0x3c8659e0` files style and layer data, font settings and two independent leader groups. The group stores are at `0x3c865a5a`–`0x3c865acf`. |
| Finish | `moSFDataHelper_c` constructor `0x3c7e2470` initializes the surface finish selector, empty text, angular and display options and both embedded helpers. Serializer `0x3c86fd00` files the legacy surface finish data and fonts, then the embedded annotation at `0x3c8700d2`. The two supplemental texts and trailing settings follow at `0x3c8700f5`–`0x3c870191`. The supported finish has empty text, unset fonts, and the initial angle. |
| Note | `moNoteDataHelper_c` constructor `0x3c7e2210` initializes the separate note strings, annotation options, tolerance defaults, text formatting and quantity defaults. Serializer `0x3c86eb50` starts with its four strings and options. It files the font at `0x3c86ed92`, then the empty attachment map at `0x3c86edc5`. The modern option and quantity tail comes from the stores at `0x3c86f3da`–`0x3c86f5f3` and the following enabled branches. The note delimiter is the constructor-supplied `X`. |

## Pinned comparison

All six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` have the same finish bytes at +13011–13333 and note bytes at +13333–13740 relative to the relation return. Their SHA-256 digests are `140e622af90241ea7d7290dee6f407d2fea7993e025671142bae1065011d4c80` and `778e67b2364d1cd96a12b7fcdd7d4791ecb6c699b422534fe780c124a7bbcc71`. Neither helper allocates a class or object slot. The independent weld reader then reaches +14784. [Hosted comparison](VerifyConfigFinishNote.py)

The replay SHA-256 is `2ceee3fcf4ba3de8a4a94aa881bebc97dddd865a246631912053b1c7c04ed70f` over the source receipt hashes, native offsets, inherited next slot and the two constructed record hashes.
