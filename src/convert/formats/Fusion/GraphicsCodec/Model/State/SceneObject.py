from __future__ import annotations
from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.State.KObjectValue import KObjectValue


@MakeDataClass(frozen=True, slots=True)
class SceneObject:
    Reference: ObjectRef
    Value: KObjectValue
