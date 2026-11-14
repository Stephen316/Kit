from dataclasses import dataclass

from convert.formats.Fusion.MeshCodec.Model.FeatureEdge import FeatureEdge
from convert.formats.Fusion.MeshCodec.Model.MeshPoint import MeshPoint
from convert.formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.formats.Fusion.MeshCodec.Model.OctaNormal import OctaNormal


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
