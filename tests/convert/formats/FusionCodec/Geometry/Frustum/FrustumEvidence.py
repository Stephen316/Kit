from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from interchange.geometry.models.VectorSpace import SpaceVector


@MakeDataClass(frozen=True, slots=True)
class FrustumEvidence:
    Table: AsmTable
    BottomRadius: float
    TopRadius: float
    Height: float
    BasePoint: SpaceVector
    SineAngle: float
    CosineAngle: float
    ParamScale: float
