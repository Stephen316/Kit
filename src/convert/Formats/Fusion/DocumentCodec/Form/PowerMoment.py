from math import prod as Product

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# the power moment contract needs a shared interpretation so editable control cages retain their document relationships
def PowerMoment(
    Point: KJournalVector, Normal: KJournalVector, Powers: tuple[int, int, int]
) -> float:
    AxisIndex = next(Index for Index, Power in enumerate(Powers) if Power)
    return (
        Point[AxisIndex] ** (Powers[AxisIndex] + 1)
        * Normal[AxisIndex]
        * Product(
            Point[Index] ** Powers[Index] for Index in range(3) if Index != AxisIndex
        )
        / (Powers[AxisIndex] + 1)
    )
