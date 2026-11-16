from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from interchange.geometry.Models.VectorSpace import SpaceVector


# the frustum evidence boundary needs grouped coverage so repository automation cannot silently change its observable contract
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
