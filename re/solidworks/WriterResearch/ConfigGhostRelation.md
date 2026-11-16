# Config-0 ghost and relation managers

`WriteGhostRelationManagers` follows the [ordinary atom manager](ConfigAtomManager.md). It writes one inline sketch-point ghost and an empty relation manager and returns both identifiers. The caller supplies the populated ghost-partition condition and automatic equation ordering. The existing Config-0 archive allocates the relation object as the next class and instance. The following model-array and detail settings belong to a separate writer.

## Native ownership

Addresses are RVAs in the installed 34.4.1.1011 [pinned binaries](../records/P04ArchiveWalk.md#inputs). The ghost-mode check uses `sldgcu.dll` from the [ordinary atom work](ConfigAtomManager.md#native-fields).

| Owner | Stored fields |
| --- | --- |
| Ghost ID manager | The model passes its +0xd90 object at `sldmodu+0x10f1a24`. RTTI identifies its virtual serializer as `moGhostBodyIdManager_c` at `+0xdc3cf0`. Constructor `+0xdc2718` seeds ID 10000. Normal registration advances that counter at `+0xdc76a4` and assigns the new ID to the inline object at `+0xdc776a`. The running ID is filed at `+0xdc3d6c`. |
| Packed ghost count | The serializer queries the model's ghost partition through `gcPartition_w::getBodies` at `+0xdc3e02`. A positive result selects flag 2 via `+0xdc3e0c`–`+0xdc3e32`. The writer combines the flag in the upper nibble and the retained record count in the low 28 bits at `+0xdc3e38`–`+0xdc3e41`. The record's inline virtual call at `+0xdc3e5f` allocates no archive slot. |
| Sketch-point ghost | The registration route gets the reference's virtual type at `+0xdc76b7`. `moCompRef_c::getGhostRefType` returns 20 for a sketch point or an `sgPointHandle` at `+0x6b96d5`. The ghost constructor retains that type and clears its flags and geometry pointer. Virtual `moGhostBodyObject_c::Serialize` at `+0xdc3fa0` files the ID, type, flags and point reference at `+0xdc4010`, `+0xdc401d`, `+0xdc402a` and `+0xdc403a`. The point-data constructor seeds the unset ID at `+0xdc2e03`. The sized source-ID array is written at `+0xdc4085` and `+0xdc40aa`. Both profiles store one unset source ID. The geometry-presence and point count are zero at `+0xdc40da` and `+0xdc4166` for this branch. |
| Empty relations | The model's +0x9d0 owner is filed as `moRelMgr_c` at `+0x10f1a80`. Its serializer at `+0x11f7f70` files an empty relation list and `RelCacheDimValueMap_c` at `+0x11f7f8a` and `+0x11f7f98`. Then it writes the external-equation filename, link flag and `su_CTime` at `+0x11f826e`, `+0x11f827d` and `+0x11f8297`. All three are empty in this profile. |
| Relation ordering and return | Stores at `+0x11f82a6` and `+0x11f82b5` file the automatic-order member +0x150 and the initial relation ID. Exported `setAutoSolveOrder` writes +0x150 at `+0x1cfa60`. The constructor sets both ID and +0x1b0 to -1. Stores at `+0x11f82c8`, `+0x11f82d4` and `+0x11f82ef` file the empty auxiliary list, unset +0x1b0 and zero feature-parameter count. The later helper at `+0x11f8880` has no further on-stream writes for the empty feature-parameter vector. |

The ghost partition may have bodies while the mechanical part has no solids. P01 still carries the one sketch-point record. Inline geometry and the separate ghost partition therefore have distinct ownership.

## Pinned comparison

The six P01 and eight P03 files at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` share the same 40-byte ghost interval and 50-byte relation interval. The relation entry includes its 16-byte schema-1 class tag. Native archive counters reach 57 for P01 and 61 for P03 after that object. The independent detail reader consumes exactly 993 more bytes from the recorded boundary in all 14 saves. [Hosted verification](VerifyConfigGhostRelation.py)

The replay SHA-256 is `0ba2e2768dbbe1c6bba1e669fdde413b75edba4e4819b4a7f0e17e77ba8fba23`. Compact sorted-key JSON records the four witnessed offsets, next map slot, ghost ID, relation object slot and span hash under each receipt SHA-256.

The generated interval ends before the leading model array and saved detail. Constructing the separate ghost partition stream, the detail/environment owners and the remaining configuration records is still pending.
