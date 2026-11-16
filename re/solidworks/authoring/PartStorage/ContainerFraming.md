# Generation-19000 ZIP date and version storage

The [standalone research framing](../../WriterResearch/PartFraming.py) emits format 4 with the existing admitted signature pair, then uses an explicit document modification time for the local and central ZIP date fields. It adds the two real version-storage children in their no-prior-history forms. The generic container emitter retains its existing behavior.

## ZIP date word

The member called `TypeId` in [the generic codec](../../../../src/convert/adapters/solidworks/Container/Container.py) occupies the conventional ZIP date and time slot. The following native paths are in installed `sldmfcu.dll` build `34.4.1.1011`, SHA-256 `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6`, preferred base `0x3c730000`.

| Native path | Result |
| --- | --- |
| ZIP directory load at `0x3c99f770` | The actual SolidWorks ZIP reader at `0x3c9a6cad` reads the 32-bit word and unpacks it at `0x3c9a6cc1..0x3c9a6d07`. The high half is the year, month and day. The low half is the hour, minute and seconds divided by two. |
| Local entry validation at `0x3c9a6980` | The call directly after the compression member consumes the date field before CRC. Its branch checks the read result and proceeds to CRC and size checks. |
| ZIP write at `0x3c9a4828..0x3c9a487e` | A nonzero packed input supplies the field directly. The other lane packs its ordinary civil date and time members. Both use the same resulting word. |
| Local and central stores | `0x3c9a3127..0x3c9a315d` writes four little-endian bytes to the local header. `0x3c9a49ff..0x3c9a4a1f` writes the same word to central offset 12. |

The valid date rule is `(year - 1980) << 25 | month << 21 | day << 16 | hour << 11 | minute << 5 | floor(second / 2)`. The research caller provides Unix time in UTC. The date field represents 1980 through 2107 and rounds downward to two seconds. It needs only one caller-supplied clock value per document.

All 518 local words in the fourteen pinned P01 and P03 format-4 directories agree with their central words. Of these, 392 contain `0xff67dd74`, which decodes with hour 27. The remaining 126 contain `0xfff7ffdf`, which decodes with month 15 and hour 31. This second value occurs in `Config-0` and `Config-0-ResolvedFeatures`. These words are historical observations. Their provenance through the caller's date structure remains unobserved. The research writer derives a valid independent clock from the same saved-time input used by the owning document.

## Version storage

The ordinary generation reader discovers the maximum numeric `_MO_VERSION_` node. The lower-level ZIP entry map specifically skips decoded paths ending in `/` at `0x3c99f9fd..0x3c99fa41`. The upper-level namespace derives type-1 parent nodes from accepted leaf paths at `0x3c7ad604..0x3c7ad6ac`. The actual loader path therefore needs a real leaf to materialize `_MO_VERSION_19000`. All fourteen saved manifests contain only `History` and `Biography` in that storage.

The independent readers have defined first-document cases:

- `SolidStorage_c::LoadVersionHistory` in pinned `doccplu.dll` SHA-256 `120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b` reads a generic archive object at RVA `0x2121f`. A compact null takes the branch at RVA `0x21224..0x21321`. It obtains the document header, calls the native `moVersionHistory_c` constructor, initializes it with `fileCreated` and installs it on the document. The path still reaches native version validation at `0x213eb`. The research stream emits only the two-byte null tag, so native initialization owns any license state and application metadata.
- `SolidStorage_c::LoadBiography` reads a type-checked `moBiography_c` at RVA `0x21f39..0x21f69`. Its schema-1 serializer is at `sldmodu.dll` `0x4c71c9f0` in the [pinned build](../../records/P04ArchiveWalk.md#inputs). The load branch reads signed prior-record count at `0x4c71cf08`. A zero count branches directly to `0x4c71d250..0x4c71d28f`, which constructs, initializes and appends a current `moBiographyRecord_c`. The generated 23-byte object carries no prior session metadata.

The two independent native reader branches justify the generated representations. The historical saves contain populated records, so these deliberately generated leaves have different bytes. [Prior version detector and configuration routing](ConfigurationIndex.md#version-and-main-stream-dispatch)

The [hosted framing check](../../WriterResearch/VerifyPartFraming.py) uses the fourteen captured ModelHeader modification times as independent scalar inputs, generates only the two typed metadata streams in memory, and verifies their names, container version, local and central clock fields and complete archive objects. No part candidate is created by that proof. Hosted execution and controlled native opening of a fully composed part remain pending.

A direct in-memory observation at Unix time corresponding to 2026-11-16 10:05:27 UTC produced a 313-byte metadata archive. Its reader reports generation 19000, format 4 and two clock words of `0x5d7050ad`, which represent 10:05:26 UTC. Its SHA-256 is `f321fbec984418045055f40b8929f4f3e95dc8943554a212cea04d3501b036f6`.
