from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Values.XferCacheMut import XferCacheMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureCache import TextureCache
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferTextureMut(
    State: SceneCodec, Value: TextureValue | None
) -> TextureValue | None:
    if not State.IsFlag(Value is not None):
        return None
    AssetName = State.TextValue(Value.AssetName if Value else None)
    SegmentId = State.Integer(Value.Reference.SegmentId if Value else None)
    ObjectId = State.Integer(Value.Reference.ObjectId if Value else None, ">Q")
    IsLayered = State.IsFlag(Value.Cache.IsLayered if Value else None)
    Primary = XferCacheMut(State, Value.Cache.Primary if Value else None)
    Secondary = None
    if State.IsFlag(Value is not None and Value.Cache.Secondary is not None):
        Secondary = XferCacheMut(State, Value.Cache.Secondary if Value else None)
    return TextureValue(
        AssetName,
        EntityRef(SegmentId, ObjectId),
        TextureCache(IsLayered, Primary, Secondary),
    )
