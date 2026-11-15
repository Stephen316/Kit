from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.OrdinarySurfaceSample import (
    OrdinarySample,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    BasisLevel,
    BasisSlope,
    MassFrame,
)


def SurfaceSample(
    Surface: NubsSurface,
    KnotsU: list[float],
    KnotsV: list[float],
    SpanU: int,
    SpanV: int,
    ParamU: float,
    ParamV: float,
) -> tuple[KJournalVector, KJournalVector, KJournalVector]:
    Width = len(KnotsU) - Surface.DegreeU - 1
    ValuesU = BasisLevel(KnotsU, SpanU, Surface.DegreeU, ParamU)
    SlopesU = BasisSlope(KnotsU, SpanU, Surface.DegreeU, ParamU)
    ValuesV = BasisLevel(KnotsV, SpanV, Surface.DegreeV, ParamV)
    SlopesV = BasisSlope(KnotsV, SpanV, Surface.DegreeV, ParamV)
    Window = [
        (RowIndex, ColumnIndex)
        for RowIndex in range(Surface.DegreeV + 1)
        for ColumnIndex in range(Surface.DegreeU + 1)
    ]
    StartU = SpanU - Surface.DegreeU
    StartV = SpanV - Surface.DegreeV
    Poles = tuple(
        Surface.Points[(StartV + RowIndex) * Width + StartU + ColumnIndex]
        for RowIndex, ColumnIndex in Window
    )
    Values = [
        ValuesU[ColumnIndex] * ValuesV[RowIndex] for RowIndex, ColumnIndex in Window
    ]
    RisingU = [
        SlopesU[ColumnIndex] * ValuesV[RowIndex] for RowIndex, ColumnIndex in Window
    ]
    RisingV = [
        ValuesU[ColumnIndex] * SlopesV[RowIndex] for RowIndex, ColumnIndex in Window
    ]
    if not Surface.Weights:
        return OrdinarySample(Values, RisingU, RisingV, Poles)
    IndexedPlaces = [
        (StartV + RowIndex) * Width + StartU + ColumnIndex
        for RowIndex, ColumnIndex in Window
    ]
    Weights = tuple(Surface.Weights[Place] for Place in IndexedPlaces)
    PointValue = MassFrame(Values, [0.0] * len(Values), Poles, Weights)[0]
    AlongU = MassFrame(Values, RisingU, Poles, Weights)[1]
    AlongV = MassFrame(Values, RisingV, Poles, Weights)[1]
    return (
        CastValue(KJournalVector, tuple(PointValue)),
        CastValue(KJournalVector, tuple(AlongU)),
        CastValue(KJournalVector, tuple(AlongV)),
    )
