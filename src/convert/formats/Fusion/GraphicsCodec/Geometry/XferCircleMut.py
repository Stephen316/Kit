from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Values.CircleArcValue import (
    CircleArcValue,
)

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferCircleMut(State: SceneCodec, Value: CircleArcValue | None) -> CircleArcValue:
    Sampling = State.Integer(Value.Sampling if Value else None, "<i")
    Interval = State.Vector(Value.Interval if Value else None, 2, "<d")
    Radius = State.Scalar(Value.Radius if Value else None, "<d")
    Center = State.Vector(Value.Center if Value else None, 3, "<d")
    Normal = State.Vector(Value.Normal if Value else None, 3, "<d")
    StartAngle = State.Scalar(Value.StartAngle if Value else None, "<d")
    EndAngle = State.Scalar(Value.EndAngle if Value else None, "<d")
    ReferencePoint = State.Vector(Value.ReferencePoint if Value else None, 3, "<d")
    if Sampling <= 0 or Radius <= 0 or Interval[0] > Interval[1]:
        raise ValueError("Invalid graphics circle arc definition")
    return CircleArcValue(
        Sampling, Interval, Radius, Center, Normal, StartAngle, EndAngle, ReferencePoint
    )
