# Standalone resolved system folders

The first six resolved roots in the generation-19000 P01 and P03 saves are Comments, Favorites, History, Selection Sets, Sensors and Design Binder. Their feature IDs are 8, 23, 24, 25, 22 and 7. The licensed feature tree verifies the names. The saved ModelHeader logs independently bind those names to the same tree IDs.

The native module is `sldmodu.dll` from SOLIDWORKS `34.4.1.1011`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. Disassembling the folder constructors with `dumpbin 14.51.36231 /DISASM` identifies the primary vtable for each folder. The archive entry is slot `+0x28`.

| Folder | Archive entry | Store sequence after the inherited record |
| --- | --- | --- |
| Comments and Design Binder | `0x4beb0af0` | Calls `moFeature_c` at `0x4bb10d90`. Then `0x4beb0b2c` and `0x4beb0b3b` save the two signed members at `+0x360` and `+0x370`. Comments has `(0,0)` and Design Binder has `(1,0)`. |
| Favorites | `0x4b63d460` | Calls the common folder entry at `0x4b63d470`. The measured empty collection and final `+0x408` word follow the common words. The collection serializes at `0x4b63d592`, and `0x4b63d5ab` writes the final 1. |
| History | `0x4b644cb0` | Calls the common folder entry at `0x4b644cc0`, then the empty list at `0x4b644d07` supplies the compact count word. |
| Selection Sets | `0x4b640a30` | Calls the common folder entry at `0x4b640a40`. The compact empty collection serializes at `0x4b640a8b`, then `0x4b640aa4` writes the signed 1 from `+0x3e0`. |
| Sensors | `0x4beb0e00` | Calls the common folder entry at `0x4beb0e10`. The standalone captures end after the two common words. |

The [inherited feature codec](CmgrInherited.py) writes the update stamp, last update generation and build, and FILETIME separately. The stores at `0x4bb10e8e`, `0x4bb10eeb` and `0x4bb10efa` read members `+0x29c`, `+0x2b8` and `+0x2bc`. The named getters `getUpdateStamp` and `getLastUpdateVersion` corroborate those fields. Sensors retains the initial update stamp 101 and zero last-update version. The other five folders have saved last-update values 19000 and 2026225. Their update stamps vary with the file and folder. [Shared feature state and FILETIME stores](CmgrOpening.md#inherited-fields-and-first-allocation)

Each folder allocates a class and an object, then instantiates its name through the `moNodeName_c` class inherited from Config-0. The six folders therefore allocate 18 slots. The read-only replay reaches byte 1221 before `moDetailCabinet_c` across all 14 pinned saves. The allocator advances from 106 to 124 in P01 and from 111 to 129 in P03. The actual source span starts at byte 6 after the resolved list header.

The source SHA map sorts the 14 source file SHA-256s and maps each to its saved folder-span SHA-256. Compact JSON SHA-256 is `21a06cba04c78d1311519d08df37d3dc310cf090075a6916abc371fd93fd583e`. The hosted verifier reconstructs the six objects and compares the exact bytes and final class map. [Hosted gate entry](VerifyResolvedFolders.py)

After the annotation cabinet, [the resolved body, markup, equation and material folders](ResolvedFolderTail.md) continue through the principal-plane definition.
