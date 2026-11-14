from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec


def CheckMove(Feature: MoveSpec) -> None:
    Offset = CastValue(object, Feature.OffsetMm)
    if not isinstance(Offset, tuple):
        raise ValueError("Fusion moves require three offset values")
    Values = CastValue(tuple[object, ...], Offset)
    if len(Values) != 3:
        raise ValueError("Fusion moves require three offset values")
    for Value in (*Values, CastValue(object, Feature.TurnDegrees)):
        if type(Value) not in (int, float) or not IsFinite(CastValue(float, Value)):
            raise ValueError("Fusion move values must be finite numbers")
    if not -360.0 < Feature.TurnDegrees < 360.0:
        raise ValueError("Fusion move turns must lie in one turn")
