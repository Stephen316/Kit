<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Definition journal attachment and notebook boundary

The `uoJournal_c` attachment occupies 65 bytes in the measured generation-19000 definitions. The surrounding `uoNotebookMgr_c` finishes 16 bytes later, leaving 199 bytes in `Contents/Definition`. The generation-18000 emitter in [Definition.py](../../../src/convert/adapters/solidworks/container/Definition.py) produces the same 81-byte span followed by 195 bytes. The older [Definition field map](../records/Definition.md#41-the-generation-rule) attributed the final scalar block to the attachment. The loader establishes separate attachment, notebook, and outer Definition boundaries.

## Loader evidence

The checked modules came from installed SOLIDWORKS 2026 `34.4.1.1011`. Addresses are preferred virtual addresses. The static lookup used Microsoft RTTI complete-object locators and archive virtual slot 5. PE import names identify the primitive operations. The REA CLI had no configured native analysis provider, so bounded instruction reads used iced-x86 1.21.0 against the installed modules.

| Module and SHA-256                                                              | Address and observation                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `slduiu.dll` `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6` | `uoJournal_c` vtable `0x4a806da8`, slot 5 thunk `0x4a02e590` → serializer `0x4a02e4f0`. Both branches serialize `this+0x08` as `CString`, `this+0x10` as `su_CTime`, and `this+0x18` as a Windows `long`. The member calls end at `0x4a02e549` when storing and `0x4a02e569` when loading.                                                                                                                                                             |
| `swccu.dll` `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49`  | `su_CTime` operators `0x31a5bc60` and `0x31a5bcb0` use a four-byte archive word. The load path recognizes `0xffffffff` as the `-1` sentinel. The store path passes the low DWORD to `0x31a44880`.                                                                                                                                                                                                                                                      |
| `slduiu.dll` `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6` | `uoNotebookMgr_c` slot 5 procedure `0x4a02e6f0` dispatches the journal pointer store at `0x4a02e80b` and load at `0x4a02e8eb`. The procedure continues with list, signed `long`, and virtual calls after the attachment. Its load branches check archive versions against `0x0a2b` at `0x4a02e95a` and `0x23a0` at `0x4a02e9a3`. These checks establish version-aware surrounding logic. They do not identify the four-byte difference observed below. |

The 2025 `33.0.0.5050` `slduiu.dll` (`d36f36b032ca0fa816f599e0bda685976b5ced5bdcf0ff60558860926f70d286`) agrees on the attachment layout. Its slot 5 thunk `0x492e58f0` jumps to `0x492e5850`, which calls the same three typed archive primitives in the same order.

The `uoNotebookMgr_c` constructor calls `0x4a032430`, which initializes both persisted `long` members (`this+0x28` at `0x4a032441` and `this+0x38` at `0x4a032448`) to 1. The same helper constructs a `suObList` for `this+0x30` at `0x4a0324f0` and `0x4a0324f7`. This resolves the virtual serializer call through that member at `0x4a02e8a4` as the third of four list serializers. The store sequence after the attachment is list, first `long`, list, second `long`, list, list. It runs from `0x4a02e85a` through `0x4a02e8ae`. On this empty-list path each list occupies a two-byte zero count. The `suObList::Serialize` export in `sldmfcu.dll` at `0x3c8dd4d0` (SHA-256 `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6`) forwards to `su_CObList::Serialize` in `swccu.dll` at `0x31a56530`.

## Discovery observations

Check the native file size and SHA-256 against the [P01 receipt](../../automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json), [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json), and [P04 receipt](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json) before opening the archives. Select files with `_MO_VERSION_19000/Biography`, open `Contents/Definition`, and locate the unique schema-0 `uoJournal_c` class definition for this corpus inspection. `ReadJournal` in [JournalAttach.py](JournalAttach.py) validates the definition at the supplied position. `ReadNotebook` in [Notebook.py](Notebook.py) reads the attachment and the default list and state sequence. `EncodeNotebook` accepts the typed attachment fields and emits the default notebook span for the first archive occurrence. A full writer still needs shared archive allocation and the outer Definition grammar.

| Corpus                            | Receipt-matching files | Attachment and notebook rebuilt exactly | Outer Definition remainder | Byte at attachment start +94 |
| --------------------------------- | ---------------------: | --------------------------------------: | -------------------------: | ---------------------------- |
| P01                               |                      6 |                            81 in 6 of 6 |                        199 | `5` in 2, `7` in 4           |
| P03                               |                      8 |                            81 in 8 of 8 |                        199 | `5` in 3, `6` in 5           |
| P04                               |                     11 |                          81 in 11 of 11 |                        199 | `5` in 3, `6` in 8           |
| Generation-18000 `EncodeStream()` |                      — |                                      81 |                        195 | `6`                          |

All 25 controls contain `Design Journal.doc`, time word `0`, and state word `0`. The first tag and string consume 57 bytes, then the two archive words consume eight. The measured notebook body after the attachment is `<HiHiHH` with values `(0, 1, 0, 1, 0, 0)`. Reading the [native tail](#part-definition-tail) leaves the same length of earlier remainder as the generation-18000 emitter. The aligned remainder differs at most at offset `+13` after the notebook. That byte is the low byte of the [saved appearance ID counter](#appearance-id-counter).

Two independently supplied attachment values produced notebook spans of 85 and 45 bytes. The inputs were `("A12 independent text", 173, 4)` and `("", -1, 0)`. Their SHA-256 digests were `4661da3e43074e7858a922151c86c40882bbfa60225ae090e1c0342dbaeb2628` and `718eec38fa3be7fbba7e173b26fb3fbce4e65e38a7f28299354af67bd2e6460d`. Both decoded to the supplied values and consumed the complete fragment. This measures the subrecord codec. Native field semantics and application acceptance remain unmeasured for the constructed values.

## Definition stream dispatch

The pinned 2026 `slduiu.dll` above contains a wide `Definition` stream name at `0x4a649c58`. In the routine beginning at `0x49733490`, the path at `0x497342bd` opens that stream, obtains its `su_CArchive` through the imported `suFileStorage::getArchive`, installs the document's `ModelContext`, and dispatches the document serializer at vtable offset `0x1008` (`0x49734358`). The primary `uiModelDoc_c` RTTI locator at `0x4a91b708` gives table `0x4a652b90`. Slot 513 points to the exported `uiModelDoc_c::Serialize(su_CArchive&)` at `0x49710220`. For the part subclass, the same slot selects the override described below.

The same build's `sldmodu.dll` (SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`) also uses a narrow `Definition` key at `0x4d257ad8`. That key is passed through `su_DBKey`; the object written with it uses the exported `moSketchBlockDef_c` runtime class at `0x4db02630`. This is a separate sketch-block serializer.

## Appearance ID counter

The `uiModelDoc_c` constructor calls the notebook constructor at `0x49758a91`, stores the result in `this+0xfd8` at `0x49758a9b`, and the notebook constructor installs the `uoNotebookMgr_c` vtable `0x4a806ee8`. The document store and load paths call slot 5 of that same member at `0x49710995` and `0x49712532`. After the notebook returns, the store path writes these fields before calling `PWMaterialManager_c::save` at `0x49710ae3`.

| Offset from notebook end | Saved field | Store call |
| --- | --- | --- |
| +0 | Windows signed `long` from document member `+0x1000` | `0x497109a1` |
| +4 | Byte from environment Boolean key `0x7a` | `0x497109ca` |
| +5 | Byte from document member `+0x1014` | `0x497109da` |
| +6 | Empty string array count | `0x49710a77` |
| +8 | Empty word array count | `0x49710a84` |
| +10 | Unsigned short from document member `+0x7b8` | `0x49710ab8` |
| +12 | Byte indicating the presence of the material manager at document member `+0x1110` | `0x49710ace` |

Both empty arrays use two-byte counts. The word array in `swccu.dll` calls `su_CArchive::WriteCount` at `0x31a4e50f`. The binary string array route at `0x31a476f0` forwards through MFC ordinal 12836. In installed `mfc140u.dll` version `14.51.36247.0` (SHA-256 `fc5848eb58982e193cdfe73f1f26cd04fce4e196f717f42b89ae27315cd52f6f`), that routine calls the count writer at `0x1801d5502`. Counts below `0xffff` consume a two-byte word.

The material manager's binary `su_CObject::Serialize` base call consumes no bytes. Its store calls at `0x4c204871` and `0x4c20487d` emit Windows signed `long` words from manager members `+0x08` and `+0x0c`. The load calls at `0x4c202070` and `0x4c20207d` restore them to the same offsets. Those words hold the low and high halves of the 64-bit value that the exported `PWMaterialManager_c::getNewApperanceID` at `0x4c1fd340` returns and increments. The manager constructor initializes that 64-bit value to 1 at `0x4c1eee0e`.

All 25 receipt-matching generation-19000 files at `466dcb172dfa3803463e07ccde963ba01671d200` agree with the little-endian field sequence `<iBB3HBiiH>` from the `ReadNotebook` return. The values were `(0, 0, 1, 0, 0, 0, 1, low, 0, 0)`. The final zero is the [material-object list count](#empty-material-manager-list). Only the low word at `+13` varies. In these saves it has the distribution in the table above. The constructor establishes the fresh counter state. Each completed save retains the counter after its own appearance allocations.

## Empty material manager list

After the two counter words, `PWMaterialManager_c::save` constructs a temporary `suObList(10)` at `0x4c20488d`. Its base constructor in `swccu.dll` initializes the count and head to zero at `0x31a55e56` and `0x31a55e61`. The manager constructor clears members `+0x18` and `+0x28` at `0x4c1eee23` and `0x4c1eee2e`. With `+0x28` null, the store branch at `0x4c2048a4` goes directly to list serialization. The populated branch appends a candidate at `0x4c204934` only when its pointer member `+0x2f0` is nonnull.

The call at `0x4c20494b` reaches `suObList::Serialize` and then `su_CObList::Serialize`. The binary store path calls `su_CArchive::WriteCount` at `0x31a56662`. A count of zero uses one unsigned 16-bit word and the null head skips object serialization. The manager then clears and destroys the temporary list and returns. Its restore path at `0x4c20209c` reads the same list and goes directly to cleanup on the null-head branch at `0x4c2020aa`.

In all 25 receipt-pinned P01, P03 and P04 files, the two counter words end at notebook end `+21` and the zero list count ends at `+23`. The document then writes its own `CString` member `+0x1138` at `0x49710af3`. The document constructor initializes that member at `0x49758312`. Reading the next archive string directly at `+23` returns the empty Unicode string and advances to `+27` in every file. These observations establish the empty material manager's exact return boundary. Populated material records still need separate evidence.

## Document rendering options

After the string at notebook end `+23`, the same `uiModelDoc_c::Serialize` store branch emits the following document members. The constructor instantiates the two `suObList` members at `0x49758348` and `0x497581c0`, the strings at `0x49758335` and `0x49758320`, and the two string arrays at `0x497581ce` and `0x497581dc`.

| Offset from notebook end | Member and archive value in all 25 saves | Store call |
| --- | --- | --- |
| +27 | Empty `suObList` at `+0x1158`, two-byte count | `0x49710b06` |
| +29 | Empty Unicode `CString` at `+0x1150`, four bytes | `0x49710b13` |
| +33 | Empty `suObList` at `+0x0f40`, two-byte count | `0x49710b26` |
| +35 | Empty Unicode `CString` at `+0x1140`, four bytes | `0x49710b33` |
| +39 | Two empty `su_CStringArray` members at `+0x0f88` and `+0x0fb0`, two bytes each | `0x49710b43`, `0x49710b53` |
| +43 | Six zero signed `long` words from `+0x1348`, `+0x1350`, `+0x134c`, `+0x1354`, `+0x0a78`, `+0x1358` in order | `0x49710b62` through `0x49710bad` |

The document constructor initializes those six scalar members at `0x49758fa1`, `0x49758fa8`, `0x49757d07` and `0x497584ca`. It calls the exported `PVDocSpecificOptionsData_c` constructor at `0x4a315c30` and retains the result in document member `+0x1370`. The store call at `0x49710bbd` and modern load call at `0x4971319c` pass that member to its exported serializer at `0x4a316280`. The serializer's modern load route reads the last five words under the version checks at `0x4a3163ee` (at least `0x147f`) and `0x4a316430` (at least `0x1825`).

The rendering-options block uses little-endian `<6iI5i>`, with line color the single unsigned `long`. Direct exported getters and setters establish the field identities below. The default constructor initializes these values independently of the captures.

| Member in wire order | Native field | Saved value |
| --- | --- | --- |
| `+0x08` | Flags with Bloom and direct caustics at bits 0 and 1 | 0 |
| `+0x0c` | Bloom threshold | 100 |
| `+0x10` | Bloom radius | 5 |
| `+0x2c` | Contour or cartoon rendering active | 0 |
| `+0x18` | Contour only | 0 |
| `+0x1c` | Line thickness | 1 |
| `+0x20` | Line color | 0 |
| `+0x24` | Monte Carlo enabled | 0 |
| `+0x28` | Ambient occlusion output | 0 |
| `+0x14` | Has contour | 1 |
| `+0x30` | Has cartoon edges | 0 |
| `+0x34` | Has cartoon shading | 0 |

Reading the six document members and six scalar words from notebook end `+27` reaches `+67` in all 25 receipt-pinned files. Reading the twelve rendering options consumes exactly 48 more bytes and reaches `+115`. At that boundary the next document `long`, member `+0x1388` written at `0x49710bfe`, is 1 in every capture. These measurements cover empty lists, empty strings and the constructor's rendering defaults.

## Part Definition tail

In installed build `34.4.1.1011`, `sldprtu.dll` (SHA-256 `cb1e260f8411a39dc44f4d8a6255ea585c7a5e60b223d0e69d3f51a258ee96de`) has the primary `uiPartDoc_c` RTTI locator at `0x334e5cd8` and vtable at `0x334af0f0`. Slot 513 selects `0x333bb1b0`. The override calls the imported `uiModelDoc_c::Serialize` at `0x333bb1c8`. On the store branch it then writes `this+0x1688` with the archive double operator at `0x333bb31d` and returns. The part load branch reads the double at `0x333bb2f5` on the supported modern path.

The base serializer's last store operation starts at the version check `0x49710dfb`. For archive versions at least `0x46c2` (18114), `0x49710e17` writes a Windows signed `long` count derived from the difference between the vector end and begin pointers, divided by eight. The base load path checks the same version at `0x49713720` and reads the count with the signed `long` operator at `0x4971373a`. Nonempty vectors visit the archive object write and read calls at `0x4943d3ce` and `0x4943d38b`. Their shared class helper at `0x4943d440` returns the `uiVariabilityTableViewData_c` runtime class descriptor at `0x4aefd010` with schema `0x80000001`. The model document constructor initializes the vector's begin, end and capacity pointers at offsets `0x11a0`, `0x11a8` and `0x11b0` to zero at `0x4975834f`–`0x4975835d`.

The 6 P01, 8 P03 and 11 P04 receipt-pinned files at `466dcb172dfa3803463e07ccde963ba01671d200` each read as little-endian `<id>` at the final twelve bytes of `Contents/Definition`. Each stores the count `0` at notebook end `+187` and the part double `1000.0` immediately after it. This accounts for the four extra bytes relative to the generation-18000 emitter. Other outer Definition fields, nonempty variability entries, and native acceptance of generated generation-19000 Definitions remain outside this evidence.
