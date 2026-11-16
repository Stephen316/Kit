from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Fields.XferChildSetMut import XferChildSetMut
from convert.Formats.Fusion.GraphicsCodec.Values.XferTargetMut import XferTargetMut

from convert.Formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# the transfer override contract needs a shared interpretation so display geometry retains its entity and scene relationships
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
