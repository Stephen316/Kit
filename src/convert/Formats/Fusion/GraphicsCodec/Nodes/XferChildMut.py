from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut

from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BodyChild import BodyChild

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# the transfer child contract needs a shared interpretation so display geometry retains its entity and scene relationships
def XferChildMut(State: SceneCodec, Value: BodyChild | None) -> BodyChild:
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(3)
    return BodyChild(Matrix, XferPayloadMut(State, Value.NodeData if Value else None))
