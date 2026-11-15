from collections.abc import Sequence

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


def DotProduct(First: Sequence[float], Second: Sequence[float]) -> float:
    return sum(
        LeftValue * RightValue
        for LeftValue, RightValue in zip(First, Second, strict=True)
    )


def CrossProduct(First: Sequence[float], Second: Sequence[float]) -> KJournalVector:
    return (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )
