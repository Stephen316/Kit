# Saved Fusion generic tags can own a nested tag with an empty identifier

## Expectation

An ASM custom attribute starts with a null attribute pointer. A generic tag attribute holds groups with a printable primary identifier. The owner of a generic tag is a topology entity.

## Actual behavior

Fusion move, split face and surface edit saves break all three rules. The census found 90 such parent tags in 18 saved archives.

| Record | Attribute pointer | Owner | Payload |
| --- | --- | --- | --- |
| Parent tag | Points to the child tag | Face (77) or body (13) | Normal tag groups |
| Child tag | Null | The parent tag | One group with an empty identifier |

The child group always has byte count 0, an empty primary identifier, secondary identifier 0, one operation identifier and approach 0. The operation identifiers are 302 to 307. The child sibling pointers are always null.

Kit rejected the parent with `ValueError("Unsupported Fusion journal qualified field")`. Kit rejected the child because `FeatureTag` refuses an empty primary identifier.

## Workaround

Keep `FeatureTag` strict. Decode only the exact child layout as `NestedTag`, which stores the owner and the operation identifier. Store the parent pointer in `TagAttrib.Attribute`. Allow a non-null attribute pointer only on a generic tag. `CheckNestTags` requires that the parent points to the child and that the child owner is the parent.

## Evidence

- [Journal attribute evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalAttributes/Evidence.json)
- [Earlier owner variant study](../../../../../re/Fusion/Study/attribute-owner-variant-decoding.json)
- [Saved archive tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/JournalAttributeTests.py)
