from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.CombineSolid import (
    CombineSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.CopyBodies import (
    CopyBodies,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.PasteSolid import (
    PasteSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.SplitSolid import (
    SplitSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)

KBodySpec = CombineSpec | SplitSpec | BodyGridSpec | BodyRingSpec | PasteSpec
KBodySpecs = (CombineSpec, SplitSpec, BodyGridSpec, BodyRingSpec, PasteSpec)
KBodyState = tuple[dict[int, PrismSolid], list[int]]


def ShownBody(State: KBodyState, Ordinal: object) -> PrismSolid:
    Bodies, Shown = State
    if type(Ordinal) is not int or Ordinal not in Shown:
        raise ValueError("Fusion body features name a visible body by its number")
    return Bodies[Ordinal]


def CombineStageMut(
    State: KBodyState, Feature: CombineSpec, Operation: int
) -> PrismSolid:
    Target = ShownBody(State, Feature.TargetBody)
    Tools = tuple(ShownBody(State, Ordinal) for Ordinal in Feature.ToolBodies)
    Ordinals = (Feature.TargetBody, *Feature.ToolBodies)
    if not Tools or len(set(Ordinals)) != len(Ordinals):
        raise ValueError("Fusion combines need distinct target and tool bodies")
    After = CombineSolid(Target, Tools, Feature, Operation)
    State[0][Target.Ordinal] = After
    for Ordinal in () if Feature.KeepTools else Feature.ToolBodies:
        State[1].remove(Ordinal)
    return After


def SplitStageMut(
    State: KBodyState,
    Feature: SplitSpec,
    Operation: int,
    Context: tuple[tuple[KPartFeature, ...], int],
) -> PrismSolid:
    Features, Index = Context
    Target = ShownBody(State, Feature.TargetBody)
    if not 0 <= Feature.PlaneIndex < Index:
        raise ValueError("Fusion splits must follow their plane")
    Plane = Features[Feature.PlaneIndex]
    if not isinstance(Plane, PlaneSpec):
        raise ValueError("Fusion splits cut along an offset plane")
    Ordinal = len(State[0]) + 1
    First, Second = SplitSolid(Target, Plane, Operation, Ordinal)
    State[0][Target.Ordinal] = First
    State[0][Ordinal] = Second
    State[1].append(Ordinal)
    return First


def PasteStageMut(State: KBodyState, Feature: PasteSpec, Operation: int) -> PrismSolid:
    Source = ShownBody(State, Feature.SourceBody)
    Pasted = PasteSolid(Source, Operation, len(State[0]) + 1)
    State[0][Pasted.Ordinal] = Pasted
    State[1].append(Pasted.Ordinal)
    return Pasted


def BodyStageMut(
    State: KBodyState,
    Feature: KBodySpec,
    Operation: int,
    Context: tuple[tuple[KPartFeature, ...], int],
) -> tuple[PrismSolid, PrismSolid]:
    if isinstance(Feature, CombineSpec):
        Before = ShownBody(State, Feature.TargetBody)
        return Before, CombineStageMut(State, Feature, Operation)
    if isinstance(Feature, SplitSpec):
        Before = ShownBody(State, Feature.TargetBody)
        return Before, SplitStageMut(State, Feature, Operation, Context)
    if isinstance(Feature, PasteSpec):
        Before = ShownBody(State, Feature.SourceBody)
        return Before, PasteStageMut(State, Feature, Operation)
    Source = ShownBody(State, Feature.SourceBody)
    Ordinal = len(State[0]) + 1
    for CopySolid in CopyBodies(Source, Feature, Operation, Ordinal):
        State[0][CopySolid.Ordinal] = CopySolid
        State[1].append(CopySolid.Ordinal)
    return Source, Source
