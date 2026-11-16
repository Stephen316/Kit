from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipes import KEdgeNames
from convert.Formats.Fusion.Sketches.FaceSupport.JoinFaceRim import KFaceEdgeMatch
from convert.Formats.Fusion.Topology.AsmEdge.AsmFaceHit import AsmFaceHit
from interchange.geometry.Models.VectorSpace import SpaceVector


# projection outputs can consume qualified edge operands without reopening the prior body
@MakeDataClass(frozen=True, slots=True)
class FaceHitProof:
    HitValue: AsmFaceHit
    Edges: dict[KEdgeNames, KFaceEdgeMatch]
    Points: dict[int, SpaceVector]
