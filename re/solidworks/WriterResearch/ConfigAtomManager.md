# Ordinary Config-0 atom manager

`WriteConfigAtomManager` starts the [second Config-0 split](ConfigSplitEdges.md), writes the zero- or one-atom list and files the manager generation. It leaves the next byte for the ghost ID manager. The P01 profile has no atom. The P03 profile takes a `BossAtomBody` containing the native feature ID and the kernel tag for the solid body supplied by the geometry producer. The returned `ConfigAtomBinding` distinguishes native atom ID, archive occurrence and Boss feature ID.

## Native fields

The following RVAs refer to the installed 34.4.1.1011 [pinned modules](../records/P04ArchiveWalk.md#inputs). The `sldgcu.dll` SHA-256 is `797f81cba7080ea6edd37eca36abeaa9a2c0539f9319b980b92abc5a875edf24`.

| Field group | Native authority |
| --- | --- |
| Allocation and inherited node | The manager advances and passes its atom ID to the constructor through `sldmodu+0xbafde2`–`+0xbafe12`. The atom constructor `+0xbacfa0` calls the concept constructor and assigns the atom vtable. Slot 5 reaches the atom serializer at `+0xbaece0`. At `+0xbaed4d` it calls the inherited concept serializer. The inherited node constructor seeds update word 1 and empty secondary flags. The ordinary record has no node name, uses the initial node flag and ID -1, and files empty child, appearance and node-list state. [Inherited node fields](CmgrOpening.md) |
| Atom ownership and display state | File stores `+0xbaed6c` and `+0xbaed7b` write the allocated atom ID and its initial flags. Stores `+0xbaeda1` and `+0xbaedc5` call the two feature owners' virtual ID getters. Each resolves to the same Boss in this profile. Store `+0xbaedd4` writes constructor-cleared atom attributes. The measured geometry mode is 0 from `+0xbaefd5`. The following stores at `+0xbaefe4`, `+0xbaeff3`, and `+0xbaf02a` write blanking state, the constructor's 1 at +0x18c and the unset mold-body type. The last dword at `+0xbaf0cd` comes from constructor value 6 at +0x19c. |
| Atom manager return | The manager initializes its member +0xa8 using the current file generation at `+0xbafb49`–`+0xbafb55` when zero. Its serializer appends that unsigned dword at `+0xbaeb11` after its last atom. The ghost manager is invoked separately at `+0x10f1a24`. |

## Partition rollback geometry

The zero inline geometry mode omits the `mo_storeBodyToArchive` call. Later in the same serializer, the ordinary archive context checks the geometry environment's +0x20 flag. The exported `sldgcu!gcEnvironment_c::getSavePartitionRBDataOn` at RVA `0x1c460` returns exactly that member. With rollback data enabled and the archive override clear, `sldmodu+0xbaf091` and `+0xbaf097` obtain the two references from atom members +0x180 and +0x1b0. The `gcEnt_w::isValid` entry at `sldgcu+0x2975d0` treats geometry handles as positive signed 32-bit entity tags. Native body backup stores the body handle in +0x180 at `sldmodu+0xbaff2b` and its `gcBody_w::isSolid` result in +0x188. The corresponding load branch reads both reference words and the solid flag at `+0xbaf31c`, `+0xbaf337` and `+0xbaf347`.

The eight P03 files save the same tag in both places and a solid flag of 1. The tags differ across the captures and their literal dwords occur only at those two Config-0 fields. The bounded writer therefore requires the matching owned kernel tag as an input. The body tag varies independently of the Boss feature ID, archive occurrence, body bounds and display tail. The native producer for the second reference member and a portable construction of the rollback geometry still need qualification. The native zero-reference branch also needs an independent load and rebuild result before a caller can select it.

The P01 and P03 archives carry separate `Config-0-Partition` and `Config-0-GhostPartition` streams. A prior first-principles single-pad case rebuilt with its partition stream omitted in SOLIDWORKS 33.5.0. That establishes an earlier cache-omission path. Generation-19000 qualification still needs its own save, load and rebuild result for the zero-reference case. [Prior native result](../records/PolylineSixPad.md#live-solidworks-proof)

## Pinned comparison

All six P01 and eight P03 receipts at revision `466dcb172dfa3803463e07ccde963ba01671d200` match the constructed manager's bytes. Its width is 18 bytes for P01 and 118 bytes for P03. The allocator reaches slots 55 and 59 respectively before the ghost manager. The independent reader crosses the 40-byte ghost record and enters the relation manager, reaching slots 57 and 61. All eight P03 Bosses resolve feature ID 34 and object occurrence 58 from the configured atom ID 101. Native licensed body counts distinguish the empty and populated choices.

The replay SHA-256 is `193129f1559b395334b21a75f00b49ccf19f343b83ccb95ce63bdab175d83865`. Compact sorted-key JSON records the second-split body start, ghost and relation boundaries, next archive slot, typed atom binding and rendered span digest under each receipt SHA-256. [Hosted verifier](VerifyConfigAtoms.py)

The comparison constructs only the owning archive span in memory. Complete second-split writing and fresh-process SOLIDWORKS acceptance are pending.
