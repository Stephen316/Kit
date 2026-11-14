from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import AsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from interchange.geometry.models.VectorSpace import SpaceVector


@MakeDataClass(frozen=True, slots=True)
class PrismEvidence:
    Table: AsmTable
    Prism: AsmPrism
    Edges: dict[int, AsmPrismEdge]
    Points: dict[int, SpaceVector]
