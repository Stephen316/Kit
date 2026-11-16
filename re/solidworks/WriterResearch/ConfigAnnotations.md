# Config-0 saved annotation definitions

`WriteSavedAnnotations` follows the [dimension styles](ConfigDimensionStyles.md) and writes the complete generation-19000 `moAnnotationDefs_c` interval. All its members serialize inline. The caller supplies the standard annotation font, the weld root font, and the revision cloud font separately.

## Native field owners

Addresses are virtual addresses in the installed 34.4.1.1011 [pinned DLL](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Annotation defaults | `moDetailDefs_c::Serialize` sends its +0x1f18 member at `0x3c86a424`. `moAnnotationDefs_c::Serialize` at `0x3c865c20` stores the base standard, bend distance and mode, attached arrow choices, leading and trailing zeros, 3D notes and annotation display and two thread options. The fields follow the stores at `0x3c865c60`–`0x3c865ce9`. Constructors at `0x3c7b2ff0` and `0x3c7b30f0` establish the member objects. |
| Shared annotation base | `moBaseAnnotationDefs_c::Serialize` at `0x3c866430` writes the standard, bend ownership and distance, leader and frame settings, the no-layer branch, then invokes the two inherited line widths and inline font at `0x3c866615`, `0x3c866627` and `0x3c866636`. The return stores automatic balloon leader style at `0x3c866646`. Constructor `0x3c7b3300` initializes the shared members and line widths. The balloon and view-location label constructors override `setUseDocBend` to false. |
| Balloon, note and datum | The parent orders slots +0x2c0, +0x418 and +0x250 first, through calls `0x3c865e2d`, `0x3c865e41` and `0x3c865e51`. Balloon `0x3c8660c0` writes fit and style, note texts, balloon sizes, quantity options and padding. The quantity delimiter comes from literal address `0x3cb49cb8` at constructor call `0x3c7b32ae`. Note `0x3c86f710` writes fit, style, justification, size, padding, spacing and period handling. Datum `0x3c8671a0` returns its six leader and label options. |
| Geometric tolerance, surface finish, weld and bend note | The next embedded members are +0x1e8, +0x108, +0xa0 and +0x178. Their serializers are `0x3c86d820`, `0x3c8701f0`, `0x3c870d10` and `0x3c866bb0`. The geometric tolerance constructor `0x3c7b34c0` sets decimal separator U+002E. Surface finish supplies its scale and revision, weld supplies its root font in addition to the base font, and the bend note adds its own balloon settings. |
| Default annotation, revision cloud and view-location label | Calls `0x3c865ee4`, `0x3c865f03` and `0x3c865f24` file the +0x4a0 base, +0x40 revision cloud and +0x398 view-location label settings. Revision cloud at `0x3c86fbb0` adds its maximum radius. View location at `0x3c8704c0` adds balloon dimensions and note content plus its sheet and zone display flags. |

## Pinned comparison

All six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` have the same 1,956-byte interval, beginning at +6019 and ending at +7975 relative to the relation return. Its SHA-256 is `740d5cc0c77735ff9d64a790ee72629a3e1be7ff62a72d373daaaf8cb9562966`. The incoming next slot stays at 66 or 70, and the independent table reader reaches +9441. [Hosted comparison](VerifyConfigAnnotations.py)

The replay SHA-256 is `c70e99640be3231a0239d84e64203b5af1f7be90e89129b9fbb924c1a9dc0b07` over the pinned source hashes, native boundaries, inherited next slot and generated span hash. Construction continues with the saved table definitions.
