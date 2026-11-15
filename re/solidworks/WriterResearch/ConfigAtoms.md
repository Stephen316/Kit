<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS configuration atom ownership

This A12 result covers the `Contents/Config-0` atom list through the start of
`moRelMgr_c` and the atom references in `Contents/Config-0-ResolvedFeatures`.
The wire and ownership observations apply to generation 19000 discovery
captures. Atom-value synthesis and the complete configuration writer remain
unverified.

## Discovery measurements

The input sizes and SHA-256 hashes matched all 25 entries across the [P01 capture
receipt](../../automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json),
[P03 capture receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)
and [P04 capture receipt](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json).
The ordered roster digest is
`03eac878a753a2d7ad1c96a3cdcd171673c26dfc0a06597d47f989f0fc6cad72`,
computed over ASCII lines formed from each filename, a colon, its lowercase
SHA-256, and a newline in path order. The reader and capture paths were
unchanged between `90352c83` and the analysis checkout `08f2f8e6`.

| Discovery family             | Captures | Atom list bytes | Config next index and resolved root count | Bytes between atom list and relation manager |
| ---------------------------- | -------: | --------------: | ----------------------------------------- | -------------------------------------------: |
| P01 rectangle sketch         |        6 |               0 | 106, 18                                   |                                           44 |
| P03 rectangle and blind boss |        8 |             100 | 111, 19                                   |                                           44 |
| P04 boss and cut controls    |       11 |             188 | 279, 21                                   |                                           76 |

The first `moAtom_c` uses a 14-byte schema-1 class definition and an 86-byte
body. Every later entry in this corpus uses a two-byte reference to the same
class and has an 86-byte body. First placement reserves a class slot and an
object slot. Another entry reserves one object slot. The existing archive
primitives re-encoded all 30 tags byte for byte. The observed class slot was 57. That slot is assigned by the surrounding archive, while the feature ID is
read from the atom body.

The five extra allocation slots in P03 compared with P01 comprise two slots
for `moAtom_c`, two for the class and object of `gcCurvatureObject_c`, and
one for an additional `moAnnotationView_c` object. Adding an atom alone does
not produce the P03 configuration namespace. For P04 the counter is 62 on
entry to the relation manager and 279 after its children and the presentation
tail. The resolved stream agrees with the completed map in every capture.

## Feature ownership across streams

The atom body begins with an inherited node record, an empty UTF-16 string,
and absent optional children. The tail starts at body offset 34.
The two signed 32-bit words at body offsets 42 and 46 each equal the native
feature ID of the operation that refers to that atom. The typed resolved
reader independently reads the operation's native ID and its transfer
object reference. All 30 operation references agree with both ID words.

| P04 captures                        | Config object 58 | Config object 59 | Resolved cut parent reference |
| ----------------------------------- | ---------------- | ---------------- | ----------------------------: |
| Baseline A, YZ plane, through-all   | cut ID 46        | boss ID 34       |                            59 |
| Baseline B and seven other variants | boss ID 34       | cut ID 46        |                            58 |

The two otherwise equivalent baseline saves refute the use of timeline order
or fixed archive slots for transfer objects. A serializer needs symbolic
ownership links from the boss and cut to their own atom nodes and from the cut
to its earlier boss atom. The resulting references can be allocated when the
configuration stream is composed. P04 serves as an ordering control for A12
and leaves cut writing outside this evidence.

The ghost records after the atom list also reverse between the P04 orderings.
The packed count has upper nibble 2 and low 28-bit values 1, 1, and 2 in P01,
P03, and P04 respectively. Each entry here contains one signed identifier and
empty geometry and point collections. The one-entry ghost list persists in
P01 with zero atoms, so the atom count cannot serve as the ghost count.

## Reproduction and remaining fields

Locate the model body with [`ReadModelEntry`](../../../src/convert/adapters/solidworks/config/ModelEntry.py)
and [`ModelAtomStart`](../../../src/convert/adapters/solidworks/config/RootFields.py).
Walk the list and validate each body return with
[`SkipAtomList`](../../../src/convert/adapters/solidworks/config/OrdinaryMap.py)
and [`AtomEnd`](../../../src/convert/adapters/solidworks/config/RootAtoms.py).
Resolve the schema definition or class reference through the map at the
relation manager. For each atom, read the initial null pointer, four signed
32-bit words, variable-width string, absent list and pointer, empty node list
and trailer, and the thirteen signed 32-bit tail words. Use the third and
fourth tail words for the ID comparison. Measure the ghost span from the
atom list end to the relation manager and use
[`ReadRectPart`](../../../src/convert/adapters/solidworks/resolved/RectanglePart.py)
for P01 and P03. For P04 use
[`ReadCutConfig`](../../../src/convert/adapters/solidworks/config/CutConfig.py),
[`ReadCutLinks`](../../../src/convert/adapters/solidworks/resolved/cut/CutLinks.py)
and [`ReadCutProof`](../../../src/convert/adapters/solidworks/resolved/cut/CutProof.py)
to read both operation references and the cut's parent reference.

The two tail words at body offsets 70 and 78 are equal within every atom and
take distinct values among the P03 captures, including 21457 and 21743 in
the two baseline saves. Their initializer and loader requirements remain
unknown. The next probe is to trace the saved values into the atom serializer,
then distinguish generated state from an allowed default with existing
same-model controls. The relation, presentation, and other configuration
fields still need independent construction rules. This comparison produced no
new SLDPRT, vendor load, rebuild, or editable acceptance evidence.
