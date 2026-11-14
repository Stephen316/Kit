from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.CheckExtrude import IsNumber
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)

KAngleLimit = 360.0


def CheckRevolve(Feature: RevolveSpec) -> None:
    Amounts = (
        Feature.InnerMm,
        Feature.OuterMm,
        Feature.LowerMm,
        Feature.UpperMm,
        Feature.AngleDegrees,
    )
    if not all(IsNumber(CastValue(object, Value)) for Value in Amounts):
        raise ValueError("Fusion revolve values must be finite numbers")
    if not 0 < Feature.InnerMm < Feature.OuterMm:
        raise ValueError("Fusion revolve profiles must stay clear of the axis")
    if not Feature.LowerMm < Feature.UpperMm:
        raise ValueError("Fusion revolve profiles must have height")
    if not 0 < Feature.AngleDegrees <= KAngleLimit:
        raise ValueError("Fusion revolve angles must lie in one turn")
    if Feature.Operation not in ("new", "join", "cut"):
        raise ValueError("Unsupported Fusion revolve operation")
    for TextValue in (Feature.SketchName, Feature.FeatureName):
        if not isinstance(CastValue(object, TextValue), str) or not TextValue:
            raise ValueError("Invalid Fusion revolve name")
        if len(TextValue) > 1024 or "\x00" in TextValue:
            raise ValueError("Invalid Fusion revolve name")
