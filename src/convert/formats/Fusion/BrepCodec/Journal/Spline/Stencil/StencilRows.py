from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.CheckGridCage import (
    KWeightSlack,
)
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip

KStencilRow = tuple[tuple[int, float], ...]
KHomogeneous = tuple[float, float, float, float]


@MakeDataClass(frozen=True, slots=True)
class StencilRows:
    Points: tuple[KJournalVector, ...]
    Homogeneous: tuple[KHomogeneous, ...]
    Weighted: tuple[bool, ...]


def RowPoint(RowValue: KStencilRow, Grips: tuple[ControlGrip, ...]) -> KJournalVector:
    return (
        sum(Value * Grips[Index].CoordX for Index, Value in RowValue),
        sum(Value * Grips[Index].CoordY for Index, Value in RowValue),
        sum(Value * Grips[Index].CoordZ for Index, Value in RowValue),
    )


def RowMass(
    RowValue: KStencilRow, Grips: tuple[ControlGrip, ...], Point: KJournalVector
) -> KHomogeneous:
    MassValue = sum(Value * Grips[Index].Weight for Index, Value in RowValue)
    if not MassValue > 0.0:
        raise ValueError("Fusion Form stencil produced a non-positive pole weight")
    return (Point[0], Point[1], Point[2], MassValue)


def IsWeighted(RowValue: KStencilRow, Grips: tuple[ControlGrip, ...]) -> bool:
    return any(abs(Grips[Index].Weight - 1.0) > KWeightSlack for Index, _ in RowValue)


def EvaluateRows(
    RowValues: tuple[KStencilRow, ...], Grips: tuple[ControlGrip, ...]
) -> StencilRows:
    Points = tuple(RowPoint(RowValue, Grips) for RowValue in RowValues)
    Weighted = tuple(IsWeighted(RowValue, Grips) for RowValue in RowValues)
    if not any(Weighted):
        return StencilRows(Points, (), Weighted)
    Masses = tuple(
        RowMass(RowValue, Grips, Point) for RowValue, Point in zip(RowValues, Points)
    )
    return StencilRows(Points, Masses, Weighted)


def Cartesian(Value: KHomogeneous) -> KJournalVector:
    return (Value[0] / Value[3], Value[1] / Value[3], Value[2] / Value[3])


def PickPoint(Values: StencilRows, Index: int) -> KJournalVector:
    if Values.Weighted[Index]:
        return Cartesian(Values.Homogeneous[Index])
    return Values.Points[Index]
