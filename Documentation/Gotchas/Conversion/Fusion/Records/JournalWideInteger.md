# Saved Fusion sculpt name attributes use a 64-bit integer token

## Expectation

Every integer in a Fusion journal fits in a signed 32-bit value. Generic ASM attributes use one fixed set of action values.

## Actual behavior

Fusion boundary fill saves write `int64_attrib-name_attrib-gen-attrib` records on faces. The census found 297 records in 9 saved archives. The final token has tag 23 and holds a signed 64-bit integer.

| Name | Integer values |
| --- | --- |
| `SCULPT_TOOL_BODY` | 354, 275 |
| `SCULPT_WORKPLANE_TOOL` | 282, -282 |

The value -282 shows that the integer is signed. The same files hold `name_attrib-gen-attrib` records on edges with the names `sb_cvtycheck_edge` and `sb_split_edge`.

Both kinds hold four tag 21 action values before the name. The 64-bit kind always holds 2, 1, 1, 2. The name kind always holds 2, 3, 1, 2.

Kit had no reader for either kind. The journal writer had no branch for tag 23.

## Workaround

Decode both kinds as `NameAttrib`. A null `NumberValue` selects the name kind. Qualify the action values against the kind. Write tag 23 with the signed 64-bit range only. Keep the 32-bit check for tags 4, 12 and 21.

The 9 boundary fill archives then failed on edges with three coedges. They read after the edge ring change in [StructureEdgeRing.md](StructureEdgeRing.md).

## Evidence

- [Journal attribute evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalAttributes/Evidence.json)
- [Earlier tag 23 study](../../../../../re/Fusion/Study/asm-int64-investigation.json)
- [Saved archive tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/JournalAttributeTests.py)
