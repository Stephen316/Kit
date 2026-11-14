from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet


@MakeDataClass(frozen=True, slots=True)
class NodeValue:
    NodeType: int
    RenderRef: str | None
    Attributes: SceneSet
    EntityStatus: int
    EntityLink: EntityRef | None
    Qualifier: float
    ClientName: str | None
    SubtypeName: str | None
    SerialId: float
    DoubleSided: int
    ColorValue: tuple[float, ...]
    ConsolFlags: int
    ImmediateFlags: int
    RenderFlags: int
    SceneFlags: int
