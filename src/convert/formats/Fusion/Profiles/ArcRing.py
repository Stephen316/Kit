from math import cos as Cosine, dist as Distance, isclose as IsClose
from math import (
    isfinite as IsFinite,
    pi as CirclePi,
    sin as SineValue,
    ulp as UnitPlace,
)

from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# profiles need the circular support evaluated at the original trim angles
def EvalArcPoint(ArcValue: ArcGeometry, Angle: float) -> PlaneVector:
    return PlaneVector(
        ArcValue.center.x + ArcValue.radius * Cosine(Angle),
        ArcValue.center.y + ArcValue.radius * SineValue(Angle),
    )


# a true diameter must close both ends of one whole semicircular arc
def CheckSemiRing(ArcValue: ArcGeometry, Diameter: LineGeometry) -> None:
    Angles = (ArcValue.start_angle, ArcValue.end_angle)
    Values = (ArcValue.center.x, ArcValue.center.y, ArcValue.radius, *Angles)
    if (
        not all(map(IsFinite, Values))
        or ArcValue.radius <= 0.0
        or not IsClose(Angles[1] - Angles[0], CirclePi, rel_tol=0.0, abs_tol=1e-10)
    ):
        raise ValueError("Fusion curved profile requires a semicircle")
    Start, Finish = (EvalArcPoint(ArcValue, Angle) for Angle in Angles)
    Endpoints = ((Diameter.start.x, Diameter.start.y), (Diameter.end.x, Diameter.end.y))
    ArcEnds = ((Start.x, Start.y), (Finish.x, Finish.y))
    Tolerance = max(1e-8, 8.0 * UnitPlace(max(map(abs, Values[:3]))))
    if (
        not all(IsFinite(Value) for Point in (*ArcEnds, *Endpoints) for Value in Point)
        or Distance(*Endpoints) <= Tolerance
        or not any(
            all(
                Distance(First, Second) <= Tolerance
                for First, Second in zip(ArcEnds, Order)
            )
            for Order in (Endpoints, Endpoints[::-1])
        )
    ):
        raise ValueError("Fusion semicircle diameter does not close the arc endpoints")
