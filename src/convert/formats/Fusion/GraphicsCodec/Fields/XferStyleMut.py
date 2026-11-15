from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Schema.StyleRules import KStyleRules
from convert.formats.Fusion.GraphicsCodec.Fields.XferFieldsMut import XferFieldsMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.StyleValue import StyleValue

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer style needs an explicit validity boundary so display geometry retains its entity and scene relationships
def XferStyleMut(
    State: SceneCodec, ClassName: str, Value: StyleValue | None
) -> StyleValue:
    Rules = KStyleRules.get(ClassName)
    if Rules is None:
        raise ValueError("Unsupported graphics text style")
    return StyleValue(XferFieldsMut(State, Rules, Value.Fields if Value else None))
