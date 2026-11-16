from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Topology.AsmEdge.AsmPrism import AsmPrism
from convert.Formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from interchange.geometry.Models.VectorSpace import SpaceVector


# the prism evidence boundary needs grouped coverage so repository automation cannot silently change its observable contract
@MakeDataClass(frozen=True, slots=True)
class PrismEvidence:
    Table: AsmTable
    Prism: AsmPrism
    Edges: dict[int, AsmPrismEdge]
    Points: dict[int, SpaceVector]
