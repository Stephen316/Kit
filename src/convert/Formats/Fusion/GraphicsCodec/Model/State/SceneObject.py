from __future__ import annotations
from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.Formats.Fusion.GraphicsCodec.Model.State.KObjectValue import KObjectValue


# scene object needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class SceneObject:
    Reference: ObjectRef
    Value: KObjectValue
