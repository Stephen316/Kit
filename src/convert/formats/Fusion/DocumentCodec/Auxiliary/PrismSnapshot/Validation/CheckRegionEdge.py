from math import dist as Distance

from convert.formats.Fusion.BrepCodec.Prism.Validation.PrismNumbers import (
    CheckReal,
    CheckVector,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import (
    RegionEdge,
)


def CheckRegionEdge(
    Value: RegionEdge,
    StartPoint: tuple[float, float, float],
    EndPoint: tuple[float, float, float],
) -> None:
    CheckReal(Value.LowerParam)
    CheckReal(Value.UpperParam)
    if not Value.LowerParam < Value.UpperParam:
        raise ValueError("Snapshot region edge interval must increase")
    CheckVector(Value.Curve.OriginCm)
    CheckVector(Value.Curve.DirectionCm)
    if (Value.Curve.LowerBound is None) != (Value.Curve.UpperBound is None):
        raise ValueError("One-sided snapshot curve bounds are unsupported")
    for Bound, Parameter, Point in zip(
        (Value.Curve.LowerBound, Value.Curve.UpperBound),
        (Value.LowerParam, Value.UpperParam),
        (StartPoint, EndPoint),
        strict=True,
    ):
        if Bound is not None:
            CheckReal(Bound)
            if Bound != Parameter:
                raise ValueError("Snapshot curve bounds disagree with its edge")
        Position = tuple(
            Origin + Parameter * Direction
            for Origin, Direction in zip(
                Value.Curve.OriginCm, Value.Curve.DirectionCm, strict=True
            )
        )
        if not Distance(Position, Point) <= 1e-8:
            raise ValueError("Snapshot curve endpoints disagree with its vertices")
