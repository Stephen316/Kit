from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


def CheckRoundFrame(
    Center: KJournalVector, AxisVector: KJournalVector, Reference: KJournalVector
) -> None:
    Vectors = (Center, AxisVector, Reference)
    if any(type(Vector) is not tuple or len(Vector) != 3 for Vector in Vectors):
        raise ValueError("Fusion round carrier requires immutable three-vectors")
    if any(
        type(Value) not in (int, float) or not IsFinite(Value)
        for Vector in Vectors
        for Value in Vector
    ):
        raise ValueError("Fusion round carrier frame must be finite")
    if any(
        abs(sum(Value * Value for Value in Vector) - 1.0) > 1e-8
        for Vector in (AxisVector, Reference)
    ):
        raise ValueError("Fusion round carrier axes must be unit length")
    if (
        abs(
            sum(
                First * Second
                for First, Second in zip(AxisVector, Reference, strict=True)
            )
        )
        > 1e-8
    ):
        raise ValueError("Fusion round carrier axes must be perpendicular")
