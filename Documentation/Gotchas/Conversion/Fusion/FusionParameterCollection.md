# Fusion parameter collection identities

The supported sample files often use parameter collection identity 16.
That value is an object identity, not an immutable numeric-record trailer.

The footer contains one zero byte followed by an eleven-byte local reference.
Its `u64` identifies the owning collection.
The previous numeric reader compared the whole footer against bytes containing identity 16.
That comparison rejected otherwise framed records owned by another collection.

Decode the reference and retain its identity.
Verify the target collection class, membership, and reciprocal name registry before claiming complete semantic proof.
Do not accept arbitrary footer bytes or infer expression dependencies from collection membership.

The existing [membership checker](../../../../src/convert/formats/Fusion/FormulaDeps/ScopedParams.py) independently establishes the footer relationship.
See the [data model](../../../Reference/Research/FusionDataModel.md#numeric-parameter) for the exact layout.
