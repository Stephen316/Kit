from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.resolved.support.SupportPlane import SupportPlane
from convert.adapters.solidworks.sketch.InlineSketch import InlineRead


# the neutral cut needs exact provenance from two separate selected archive streams
@Dataclass(frozen=True, slots=True)
class CutSource:
    Support: SupportPlane
    SketchData: InlineRead
    ProfileId: int
    BossId: int
    ConfigStream: str
    ResolvedStream: str
