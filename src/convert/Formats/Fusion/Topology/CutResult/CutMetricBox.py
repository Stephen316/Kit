from dataclasses import dataclass as MakeDataClass
from math import isclose as IsClose
from typing import TypeAlias

from convert.Formats.Fusion.Topology.AsmEdge.AsmPoints import KAsmMatchTol
from convert.Formats.Fusion.Topology.CutResult.ResultBounds import ResultBounds
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector

# each corner chooses the lower or upper endpoint independently on the three axes
KBoxCorner: TypeAlias = tuple[bool, bool, bool]


# coordinate tuples keep axes addressable when the saved support rotates
def AxisValues(Point: SpaceVector) -> tuple[float, float, float]:
    return Point.x, Point.y, Point.z


# exact saved vertices must supply every corner of each physical box
@MakeDataClass(frozen=True, slots=True)
class CutMetricBox:
    Lower: tuple[float, float, float]
    Upper: tuple[float, float, float]
    Corners: dict[KBoxCorner, int]


# use the carrier tolerance to absorb repeated representations of the same coordinate
def BoxEnd(Value: float, Lower: float, Upper: float) -> bool | None:
    if IsClose(Value, Lower, rel_tol=0.0, abs_tol=KAsmMatchTol):
        return False
    if IsClose(Value, Upper, rel_tol=0.0, abs_tol=KAsmMatchTol):
        return True
    return None


# a duplicate coordinate cannot replace a distinct corner in the saved topology
def ReadMetricBox(
    Points: dict[int, SpaceVector], Bounds: BoundingBox
) -> tuple[CutMetricBox, dict[int, SpaceVector]]:
    Lower, Upper = AxisValues(Bounds.minimum), AxisValues(Bounds.maximum)
    if any(
        EndValue - Start <= 2 * KAsmMatchTol
        for Start, EndValue in zip(Lower, Upper, strict=True)
    ):
        raise ValueError("Fusion Cut mass box is degenerate")
    Corners: dict[KBoxCorner, int] = {}
    Other: dict[int, SpaceVector] = {}
    for Identity, Point in Points.items():
        First, Second, Third = tuple(
            BoxEnd(Value, Start, EndValue)
            for Value, Start, EndValue in zip(
                AxisValues(Point), Lower, Upper, strict=True
            )
        )
        if First is None or Second is None or Third is None:
            Other[Identity] = Point
            continue
        Corner = (First, Second, Third)
        if Corner in Corners:
            raise ValueError("Fusion Cut mass box repeats a native corner")
        Corners[Corner] = Identity
    if len(Corners) != 8:
        raise ValueError("Fusion Cut mass box lacks complete native corners")
    return CutMetricBox(Lower, Upper, Corners), Other


# the verified result can expose mass only when its vertex inventory closes two boxes
def ReadCutBoxes(
    Points: dict[int, SpaceVector], Bounds: BoundingBox
) -> tuple[CutMetricBox, CutMetricBox]:
    Outer, Remaining = ReadMetricBox(Points, Bounds)
    if len(Remaining) != 8:
        raise ValueError("Fusion Cut mass requires eight separate cavity vertices")
    Inner, Other = ReadMetricBox(Remaining, ResultBounds(Remaining))
    if Other:
        raise ValueError("Fusion Cut mass cavity has unowned vertices")
    return Outer, Inner
