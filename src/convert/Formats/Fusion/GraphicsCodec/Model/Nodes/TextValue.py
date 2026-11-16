from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.RenderFrame import RenderFrame
from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


# text value needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class TextValue:
    Frame: RenderFrame
    Matrix: tuple[float, ...]
    Envelope: tuple[float, ...]
    TextData: str | None
    Alignment: int
    Escapement: float
    TextStyle: ObjectRef | None
    ParaStyle: ObjectRef | None
    BlockStyle: ObjectRef | None
    Anchor: tuple[float, ...]
    Priority: int
