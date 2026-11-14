# Material texture lists use a one-byte count

Other material lists start with a four-byte count.
A `TextureURI` value starts with a one-byte count instead.
Each text after it has the usual four-byte length.

A reader that expects a four-byte count fails on 43 textured library appearances.
They include rubbers, many woods, fabrics, leather, paper, foams, rough steels and CFRP.

A `Distance` value uses the same layout as a `Float` with a unit.
A `PropertyAlias` field has no stored record.

Kit reads and re-writes all 356 sweep packages with these rules.
Kit does not yet write textures.
The [family notes](../../../../../re/Fusion/Reconstruction/Materials/FamilyNotes.md) record the trace.
