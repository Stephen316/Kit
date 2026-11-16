from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.Formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse


# prism graph needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismGraph:
    ShellId: int
    Faces: tuple[int, ...]
    Rings: dict[int, tuple[AsmUse, ...]]
    Edges: dict[int, AsmPrismEdge]
    Points: dict[int, tuple[float, float, float]]
