from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)


def IsFiniteValue(Value: object) -> bool:
    return type(Value) in (int, float) and IsFinite(CastValue(float, Value))


def CheckOffset(Feature: OffsetSpec) -> None:
    if not IsFiniteValue(CastValue(object, Feature.DistanceMm)):
        raise ValueError("Fusion offset distances must be finite numbers")
    if Feature.DistanceMm == 0:
        raise ValueError("Fusion offset distances must not be zero")
    SideValue = CastValue(object, Feature.SideMm)
    if SideValue is None:
        return
    if not isinstance(SideValue, tuple):
        raise ValueError("Fusion offset sides require two planar coordinates")
    Values = CastValue(tuple[object, ...], SideValue)
    if len(Values) != 2 or not all(IsFiniteValue(Value) for Value in Values):
        raise ValueError("Fusion offset sides require two planar coordinates")
