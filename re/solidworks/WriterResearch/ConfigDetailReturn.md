# Config-0 saved detail return

`WriteSavedDetailEnd` follows the [weld and geometric tolerance helpers](ConfigWeldTolerance.md). It appends the remaining generation-19000 detail settings and the model's empty shared parameter array. The caller supplies three unset annotation faces, two point-size font faces, and the saved description and cut-list templates.

## Native ownership

Addresses are virtual addresses in the installed 34.4.1.1011 [pinned binaries](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Center mark, datum feature and datum target | `moDetailDefs_c` calls its embedded +0xb88, +0xcd8 and +0xde0 members at `0x3c86a4c9`, `0x3c86a4d9` and `0x3c86a4e9`. Their constructors at `0x3c7e0de0`, `0x3c7e0e80` and `0x3c7e0ee0` initialize the supported field groups. The target constructor sets both 0.03 dimensions at `0x3c7e0f7b`–`0x3c7e0f89`. The three serializers at `0x3c866d60`, `0x3c867290` and `0x3c867420` each call the shared annotation helper. |
| Swift | The parent writes +0xf68 at `0x3c86a4fd`. Constructor `0x3c84c1d0` and `setDefaultFlags`, `setDefaultPrecisions` and `setDefaultTolerances` at `0x3c84f600`, `0x3c84f790` and `0x3c84f9f0` establish the native scalar defaults. `moSwiftGtsOptions_c::Serialize` at `0x3c84c490` writes the tolerance, precision and option fields in the filed order. This modern record stays separate from the earlier legacy Swift angle and selector. |
| Print widths and drawing options | `utLineWidthPrintData_c` constructor `0x3c85aab0` sets eight single-precision widths and serializer `0x3c85acb0` files them inline through the call at `0x3c86a541`. The parent then stores hatch density, drawing zone, rounding and border options at `0x3c86ae89` through `0x3c86b30a`. The border and zone formats at members +0xa0 and +0xa8 serialize at `0x3c86b340` and `0x3c86b350`. `utCharFormat_c::setCharHeightInPoints` at `0x3c7d06e0` establishes the -1.0 system-height sentinel and independently stored integer point size. |
| Descriptions and detail return | `moDetailDefs_c::Serialize` files the solid-body and sheet-metal strings and description options at `0x3c86b42a`–`0x3c86b4c5`, then files the three cut-list templates at `0x3c86b635`–`0x3c86b65f`. Its last model option store is at `0x3c86b7d0`. |
| Shared parameters | Model constructor `sldmodu` at `0x4c00ce42` creates the +0x9c8 member. Its RTTI identifies `moSharedParams_c` at vtable `0x4d0c5d78` with serializer `0x4c553d10`. The part model invokes it at `0x4c232178` and then writes the environment pointer at `0x4c2321de`. The supported shared parameter array has an empty short count and allocates no classes or objects. |

## Pinned comparison

The six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` have the same 2,396-byte interval from +15172 through +17568 relative to the relation return. Datum fields end at +15756, Swift ends at +16568 and the detail owner returns at +17566. The shared parameter count ends at +17568. Their combined SHA-256 is `1c1fe105cd3355974210787336d0621444f70786686baf4e7017f429043de826`. The next slot remains 66 for P01 and 70 for P03 across this interval. The independent environment reader ends at +19056 with next slot 79 or 83.

[Hosted comparison](VerifyConfigDetailEnd.py) will compare the generated return to all 14 native intervals and validate the complete live map. The expected native-only replay SHA-256 is `3b099160e1ab5803a6a4d06712abe98aebbec950fef8dc5943c8a2647ad0429a`.
