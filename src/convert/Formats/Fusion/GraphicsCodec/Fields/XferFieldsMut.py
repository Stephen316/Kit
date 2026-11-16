from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Schema.FieldRule import FieldRule
from convert.Formats.Fusion.GraphicsCodec.Fields.XferFieldMut import XferFieldMut

from convert.Formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer fields needs an explicit validity boundary so display geometry retains its entity and scene relationships
def XferFieldsMut(
    State: SceneCodec,
    Rules: tuple[FieldRule, ...],
    Values: tuple[FieldValue[SceneSet], ...] | None,
) -> tuple[FieldValue[SceneSet], ...]:
    if not State.IsReading and (
        Values is None
        or tuple(Entry.FieldName for Entry in Values)
        != tuple(Entry.FieldName for Entry in Rules)
    ):
        raise ValueError("Incorrect graphics fields or field order")
    return tuple(
        XferFieldMut(State, FieldRuleValue, Values[Index] if Values else None)
        for Index, FieldRuleValue in enumerate(Rules)
    )
