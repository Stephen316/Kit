from dataclasses import dataclass as MakeDataClass
from math import (
    cos as Cosine,
    dist as Distance,
    isfinite as IsFinite,
    sin as SineValue,
    tau as FullTurn,
)
from typing import cast as CastValue

from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# each analytic carrier needs endpoints available independently of its eventual loop direction
@MakeDataClass(frozen=True, slots=True)
class TrimOperand:
    Geometry: LineGeometry | ArcGeometry
    Start: PlaneVector
    Finish: PlaneVector


# oriented uses leave the source curve parameterization unchanged
KTrimUse = tuple[TrimOperand, bool]


# bounded operands reject full turns and singular or nonfinite endpoint calculations
def ReadOperand(Geometry: LineGeometry | ArcGeometry) -> TrimOperand:
    if isinstance(Geometry, LineGeometry):
        Start, Finish = Geometry.start, Geometry.end
    elif isinstance(CastValue(object, Geometry), ArcGeometry):
        Center = Geometry.center
        Radius = Geometry.radius
        Lower, Upper = Geometry.start_angle, Geometry.end_angle
        if (
            not all(map(IsFinite, (Center.x, Center.y, Radius, Lower, Upper)))
            or Radius <= 0.0
            or not 0.0 < Upper - Lower < FullTurn
        ):
            raise ValueError(
                "Extrude arc requires a finite positive radius and bounded turn"
            )
        Start, Finish = (
            PlaneVector(
                Center.x + Radius * Cosine(Angle), Center.y + Radius * SineValue(Angle)
            )
            for Angle in (Lower, Upper)
        )
    else:
        raise ValueError("Extrude trim requires line or circular arc geometry")
    Endpoints = ((Start.x, Start.y), (Finish.x, Finish.y))
    if not all(IsFinite(Value) for Point in Endpoints for Value in Point) or not (
        0.0 < Distance(*Endpoints) < float("inf")
    ):
        raise ValueError("Extrude trim requires finite distinct endpoints")
    return TrimOperand(Geometry, Start, Finish)
