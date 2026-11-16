<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 ordinary SOLIDWORKS part information

`EncodePartInformation` feeds the existing information XML serializer
from the generated output path, header file reference, core summary,
current local calendar, configuration units, ordinary part properties
and optional calculated solid mass. A P01 sketch-only part emits the
document and unit properties. A P03 part with one aligned blind boss
also emits the first configuration's mass summary.
[Information fields](../../../../../../re/solidworks/WriterResearch/PartInformationFields.py)

## Native document sources

The pinned SOLIDWORKS 34.4.1.1011 `slduiu.dll` has SHA-256
`88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6`.
Its `iSubGetSystemPropertyString` routine starts at `0x49923aa0`.
File Name is the current output basename without the extension. Folder
Name comes from the prior full path and ends with a separator when the
prior path has a directory. The controls have an empty prior reference
on their first save. Both names correlate with the capture output and
Header2 independently. Configuration retrieval at `0x499244b4` and BOM
part number retrieval at `0x499245c6` join the first configuration and its
file title on all 14 controls.

The short and long calendar calls at `0x499240d3` and `0x4992411f` give
Windows the current date and default calendar formatting. The caller
supplies this date separately from the creation and save times. The
summary getters at `0x49924373` and `0x499243e1` use the document
summary's creation and last-save properties. The observed English
day/month/year display and 24-hour clock are supported with an explicit
caller time zone. Read-only checks compare the timestamps and last
saver to `docProps/core.xml` for every capture. The independent summary
text inputs remain available for authored metadata.

`setDocumentOrientation` at `0x497c8230` obtains the world-orientation
key at `0x497c85cc` and writes 0 for Z-up or 1 for Y-up at
`0x497c85e1` through `0x497c8613`. The design-table probe at
`0x49788a13` emits the presence flag at `0x49788a72`. The separate
custom-property architecture selector at `0x49733404` supplies
`IsCPReArchEnabled`. The bounded ordinary part profile has no design
table, uses the modern property architecture, and has Component Type
0 through the native regular document branch at `0x49788d52` to
`0x49788da8`.

## Native unit and mass fields

`addSytemUnits` at `0x4977a600` connects property names to typed
preference selectors. `0x497cc4d0` dispatches the requests to the native
integer and toggle preference getters. These paths independently
identify the source of the ordinary metric and decimal-inch profiles.

| Information unit field | Independent native owner |
| --- | --- |
| Unit system and active length | Preference selectors 0x107 and 0x2f reach `0x4929ee11` and `0x4929ee74`. Length is direct for the measured two units. Unit system uses its one-based API enum. |
| Primary and dual decimal mode, precision and denominator | Selectors 0x30 to 0x32 and 0xff to 0x101 read formatter members +0x10, +0xc and +0x28. The two denominators come from the existing Config-0 formatter profile. The dual length selector 0xfe reads the nested length object. |
| Angle, time, energy, force and power | Integer unit queries use each named default unit owner. Precision getters reach member +0xc. The time, energy, force and power API enums are one-based for the observed profiles. |
| Mass property units | `0x4929f03f` through `0x4929f150` read the configured density units and their fallback length formatter. Mass and volume use their one-based API enums for the observed profiles. |
| Decimal rounding and fractional display toggles | Selector 0x20a gets the saved document detail rounding member +0x2c10 at `0x492a022e`. Selectors 0x3e, 0x3f, 0xfc and 0xfd use the bounded length-format flags through the toggle API. |

`SaveMassProperties` starts at `0x49772f00`. It obtains the native
configuration mass state at `0x4977308f` and its storage name at
`0x497730cd`. The `gcMassProp_c::getDataOut` getter at
`sldgcu.dll` address `0x43c1b7a0` emits center, volume, surface area,
mass, diagonal inertia and three negated product moments in the
witnessed notation. That DLL has SHA-256
`797f81cba7080ea6edd37eca36abeaa9a2c0539f9319b980b92abc5a875edf24`.
The twelve physical SI values use 16 decimal places at `0x49773162`.
Two measured ordinary configuration flags append `1.000000, 0.000000`
at `0x497731a7`. Config-0's unit settings can change while the saved
mass values remain in SI. The authored cuboid yields exact zero
inertia products. The native kernel can introduce signed noise below
display precision for those three products.

## Independent hosted comparison

The existing hosted verifier continues to require complete native
information member identity. It also reconstructs the same fourteen
members from Header2, core summary clocks, capture output identity,
Config-0 units and the separate CMgr mass record. P03 adds a comparison
using calculated mass from the reached rectangular solid and document
density. The calculation check allows the sign of zero only in the
three inertia product strings. The read-only native wire digest
aggregate remains
`b27ac51f7278cbd4a125f9cc6f38391fe0402e849628ecb11f9656c2a118e573`.
Native acceptance of the composed part remains pending.
[Hosted comparison](../../../../../../re/solidworks/WriterResearch/VerifyPartInformation.py)
