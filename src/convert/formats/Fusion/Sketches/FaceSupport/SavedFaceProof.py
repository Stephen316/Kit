from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Sketches.FaceSupport.FaceHitProof import FaceHitProof
from convert.formats.Fusion.Topology.AsmEdge.AsmHistory import AsmHistory
from convert.formats.Fusion.Topology.AsmEdge.AsmRevisions import AsmRevision


# the reusable face witness retains both wire origins and directed typed incidence
@MakeDataClass(frozen=True, slots=True)
class SavedFaceProof:
    History: AsmHistory
    Revision: AsmRevision
    Member: str
    FaceEvidence: FaceHitProof
