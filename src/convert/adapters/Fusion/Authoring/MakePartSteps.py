from convert.adapters.Fusion.Authoring.MakePartParams import DrivingLength
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureStep import FeatureStep

# the step kinds vocabulary must stay centralized so native adapter translation agrees on supported native identities
KStepKinds: dict[type[object], FeatureKind] = {
    FilletSpec: FeatureKind.KFillet,
    ChamferSpec: FeatureKind.KChamfer,
    ExtrudeSpec: FeatureKind.KExtrusion,
    HoleSpec: FeatureKind.KHole,
    PatternSpec: FeatureKind.KPattern,
    CircularSpec: FeatureKind.KPattern,
    MirrorSpec: FeatureKind.KMirror,
    PlaneSpec: FeatureKind.KReference,
    AxisSpec: FeatureKind.KReference,
    PointSpec: FeatureKind.KReference,
    RevolveSpec: FeatureKind.KRevolution,
    MoveSpec: FeatureKind.KNative,
    OffsetSpec: FeatureKind.KOffset,
    DraftSpec: FeatureKind.KDraft,
    CombineSpec: FeatureKind.KBoolean,
    SplitSpec: FeatureKind.KNative,
    BodyGridSpec: FeatureKind.KPattern,
    BodyRingSpec: FeatureKind.KPattern,
    LoftSpec: FeatureKind.KLoft,
    SweepSpec: FeatureKind.KSweep,
    PasteSpec: FeatureKind.KNative,
}


# the step kind contract needs a shared interpretation so public document claims remain grounded in native records
def StepKind(Feature: KPartFeature) -> FeatureKind:
    return KStepKinds.get(type(Feature), FeatureKind.KShell)


# the part steps operation needs a consistent construction rule so public document claims remain grounded in native records
def MakePartSteps(SpecValue: DocumentSpec) -> tuple[FeatureStep, ...]:
    Steps: list[FeatureStep] = []
    Previous = "extrude"
    for Index, Feature in enumerate(SpecValue.Features):
        Identity = "feature" + str(Index + 1)
        Owned = () if DrivingLength(Feature) is None else (Identity + "-amount",)
        Steps.append(
            FeatureStep(
                Identity,
                Feature.FeatureName,
                StepKind(Feature),
                Index + 2,
                (Previous,),
                parameter_ids=Owned,
            )
        )
        Previous = Identity
    return tuple(Steps)
