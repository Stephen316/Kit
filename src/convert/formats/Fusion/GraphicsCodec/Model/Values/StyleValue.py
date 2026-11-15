from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet


# style value needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class StyleValue:
    Fields: tuple[FieldValue[SceneSet], ...]
