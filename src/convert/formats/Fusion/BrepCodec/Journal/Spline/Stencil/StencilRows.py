from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.CheckGridCage import (
    KWeightSlack,
)
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip

# the stencil row shape must stay shared so spline stencil reconstruction uses one contract for compatible values
KStencilRow = tuple[tuple[int, float], ...]

# the homogeneous shape must stay shared so spline stencil reconstruction uses one contract for compatible values
KHomogeneous = tuple[float, float, float, float]


# stencil rows needs an explicit state contract so control cage contributions retain their intended weights
@MakeDataClass(frozen=True, slots=True)
class StencilRows:
    Points: tuple[KJournalVector, ...]
    Homogeneous: tuple[KHomogeneous, ...]
    Weighted: tuple[bool, ...]


# the row point contract needs a shared interpretation so control cage contributions retain their intended weights
def RowPoint(RowValue: KStencilRow, Grips: tuple[ControlGrip, ...]) -> KJournalVector:
    return (
        sum(Value * Grips[Index].CoordX for Index, Value in RowValue),
        sum(Value * Grips[Index].CoordY for Index, Value in RowValue),
        sum(Value * Grips[Index].CoordZ for Index, Value in RowValue),
    )


# row mass needs an explicit validity boundary so control cage contributions retain their intended weights
def RowMass(
    RowValue: KStencilRow, Grips: tuple[ControlGrip, ...], Point: KJournalVector
) -> KHomogeneous:
    MassValue = sum(Value * Grips[Index].Weight for Index, Value in RowValue)
    if not MassValue > 0.0:
        raise ValueError("Fusion Form stencil produced a non-positive pole weight")
    return (Point[0], Point[1], Point[2], MassValue)


# the weighted decision must stay consistent so control cage contributions retain their intended weights
def IsWeighted(RowValue: KStencilRow, Grips: tuple[ControlGrip, ...]) -> bool:
    return any(abs(Grips[Index].Weight - 1.0) > KWeightSlack for Index, _ in RowValue)


# the evaluate rows contract needs a shared interpretation so control cage contributions retain their intended weights
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


# the cartesian contract needs a shared interpretation so control cage contributions retain their intended weights
def Cartesian(Value: KHomogeneous) -> KJournalVector:
    return (Value[0] / Value[3], Value[1] / Value[3], Value[2] / Value[3])


# pick point must resolve unambiguously so control cage contributions retain their intended weights
def PickPoint(Values: StencilRows, Index: int) -> KJournalVector:
    if Values.Weighted[Index]:
        return Cartesian(Values.Homogeneous[Index])
    return Values.Points[Index]
