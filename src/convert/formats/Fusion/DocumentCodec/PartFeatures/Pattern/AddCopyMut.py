from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
    KCountClass,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddPlaceMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyRefs import (
    AddAdjacentMut,
    AddAxisMut,
    AddEntityRefMut,
    AddSeedMut,
    AddSourceMut,
    UnitAxis,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PatternSolid import (
    KCopySpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import (
    FocusRole,
)

KNoLimit = -1
KGridAxes = ("x_axis", "y_axis")
KPatternModes: dict[str, object] = dict(
    computeOption=2, computeType=1, countUMax=KNoLimit
)
KCopyClasses: dict[type[object], tuple[str, str]] = {
    PatternSpec: ("DcRectangularPattern", "DcRectangularPatternData"),
    CircularSpec: ("DcCircularPattern", "DcCircularPatternData"),
    MirrorSpec: ("DcMirrorPattern", "DcMirrorPatternData"),
}


def OccurTags(Feature: KCopySpec) -> list[int]:
    if isinstance(Feature, PatternSpec):
        return [
            (Across + Along) * (Across + Along + 1) // 2 + Across + 1
            for Along in range(Feature.CountV)
            for Across in range(Feature.CountU)
        ]
    Count = 2 if isinstance(Feature, MirrorSpec) else Feature.Count
    return list(range(1, Count + 1))


def AddCountMut(Author: AuthorState, Prefix: str, NameValue: str, Count: int) -> str:
    RoleName = Prefix + NameValue.lower()
    Owner = Prefix + "feature"
    Amount = float(Count)
    AddParamMut(Author, RoleName, Owner, NameValue, Amount, "", None, KCountClass)
    return RoleName


def LinkBaseMut(Author: AuthorState, Prefix: str, Stage: PartStage) -> None:
    Reference = Author.Reference
    Feature = Stage.Feature
    if not isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        raise ValueError("Fusion copy authoring requires a pattern or mirror")
    TagValues = OccurTags(Feature)
    for Index, TagValue in enumerate(TagValues):
        Fields: dict[str, object] = dict(
            occTagId=TagValue, rPatternData=Reference(Prefix + "data")
        )
        Author.Allocate(
            Prefix + "occ_" + str(Index), "DcPatternBodyOccurrence", Fields=Fields
        )
    Owned = sorted(
        (TagValue, Stage.Operations[Index])
        for Index, TagValue in enumerate(TagValues)
        if Index
    )
    Author.Change(
        Prefix + "data",
        additionalAffectedBodies=[Reference(FocusRole(Author, "dc_body"))],
        extengType=not isinstance(Feature, PatternSpec),
        occOperationIdsMap=[
            {"key": TagValue, "value": Value} for TagValue, Value in Owned
        ],
        patternOccurrences=[
            Reference(Prefix + "occ_" + str(Index)) for Index in range(len(TagValues))
        ],
        rCountUParam=Reference(Prefix + "countu"),
        rDcFeature=Reference(Prefix + "feature"),
        rSourceRef=Reference(Prefix + "source"),
        **KPatternModes,
    )
    Author.Change(
        Prefix + "feature",
        rPatternBaseData=Reference(Prefix + "data"),
        rPatternSource=Reference(Prefix + "source_set"),
    )


def AddGridMut(Author: AuthorState, Prefix: str, Feature: PatternSpec) -> list[str]:
    Reference = Author.Reference
    Owner = Prefix + "feature"
    Roles = [AddCountMut(Author, Prefix, "CountV", Feature.CountV)]
    for NameValue, Amount in (("u", Feature.SpacingUMm), ("v", Feature.SpacingVMm)):
        RoleName = Prefix + "space_" + NameValue
        AddParamMut(Author, RoleName, Owner, NameValue + "SpaceDistance", Amount, "mm")
        Roles.append(RoleName)
    Roles += AddAxisMut(Author, Prefix, "axis_u", KGridAxes[0])
    Roles += AddAxisMut(Author, Prefix, "axis_v", KGridAxes[1])
    Author.Change(
        Prefix + "data",
        countVMax=KNoLimit,
        deducedDir=UnitAxis(KGridAxes[1]),
        dirU=Reference(Prefix + "space_u"),
        dirV=Reference(Prefix + "space_v"),
        rCountVParam=Reference(Prefix + "countv"),
        rUDirMR=Reference(Prefix + "axis_u"),
        rVDirMR=Reference(Prefix + "axis_v"),
    )
    return Roles


def AddTurnMut(Author: AuthorState, Prefix: str, Feature: CircularSpec) -> list[str]:
    Reference = Author.Reference
    RoleName = Prefix + "angle"
    Expression = ExprText(Feature.TotalDegrees) + " deg"
    Amount = Radians(Feature.TotalDegrees)
    Owner = Prefix + "feature"
    AddParamMut(Author, RoleName, Owner, "TotalAngle", Amount, "deg", Expression)
    Roles = [RoleName] + AddAxisMut(Author, Prefix, "axis", "z_axis")
    Author.Change(
        Prefix + "data", rAngle=Reference(RoleName), rAxisDir=Reference(Prefix + "axis")
    )
    return Roles


def AddFlipMut(Author: AuthorState, Prefix: str, Feature: MirrorSpec) -> list[str]:
    Reference = Author.Reference
    PlaneRole = "f" + str(Feature.PlaneIndex + 1) + "_plane"
    AddPlaceMut(Author, Prefix, ("mirror_plane", "ModelDataRef"), {})
    RefRole = AddEntityRefMut(Author, Prefix, "mirror_plane_ref", (PlaneRole, 5))
    PlaneValue = Author.FindEntity(PlaneRole).FieldValues["plane"]
    Cache: dict[str, object] = {
        "rCachedGeometry": PlaneValue,
        "progenitor": AddSeedMut(Author, RefRole, PlaneRole),
    }
    Author.Allocate(RefRole + "_cache", "ETCachedPlane", Fields=Cache)
    Author.Change(RefRole, caches=[Reference(RefRole + "_cache")])
    Author.Change(
        Prefix + "mirror_plane", dataRefs=[Reference(RefRole)], trackingType=5
    )
    Owner, Tolerance = Prefix + "feature", Prefix + "tolerance"
    AddParamMut(Author, Tolerance, Owner, "mirrorStitchTolerance", 0.01, "mm")
    Author.Change(
        Prefix + "data",
        mirrorStitchTolerance=Reference(Tolerance),
        rRefPlaneDataRef=Reference(Prefix + "mirror_plane"),
    )
    return [Prefix + "mirror_plane", RefRole, Tolerance]


def AddCopyMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, TagSet: tuple[int, int, int]
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        raise ValueError("Fusion copy authoring requires a pattern or mirror")
    ClassName, DataName = KCopyClasses[type(Feature)]
    AddNodeMut(Author, Prefix + "feature", ClassName, None)
    Author.Allocate(Prefix + "data", DataName)
    SourceRole = "f" + str(Feature.SourceIndex + 1) + "_feature"
    Children = AddSourceMut(Author, Prefix, SourceRole, TagSet)
    if not isinstance(Feature, PatternSpec):
        AddAdjacentMut(Author, Prefix, TagSet[0])
    Count = Feature.CountU if isinstance(Feature, PatternSpec) else 2
    Count = Feature.Count if isinstance(Feature, CircularSpec) else Count
    Children.append(AddCountMut(Author, Prefix, "countU", Count))
    if isinstance(Feature, PatternSpec):
        Children += AddGridMut(Author, Prefix, Feature)
    elif isinstance(Feature, CircularSpec):
        Children += AddTurnMut(Author, Prefix, Feature)
    else:
        Children += AddFlipMut(Author, Prefix, Feature)
    LinkBaseMut(Author, Prefix, Stage)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    return Children
