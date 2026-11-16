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

## Base header

The base configuration serializes a comment, signed configuration member, flags, alternate name and three bookkeeping words at `0x4c2159cb..0x4c215a2b`. These occupy bytes 1206–1234 in all fourteen P01/P03 controls. The archive load path reads the same members in order from `0x4c21618f`. The two names start empty in the standalone constructor at `0x4bdbe9c4` and `0x4bdbe9e0`, with the latter accepting an explicit comment. Named accessors `getComment` and `getAlternateName` anchor `+0x4a8` and `+0x498`. The signed `+0x4b0` starts at `-1` at `0x4bdbe9fc` and `0x4bdbfc14`. The measured standalone branch retains this value.

| State | Native provenance | Receipt-pinned evidence |
| --- | --- | --- |
| Preview missing and out of date | Constructor `0x4bdbea11` sets `0x100`. The named preview setters at `0x4b291af0` and `0x4b291b20` write `0x100` and `0x80`. Both preview-install paths clear them together. | Both bits set in all fourteen. |
| Blank-state migration marker and linked atom tree | `0x4b599b00` tests `0x400000` and can transfer atom blank data to this configuration via `0x4b599eab`. It sets the same marker at `0x4b599f40` and `0x4b599faa`. The linked-tree builder sets `0x80000000` at `0x4bdcd866` before walking feature atoms. | Both bits set, including P01 with zero linked atoms. |
| Model highest ID `+0x85c` | `moConfigurationMgr_c::syncRebuildStamps` calls `moHeader_c::getHighestID` at `0x4b8a0eb4` and assigns the result at `0x4b8a0eba`. | P01 28, P03 34. |
| Session update stamp `+0x860` | `moModel_c::updateSessionStamp` calls `moHeader_c::getNextUpdateStamp` at `0x4c038c86` and stores the active configuration member at `0x4c038c9a`. | Across repeated saves and parameter edits, the observed range is 117–232. |
| Mass property stamp `+0x670` | The base constructor at `0x4bdbeb36` starts it at zero. `moBaseConfiguration_c::copyMassProp` at `0x4bdd0660` stores its nonzero caller input at `0x4bdd0685`. | Zero across P01. P03 spans 105–121. |

The [header codec](CmgrBaseHeader.py) writes the measured standalone state with those four flags. It accepts the three bookkeeping words as caller inputs. The hosted archive comparison consumes the saved words to measure reconstructability. An independent generated document must supply its own allocator watermark and stamp state. Other flag profiles and configuration text lie outside this codec.

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

[`EncodeEmptyMass` and `ReadEmptyMass`](CmgrMass.py) take the enclosing generation and body count explicitly. The reader checks the scalar groups and both wide CStrings, preserving the enclosing archive cursor at the next configuration field. The empty codec applies to the constructor-derived no-body shape above.

