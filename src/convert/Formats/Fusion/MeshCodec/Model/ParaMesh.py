from dataclasses import dataclass

from convert.Formats.Fusion.MeshCodec.Model.FeatureEdge import FeatureEdge
from convert.Formats.Fusion.MeshCodec.Model.MeshPoint import MeshPoint
from convert.Formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.Formats.Fusion.MeshCodec.Model.OctaNormal import OctaNormal


# para mesh needs an explicit state contract so vertex and index streams retain their intended connectivity
@dataclass(frozen=True)
class ParaMesh:
    Registry: MeshRegistry
    Positions: tuple[MeshPoint, ...]
    Corners: tuple[int, ...]
    TerminalWord: int
    Normals: tuple[OctaNormal, ...]
    Overrides: tuple[int, ...]
    Edges: tuple[FeatureEdge, ...]
    FaceGroups: tuple[int, ...]
