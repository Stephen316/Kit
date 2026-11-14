from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet


@MakeDataClass(frozen=True, slots=True)
class StyleValue:
    Fields: tuple[FieldValue[SceneSet], ...]