For the P03 blind boss, reconstruct the eight corners by extruding the four measured perimeter corners along the signed measured principal normal. The extrusion must be one-sided in a single principal direction and produce exactly the corners of a cuboid. Let `dx,dy,dz` be its positive world-axis lengths in metres. Its centroid is the midpoint of the two coordinate bounds. Volume is `dx*dy*dz` and surface area is `2*(dx*dy+dy*dz+dz*dx)`. Mass is volume times the supplied uniform density. The eight receipt controls agree with density `1000 kg/m³`, also recorded at the [part Definition tail](DefinitionJournal.md#part-definition-tail). The live assignment of that density remains unobserved.

The centroidal moment about X is `mass*(dy*dy+dz*dz)/12`, with the cyclic forms for Y and Z. The axis-aligned cuboid has zero off-diagonal moments. Exported `moMassProp_c::getTensor` at `0x4bc2a080` exposes the three diagonals at `+0x38,+0x40,+0x48` and off-diagonals XY, XZ and YZ at `+0x50,+0x60,+0x58`. The archive writes this same six-member order. All twelve computed geometric fields match the eight P03 records within an absolute diagonal moment delta of `4.24e-22 kg·m²` and a largest stored off-diagonal residual of `1.77e-22 kg·m²`. The normalized comparison SHA-256 is `29227e00817727f76f69c4d0958c26a4b49c99e4cee7b468ad2efa57ffe769e9`. This is agreement to tolerance. The original kernel's floating-point residuals are independently retained in the captures.

[`CalcBossMass`](CmgrBossMass.py) accepts the proven axis-aligned cuboid's world bounds in metres and explicit density in kilograms per cubic metre. It returns the twelve physical fields with axes in saved world order and no archive emission. Establish the cuboid from its owned profile and signed extent before using its bounds.

The checked solid cache scalar `0.995` also has a native default route. Exported `gcBody_w::getMultiMassProps` at `0x43c1be00` in `sldgcu.dll` selects that literal at `0x43c1be95` for nonpositive accuracy input and stores it in the first mass-property member. `moMassProp_c::combine` also floors that member at `0.995` through `0x4bc1e446..0x4bc1e45a`. The installed `sldgcu.dll` SHA-256 is `797f81cba7080ea6edd37eca36abeaa9a2c0539f9319b980b92abc5a875edf24`. This supports the measured default body profile. Overridden input accuracy and computed P04 cutout caches require separate writer evidence.

### Default populated options and frame

The first four signed fields at byte 1330 are anchored by `getIncludesHidden` at `0x4b2ac030` and `isAssigned`, `isForceAssigned` and `getIncludesAssignedMass` at `0x4b289d20`, `0x4b289d00` and `0x4b2ac020`. The constructor sets `+0x1c0` to one and clears the other three. The store normalizes `+0x1cc` to a signed Boolean at `0x4bc1d40a..0x4bc1d41b`. The following `+0x1e0` starts at zero. The native calculation resolves density through the atom's material and fallback sources, including the named `SDL/TYSA_DENSITY` attribute at `0x4bc25389`. It groups valid bodies by that density at `0x4bc253d3..0x4bc254f5`, calls `gcBody_w::getMultiMassProps` at `0x4bc25795` and sets `+0x1e0` at `0x4bc25857` when more than one group participates. The single uniform solid uses the zero branch.

The same initializer zeros the four serialized option members `+0x134..+0x140` and initializes the coordinate name pointers `+0x148` and `+0x150` to null. The serializer checks each pointer before writing its CString at `0x4bc1d4ac` and `0x4bc1d4e1`. The next zero word is the legacy flag `+0x1f0`, which `getIsLegacyMassProp` reads at `0x4b2875b0`. The initializer zeros the coordinate origin members at `+0xc8..+0xd8` and assigns the named Cartesian unit vectors with `xAxis`, `yAxis` and `zAxis` imports at `0x4bc1be3c`, `0x4bc1be4f` and `0x4bc1be65`. It sets `+0x15c` to one and zeros `+0x128`. Alternate override and coordinate-system cases lie outside this profile.

[`EncodeBossMass`](CmgrBossMass.py) constructs the 254-byte default record for one proved axis-aligned rectangular boss at an explicit uniform density. [`ReadBossMass`](CmgrBossMass.py) preserves native values and checks the default options and coordinate wrappers. In all eight P03 saves those 158 wrapper bytes are identical, including the kernel default `0.995`. The [archive verifier](VerifyCmgrBoss.py) proves the rectangular perimeter and signed end against the receipt, then compares generated wrapper bytes exactly and geometry numerically. [Reproduction and limits](../../../Documentation/Changes/Research/Writers/SolidWorksBossCmgrMass.md)

## Base configuration collections

After the mass property record, the unsigned four-byte `su_CTime` at `0x4c215a57` is 631152000. The standalone base constructor at `0x4bdbeb62` initializes this member to midnight on 1990-01-01. The serializer zeros the next pointer itself at `0x4c215a5d` and calls the configuration pointer operator at `0x4c215a68`. The filtered inline `suObList` at `0x4c215b21` has compact count zero. The constructor creates its empty source at `0x4bdbebb4`. These reach byte 1496.

The signed word at 1496 is the saved solid body count. At `0x4c215b94` the serializer copies the previous count to `+0x6fc`, read at `0x4b288ab0` by `getPreviousNumberSavedBodies`. The current part path obtains the opened model and calls vtable `+0x12b0` at `0x4c215bec`. The part constructor installs primary vtable `0x4d1222a8`. Its slot points to `0x4c1ae070`, which passes the atom manager, an unfiltered selector and null feature to exported `getNumberSolidBodies` at `0x4bcf6b40`. The serializer retains the result in `+0x6f8` and writes it at `0x4c215c00`. The next byte at 1500 is configuration accuracy level `+0x688`, from the accessor `getAccuracyLevelInMassPropCalc` at `0x4b283830`. It is zero in all eight P03 saves and is separate from the mass record's `0.995` double.

| Start | Save order in the measured standalone parts | Native stores |
| --- | --- | --- |
| 1496 | Signed solid body count `+0x6f8`, zero for P01 and one for the solid controls. Zero accuracy level byte and zero byte from `+0x968`, empty inline list `+0x528`, unsigned 19000, saved mode byte 1, presence byte 0, null `moToolboxPartSpecArray_c`, empty inline list `+0xa98`. | `0x4c215c00..0x4c215d31` |
| 1514 | Two signed words `(0,1)`, empty signed counted object map, two signed words `(0,1)`, two floats `(-1,-1)`, two empty signed array counts, signed `(1,0)`, six signed zeros, signed 1, empty third signed array count, then signed `(-1,1,0)`. | `0x4c215d3e..0x4c216058` |
| 1602 | Empty unsigned counted visual-properties map, empty signed counted nested map, then the signed atom material-state map. The third map is empty in P01, `(101,0)` in P03, and `(101,0),(102,0)` in P04. | `0x4c2175e2`, `0x4c21764a`, `0x4c2178ec` |
| After those pairs | Signed zero, signed count and signed pairs, empty signed counted pair map, empty map with unsigned longs as values, compact empty `su_CMapStringToInt`, signed zero, empty signed counted map, empty signed `moCustomPropertyList`, null `moAbbrViewManager_c`, signed zero, unsigned empty set count. Only P04 populates the second pair map with `(102,101)`. | `0x4c217c27..0x4c2183ea`. The custom property list uses slot 5 at `0x4be5ed10`; the compact string-map count delegates through `swccu.dll` `0x31a47566`. |

The [collection opening codec](CmgrCollectionFront.py) constructs bytes 1488–1514. It takes the measured standalone save mode and the model's count of zero or one solid bodies. The standalone constructor sets accuracy zero at `0x4bdbefd7` and `+0x968` zero at `0x4bdbecad`. It creates empty lists `+0x528` and `+0xa98` at `0x4bdbea44` and `0x4bdbed9a`. The model-present branch passes the enclosing archive generation at `0x4c215c73`, then obtains save mode from the environment at `0x4c215c99` with fallback 1. The presence source `+0x610` and toolbox source `+0x660` start null at `0x4bdbeab1` and `0x4bdbeb06`. Their branches are independent at `0x4c215cd6` and `0x4c215d14`. The scope keeps each absent.

The atom material-state map at configuration member `+0xb00` is created at `0x4bdbf9f5..0x4bdbfa02`. `updateLinkedAtomIDTree` inserts state zero for a missing atom key at `0x4bdf62cf..0x4bdf62e8`. This accounts for the corresponding P03 atom identity and its default value before the linked-atom record. `isMaterialApplied`, `isMaterialPropagated` and `isMaterialRemoved` check values two, three and one through `0x4bde19b0..0x4bde1a3a`. Those states need separately measured authoring.

The [remaining collection codec](CmgrCollections.py) appends the following standalone defaults, with zero or one owned atom. The signed map serializer at `0x4c20e6bb..0x4c20e6e2` supplies atom map count, key and state widths. It reads the count from the initialized map object and enumerates the pairs.

| Record | Source members | Initialization and serialization |
| --- | --- | --- |
| 1514–1542 | `+0xaf0,+0xaf4,+0x630,+0x784,+0x788,+0x78c,+0x790` | The standalone constructor writes 0 and 1 at `0x4bdbedaf..0x4bdbedb6`, creates the empty counted map at `0x4bdbead8`, clears `+0x784` via the qword at `0x4bdbec19`, sets `+0x788` at `0x4bdbec20` and initializes both float members to -1 at `0x4bdbef58..0x4bdbef63`. Stores are `0x4c215d3e..0x4c215e88`. |
| 1542–1602 | Array counts for `+0x358,+0x380,+0x3d0` and scalars `+0xb30,+0x828,+0x82c..+0x840,+0x844,+0x750,+0xbd4,+0x850` | The array constructor calls at `0x4bdbe8be,0x4bdbe8ee,0x4bdbe942` initialize empty pointer arrays. Scalar stores at `0x4bdbedea,0x4bdbec4b,0x4bdbfa31..0x4bdbfa47,0x4bdbec52,0x4bdbebef,0x4bdbee8a,0x4bdbec5d` supply the defaults. The save path writes array sizes, scalar words and six ordered dwords at `0x4c215e9f..0x4c216058`. |
| 1602–material-state count | Visual map counts `+0x428,+0x438` | Calls at `0x4bdbe980,0x4bdbe98d` initialize the two empty maps via `0x4b2e1652,0x4bdbcc92`. The store reads their counts at `0x4c2175d8,0x4c217640`. |
| After material-state pairs | Scalar `+0xb08`; maps `+0x460,+0xb10,+0xa50`; string-to-int map `+0x600` | Constructor sites `0x4bdbedc8,0x4bdbe9b4,0x4bdbedd6,0x4bdbed4d,0x4bdbeaa3` set the scalar zero, empty map objects and null string-map pointer. The latter emits a temporary empty string map via `0x4c217eee..0x4c217f02` when null. The counted maps store in order through `0x4c217c27..0x4c217e42`. |
| After string map to link-map start | Scalar `+0xb34`; counts `+0xb60,+0xb68`; pointer `+0xb80`; scalar `+0x74c`; set count `+0xa78` | The zero high half of qword 1 at `0x4bdbedea` supplies `+0xb34`. The `+0xb58` map starts empty via `0x4bdbee20`. The inline custom-property list uses the empty `suPtrArray` initializer at `0x4be5e382`; the store creates that object if absent at `0x4c2180c4` and the list count is written at `0x4be5ed55`. The `moAbbrViewManager_c` pointer starts null at `0x4bdbee33` and stores via `0x4c218300`. The initial `+0x74c` is the zero high half of the qword at `0x4bdbebe8`. The set is initialized empty at `0x4bdbed70` via `0x4bdbccd2`. |

The checked collection range ends at 1654 for P01 and 1662 for P03. The verifier measures the real material-state keys against the following typed linked-atom definitions, then emits the default map from those owned atom IDs. Both configuration and collection records keep the inherited archive map through this boundary. Custom states, populated optional collections and histories with multiple atoms need their own rules.

For reproduction, follow the [receipt and archive pins](CmgrVisual.md#inputs-and-reproduction), start after the checked visual return and seed the same `ArchiveCursor` map ending at index 9. Decode the scalar and string sequence and require typed compact nulls at the pointer fields. The resulting linked-atom starts are 1654 for six P01s, 1662 for eight P03s and 1678 for eleven P04s. For independently measured body volume and center, compare after unit conversion at absolute tolerances `1e-7 mm³` and `1e-8 mm`. Preserve the no-body value for P01.
