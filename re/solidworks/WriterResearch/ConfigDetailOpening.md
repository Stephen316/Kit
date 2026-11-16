# Config-0 detail opening

The configuration model files an empty inline model array and its document detail settings after the ghost and relation managers that follow the [atom manager](ConfigAtomManager.md). `WriteDetailOpening` constructs the first 116 bytes after the relation manager for generation 19000. `WritePlainCharFormat` constructs the distinct inline character format. A complete detail writer must supply the records between these intervals before appending the character format to the shared archive.

## Native ownership

Addresses are RVAs for installed 34.4.1.1011 [pinned source](../records/P04ArchiveWalk.md#inputs).

| Wire span | Owned fields and native implementation |
| --- | --- |
| 0–2 | The part model calls the inline array serializer for its +0xb08 member at `sldmodu+0x10f1c7c`. The supported branch has zero entries. The modern model then calls its +0xae0 virtual detail serializer at `sldmodu+0x10f1ee2`. |
| 2–44 | `moDetailDefs_c::Serialize`, starting at `sldmfcu+0x137730`, stores base standard, custom standard name, center mark size/lines, option flags, virtual sharp type, centerline distance, five automatic-insertion/display options and the cosmetic-thread option at `+0x137790`–`+0x137837`. The supported standard selector is 4 with an empty custom name and virtual sharp type 2. The constructor sets center mark size and centerline distance at `+0xb1041` and `+0xb1015`. The exported `setUseTableTemplateSettings`, `setDisplayGraphicBodiesInDrawingViews` and `setCLUseCenterline` at `+0xbc1f0`, `+0xbb890` and `+0xbb620` own flag bits 14, 18 and 20. |
| 44–116 | The same serializer writes three unsigned linear precisions and three double tolerances, then the three angular precisions and their tolerances, at `+0x13783d`–`+0x1378f7`. The caller supplies the actual document precision settings, including the archived floating-point values. These are distinct from the earlier model-unit selectors. |
| 689–789 | The detail serializer calls the +0x90 format object at `sldmfcu+0x13a401`. `utCharFormat_c::Serialize` at `+0x9f940` writes its framed typeface, system-unit character height, height mode, escapement, style bits, line spacing, width factor, oblique angle, line width, character spacing and font weight. The modern weight field is gated by generation 16109 at `+0x9fa2e`. The narrow encoder uses the ordinary unstyled constructor settings from `+0x9f517`–`+0x9f56a`. The document supplies its typeface, height and line spacing. |

## Pinned comparison

All six P01 and eight P03 receipts at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` share the two exact intervals above. The opening SHA-256 is `6bfbf8c53ada99530d571a98d60420d1de32ac5426445871d629c33c5693aaec`. The saved Century Gothic format SHA-256 is `2f7b80231ff690d22de9a2e66d91d5741077d0094d484d0043ef08a1ac459ce0`. The existing packaged reader discovers the font at +689 and returns the complete detail start at +993, with the original slot count of 57 for P01 and 61 for P03.

[Hosted verification](VerifyConfigDetail.py) compares each constructed interval directly with its receipt-owned bytes and confirms the unchanged archive map. Its replay digest `28ca63bc7a3bfd1f64917d471b2bb2146c477a0d4ebf15276ff4effc9ab7e0c8` covers compact JSON rows keyed by the source SHA-256 and carrying both intervals, the independent detail return and the inherited next slot.

Construction still needs the settings at 116–689 and 789–993, followed by the saved styles and environment owner. In the pinned captures the full saved detail consumes 17,568 bytes and nine archive slots. The following environment consumes 1,488 bytes and 13 slots in both profiles.
