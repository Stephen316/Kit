from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.config.CutEquation import CutEquation
from convert.adapters.solidworks.resolved.OriginProfile import OriginProfile
from convert.adapters.solidworks.sketch.InlineSketch import InlineRead


# cut constraint identities must retain both archived owner streams and equation operands
@Dataclass(frozen=True, slots=True)
class CutRuleSource:
    SketchData: InlineRead
    ProfileId: int
    Origin: OriginProfile
    Equations: tuple[CutEquation, CutEquation]
    OuterProfileId: int
    ConfigStream: str
    ResolvedStream: str
