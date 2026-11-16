<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Configuration manager atom links and part return

The generation-19000 part configuration contains a counted linked-atom map. The native map preserves keys even when their pointer values are null. The first supported geometric target, P03, needs one link node with only its feature ID array populated. [Configuration atom ownership](ConfigAtoms.md), [Terminal manager fields](CmgrTail.md)

## Linked-atom map

In the [pinned `sldmodu.dll`](CmgrTail.md#root-and-feature-stamps), the base configuration serializer at `0x4c215630` writes the signed map count at `0x4c21848f`. The loop at `0x4c2184b6..0x4c2184c3` writes each signed atom key and the typed node pointer.

`moLinkedAtomIdNode_c` has archive slot 5 at `0x4b567d50`. It writes the signed atom ID from member `+0x08`. Its calls at `0x4b567e4d` and `0x4b567e59` write two counted DWORD arrays. Each measured array has a compact unsigned 16-bit count. The four map calls at `0x4b567e84`, `0x4b567eb1`, `0x4b567edb` and `0x4b567f05` visit members `+0xf0`, `+0x100`, `+0x110` and `+0x120` in order. Each uses the count, signed key and typed object call at `0x4b56869e`, `0x4b5686ba` and `0x4b5686e3`. Exported `getAllAncestors` and `getAllDescendants` use the third and fourth maps respectively. The exported configuration `getImmediateAncestors` uses the first map.

| Capture family | Root map span | Typed nodes and archive allocations |
| --- | --- | --- |
| P01, 6 saves | 1654–1658 | Empty map. Next object index remains 9. |
| P03, 8 saves | 1662–1724 | Key and atom ID 101. First array contains feature ID 34, second array and four maps empty. Class 9, object 10. Next index is 11. |
| P04, 11 saves | 1678–1798 | Key and atom ID 101 has feature ID 34. Maps 2 and 4 each contain key 102 with a null pointer. Atom 102 has feature ID 46. Maps 1 and 3 each contain key 101 with a null pointer. Both second arrays and other maps empty. Class 9, objects 10 and 11. Next index is 12. |

The store rebuilds its two DWORD arrays before invoking their serializers. At `0x4b567d9c` and `0x4b567dad` it clears the arrays. The loops at `0x4b567dbd..0x4b567df8` and `0x4b567e04..0x4b567e42` read each feature reference's saved data and append its first DWORD. The first array has one owner for the ordinary rectangular boss. The separately checked Config-0 atom and ResolvedFeatures owner agree on that feature ID. A sketch-only configuration has an empty map. [Feature and atom provenance](ConfigAtoms.md#feature-ownership-across-streams)

[`WriteCmgrLinks`](CmgrLinks.py) emits an empty map or one independent atom link from a caller-supplied pair of positive atom and feature IDs. It allocates a schema-1 link node through the caller's compact archive namespace. The second feature array and all four relation maps are empty for this scope. Connected histories and a pre-existing link class require separate encoding. [Coverage and hosted verification](../../../Documentation/Changes/Research/Writers/SolidWorksCmgrAtomLinks.md)

## Base return

The ordinary generation-19000 base return uses the following fields after the linked atom map. All scalar words are signed 32-bit values. The absent envelope pointer is a compact null.

| Field | Constructor or model state | Store |
| --- | --- | --- |
| Optional object presence, zero | The base constructor clears `+0xb88` at `0x4bdc00e7`. | The absence route writes zero at `0x4c218817`. |
| Empty named map count | The constructor at `0x4bdc00da` calls `0x4b797a60`, which clears size at `0x4b797a72`. | The helper reached at `0x4c21888a` writes the map size at `0x4c20ea7b`. |
| Scalar `+0xbd0`, zero | Initialized at `0x4bdc0130`. | `0x4c2188e2` |
| Empty signed pair map count | The constructor call at `0x4bdc00fc` clears the map size at `0x4b2d1e62`. | `0x4c21894d` calls the counted map writer at `0x4c20e6a0`. P04 carries a populated pair `(102,101)`. |
| Configuration mode `+0x4c8`, value 2 | The constructor clears the word at `0x4bdbfc76`. The initialized modern thread reference mode sets bit 1 through `moModel_c::initCThreadRefMgr` at `0x4b584587`. | `0x4c2189a5` |
| Inherited word `+0x4cc`, zero | The base initializer clears it at `0x4bdbea1c`. The new part constructor's base call copies it from the active configuration at `0x4bdbfc84..0x4bdbfc8a`. The bounded profile uses the inherited default. | `0x4c2189ff` |
| Scalar `+0xa80`, zero | Initialized at `0x4bdc001f`. | `0x4c218a59` |
| Absent envelope publisher | The constructor clears `+0xbd8` at `0x4bdc0142`. | The typed `moEnvelopePublisher_c` pointer at `0x4c218ab3` is null. |
| Empty final vector count | Constructor call `0x4bdc0186` creates the empty container at `+0xbf8`. The linked sentinel is initialized at `0x4b277872..0x4b277879`. | `0x4c218e34..0x4c218e9b` gathers its keys and writes their count. |

The ordinary standalone part has archive condition 1 clear and skips the conditional word at `0x4c218dd0`. The base returns at bytes 1692, 1758 and 1840 for P01, P03 and P04.

In installed `sldprtu.dll` SHA-256 `cb1e260f8411a39dc44f4d8a6255ea585c7a5e60b223d0e69d3f51a258ee96de`, the eligible opened-model branch at `0x3339f2a4..0x3339f2ae` calls exported `initNewCThreadArch`. It checks the model state and the new-part option at `0x4b5845b0..0x4b5845f3` and delegates to `initCThreadRefMgr`. The latter sets the mode bit by configuration, including sketch-only controls. The [base-return constructor](CmgrBaseEnd.py) requires that mode as a caller input. Alternate mode, inherited settings and populated collections need separate construction evidence.

## Inline part configuration object

`moPartConfiguration_c::Serialize` calls slot 5 of member `+0x4d0` at `0x4c226637`. The base constructor creates that member at `0x4bdbde93` and stores it at `0x4bdbdea0`. Its constructor at `0x4bdc1510` installs the `moPartConfigObject_c` vtable `0x4cec5f88`. Slot 5 at `0x4c225080` writes signed members `+0x0c` and `+0x08` in that order. Their initialized and saved values are `1` and `-1`. Those words begin the part object. They follow the base configuration's zero vector count.

| Order | Archive fields | Native store calls |
| --- | --- | --- |
| 1 | Two signed words, `1` and `-1`, and null `moReferencedConfiguration_c` and `moVisualProperties_c` pointers | `0x4c2250d1`, `0x4c2250dd`, `0x4c2250ed`, `0x4c2250fd` |
| 2 | Seven empty inline `suObList` counts in member order `+0x10`, `+0x60`, `+0x100`, `+0x80`, `+0x68`, `+0x58`, `+0x78` | `0x4c225380`, `0x4c22548d`, `0x4c225565`, `0x4c225646`, `0x4c22581a`, `0x4c2258ff`, `0x4c2259f3` |
| 3 | Five unsigned 16-bit absence flags for list members `+0xc8`, `+0xd0`, `+0xe0`, `+0xe8`, `+0xf0` | `0x4c225ac0`, `0x4c225aec`, `0x4c225c47`, `0x4c225d16`, `0x4c225de5` |
| 4 | Empty inline `suObList` for member `+0x70`, two signed zeros from `+0xd8` and `+0xf8`, then the unsigned 16-bit absence flag for `+0x98` | `0x4c225ed0`, `0x4c225f6f`, `0x4c225fc4`, `0x4c226025` |
| 5 | Null object, null typed `suObList`, null object | `0x4c2260d1`, `0x4c226165`, `0x4c2261b4` |

The constructor sets the absent members to zero and constructs the first inline list at `0x4bdc1545`. The store constructs empty temporary lists at the other inline calls when their members are absent. Each invokes [the compact count serializer](CmgrTail.md#root-and-feature-stamps) directly. The final object field is gated on generation at least `0x4973` (18803) at `0x4c226196`. The generation-19000 object is 54 bytes with the measured empty members.

The containing part then writes double `-1.0`, a null `gcXhatch_c`, a signed zero and an empty per-body appearance vector count at `0x4c22672d..0x4c226894`. Condition 1 clear admits both the `moExplPrtId_c` pointer and `suObArray` pointer at `0x4c226a38` and `0x4c226a47`. Both are null. This adds 22 bytes before the frozen checksum. A typed walk verified all 25 receipt-pinned controls with no additional archive allocations.

| Capture family | Inline object span | Part suffix ends at frozen checksum |
| --- | --- | --- |
| P01, 6 saves | 1692–1746 | 1768 |
| P03, 8 saves | 1758–1812 | 1834 |
| P04, 11 saves | 1840–1894 | 1916 |

## Part return and manager aliases

In `moPartConfiguration_c::Serialize` the call at `0x4c226bf7` computes the frozen-feature checksum. The field at `0x4c226c08` is unsigned and is zero in all 25. The following signed value and `su_CMapPtrToPtr` count at `0x4c226c3b..0x4c226c4b` are `-1` and the saved atom count. The loop at `0x4c226c91..0x4c226cae` emits each enumerated key and value as two longs. P01 has no entries. P03 has one entry `(101,0)`. P04 has both entries with value zero. Eight P04 files have order 101, 102 and three have order 102, 101. This is native map enumeration order. The historical [encoder](../../../src/convert/adapters/solidworks/Container/Cmgr.py) calls the analogous field a reverse table.

The four fields after this map are `(0,0,-1,-1)` from `0x4c226cc5`, `0x4c226cd4`, `0x4c226ce4` and `0x4c226cf4`. The first value is an empty map count. The two zero words at `0x4c226f29` and `0x4c226f34` are the high and low words of the part's final entry count. The checksum-to-return spans are 1768–1804, 1834–1878 and 1916–1968.

The enclosing manager writes its second configuration pointer at `0x4c21c890` as an alias to the first part object, slot 4. `0x4c21c89f` writes the next configuration ID from manager member `+0x40c`. The first active part constructor calls `0x4b895b10` at `0x4bdc02ab`, which takes ID 0 and increments the next value to 1. This saved word is independent of list length.

`0x4c23f490` filters the configuration list, including the ordinary configuration because its `+0xbe0` member starts at zero at `0x4bdc0149`. The list serializer reached at `0x4c23f4e8` writes a compact count 1 and the same object reference. `0x4c21cb03` writes the signed count of the preceding collected external-object list, one in this profile. These 14 bytes lead to the [first external object definition](CmgrTail.md#external-file-and-referenced-configuration) at offsets 1818, 1892 and 1982 respectively. All 25 modern and the old comparator preserve these aliases. [Alias construction and verification](../../../Documentation/Changes/Research/Writers/SolidWorksCmgrReturns.md)

The [feature and mass property records](CmgrMiddle.md) establish the continuous typed walk from the visual return to this linked-atom map. Encoding should derive the recorded boundaries from each typed body and shared archive namespace.

The [research part codec](CmgrPartEnd.py) reads and constructs the ordinary generation-19000 part suffix with an explicit archive condition and ordered atom IDs. The [archive verifier](VerifyCmgrPart.py) retains the opening class and object map, resumes at the independently recorded linked-atom starts in the table above and derives the part start through the typed linked nodes and base return. Both manager aliases resolve to the same saved part object before the next external object definition. [Coverage and limits](../../../Documentation/Changes/Research/Writers/SolidWorksCmgrPartReturn.md)
