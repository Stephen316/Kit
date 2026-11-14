from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.CheckExtrude import (
    CheckExtrude,
    IsNumber,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec


def CheckLoftNames(Feature: LoftSpec) -> None:
    Names = (
        Feature.LowerName,
        Feature.PlaneName,
        Feature.UpperName,
        Feature.FeatureName,
    )
    for TextValue in Names:
        if not isinstance(CastValue(object, TextValue), str) or not TextValue:
            raise ValueError("Invalid Fusion loft name")
        if len(TextValue) > 1024 or "\x00" in TextValue:
            raise ValueError("Invalid Fusion loft name")


def CheckLoft(Feature: LoftSpec) -> None:
    CheckLoftNames(Feature)
    if not IsNumber(CastValue(object, Feature.HeightMm)) or Feature.HeightMm <= 0:
        raise ValueError("Fusion loft heights must be finite and positive")
    Profiles = (Feature.LowerProfile, Feature.UpperProfile)
    if not all(isinstance(CastValue(object, Profile), tuple) for Profile in Profiles):
        raise ValueError("Fusion loft profiles must be tuples")
    for Profile in Profiles:
        CheckExtrude(ExtrudeSpec(Profile, Feature.HeightMm))
        if any(isinstance(Curve, ArcCurve) for Curve in Profile):
            raise ValueError("Fusion loft profiles hold straight lines or one circle")
    if len(Feature.LowerProfile) != len(Feature.UpperProfile):
        raise ValueError("Fusion loft profiles need the same number of curves")
