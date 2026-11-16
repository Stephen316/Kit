<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Offline FreeCAD two-length extrusion readiness

The A16/B06 preflight exercises the public `WriteDocument` route from
a freshly authored portable rectangle to `freecad.fcstd`, with
`AllowCarrier=False`. It round-trips each input through the portable
JSON contract, writes the FCStd to an in-memory stream, and reads the
actual `Part::Extrusion`, sketch link, spreadsheet cells and expression
engine in its `Document.xml`. The run used SDK source
`adee447ebc3e8202f167d54d31af5adba4fe60d7`.
[Preflight](../../../../../re/automation/FreeCadTwoLengthReadiness.py),
[public write entry](../../../../../src/convert/api/ApiWrite.py)

The 37 × 21 mm test sketch and its depth values were authored for this
replay. The two-length document has independent forward and reverse
driver IDs, each owned by the same Boss. Each reordered control reverses
the generic parameter roster while preserving the explicit end-owner
binding in `length_parameter_ids`. The symmetric control has a single
total-thickness driver.

| Input                                                    | SDK observation                                                                 | Target expression binding                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Two lengths of 11 and 5 mm, original or reordered roster | Emits both scalar lengths and both spreadsheet cells                            | `LengthFwd` points to the forward driver. `LengthRev` has no expression. |
| Two lengths of 7 and 7 mm, original roster               | Emits both lengths and both cells                                               | `LengthFwd` points to the forward driver. `LengthRev` has no expression. |
| Two lengths of 7 and 7 mm, reordered roster              | Emits the same lengths and cells with the same portable end owners              | `LengthFwd` points to the reverse driver. `LengthRev` has no expression. |
| Symmetric total thickness of 16 mm                       | Emits a symmetric extrusion, a 16 mm forward property and zero reverse distance | `LengthFwd` points to the sole total-thickness driver.                   |
| Open rectangle with the same two-length intent           | Refuses the required extrusion and emits zero bytes                             | No target expression.                                                    |

The first four controls expose the same missing reverse dependency.
Matching numeric lengths can also change the forward binding when the
generic roster is reordered. The existing native emitter selects that
driver by value and writes an expression only for `LengthFwd`. The
SDK reported `application_usable` and `vendor_loadable` on the five
emitted archives. These are SDK result fields. The replay establishes
the emitted properties and relationships. A FreeCAD load, independent
edits, rebuild, save and fresh reopen remain open.
[Native emission](../../../../../src/convert/adapters/freecad/Archive.py)

The two historical grids on PR #120 record distinct end owners for
10/4, 14/4 and 10/7 mm, and one total owner for the 10, 14 and 18 mm
midplane cases. None of those six source SHA-256 values appears in the
pinned PR #94 corpus. Their published neutral records supply reference
observations, and the preflight creates its own unrelated inputs.
[Two-length reference](https://github.com/TryUniCAD/Kit/blob/89bb7b32759f3ca00a1abed733761ff3f70ab98d/re/solidworks/measurements/VerifiedDecodeEvidence/TwoLength.md),
[midplane reference](https://github.com/TryUniCAD/Kit/blob/89bb7b32759f3ca00a1abed733761ff3f70ab98d/re/solidworks/measurements/VerifiedDecodeEvidence/Midplane.md),
[corpus pin](../../../../../re/automation/Corpus.json)

```sh
python -B re/automation/FreeCadTwoLengthReadiness.py
```

The aggregate SHA-256 over the six observations is
`bd444283432690252981e914cc16105da262fa750e8b3c924f849f21b6d8fd4f`.
The directional native route remains subject to the A13 and A15
dependencies and independent acceptance.
[Automation register](../../../../Reference/Research/AutomationSteps.md)
