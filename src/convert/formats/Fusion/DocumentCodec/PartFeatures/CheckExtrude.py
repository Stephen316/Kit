from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)

KCurveLimit = 64


def IsNumber(Value: object) -> bool:
    return type(Value) in (int, float) and IsFinite(CastValue(float, Value))


def CurveNumbers(Curve: object) -> tuple[object, ...]:
    if isinstance(Curve, LineCurve):
        return (*Curve.StartMm, *Curve.FinishMm)
    if isinstance(Curve, ArcCurve):
        return (*Curve.CenterMm, Curve.RadiusMm, Curve.StartDegrees, Curve.SweepDegrees)
    if isinstance(Curve, CircleCurve):
        return (*Curve.CenterMm, Curve.RadiusMm)
    raise ValueError("Unsupported Fusion sketch profile curve")


def CheckCurve(Curve: object) -> None:
    Numbers = CurveNumbers(Curve)
    if not all(IsNumber(Value) for Value in Numbers):
        raise ValueError("Fusion sketch curve values must be finite numbers")
    if isinstance(Curve, LineCurve) and Curve.StartMm == Curve.FinishMm:
        raise ValueError("Fusion sketch lines must have length")
    if isinstance(Curve, (ArcCurve, CircleCurve)) and Curve.RadiusMm <= 0:
        raise ValueError("Fusion sketch arcs must have a positive radius")
    if isinstance(Curve, ArcCurve) and not 0 < abs(Curve.SweepDegrees) < 360:
        raise ValueError("Fusion sketch arcs must sweep less than a full turn")


def CheckExtrude(Feature: ExtrudeSpec) -> None:
    Profile = CastValue(object, Feature.Profile)
    if not isinstance(Profile, tuple):
        raise ValueError("Fusion extrude profiles must be tuples")
    if not 0 < len(Feature.Profile) <= KCurveLimit:
        raise ValueError("Fusion extrude profiles need between one and 64 curves")
    for Curve in Feature.Profile:
        CheckCurve(Curve)
    Circles = sum(isinstance(Curve, CircleCurve) for Curve in Feature.Profile)
    if Circles and len(Feature.Profile) != 1:
        raise ValueError("Fusion extrude circle profiles must stand alone")
    if Feature.Operation not in ("new", "join", "cut", "intersect"):
        raise ValueError("Unsupported Fusion extrude operation")
    if Feature.Extent not in ("one", "flip", "symmetric", "two"):
        raise ValueError("Unsupported Fusion extrude extent")
    Amounts = (Feature.DistanceMm, Feature.AgainstMm)
    if not all(IsNumber(Value) for Value in Amounts) or Feature.DistanceMm <= 0:
        raise ValueError("Fusion extrude distances must be finite and positive")
    if (Feature.Extent == "two") != (Feature.AgainstMm > 0):
        raise ValueError("Fusion extrude second distances belong to two-sided extents")
    for TextValue in (Feature.SketchName, Feature.FeatureName):
        if not isinstance(CastValue(object, TextValue), str) or not TextValue:
            raise ValueError("Invalid Fusion extrude name")
        if len(TextValue) > 1024 or "\x00" in TextValue:
            raise ValueError("Invalid Fusion extrude name")
