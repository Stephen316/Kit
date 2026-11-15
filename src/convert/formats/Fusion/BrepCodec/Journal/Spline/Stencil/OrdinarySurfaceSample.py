from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


def OrdinarySample(
    Values: list[float],
    RisingU: list[float],
    RisingV: list[float],
    Poles: tuple[KJournalVector, ...],
) -> tuple[KJournalVector, KJournalVector, KJournalVector]:
    PointValue = [0.0, 0.0, 0.0]
    AlongU = [0.0, 0.0, 0.0]
    AlongV = [0.0, 0.0, 0.0]
    for Place, PoleValue in enumerate(Poles):
        for AxisIndex in range(3):
            PointValue[AxisIndex] += Values[Place] * PoleValue[AxisIndex]
            AlongU[AxisIndex] += RisingU[Place] * PoleValue[AxisIndex]
            AlongV[AxisIndex] += RisingV[Place] * PoleValue[AxisIndex]
    return (
        CastValue(KJournalVector, tuple(PointValue)),
        CastValue(KJournalVector, tuple(AlongU)),
        CastValue(KJournalVector, tuple(AlongV)),
    )
