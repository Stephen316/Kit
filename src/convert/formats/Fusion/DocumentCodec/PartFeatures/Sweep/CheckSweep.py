from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.CheckExtrude import (
    KCurveLimit,
    CheckCurve,
    IsNumber,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)


def CheckSweepNames(Feature: SweepSpec) -> None:
    for TextValue in (Feature.ProfileName, Feature.PathName, Feature.FeatureName):
        if not isinstance(CastValue(object, TextValue), str) or not TextValue:
            raise ValueError("Invalid Fusion sweep name")
        if len(TextValue) > 1024 or "\x00" in TextValue:
            raise ValueError("Invalid Fusion sweep name")


def CheckSweep(Feature: SweepSpec) -> None:
    CheckSweepNames(Feature)
    Amounts = (Feature.LeftMm, Feature.RightMm, Feature.LowerMm, Feature.UpperMm)
    if not all(IsNumber(CastValue(object, Value)) for Value in Amounts):
        raise ValueError("Fusion sweep profile values must be finite numbers")
    if not Feature.LeftMm < Feature.RightMm:
        raise ValueError("Fusion sweep profiles must have width")
    if not Feature.LowerMm < Feature.UpperMm:
        raise ValueError("Fusion sweep profiles must have height")
    PathValue = CastValue(object, Feature.Path)
    if not isinstance(PathValue, tuple):
        raise ValueError("Fusion sweep paths must be tuples")
    if not 0 < len(Feature.Path) <= KCurveLimit:
        raise ValueError("Fusion sweep paths need between one and 64 curves")
    for Curve in Feature.Path:
        if not isinstance(CastValue(object, Curve), (LineCurve, ArcCurve)):
            raise ValueError("Fusion sweep paths hold lines and arcs")
        CheckCurve(Curve)
