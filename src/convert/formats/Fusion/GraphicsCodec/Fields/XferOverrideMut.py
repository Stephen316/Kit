from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Fields.XferChildSetMut import XferChildSetMut
from convert.formats.Fusion.GraphicsCodec.Values.XferTargetMut import XferTargetMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferOverrideMut(
    State: SceneCodec, Values: tuple[OverrideSet[SceneSet], ...] | None
) -> tuple[OverrideSet[SceneSet], ...]:
    Count = State.CountValue(len(Values) if Values is not None else None)
    Results: list[OverrideSet[SceneSet]] = []
    for Index in range(Count):
        Value = Values[Index] if Values is not None else None
        SetValue = XferChildSetMut(State, Value.SetValue if Value else None)
        Target = XferTargetMut(State, Value.Target if Value else None)
        ChildCount = State.CountValue(len(Value.ChildSets) if Value else None, "<i")
        Children = tuple(
            XferChildSetMut(State, Value.ChildSets[Number] if Value else None)
            for Number in range(ChildCount)
        )
        Results.append(OverrideSet(SetValue, Target, Children))
    Result = tuple(Results)
    State.CheckResult(Values, Result)
    return Result
