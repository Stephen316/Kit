<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Configuration manager feature and mass properties

The generation-19000 configuration continues from the [visual properties](CmgrVisual.md) return through inherited feature fields, mass properties and the base configuration's maps. A typed replay from byte 1095 reaches the [linked-atom map](CmgrAtoms.md) for all 25 receipt-pinned captures. The ordinary part path preserves archive index 9 throughout. [Configuration manager opening](CmgrOpening.md)

## Inherited feature

In the [pinned `sldmodu.dll`](CmgrTail.md#root-and-feature-stamps), the primary `moPartConfiguration_c` vtable at `0x4ce29ff8` and `moConfigurationMgr_c` vtable at `0x4cec3b90` use `0x4c1783a0` and `0x4c179160` in slots `+0x4b8` and `+0x4c0`. The first hook writes the typed `moVisualProperties_c` pointer at `0x4c178455` from the feature's `+0x78` member. The latter hook emits no fields for this measured shape. In the ordinary file archive, `swccu.dll` `su_DBKey` at `0x31a444d0` returns without consuming bytes. Its database path is separate.

| Start | Fields and checked values | Native store sequence |
| --- | --- | --- |
| 1095 | Two signed zeros, unsigned update stamp 101, byte 0 for absent secondary text, four signed words `(0,0,0,19000)`, double zero, signed creation build 2026225. The exported `getLastUpdateVersion` returns members `+0x2b8` and `+0x2bc`. The exported `getCreateVersion` uses build member `+0x2b4`. | `0x4bb10e47..0x4bb10f29` |
| 1136 | Null `moFolder_c` pointer, empty wide CString, byte zero. `moEntVisProp_c` writes `u16,u16,u8,u32,u16` values `(65535,0,3,0xffffffff,65535)`. `utLineWidth_c` writes signed short and float, each `-1`. | `0x4bb10fbb..0x4bb10fea`, `0x4c14ef6f..0x4c14f09e`, and `sldmfcu.dll` `0x3c85a71e`, `0x3c85a72b` |
| 1160 | Two signed zeros, null `moFeatComment_c` pointer, unsigned zero, bytes 4 and 0, signed zeros for `+0x318` and hidden state, and signed `-1` from `+0x30c`. Two unsigned stamp words vary between saves. The final unsigned short and two signed words are 2, 370108 and 1. | `0x4bb11035..0x4bb11210` |

The base configuration begins at byte 1206 with empty wide CString, signed `-1`, unsigned `0x80400180`, a second empty wide CString, and three unsigned members `+0x85c`, `+0x860` and `+0x670`. These are written at `0x4c2159cb..0x4c215a2b` and vary with feature and save state.

## Mass property record

The next call at `0x4c215a3b` reaches exported `moMassProp_c::Serialize` at `0x4bc1d2e0`. It takes its owner from the base configuration and writes the following sequence.

| Span | Save order | Native stores |
| --- | --- | --- |
| 1234–1330 | Twelve doubles from members `+0x20,+0x28,+0x30,+0x10,+0x08,+0x18,+0x38,+0x40,+0x48,+0x50,+0x60,+0x58`. The named raw accessors anchor center of mass, volume, area and mass. | `0x4bc1d32f..0x4bc1d3d4` |
| 1330–1374 | Five signed integers `(1,0,0,0,0)`, double from `+0x00`, then four signed zeros. The double is 0 for P01 and 0.995 for the solid controls. | `0x4bc1d3e4..0x4bc1d479` |
| 1374–1488 | Two empty wide CStrings, a signed zero, three zero doubles, three identity-basis vectors, signed 1 and unsigned short zero. Each `mgVector_c::save` writes three doubles in the ordinary archive. | `0x4bc1d4ac..0x4bc1d580` and `sldmgu.dll` `0x31e13b61..0x31e13b7d` |

The `sldmgu.dll` SHA-256 is `3b82cfcaa13f099fca4f9741acbb11479dab7a6f20656052d5a750e61c6fee1e`. All six P01 files have no solid body and zero in the first twelve doubles. For all 19 solid P03 and P04 files, scaling the first three doubles from metres to millimetres and the fourth from cubic metres to cubic millimetres agrees with independent reopen measurements. The reversed P03 saves negative Z and both YZ controls permute the centroids to the measured frame.

### Constructor and rectangular boss inputs

The default initializer at `0x4bc1bd50` zeros the base scalar, area, volume, mass, centroid, tensor, auxiliary scalars and both coordinate-system-name pointers. It installs the Cartesian unit vectors in both axis arrays and assigns the trailing signed 1 at `0x4bc1be14`. The model constructor at `0x4bc1c630` calls this initializer, sets the signed `+0x1c0` flag to 1 and clears `+0x1c4,+0x1c8,+0x1cc,+0x1e0,+0x1f0`. This accounts for the empty profile as written. The six P01 records are each 254 bytes and have SHA-256 `dd69d4585ca970361fa398485ea5f2e828b0f76ebcc6b9a3ebe4287cc5cd9f31`.

For the P03 blind boss, reconstruct the eight corners by extruding the four measured perimeter corners along the signed measured principal normal. The extrusion must be one-sided in a single principal direction and produce exactly the corners of a cuboid. Let `dx,dy,dz` be its positive world-axis lengths in metres. Its centroid is the midpoint of the two coordinate bounds. Volume is `dx*dy*dz` and surface area is `2*(dx*dy+dy*dz+dz*dx)`. Mass is volume times the supplied uniform density. The eight receipt controls agree with density `1000 kg/m³`, also recorded at the [part Definition tail](DefinitionJournal.md#part-definition-tail). The live assignment of that density remains unobserved.

The centroidal moment about X is `mass*(dy*dy+dz*dz)/12`, with the cyclic forms for Y and Z. The axis-aligned cuboid has zero off-diagonal moments. Exported `moMassProp_c::getTensor` at `0x4bc2a080` exposes the three diagonals at `+0x38,+0x40,+0x48` and off-diagonals XY, XZ and YZ at `+0x50,+0x60,+0x58`. The archive writes this same six-member order. All twelve computed geometric fields match the eight P03 records within an absolute diagonal moment delta of `4.24e-22 kg·m²` and a largest stored off-diagonal residual of `1.77e-22 kg·m²`. The normalized comparison SHA-256 is `29227e00817727f76f69c4d0958c26a4b49c99e4cee7b468ad2efa57ffe769e9`. This is agreement to tolerance. The original kernel's floating-point residuals are independently retained in the captures.

The checked solid cache scalar `0.995` also has a native default route. Exported `gcBody_w::getMultiMassProps` at `0x43c1be00` in `sldgcu.dll` selects that literal at `0x43c1be95` for nonpositive accuracy input and stores it in the first mass-property member. `moMassProp_c::combine` also floors that member at `0.995` through `0x4bc1e446..0x4bc1e45a`. The installed `sldgcu.dll` SHA-256 is `797f81cba7080ea6edd37eca36abeaa9a2c0539f9319b980b92abc5a875edf24`. This supports the measured default body profile. Overridden input accuracy and computed P04 cutout caches require separate writer evidence.

## Base configuration collections

After the mass property record, the unsigned four-byte `su_CTime` at `0x4c215a57` is 631152000. The base constructor at `0x4bdbd9f8` initializes this member to midnight on 1990-01-01. The following base-configuration pointer is null. The filtered inline `suObList` at `0x4c215b21` has compact count zero. These reach byte 1496.

| Start | Save order in the measured standalone parts | Native stores |
| --- | --- | --- |
| 1496 | Signed word `+0x6f8`, zero for P01 and one for the solid controls. Two zero bytes, empty inline list `+0x528`, unsigned 19000, saved mode byte 1, presence byte 0, null `moToolboxPartSpecArray_c`, empty inline list `+0xa98`. | `0x4c215c00..0x4c215d31` |
| 1514 | Two signed words `(0,1)`, empty signed counted object map, two signed words `(0,1)`, two floats `(-1,-1)`, two empty signed array counts, signed `(1,0)`, six signed zeros, signed 1, empty third signed array count, then signed `(-1,1,0)`. | `0x4c215d3e..0x4c216058` |
| 1602 | Empty unsigned counted visual-properties map, empty signed counted nested map, followed by signed count and signed pairs. This third map is empty in P01, `(101,0)` in P03, and `(101,0),(102,0)` in P04. | `0x4c2175e2`, `0x4c21764a`, `0x4c2178ec` |
| After those pairs | Signed zero, signed count and signed pairs, empty signed counted pair map, empty map with unsigned longs as values, compact empty `su_CMapStringToInt`, signed zero, empty signed counted map, empty signed `moCustomPropertyList`, null `moAbbrViewManager_c`, signed zero, unsigned empty set count. Only P04 populates the second pair map with `(102,101)`. | `0x4c217c27..0x4c2183ea`. The custom property list uses slot 5 at `0x4be5ed10`; the compact string-map count delegates through `swccu.dll` `0x31a47566`. |

For reproduction, follow the [receipt and archive pins](CmgrVisual.md#inputs-and-reproduction), start after the checked visual return and seed the same `ArchiveCursor` map ending at index 9. Decode the scalar and string sequence and require typed compact nulls at the pointer fields. The resulting linked-atom starts are 1654 for six P01s, 1662 for eight P03s and 1678 for eleven P04s. For independently measured body volume and center, compare after unit conversion at absolute tolerances `1e-7 mm³` and `1e-8 mm`. Preserve the no-body value for P01.
