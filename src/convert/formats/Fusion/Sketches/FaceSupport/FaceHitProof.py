from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Sketches.FaceSupport.FaceRecipes import KEdgeNames
from convert.formats.Fusion.Sketches.FaceSupport.JoinFaceRim import KFaceEdgeMatch
from convert.formats.Fusion.Topology.AsmEdge.AsmFaceHit import AsmFaceHit
from interchange.geometry.models.VectorSpace import SpaceVector


# projection outputs can consume qualified edge operands without reopening the prior body
@MakeDataClass(frozen=True, slots=True)
class FaceHitProof:
    HitValue: AsmFaceHit
    Edges: dict[KEdgeNames, KFaceEdgeMatch]
    Points: dict[int, SpaceVector]
