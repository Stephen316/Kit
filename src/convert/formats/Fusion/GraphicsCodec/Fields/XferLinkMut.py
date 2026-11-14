from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Values.XferTextureMut import XferTextureMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferLinkMut(
    State: SceneCodec, WireKind: str, Current: object
) -> TextureValue | ObjectRef | None:
    if WireKind == "texture":
        if Current is not None and not isinstance(Current, TextureValue):
            raise ValueError("Expected typed graphics texture mapping")
        return XferTextureMut(State, Current)
    if WireKind != "qualifier":
        raise ValueError("Unsupported linked graphics field descriptor")
    if Current is not None and not isinstance(Current, ObjectRef):
        raise ValueError("Expected a graphics selection qualifier reference")
    return State.LinkedObject("AlphaImageSelectionQualifier", Current)
