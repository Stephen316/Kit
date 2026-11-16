from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BodyChild import BodyChild
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue


# boundary representation world needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class BrepWorld:
    EdgeGroup: BodyChild | None
    EdgeNodes: tuple[LodValue, ...]
    FaceGroup: BodyChild | None
    FaceNodes: tuple[LodValue, ...]
    ModelBox: tuple[float, ...] | None
