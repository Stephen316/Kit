from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Fields.XferSetMut import XferSetMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodeValue import NodeValue
from convert.formats.Fusion.GraphicsCodec.Values.XferEntityMut import XferEntityMut

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferNodeMut(State: SceneCodec, Value: NodeValue | None, IsQuick: bool) -> NodeValue:
    NodeType = State.Integer(Value.NodeType if Value else None)
    RenderRef = None if IsQuick else State.TextValue(Value.RenderRef if Value else None)
    if RenderRef is not None:
        if RenderRef != State.ActiveNode:
            raise ValueError("Graphics node data references a different render node")
        State.NodeLinks.add(RenderRef)
    Attributes = XferSetMut(State, Value.Attributes if Value else None)
    EntityStatus, EntityLink = XferEntityMut(
        State,
        Value.EntityStatus if Value else None,
        Value.EntityLink if Value else None,
    )
    Qualifier = State.Scalar(Value.Qualifier if Value else None, "<d")
    ClientName = State.OptionalText(Value.ClientName if Value else None)
    SubtypeName = State.OptionalText(Value.SubtypeName if Value else None)
    SerialId = State.Scalar(Value.SerialId if Value else None, "<d")
    if any(
        Number < 0 or Number > 2**53 or Number != int(Number)
        for Number in (Qualifier, SerialId)
    ):
        raise ValueError("Graphics identity exceeds exact numeric range")
    DoubleSided = State.Integer(Value.DoubleSided if Value else None)
    ColorValue = State.Vector(Value.ColorValue if Value else None, 4)
    ConsolFlags = State.Integer(Value.ConsolFlags if Value else None)
    ImmediateFlags = State.Integer(Value.ImmediateFlags if Value else None, "<i")
    RenderFlags = State.Integer(Value.RenderFlags if Value else None)
    SceneFlags = State.Integer(Value.SceneFlags if Value else None)
    Result = NodeValue(
        NodeType,
        RenderRef,
        Attributes,
        EntityStatus,
        EntityLink,
        Qualifier,
        ClientName,
        SubtypeName,
        SerialId,
        DoubleSided,
        ColorValue,
        ConsolFlags,
        ImmediateFlags,
        RenderFlags,
        SceneFlags,
    )
    State.CheckResult(Value, Result)
    return Result
