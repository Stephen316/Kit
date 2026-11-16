from math import isfinite as IsFinite

from convert.Formats.Fusion.BrepCodec.Journal.Round.CheckRoundFrame import (
    CheckRoundFrame,
)
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode


# invalid round node input must fail here so topology changes retain their native revision relationships
def CheckRoundNode(Value: SphereNode | TorusNode) -> None:
    Radii: tuple[float, ...]
    if isinstance(Value, SphereNode):
        Radii = (Value.RadiusCm,)
        AxisVector = Value.PoleDirection
    else:
        Radii = (Value.MajorRadiusCm, Value.MinorRadiusCm)
        AxisVector = Value.AxisVector
    CheckRoundFrame(Value.CenterCm, AxisVector, Value.ReferenceAxis)
    if (
        any(
            type(Radius) not in (int, float) or not IsFinite(Radius) for Radius in Radii
        )
        or Radii[0] <= 0
        or Radii[-1] == 0
    ):
        raise ValueError("Fusion round carriers require positive finite radii")
    if isinstance(Value, TorusNode) and Value.MajorRadiusCm == abs(Value.MinorRadiusCm):
        raise ValueError("Fusion horn-torus carriers are not qualified")
    for Bound in (Value.ULower, Value.UUpper, Value.VLower, Value.VUpper):
        if Bound is not None and (
            type(Bound) not in (int, float) or not IsFinite(Bound)
        ):
            raise ValueError("Fusion round carrier bounds must be finite")
    if type(Value.ReversedV) is not bool:
        raise ValueError("Fusion round carrier V direction must be boolean")
