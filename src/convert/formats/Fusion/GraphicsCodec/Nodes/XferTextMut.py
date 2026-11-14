from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferFrameMut import XferFrameMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferTextMut(State: SceneCodec, Value: TextValue | None) -> TextValue:
    Frame = XferFrameMut(State, Value.Frame if Value else None)
    Matrix = State.Vector(Value.Matrix if Value else None, 16)
    Envelope = State.Vector(Value.Envelope if Value else None, 2)
    TextData = State.OptionalText(Value.TextData if Value else None)
    Alignment = State.Integer(Value.Alignment if Value else None, "<i")
    Escapement = State.Scalar(Value.Escapement if Value else None)
    TextStyle = State.LinkedObject("TextStyle", Value.TextStyle if Value else None)
    ParaStyle = State.LinkedObject("ParagraphStyle", Value.ParaStyle if Value else None)
    BlockStyle = State.LinkedObject("BlockStyle", Value.BlockStyle if Value else None)
    Anchor = State.Vector(Value.Anchor if Value else None, 2)
    Priority = State.Integer(Value.Priority if Value else None, "<i")
    return TextValue(
        Frame,
        Matrix,
        Envelope,
        TextData,
        Alignment,
        Escapement,
        TextStyle,
        ParaStyle,
        BlockStyle,
        Anchor,
        Priority,
    )
