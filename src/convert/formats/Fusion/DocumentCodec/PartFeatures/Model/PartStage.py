from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


@MakeDataClass(frozen=True, slots=True)
class PartStage:
    Feature: KPartFeature
    Before: PrismSolid
    After: PrismSolid
    Operations: tuple[int, ...]
    StateId: int
    FamilyIndex: int
    Sketch: SketchPlan | None = None
    Bodies: tuple[PrismSolid, ...] = ()
    Shown: tuple[int, ...] = ()
    Upper: SketchPlan | None = None
