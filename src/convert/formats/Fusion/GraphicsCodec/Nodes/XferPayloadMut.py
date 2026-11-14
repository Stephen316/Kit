from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferNodeMut import XferNodeMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferPayloadMut(State: SceneCodec, Value: NodePayload | None) -> NodePayload:
    Selector = State.Integer(Value.Selector if Value else None)
    DataValue, IsXref, ActEntity, InstanceId = None, None, None, None
    if Selector in (2, 3, 4, 5, 6, 7):
        DataValue = XferNodeMut(State, Value.DataValue if Value else None, True)
        if Selector == 4:
            IsXref = State.IsFlag(Value.IsXref if Value else None)
            if IsXref:
                ActEntity = State.Integer(Value.ActEntity if Value else None, ">Q")
            if State.ClassVersion("F360InstanceNode"):
                InstanceId = State.Integer(Value.InstanceId if Value else None)
    elif Selector:
        raise ValueError("Unsupported graphics node data serializer")
    Result = NodePayload(Selector, DataValue, IsXref, ActEntity, InstanceId)
    State.CheckResult(Value, Result)
    return Result
