# Resolved body, markup, equation and material folders

The generation-19000 P01 and P03 saves put Surface Bodies (tree ID 10) and Solid Bodies (9) immediately after the [annotation cabinet](ResolvedCabinet.md). The environment reference follows those two roots. The remaining folders are Markups (21), Equations (16) and `Material <not specified>` (11). The licensed feature tree establishes the display names, and the ModelHeader revision records independently bind them to the tree IDs.

The archive entry for each class is vtable slot `+0x28` in SOLIDWORKS `34.4.1.1011` `sldmodu.dll`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

| Owner | Archive entry | Ordinary standalone store path |
| --- | --- | --- |
| Surface and Solid Bodies | `0x4c214f70` | Calls the shared folder owner at `0x4beb0af0`. The stores at `0x4c214fb0` and `0x4c214fc3` write the two signed members at `+0x37c` and `+0x380`. The object paths at `0x4c214ff4` and `0x4c215028` carry compact nulls in these saves. |
| Markups | `0x4beb0af0` | The runtime class factory at `0x4beac320` calls the constructor at `0x4bead040`, which installs the primary vtable `0x4d045788`. The slot points to the shared folder store. |
| Equations | `0x4bb10360` | Calls the same folder owner at `0x4bb10370` and returns after its two signed words. |
| Material | `0x4beb0ca0` | Calls the shared folder owner. The call at `0x4beb0cda` saves the wide string at `+0x378`, followed by the signed flags word at `0x4beb0d08`. The unassigned state is an empty string and the high-bit flag. |

Each folder has the [shared named node](ResolvedFolders.md), an empty node list and explicit inherited feature bookkeeping. Body and Material folders carry the saved last-update generation and build `19000/2026225`. Markups and Equations carry `0/0`. The caller supplies the per-folder stamp and FILETIME. The body lists are empty and the material assignment is absent in this profile.

The five definitions and their name objects consume 15 new slots. The intervening `moEnvFolder_c` object aliases slot 67 in P01 and slot 71 in P03. The writer uses the configuration's object map to resolve the caller's reference. The archive advances from byte 1873 to the principal plane definition at byte 2944. Its next slot moves from 132 to 147 in P01 and from 137 to 152 in P03.

Read-only replay across the 14 pinned saves established the range and inherited allocation. The compact JSON map of source-file digest to saved range digest hashes to `d7cd9e7f9f20eb1a8eafbf46e7ccfc4a0dabb51dfc60c6b399e19a6264c8d61f`. The hosted verifier compares the generated prefix through the Material folder with the saved bytes and the complete class and object maps. [Hosted verification entry](VerifyResolvedFolders.py)
