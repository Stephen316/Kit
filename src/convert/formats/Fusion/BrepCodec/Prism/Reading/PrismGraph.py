from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse


@MakeDataClass(frozen=True, slots=True)
class PrismGraph:
    ShellId: int
    Faces: tuple[int, ...]
    Rings: dict[int, tuple[AsmUse, ...]]
    Edges: dict[int, AsmPrismEdge]
    Points: dict[int, tuple[float, float, float]]
