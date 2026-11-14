from dataclasses import dataclass
from convert.formats.Fusion.TSplineCodec.Model.CageFace import CageFace
from convert.formats.Fusion.TSplineCodec.Model.CageEdge import CageEdge
from convert.formats.Fusion.TSplineCodec.Model.CageVertex import CageVertex
from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink
from convert.formats.Fusion.TSplineCodec.Model.EndCondition import EndCondition


@dataclass(frozen=True)
class CageTopology:
    Faces: tuple[CageFace, ...]
    Edges: tuple[CageEdge, ...]
    Vertices: tuple[CageVertex, ...]
    Links: tuple[CageLink, ...]
    EndConditions: tuple[EndCondition, ...] = ()
