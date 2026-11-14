from math import isfinite as IsFinite, sqrt as SquareRoot

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


def Subtract(First: KJournalVector, Second: KJournalVector) -> KJournalVector:
    return First[0] - Second[0], First[1] - Second[1], First[2] - Second[2]


def DotProduct(First: KJournalVector, Second: KJournalVector) -> float:
    return sum(
        FirstVal * SecondVal for FirstVal, SecondVal in zip(First, Second, strict=True)
    )


def CrossProduct(First: KJournalVector, Second: KJournalVector) -> KJournalVector:
    return (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )


def Normalize(Value: KJournalVector) -> KJournalVector:
    Length = SquareRoot(DotProduct(Value, Value))
    if not IsFinite(Length) or Length < 1e-12:
        raise ValueError("Degenerate Fusion planar carrier direction")
    return Value[0] / Length, Value[1] / Length, Value[2] / Length
