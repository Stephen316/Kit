from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec

# draft limit needs one explicit bound so parametric feature reconstruction cannot accept inconsistent resource or layout limits
KDraftLimit = 45.0


# invalid draft input must fail here so feature parameters remain connected to the resulting geometry
def CheckDraft(Feature: DraftSpec) -> None:
    Angle = CastValue(object, Feature.AngleDegrees)
    if type(Angle) not in (int, float) or not IsFinite(CastValue(float, Angle)):
        raise ValueError("Fusion draft angles must be finite numbers")
    if not 0.0 < abs(Feature.AngleDegrees) < KDraftLimit:
        raise ValueError("Fusion draft angles must lie between 0 and 45 degrees")
