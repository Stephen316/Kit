<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Definition journal attachment and notebook boundary

The `uoJournal_c` attachment occupies 65 bytes in the measured generation-19000 definitions. The next 215 bytes belong to the enclosing serialization path. The generation-18000 emitter in [Definition.py](../../../src/convert/adapters/solidworks/container/Definition.py) produces the same attachment followed by 211 bytes. The older [Definition field map](../records/Definition.md#41-the-generation-rule) attributed the final scalar block to the attachment. The loader establishes a shorter ownership boundary.

## Loader evidence

The checked modules came from installed SOLIDWORKS 2026 `34.4.1.1011`. Addresses are preferred virtual addresses. The static lookup used Microsoft RTTI complete-object locators and archive virtual slot 5. PE import names identify the primitive operations. The REA CLI had no configured native analysis provider, so bounded instruction reads used iced-x86 1.21.0 against the installed modules.

| Module and SHA-256                                                              | Address and observation                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `slduiu.dll` `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6` | `uoJournal_c` vtable `0x4a806da8`, slot 5 thunk `0x4a02e590` → serializer `0x4a02e4f0`. Both branches serialize `this+0x08` as `CString`, `this+0x10` as `su_CTime`, and `this+0x18` as a Windows `long`. The member calls end at `0x4a02e549` when storing and `0x4a02e569` when loading.                                                                                                                                                             |
| `swccu.dll` `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49`  | `su_CTime` operators `0x31a5bc60` and `0x31a5bcb0` use a four-byte archive word. The load path recognizes `0xffffffff` as the `-1` sentinel. The store path passes the low DWORD to `0x31a44880`.                                                                                                                                                                                                                                                      |
| `slduiu.dll` `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6` | `uoNotebookMgr_c` slot 5 procedure `0x4a02e6f0` dispatches the journal pointer store at `0x4a02e80b` and load at `0x4a02e8eb`. The procedure continues with list, signed `long`, and virtual calls after the attachment. Its load branches check archive versions against `0x0a2b` at `0x4a02e95a` and `0x23a0` at `0x4a02e9a3`. These checks establish version-aware surrounding logic. They do not identify the four-byte difference observed below. |

The 2025 `33.0.0.5050` `slduiu.dll` (`d36f36b032ca0fa816f599e0bda685976b5ced5bdcf0ff60558860926f70d286`) agrees on the attachment layout. Its slot 5 thunk `0x492e58f0` jumps to `0x492e5850`, which calls the same three typed archive primitives in the same order.

## Discovery observations

Check the native file size and SHA-256 against the [P01 receipts](../../automation/PairedCaptures/P01), [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json), and [P04 receipts](../../automation/PairedCaptures/P04) before opening the archives. Select files with `_MO_VERSION_19000/Biography`, open `Contents/Definition`, and locate the unique schema-0 `uoJournal_c` class definition for this corpus inspection. `ReadJournal` in [JournalAttach.py](JournalAttach.py) validates the definition at the supplied position. `EncodeJournal` accepts only the typed attachment fields and emits the first archive occurrence. A full writer still needs shared archive allocation and the enclosing notebook grammar.

| Corpus                            | Receipt-matching files | Attachment bytes rebuilt exactly | Notebook remainder | Byte at attachment start +94 |
| --------------------------------- | ---------------------: | -------------------------------: | -----------------: | ---------------------------- |
| P01                               |                      6 |                     65 in 6 of 6 |                215 | `5` in 2, `7` in 4           |
| P03                               |                      8 |                     65 in 8 of 8 |                215 | `5` in 3, `6` in 5           |
| P04                               |                     11 |                   65 in 11 of 11 |                215 | `5` in 3, `6` in 8           |
| Generation-18000 `EncodeStream()` |                      — |                               65 |                211 | `6`                          |

All 25 controls contain `Design Journal.doc`, time word `0`, and state word `0`. The first tag and string consume 57 bytes, then the two archive words consume eight. Each generation-19000 notebook remainder can be aligned to the existing generation-18000 emitter's remainder with a four-byte zero span immediately before the final `f64` in that alignment. The aligned remainder differs at most at positions `+2` and `+29` after the attachment. Consecutive zero bytes permit other alignment positions. The field width, meaning, and placement of the extra span remain unresolved. The `+29` byte varies across independent baseline saves and is unsuitable as a generation constant.

Two independently supplied attachment values produced 69 and 29 bytes. The inputs were `("A12 independent text", 173, 4)` and `("", -1, 0)`. Their SHA-256 digests were `b0a2595fcc794ed1fff90f4c99edc6fa39f341c06aefb976812212a0bd553ab3` and `3e8ea595f8d8235eed609bd9701336937405481adea1be459f25fce71ad28979`. Both decoded to the supplied values and consumed the complete fragment. This measures the subrecord codec. Native field semantics and application acceptance remain unmeasured for the constructed values.

The next notebook probe starts at the parent call sites and assigns the list and virtual-call reads to concrete archive positions. That check must establish the width and owner of the four-byte difference before any generation-19000 Definition stream is emitted.
