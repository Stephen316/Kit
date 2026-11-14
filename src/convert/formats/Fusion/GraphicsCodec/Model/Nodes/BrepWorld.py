from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BodyChild import BodyChild
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue


@MakeDataClass(frozen=True, slots=True)
class BrepWorld:
    EdgeGroup: BodyChild | None
    EdgeNodes: tuple[LodValue, ...]
    FaceGroup: BodyChild | None
    FaceNodes: tuple[LodValue, ...]
    ModelBox: tuple[float, ...] | None
