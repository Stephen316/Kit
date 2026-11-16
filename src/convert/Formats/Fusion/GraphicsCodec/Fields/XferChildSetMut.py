from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Fields.XferSetBaseMut import XferSetBaseMut

from convert.Formats.Fusion.GraphicsCodec.Model.Values.AppliedSet import AppliedSet
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# the transfer child set contract needs a shared interpretation so display geometry retains its entity and scene relationships
def XferChildSetMut(
    State: SceneCodec, Value: AppliedSet[SceneSet] | None
) -> AppliedSet[SceneSet]:
    IsSpecific = State.IsFlag(Value is not None and Value.ApplyTypes is not None)
    SetValue = XferSetBaseMut(State, Value.SetValue if Value else None, 2)
    ApplyTypes = None
    if IsSpecific:
        Values = Value.ApplyTypes if Value else None
        Count = State.CountValue(len(Values) if Values is not None else None)
        ApplyTypes = tuple(
            State.Integer(Values[Index] if Values is not None else None)
            for Index in range(Count)
        )
    return AppliedSet(SetValue, ApplyTypes)
