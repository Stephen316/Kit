<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS backward compatibility content manager

Generation 19000 ordinary standalone parts save `SwDocContentMgr/SwDocContentMgrInfo`
as a schema-1 `moBCModeInfo_c` object. The supported member has one unparented
active saved configuration, empty compatibility labels and saved external
references, no exploded view or configuration update request, and either no
solid-body folder entries or one body name and visibility entry. The caller
supplies the configuration, both material strings, observed compound flags,
density value, three native unit enums, header times and update stamp, and the
body owner, name and visibility when present. The constructor checks the
witnessed mask and density sentinel and the two observed unit combinations. It
encodes the object, lists and count fields into a fresh archive writer.
[Constructor and reader](ContentManager.py)

## Native producer and field ownership

The read-only producer inspection used installed SOLIDWORKS 34.4.1.1011
`doccplu.dll` SHA-256
`120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b`
and `sldmodu.dll` SHA-256
`2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.
Addresses below are image-relative offsets in these two builds.

| Owner                 | Observed storing path and value source                                                                                                                                                                                                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Storage and object    | `doccplu!SolidStorage_c::SaveBackWardComptiableData` starts at `0x29670`, opens the storage and member at `0x29701` and `0x2975f`, calls the default constructor at `0x297e9`, and archives the object at `0x29f88`.                                                                                     |
| Saved header          | The producer calls `syncHeaderTimeStamps` at `0x29811`. That function starts at `sldmodu:0x602110` and copies the creation time, update time and current update stamp into their own members.                                                                                                            |
| Saved configuration   | The producer iterates `getConfigurationsList` and assigns index, configuration flags, update flag, density, presence of exploded views, parent and two material strings. The source calls are `0x29836`, `0x2998c`, `0x299c7`, `0x299ff`, `0x29a42`, `0x29a4a/0x29a84`, `0x29b70` and `0x29c25/0x29caa`. |
| Native document units | The three setter calls at `0x29f04`, `0x29f36` and `0x29f68` each consume their owning native unit record.                                                                                                                                                                                               |
| Solid body            | The producer calls `setUpSolidBodyFolderData` at `0x29ce8`. The helper starts at `sldmodu:0x601ca0` and reads the atom ID at `0x601e51`, its virtual name at `0x601e67`, and visibility as the inverse of `moAtom_c::isBlanked(nullptr)` at `0x601fa8/0x602042`.                                         |

`moBCModeInfo_c::Serialize` starts at `sldmodu:0x5ff0c0`.
The storing branch writes the two unsigned `su_CTime` words and an
unsigned update stamp. The ordinary branch uses an empty inline `suObList`
and one schema-0 `su_CStringArray` object with zero elements. The
construction and serializer paths select these defaults independently of
saved body contents. The next object index closes at 5.

The body name folder writes the entry count as a signed word and, for a
populated folder, repeats it as an unsigned word before the signed atom
ID and framed name. The visibility folder writes its count, repeat,
atom ID and 0 or 1 visibility as signed words. The first counts appear
at `0x5ff273` and `0x5ff373` respectively. The final two maps
are saved at `0x5ff5b2` and `0x5ff5c1` before the storing branch
returns. The reader requires whole-stream consumption, exact configuration
keys, matching body atoms and matching repeated counts.

## Sealed replay

The verifier reads the two SOLIDWORKS 34.4.1.1011 capture receipts and
their independently measured sources pinned at
`466dcb172dfa3803463e07ccde963ba01671d200`. It compares the content
timestamps and stamp with the independently parsed Header2 fields and joins
the active saved configuration and body folder to the typed configuration
and measured native model. The public information XML and native measurement
join the two unit domains. Public metric `(0, 5, 2)` agrees with internal
`(0, 4, 1)`. Public inch `(3, 3, 4)` agrees with internal `(3, 2, 3)`.
The tuple order is length, system, and mass.
[P01 SOLIDWORKS receipt](../../automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json),
[P03 SOLIDWORKS receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

| Sealed cohort | Complete generated bytes        | Body ownership                                                                                            |
| ------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------- |
| P01           | Six distinct 421-byte members   | No body folder entries or independently measured solid bodies.                                            |
| P03           | Eight distinct 463-byte members | Atom 101, named `BlindBoss` and visible. The extra 42 bytes belong to the saved body name and visibility. |

Run the source-pinned replay with the project's pinned Python environment.

```sh
python re/solidworks/WriterResearch/VerifyContentManager.py
```

All 14 complete members compare byte for byte. The replays bind each
source SHA-256 to its generated member digest and decoded state. Their
aggregate SHA-256 is
`6d54767e03caf52459ae49a0c8ed84dd05cbc5a60456e451d2180c00313910a0`.
The two fresh controls round-trip a different configuration and timestamps,
one with a renamed hidden atom and one without a body. The four malformed
controls reject truncation, an appended byte, a mismatched folder atom,
and an inconsistent repeated folder count. [Verifier](VerifyContentManager.py)

The archive-only replay establishes the bounded member layout and
construction. A prior observation found that a legacy assembly opened
after omission of this member. The licensed P03 omission run retained the
member. Standalone part omission, package assembly, and native acceptance
of the generated member still require licensed evidence.
[Legacy assembly measurement](../measurements/Measure.md),
[Licensed P03 omission run](../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)
