<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Configuration manager terminal records

The two terminal `suObList` records in the 25 generation-19000 discovery saves are empty. The feature stamps and remaining fields belong to the enclosing configuration manager. Typed archive reads account for every byte from the first list definition to EOF. [Visual record and corpus provenance](CmgrVisual.md)

## External file and referenced configuration

The same terminal walk extends backward to the manager's `moExtObject_c` pointer at `0x4c21cb40`. In installed `sldarchiveu.dll` SHA-256 `fce17ce9f2b79e188ee0c20ca51cd36cd246d92bf2d35c2010a03f4bb5c304c6`, the object's archive slot `0x31a0d8e0` serializes a shared file inline via the call at `0x31a0d95c`. The `moSharedFileDef_c` serializer at `0x31a0e940` writes two `moCStringHandle_c` pointers at `0x31a0ea3f` and `0x31a0ea4d`. The string handle stores exactly one CString at `0x3c7d799f` in `sldmfcu.dll`. The first handle defines the class and carries the path. The second reuses the class to allocate a distinct object for the title.

All eight small modern saves have empty paths and generated part titles. The other 17 carry the previous baseline-A file's leaf name and matching title. Their paths use 194 archive bytes instead of four, and their titles use 54 bytes instead of 14 or 16. The 230-byte difference between matching size strata within a family comes from those two strings. No capture pathname is needed to construct the empty-path form.

The following fields finish the external object and resume the manager. All rows use the observed modern form. The zero tail values and string widths also agree with the historical control.

| Owner | Fields and measured values after both handles |
| --- | --- |
| Shared file | Four calls at `0x31a0ea5a`, `0x31a0ea67`, `0x31a0eafb` and `0x31a0eb3b` start the suffix with unsigned short `2`, byte zero, a four-byte `su_CTime`, and three successive empty CStrings (ending at `0x31a0ebbb`). `0x31a0ebf3` writes a final zero byte. |
| External object | `0x31a0d9cd` writes the flags byte, observed as 0 with an empty path and 8 with a prior path. `0x31a0da2a` writes a zero `su_CTime`. Calls at `0x31a0dae5`, `0x31a0daf1` and `0x31a0db30` write three zero longs. |
| Referenced configuration | The call at `0x31a0db40` enters the inline reference whose archive slot is `0x31a181b0`. It stores the wide CString `Default` and signed zero index. |
| External object return | `0x31a0db7d`, `0x31a0dc44` and `0x31a0dc7b` write zero long, zero `su_CTime` and zero long. |
| Manager before first list | `0x4c21cb58`, `0x4c21cb68` and `0x4c21cb78` write signed zero, an empty wide CString and a signed zero map count. |

Starting after the title, the external object returns 71 bytes later and the first `suObList` begins 12 bytes after that. This walk reaches the already checked first list in all 25 discovery saves and the historical comparison. Configuration-manager data prior to the external object still needs typed attribution.

## Root and feature stamps

The exact installed SOLIDWORKS 2026 build is `34.4.1.1011`. In `sldmodu.dll` SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`, `moExtObjHelper_c::loadConfigurationMgrFromFile` opens `CMgr`, reads a single manager at `0x4be9139c` and closes the archive. The manager's primary archive slot is `0x4c21c740`. Its calls at `0x4c21cbfa` and `0x4c21cf5b` write the two `suObList` pointers. The class's serializer at `0x3c8dd4d0` in [`sldmfcu.dll`](CmgrVisual.md#version-and-ownership) delegates to `su_CObList::Serialize` at `0x31a56530` in `swccu.dll` SHA-256 `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49`. The `WriteCount` call at `0x31a56662` encodes the empty list in one 16-bit word.

After the first empty list, `0x4c21cd25` writes the signed manager-map count. For each entry `0x4c21cd45` writes the signed feature tree ID, and `0x4c21cd8d` and `0x4c21cd98` write the high and low unsigned stamp words. The three families carry respectively zero entries, one entry with tree ID 34, and two entries with tree IDs 34 and 46. The counts corroborate the [separately resolved atom ownership](ConfigAtoms.md). The following calls store five separate values before the second list tag. `0x4c21cdba` calls the manager's empty keyed-map serializer and `0x4c21cddd`, `0x4c21cee9`, `0x4c21cef8` and `0x4c20ea7b` supply the other fields. In all controls these values are `(0, 0, 1, 0, 0)`, with archive layout `<3iIi`.

The first list uses a schema-1 definition. The second defines another object through the same class. Its compact class word is `0x800e`, `0x8010` or `0x8011` in P01, P03 and P04 respectively. An independent writer needs the allocated class index from the enclosing archive. The observed token values identify the saved occurrences.

## Fields after the second list

| Native store owner or call site | Observed values and width |
| --- | --- |
| Second `su_CObList` count | Empty `u16` |
| `0x4ba11583`, `0x4ba1160b`, `0x4c6e31f6`, `0x4c6e328b` | Four empty `long` map counts |
| `0x4c21cfa4` | Empty signed vector count |
| `0x4c21d00d`, `0x4c21d058` | Empty `su_CStringArray` count (`u16`), then signed zero |
| `0x4c21d092`, `0x4c21d0a1` | Unsigned value 2 and empty plane map count |
| `0x4c23a99b..0x4c23aaaa` | Empty wide CString, three zero `long` members and a four-byte `su_CTime` sentinel `0xffffffff` |
| `0x4c21d1c9`, `0x4c21d43a` | Empty signed map count and signed zero |
| `0x4c21d47f` | Unsigned zero presence field before EOF, for generation 18114 or later |

The last version check is `0x46c2` at `0x4c21d464`. The presence predicate at `0x4b896b60` compares the two map sizes at manager members `+0x8a8` and `+0x8b8` with zero. Every measured modern save takes the empty branch, reaching EOF 68 bytes after the second list's class tag. The historical donor without this field reaches EOF 64 bytes after that tag. Populated data behind the selector needs independent evidence.

The proof checked the same 25 [receipt-pinned saves](CmgrVisual.md#inputs-and-reproduction) and the generation-18000 comparison. Its terminal offsets are reproduced by applying the typed widths from the stream end, checking the exact class definition and class reference, reading the counted entries and reaching EOF again in the forward direction. Offsets below record the observed positions. [Earlier atom links and configuration aliases](CmgrAtoms.md)

| Controls | First list definition offsets | Second list class-reference offsets |
| --- | --- | --- |
| P01 | 1963, 2193 | 2003, 2233 |
| P03 | 2037, 2039, 2267 | 2089, 2091, 2319 |
| P04 | 2127, 2129, 2357 | 2191, 2193, 2421 |
| Generation-18000 comparison | 1839 | 1891 |

The [research terminal writer](CmgrTail.py) takes the enclosing archive's allocator and explicit feature stamps. It allocates both list objects through the shared class map and emits the typed manager fields through EOF. The terminal reader reached EOF for all 25 pinned generation-19000 saves. The six P01, eight P03 and eleven P04 reads allocated the list class and its two objects from starting indices 14, 16 and 17 respectively. The [hosted verification](VerifyCmgrColor.py) checks exact generated bytes in all three observed namespaces. Hosted reconstruction and complete native part acceptance remain open.
