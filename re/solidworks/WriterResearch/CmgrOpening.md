<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of the
PolyForm Strict License 1.0.0 and voids all licenses granted to you
under it immediately and permanently.
-->

# Configuration manager opening

The standalone manager and its first part configuration share a lightweight concept header. The manager then writes its inherited feature fields to the first part pointer. The part concept header adds the allocated `Default` name and leads to the [visual properties](CmgrVisual.md). All 25 generation-19000 [receipt-pinned controls](CmgrVisual.md#inputs-and-reproduction) agree on the class and object allocations below.

## Native ownership

The initial manager definition has schema 1. The archive slot at `0x4c21c740` in the [pinned `sldmodu.dll`](CmgrTail.md#root-and-feature-stamps) calls `moFeature_c::Serialize` at `0x4c21c7d3` for the modern version. The nested part enters the same inherited serializer at `0x4c2156c5`. Both use the `moConcept_c::SerializeLWData` hook at `0x4c1783a0`, which delegates to `moNode_c::SerializeLWData` at `0x4c1783c3`.

The node serializer's call at `0x4c178b11` writes the typed `moNodeName_c` pointer from member `+0x18`. Its class descriptor is `0x4daebb00`. Exported `moNodeName_c::Serialize` at `0x4c177890` writes one wide CString from `+0x08` and returns. The manager pointer is null and the part pointer materializes a name with value `Default`.

| Node owner | Typed fields after the name pointer or named body |
| --- | --- |
| Manager, byte 28 | Signed `+0x0c` 0, unsigned `+0x28` `0x40000000`, signed node ID `+0x08` −1, unsigned `+0x2c` 0, empty wide CString from `+0x20`. |
| Part, byte 228 | Signed `+0x0c` 0, unsigned `+0x28` `0x40000000`, signed node ID `+0x08` 0, unsigned `+0x2c` 512, empty wide CString from `+0x20`. |

The scalar store calls are `0x4c178b1c`, `0x4c178b38`, `0x4c178b47` and `0x4c178d6a`. The last unsigned field is gated on version at least `0x143b`. The wide CString store at `0x4c178df6` is gated on version at least `0x23ce`. The flags write temporarily clears bit `0x1000` through `moNode_c::clearFlag` before restoring the member. This source sequence explains the first eight bytes often read as `2.0` by the historical encoder. They are a signed integer followed by unsigned flags.

The native `moNode_c` constructor at `0x4c03a5c0` initializes ID `-1`, absent name, empty secondary text and flags `0x40000000`. The bit is exposed by `SetNeedsIDToBeSet` at `0x4c03b510`. The part constructor route through `0x4bdc02ab` takes and increments the manager's configuration ID counter `+0x40c`. The first part's assigned ID is 0 in the controls. The constructor evidence covers the identified defaults and source for the assigned ID. The saved state supplying member `+0x0c` and the part-specific `+0x2c` value remain bounded to the measured profile.

After the node header, the concept serializer writes a signed presence value at `0x4c178414` for its optional `+0x68` object. It is zero for both owners. The next operation at `0x4c178455` writes the typed visual-properties pointer from `+0x78`. The manager has a null at byte 52. The part has the class definition at byte 252.

## Inherited fields and first allocation

The 111-byte manager interval at 54–165 has the same ordered `moFeature_c` fields as the [part interval after its visual record](CmgrMiddle.md#inherited-feature). The constructor at `0x4bb37828` writes update stamp 101. The calls at `0x4bb37883` and `0x4bb37895` supply service pack and sub-service-pack bytes from `moVersionManager_c`. The calls at `0x4bb37924` and `0x4bb37936` supply the Parasolid session behavior version and full creation date code. The current profile observes service pack 4, sub-service-pack 0, session behavior 370108 and creation date code 2026225. The manager and part each carry their own pair of unsigned stamp words.

The normal manager path with member `+0x438` absent writes its `+0x360` first configuration at `0x4c21c881`. The typed writer `0x4c211900` accepts `moBaseConfiguration_c`, and the ordinary archive writes the actual `moPartConfiguration_c` class. The first configuration's alias is covered by the [part continuation](CmgrAtoms.md#part-return-and-manager-aliases).

| Definition start | Saved class | Class / object slot |
| --- | --- | --- |
| 0 | `moConfigurationMgr_c` | 1 / 2 |
| 165 | `moPartConfiguration_c` | 3 / 4 |
| 192 | `moNodeName_c` | 5 / 6 |
| 252 | `moVisualProperties_c` | 7 / 8 |

Replaying the typed fields and compact nulls through `ArchiveCursor` from slot 1 reaches the visual body at byte 278 with next index 9. The four nulls before the part class leave the next index at 3. Independent reopen evidence names the active configuration `Default` in all 25. The normalized typed opening comparison SHA-256 is `2f6e109230bb617781181b731d7fb4c890fa5e90e0079faf72f5a375e82f9d24`. Inspect versioned fields with the same installed symbols before extending this measured shape.
