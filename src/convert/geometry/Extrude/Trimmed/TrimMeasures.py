from math import (
    dist as Distance,
    fsum as SumFloats,
    isfinite as IsFinite,
    sin as SineValue,
)

from convert.geometry.Extrude.Trimmed.TrimOperand import KTrimUse
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# the stable circular segment integral avoids cancellation for shallow arcs
def ArcArea(ArcValue: ArcGeometry) -> float:
    AngleSpan = ArcValue.end_angle - ArcValue.start_angle
    if AngleSpan >= 0.01:
        return (
            ArcValue.radius
            * (ArcValue.radius * (AngleSpan - SineValue(AngleSpan)))
            / 2.0
        )
    Square = AngleSpan * AngleSpan
    Ratio = 1.0 / 6.0 - Square * (
        1.0 / 120.0 - Square * (1.0 / 5040.0 - Square / 362880.0)
    )
    RadiusSpan = ArcValue.radius * AngleSpan
    return RadiusSpan * (RadiusSpan * AngleSpan * Ratio) / 2.0


# green area decomposes into a translated chord polygon and exact circular segments
def MeasureTrim(
    Points: tuple[PlaneVector, ...], RingUses: tuple[KTrimUse, ...]
) -> tuple[float, float]:
    Origin = Points[0]
    Chords = (
        (
            (First.x - Origin.x) * (Second.y - Origin.y)
            - (First.y - Origin.y) * (Second.x - Origin.x)
        )
        / 2.0
        for First, Second in zip(Points, Points[1:] + Points[:1])
    )
    Bulges = (
        (-1.0 if Reversed else 1.0) * ArcArea(PartValue.Geometry)
        for PartValue, Reversed in RingUses
        if isinstance(PartValue.Geometry, ArcGeometry)
    )
    Lengths = (
        (
            PartValue.Geometry.radius
            * (PartValue.Geometry.end_angle - PartValue.Geometry.start_angle)
            if isinstance(PartValue.Geometry, ArcGeometry)
            else Distance(
                (PartValue.Start.x, PartValue.Start.y),
                (PartValue.Finish.x, PartValue.Finish.y),
            )
        )
        for PartValue, _ in RingUses
    )
    try:
        AreaValue, Length = SumFloats((*Chords, *Bulges)), SumFloats(Lengths)
    except (ValueError, OverflowError) as ErrorInfo:
        raise ValueError(
            "Extrude trim profile measures exceed floating range"
        ) from ErrorInfo
    if not (
        IsFinite(AreaValue) and AreaValue != 0.0 and IsFinite(Length) and Length > 0.0
    ):
        raise ValueError("Extrude trim requires positive finite profile measures")
    return AreaValue, Length
