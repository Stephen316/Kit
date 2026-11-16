# Config-0 and ResolvedFeatures archive state

The generation-19000 standalone P01 and P03 parts use one object namespace across `Contents/Config-0` and `Contents/Config-0-ResolvedFeatures`. Each group of archive records has its own byte framing. The inherited next slot and the resolved list's outer entry count measure different things.

## Native writers and loaders

The installed build is 34.4.1.1011. The [loader walk](../../records/P04ArchiveWalk.md#inputs) pins `doccplu.dll`, `sldmodu.dll` and `swccu.dll`. The `slduiu.dll` SHA-256 is `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6`.

| Owner | Store operation |
| --- | --- |
| `sldmodu` split archive helper | At RVAs `0x10cee92` and `0x10ceeb6` the native store path records positions immediately before and after the placeholder dword. Teardown subtracts the second position from the final position at `0x10cf799`–`0x10cf79f` and patches exactly four bytes at `0x10cf7c9`. The first Config-0 split begins after the root class and length. The second begins immediately after its own length and ends at the stream end. |
| `doccplu!SolidStorage_c::iSaveModelDefn` | At `0x180025830` the cache constructor uses state 2 after the active model definition has been serialized. |
| `slduiu!saveResolvedFeatureList` | At RVA `0x888166` it restores archive cache state 1. At `0x888173` it writes the signed 32-bit live counter at archive +0x50, then at `0x888184` it serializes the actual outer `suObList`. The compact `WriteCount` form is a u16 below `0xffff`. |

The matching loaders cache state 2 at `doccplu+0x3d8d8` and restore state 1 at `sldmodu+0x4489bc`. The archive transfer copies the pointer array and next-slot counter through `swccu+0x9210`. The initial root definition occupies class slot 1 and instance slot 2. The native header pushes the self external object directly at slot 3 via `sldmodu+0x1039fb2` and `swccu+0x9d00`. Its record consumes a map slot without a pointer tag. The native environment root in ResolvedFeatures is a compact object alias to the `moEnvFolder_c` emitted in Config-0. This alias counts as a resolved root and consumes no new slot.

## Receipt-pinned comparisons

The six P01 and eight P03 saves at receipt revision `466dcb172dfa3803463e07ccde963ba01671d200` have the following extents and allocations. The native parsed classes and objects together occupy every slot from 1 to the next slot exclusive. Slot 3 is the only typed object without a class definition in the namespace.

| Profile | First body bytes | Second body bytes | Config classes | Config objects | Next slot | Resolved roots | Environment slot |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | 2875, 2915 | 22076, 22148 | 38 | 67 | 106 | 18 | 67 |
| P03 | 3034, 3036, 3074 | 22706, 22714, 22778 | 40 | 70 | 111 | 19 | 71 |

The map census has SHA-256 `e6f204e0ca9e4d6910c3268e9efde27bae0b55a0df7c77717defb6e68a1dc772` over compact sorted-key JSON keyed by receipt artifact SHA-256. Each value holds the two split lengths, next slot, sorted class entries, sorted object entries, resolved root count and environment slot, in that order.

The [hosted verification](../../WriterResearch/VerifyConfigResolvedFraming.py) reconstructs the already typed Config-0 root and appearance prefix on the tracked allocator and verifies its exact bytes and map. It independently walks both full native Config-0 splits using the ordinary reader and compares their framing words. It counts the direct resolved entries from the parsed system list, origin, sketch and optional Boss. The generated header and inherited environment alias match the native bytes for those fields.

## Composition boundary

`BuildConfigArchive` writes the root tag, records the implicit external object and runs typed owners of the first and second split on one writer. It derives each length from bytes that its own callback produced. The result includes the full archive state with the bytes. `BuildResolvedArchive` resumes that state in a separate buffer. It writes one entry per supplied outer constructor, including aliases, and derives the root count from that list. A constructor writes its nested children in the same call. The tail serializes after the list and uses the same allocator.

The [ordinary split constructors](../../WriterResearch/ConfigSplitEdges.md) now supply the complete first callback and the initial atom-manager state for the second.

`PartArchiveWriter` tracks both `BeginObject` and `begin_object`, checks alias ownership, and exposes `ReserveObject` for proven native insertions without tags. Passing its state to another writer takes a copy of the class and object maps. Snapshot validation rejects untracked index gaps and overlapping ownership.

This research code composes the framing around explicit typed callers. Complete Config-0 and ResolvedFeatures record construction, full document packaging, and an independent native fresh-process acceptance run remain pending.
