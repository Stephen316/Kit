from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Fields.XferAttrMut import XferAttrMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferSetBaseMut(State: SceneCodec, Value: SceneSet | None, SetKind: int) -> SceneSet:
    FlagsValue = State.Integer(Value.FlagsValue if Value else None)
    RemovedFlags = State.Integer(Value.RemovedFlags if Value else None)
    AppendCount = State.CountValue(len(Value.AppendTypes) if Value else None)
    AppendTypes = tuple(
        State.Integer(Value.AppendTypes[Index] if Value else None)
        for Index in range(AppendCount)
    )
    AttrCount = State.CountValue(len(Value.Attributes) if Value else None, "<i")
    Attributes = tuple(
        XferAttrMut(State, Value.Attributes[Index] if Value else None)
        for Index in range(AttrCount)
    )
    return SceneSet(SetKind, FlagsValue, RemovedFlags, AppendTypes, Attributes)
