from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Schema.FieldRule import FieldRule
from convert.formats.Fusion.GraphicsCodec.Fields.XferFieldMut import XferFieldMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


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
