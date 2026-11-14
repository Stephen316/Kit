from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BodyChild import BodyChild

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferChildMut(State: SceneCodec, Value: BodyChild | None) -> BodyChild:
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(3)
    return BodyChild(Matrix, XferPayloadMut(State, Value.NodeData if Value else None))
