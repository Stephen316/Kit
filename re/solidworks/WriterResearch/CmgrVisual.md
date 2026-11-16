<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Configuration manager visual properties

The generation-18000 [configuration manager emitter](../../../src/convert/adapters/solidworks/container/Cmgr.py) includes a 104-byte compatibility record that generation 19000 omits. The record is inside the configuration's visual properties. A separate optional visual property is present in all 25 measured generation-19000 saves. It adds 300 bytes. The installed serializer and saved archives establish both changes.

## Version and ownership

The evidence uses installed SOLIDWORKS 2026 `34.4.1.1011`, `sldmfcu.dll` SHA-256 `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6` with preferred base `0x3c730000`. The exported `moVisualProperties_c::Serialize` at `0x3c930ca0` agrees with the RTTI vtable's archive slot 5. The signed integer, unsigned integer, unsigned long, float, double and wide CString operations come from the `su_CArchive` imports. The stored integer and float primitives are little-endian.

- `getMatProps` at `0x3c75f9b0` exposes the outer object's `+0x20` member as `uoMaterialProperties`. The call at `0x3c930d19` serializes it inline at `0x3c861a60`. Its accessor `getRVAppProps` at `0x3c75f810` exposes `+0x90` as `uoRVAppearanceProperties`. The presence word at `0x3c861c29` precedes the inline call at `0x3c861c39` to `0x3c8a7d40`.
- The `uoRVAppearanceProperties` serializer writes the `+0x98` float at `0x3c8a80f0`. The following checks at `0x3c8a80ff` and `0x3c8a8113` include the compatibility record for archive versions `13128..18105` inclusive. The temporary initializer at `0x3c8a5b50` constructs three empty CStrings and zeros every serialized numeric member. The calls at `0x3c8a812f..0x3c8a827f` write the three strings, 17 floats, two unsigned integers and four signed integers, in that order. The measured generation-18000 record contains four bytes per empty wide CString and 92 numeric bytes.
- After that guarded branch the enclosing `uoMaterialProperties` writes its `+0xb8` CString at `0x3c861c52`, a presence word for `+0x98`, and the counted collection at `0x3c897c80`. The presence word and collection count are both zero in the measured forms.
- The outer `moVisualProperties_c` serializer writes the `+0x88` presence word at `0x3c930dba` for archive version `16137` or later. Exported `getDSPBRprops` at `0x3c773a00` identifies that pointer as `uoDSPBRProperties_c`. The outer default constructor clears it at `0x3c9307ef`. The observed modern saves carry a populated object. Its acquisition path and independently constructible values remain open.

## Saved spans

All four tested class definitions use schema 1, with `moConfigurationMgr_c`, `moPartConfiguration_c`, `moNodeName_c` and `moVisualProperties_c` starting at offsets `0`, `165`, `192` and `252` in these saves. Read the visual body as three unsigned longs followed by the material record. Advance through the typed fields and the encoded CString lengths to reach the version check. The table records the resulting offsets in these files. The writer's existing reserved byte groups combine parts of several native fields.

| Boundary | Generation 18000 | Generation 19000 |
| --- | --- | --- |
| Visual body start | 278 | 278 |
| Compatibility branch after the `+0x98` float | 743, emits through 847 | 743, omitted |
| Enclosing `+0xb8` CString | 847 | 743 |
| Inline material record returns | 859 | 755 |
| Outer DSPBR presence word | 895, zero | 791, one |
| DSPBR body | Absent | 795–1095 |
| Visual record returns | 899 | 1095 |

The optional record's store procedure at `0x3c78af90` writes 26 floats, one signed integer, 18 floats, one signed integer, two floats, five CStrings and one float. At `0x3c78b41e`, archive version `18101` or later adds two CStrings, one signed integer, six floats and two CStrings. At `0x3c78b508`, archive version `18802` or later adds two floats and three CStrings. All 25 records contain 55 floats, three integers and 12 CStrings. The only nonempty strings are `basic` and `2025x`. The 300-byte DSPBR body has SHA-256 `3b77a4c24f8a5953b871c3b9fa7b0df54008ddf61bacb11baffc7c78fba937a9` in every measured save. Its end leaves later configuration-manager members outside this proof.

## Inputs and reproduction

Use [`capture_inputs`](../../automation/SolidworksCensusInputs.py) at capture revision `466dcb172dfa3803463e07ccde963ba01671d200`. It checks the three discovery receipts, independent reopen measurements and exact native file identities for six P01, eight P03 and eleven P04 saves. Read `Contents/CMgr` through [`SldprtArchive`](../../../src/convert/adapters/solidworks/container/Container.py), checking generation through `ContainerMo`. The old comparison is the [1,957-byte CMgr donor](../Fixtures/donors/boss1_front_rect_blind/container/Contents__CMgr.bin) in revision `1dcffae99f4bbf2a70f1c47fe24cee004b5f0ab2`, SHA-256 `3e2894581c3f5b25f523146a01e0f394d9c027f22c6a6a343000d64078fe6cd5`. Use the schema-1 visual tag, the `su_CArchive` operation sequence above and [`FieldCursor`](../../../src/convert/adapters/solidworks/container/ArchiveCursor.py) to compare the boundaries. The store calls can be inspected with `dumpbin /DISASM:NOBYTES /RANGE:<start>,<end>` against the pinned DLL. The archived values verify the sequence and cannot supply default values for an independent writer.
