from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRule import (
    FamilyRule,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)

KFamilyRules: dict[type[object], FamilyRule] = {
    FilletSpec: FamilyRule("DcFilletEdgeFeature", "Fillet", 1, 8),
    ChamferSpec: FamilyRule("DcChamferFeature", "Chamfer", 1, 8),
    ShellSpec: FamilyRule("DcShellFeature", "Shell", 2, 16),
    ExtrudeSpec: FamilyRule("DcExtrudeFeature", "Extrude", 3, 8),
    HoleSpec: FamilyRule("DcHoleFeature", "Hole", 1, 4),
    PatternSpec: FamilyRule("DcRectangularPattern", "R-Pattern", 0, 4),
    CircularSpec: FamilyRule("DcCircularPattern", "C-Pattern", 0, 4),
    MirrorSpec: FamilyRule("DcMirrorPattern", "Mirror", 2, 4),
    PlaneSpec: FamilyRule("DcWorkPlane", "WorkPlane", 1, 4),
    AxisSpec: FamilyRule("DcWorkAxis", "WorkAxis", 1, 4),
    PointSpec: FamilyRule("DcWorkPoint", "WorkPoint", 1, 4),
    RevolveSpec: FamilyRule("DcRevolveFeature", "Revolve", 2, 8),
    MoveSpec: FamilyRule("DcMoveFeature", "Move", 1, 4),
    OffsetSpec: FamilyRule("DcOffsetFacesFeature", "OffsetFaces", 2, 16),
    DraftSpec: FamilyRule("DcDraftFeature", "Draft", 2, 16),
    CombineSpec: FamilyRule("DcCombineFeature", "Combine", 1, 4),
    SplitSpec: FamilyRule("DcSplitBodyFeature", "Split", 1, 4),
    BodyGridSpec: FamilyRule("DcRectangularPattern", "R-Pattern", 0, 4),
    BodyRingSpec: FamilyRule("DcCircularPattern", "C-Pattern", 0, 4),
    LoftSpec: FamilyRule("DcLoftFeature", "Loft", 4, 8),
    SweepSpec: FamilyRule("DcSweepFeature", "Sweep", 3, 8),
    PasteSpec: FamilyRule("DcPasteBodies", "CopyPasteBodies", 2, 4),
}


def FamilyOf(Feature: KPartFeature) -> FamilyRule:
    RuleValue = KFamilyRules.get(type(Feature))
    if RuleValue is None:
        raise ValueError("Unsupported Fusion part feature family")
    return RuleValue


def OperationsOf(Feature: KPartFeature) -> int:
    if isinstance(Feature, (PatternSpec, BodyGridSpec)):
        return Feature.CountU * Feature.CountV
    if isinstance(Feature, (CircularSpec, BodyRingSpec)):
        return Feature.Count
    return FamilyOf(Feature).OperationCount


def IsStateless(Feature: KPartFeature) -> bool:
    return isinstance(Feature, (PlaneSpec, AxisSpec, PointSpec))


def IsSketched(Feature: KPartFeature) -> bool:
    return isinstance(Feature, (ExtrudeSpec, RevolveSpec))
