from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Schema.AttrRules import KAttrRules
from convert.formats.Fusion.GraphicsCodec.Schema.VersionRules import KVersionRules
from convert.formats.Fusion.GraphicsCodec.Fields.XferFieldsMut import XferFieldsMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferAttrMut(
    State: SceneCodec, Value: GraphicAttr[SceneSet] | None
) -> GraphicAttr[SceneSet]:
    ClassName = State.TextValue(Value.ClassName if Value else None)
    Rules = KAttrRules.get(ClassName)
    if Rules is None:
        raise ValueError(f"Unsupported graphics attribute class: {ClassName}")
    if ClassName in {Versioned for Versioned, _ in KVersionRules}:
        if State.Globals is None:
            raise ValueError("Graphics attribute precedes its serializer version")
        Version = dict(State.Globals.Versions)[ClassName]
        Rules = KVersionRules.get((ClassName, Version), Rules)
    Priority = State.Integer(Value.Priority if Value else None, "<i")
    WinTies = State.IsFlag(Value.WinTies if Value else None)
    Fields = XferFieldsMut(State, Rules, Value.Fields if Value else None)
    return GraphicAttr(ClassName, Priority, WinTies, Fields)
