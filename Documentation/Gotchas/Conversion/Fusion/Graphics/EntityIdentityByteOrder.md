# OGS entity identities use explicit big-endian bytes

Most OGS fixed-width values are little endian. Applying that rule to `EntityID` or `ACTEntityID` consumes the expected eight bytes but produces an unrelated entity identity.

Read in big-endian numeric order, the identities in the two decoded graphics controls resolve to entities in the document graph. Segment IDs remain ordinary little-endian uint32 values.

Decode the two identity fields with their explicit order and resolve the resulting segment/object pair against the document graph. The [wire model](../../../../../re/Fusion/Reconstruction/OgsScene/WireModel.md) distinguishes these from float64 qualifiers and serialization IDs.
