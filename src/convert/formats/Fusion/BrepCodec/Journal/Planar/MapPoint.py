from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)


def MapPoint(Value: TransformNode, Point: KJournalVector) -> KJournalVector:
    Coordinates = tuple(
        Value.ScaleFactor
        * (
            Point[0] * Value.ColumnX[Index]
            + Point[1] * Value.ColumnY[Index]
            + Point[2] * Value.ColumnZ[Index]
        )
        + Value.TranslationCm[Index]
        for Index in range(3)
    )
    return Coordinates[0], Coordinates[1], Coordinates[2]
