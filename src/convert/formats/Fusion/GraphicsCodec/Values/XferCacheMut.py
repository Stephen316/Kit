from __future__ import annotations
from typing import TYPE_CHECKING

from convert.formats.Fusion.GraphicsCodec.Model.Values.CacheData import CacheData

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferCacheMut(State: SceneCodec, Value: CacheData | None) -> CacheData:
    ModeValue = State.Integer(Value.ModeValue if Value else None, "<i")
    if ModeValue not in range(7):
        raise ValueError("Unsupported graphics texture mapping mode")
    AxisValue = State.Vector(Value.AxisValue if Value else None, 3, "<d")
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    BakedMatrix = State.Vector(Value.BakedMatrix if Value else None, 16, "<d")
    MappingMatrix = State.Vector(Value.MappingMatrix if Value else None, 16, "<d")
    CylinderCap = (
        State.IsFlag(Value.CylinderCap if Value else None) if ModeValue == 4 else None
    )
    SquareCap = (
        State.IsFlag(Value.SquareCap if Value else None) if ModeValue == 4 else None
    )
    WoodOrigin = (
        State.Vector(Value.WoodOrigin if Value else None, 3, "<d")
        if ModeValue == 6
        else None
    )
    WoodAxis = (
        State.Vector(Value.WoodAxis if Value else None, 3, "<d")
        if ModeValue == 6
        else None
    )
    Result = CacheData(
        ModeValue,
        AxisValue,
        Bounds,
        BakedMatrix,
        MappingMatrix,
        CylinderCap,
        SquareCap,
        WoodOrigin,
        WoodAxis,
    )
    State.CheckResult(Value, Result)
    return Result
