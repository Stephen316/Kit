from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.RenderFrame import RenderFrame
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


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
