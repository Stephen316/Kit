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

All 25 controls contain `Design Journal.doc`, time word `0`, and state word `0`. The first tag and string consume 57 bytes, then the two archive words consume eight. The measured notebook body after the attachment is `<HiHiHH` with values `(0, 1, 0, 1, 0, 0)`. Each generation-19000 remainder after the notebook can be aligned to the generation-18000 emitter's remainder with a four-byte zero span immediately before the final `f64` in that alignment. The aligned remainder differs at most at offset `+13` after the notebook. Consecutive zero bytes permit other alignment positions. The field width, meaning, and placement of the extra span remain unresolved. The `+13` byte varies across independent baseline saves and is unsuitable as a generation constant.

Two independently supplied attachment values produced notebook spans of 85 and 45 bytes. The inputs were `("A12 independent text", 173, 4)` and `("", -1, 0)`. Their SHA-256 digests were `4661da3e43074e7858a922151c86c40882bbfa60225ae090e1c0342dbaeb2628` and `718eec38fa3be7fbba7e173b26fb3fbce4e65e38a7f28299354af67bd2e6460d`. Both decoded to the supplied values and consumed the complete fragment. This measures the subrecord codec. Native field semantics and application acceptance remain unmeasured for the constructed values.

The next Definition probe starts with the caller that resumes after the notebook. Recover the width, owner, and initializer of the remaining four-byte difference there before emitting a generation-19000 Definition stream.

## Definition stream dispatch

The pinned 2026 `slduiu.dll` above contains a wide `Definition` stream name at `0x4a649c58`. In the routine beginning at `0x49733490`, the path at `0x497342bd` opens that stream, obtains its `su_CArchive` through the imported `suFileStorage::getArchive`, installs the document's `ModelContext`, and dispatches the document serializer at vtable offset `0x1008` (`0x49734358`). The primary `uiModelDoc_c` RTTI locator at `0x4a91b708` gives table `0x4a652b90`. Slot 513 points to the exported `uiModelDoc_c::Serialize(su_CArchive&)` at `0x49710220`. This pins a stream-to-document entry for the next call trace. The inner call chain from that entry through the notebook and the generation-19000 tail remains open.

The same build's `sldmodu.dll` (SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`) also uses a narrow `Definition` key at `0x4d257ad8`. That key is passed through `su_DBKey`; the object written with it uses the exported `moSketchBlockDef_c` runtime class at `0x4db02630`. This is a separate sketch-block serializer.
