from math import dist as Distance

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismEdge import PrismEdge
from convert.formats.Fusion.BrepCodec.Prism.Validation.PrismNumbers import (
    CheckReal,
    CheckVector,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
)


def CheckPrismEdge(
    Value: PrismEdge, Index: int, Corners: tuple[tuple[float, float, float], ...]
) -> None:
    if type(Value.StartCorner) is not int or type(Value.EndCorner) is not int:
        raise ValueError("Prism edge corner identities must be integers")
    if (Value.StartCorner, Value.EndCorner) not in (
        KEdgeCorners[Index],
        KEdgeCorners[Index][::-1],
    ):
        raise ValueError("Prism edge corners disagree with its geometric role")
    if type(Value.OwnerFace) is not int or not 0 <= Value.OwnerFace < 6:
        raise ValueError("Invalid prism edge owner face")
    if not {Value.StartCorner, Value.EndCorner} <= set(KFaceCorners[Value.OwnerFace]):
        raise ValueError("Prism edge owner face is not incident")
    CheckReal(Value.LowerParam)
    CheckReal(Value.UpperParam)
    if not Value.LowerParam < Value.UpperParam:
        raise ValueError("Prism edge interval must increase")
    CheckVector(Value.Curve.OriginCm)
    CheckVector(Value.Curve.DirectionCm)
    if (Value.Curve.LowerBound is None) != (Value.Curve.UpperBound is None):
        raise ValueError("One-sided prism curve bounds are unsupported")
    for Bound, Parameter, Corner in zip(
        (Value.Curve.LowerBound, Value.Curve.UpperBound),
        (Value.LowerParam, Value.UpperParam),
        (Value.StartCorner, Value.EndCorner),
        strict=True,
    ):
        if Bound is not None:
            CheckReal(Bound)
            if Bound != Parameter:
                raise ValueError("Prism curve bounds disagree with its edge")
        Position = tuple(
            Origin + Parameter * Direction
            for Origin, Direction in zip(
                Value.Curve.OriginCm, Value.Curve.DirectionCm, strict=True
            )
        )
        if not Distance(Position, Corners[Corner]) <= 1e-8:
            raise ValueError("Prism curve endpoints disagree with its corners")
