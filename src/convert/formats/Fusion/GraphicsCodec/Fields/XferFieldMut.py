from __future__ import annotations
from typing import TYPE_CHECKING
from typing import cast as CastValue
from convert.formats.Fusion.GraphicsCodec.Schema.FieldRule import FieldRule
from convert.formats.Fusion.GraphicsCodec.Fields.XferLinkMut import XferLinkMut
from convert.formats.Fusion.GraphicsCodec.Fields.XferOverMut import XferOverMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.TextureValue import TextureValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget
from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferFieldMut(
    State: SceneCodec, FieldRuleValue: FieldRule, Value: FieldValue[SceneSet] | None
) -> FieldValue[SceneSet]:
    Result: (
        bool
        | int
        | float
        | str
        | None
        | tuple[float, ...]
        | TextureValue
        | ObjectRef
        | NodeTarget
        | tuple[OverrideSet[SceneSet], ...]
    )
    Current = Value.DataValue if Value else None
    if FieldRuleValue.WireKind in ("texture", "qualifier"):
        Result = XferLinkMut(State, FieldRuleValue.WireKind, Current)
    elif FieldRuleValue.WireKind in ("path", "target", "overrides"):
        Result = XferOverMut(State, FieldRuleValue.WireKind, Current)
    elif FieldRuleValue.WireKind == "absent":
        State.EmptyLinks(1)
        Result = None
    elif FieldRuleValue.WireKind == "zero":
        Result = State.Integer(CastValue(int | None, Current))
        if Result:
            raise ValueError("Unsupported nonempty graphics tab stops")
    elif FieldRuleValue.WireKind == "bool":
        Result = State.IsFlag(CastValue(bool | None, Current))
    elif FieldRuleValue.WireKind in ("i32", "u32"):
        Result = State.Integer(
            CastValue(int | None, Current),
            "<i" if FieldRuleValue.WireKind == "i32" else "<I",
        )
    elif FieldRuleValue.WireKind in ("f32", "f64"):
        Format = "<f" if FieldRuleValue.WireKind == "f32" else "<d"
        Result = (
            State.Scalar(CastValue(float | None, Current), Format)
            if FieldRuleValue.ItemCount == 1
            else State.Vector(
                CastValue(tuple[float, ...] | None, Current),
                FieldRuleValue.ItemCount,
                Format,
            )
        )
    elif FieldRuleValue.WireKind == "text":
        Result = State.TextValue(CastValue(str | None, Current))
    elif FieldRuleValue.WireKind == "opt-text":
        Result = State.OptionalText(CastValue(str | None, Current))
    else:
        raise ValueError("Unsupported graphics field descriptor")
    return FieldValue(FieldRuleValue.FieldName, Result)
