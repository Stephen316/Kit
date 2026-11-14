from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import (
    FamilyOf,
    IsSketched,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes


def TwinOwners(Stage: PartStage, Prefix: str) -> list[tuple[str, tuple[int, ...]]]:
    Values = Stage.Operations
    if isinstance(Stage.Feature, SweepSpec):
        return [
            (Prefix + "dc_sketch", Values[:1]),
            (Prefix + "up_dc_sketch", Values[1:2]),
            (Prefix + "feature", Values[2:]),
        ]
    return [
        (Prefix + "dc_sketch", Values[:1]),
        (Prefix + "wp_feature", Values[1:2]),
        (Prefix + "up_dc_sketch", Values[2:3]),
        (Prefix + "feature", Values[3:]),
    ]


def TimelineOwners(
    Author: AuthorState, Stages: tuple[PartStage, ...]
) -> list[tuple[str, tuple[int, ...]]]:
    First = Author.Policy.FirstOperationId
    Owners: list[tuple[str, tuple[int, ...]]] = []
    if Author.SpecValue.ProfileKind != "part":
        Owners = [("dc_sketch", (First,)), ("dc_extrude", (First + 1, First + 2))]
    for Index, Stage in enumerate(Stages):
        Prefix = "f" + str(Index + 1) + "_"
        if isinstance(Stage.Feature, (LoftSpec, SweepSpec)):
            Owners.extend(TwinOwners(Stage, Prefix))
            continue
        if IsSketched(Stage.Feature):
            Owners.append((Prefix + "dc_sketch", Stage.Operations[:1]))
            Owners.append((Prefix + "feature", Stage.Operations[1:]))
            continue
        if isinstance(Stage.Feature, PasteSpec):
            Owners.append((Prefix + "base", Stage.Operations[:1]))
            Owners.append((Prefix + "feature", Stage.Operations[1:]))
            continue
        if not isinstance(Stage.Feature, (PatternSpec, CircularSpec, MirrorSpec)):
            Owners.append((Prefix + "feature", Stage.Operations))
            continue
        Owners.append((Prefix + "feature", Stage.Operations[:1]))
        Owners.extend(
            (Prefix + "occ_" + str(Ordinal), (Operation,))
            for Ordinal, Operation in enumerate(Stage.Operations)
            if Ordinal
        )
    return Owners


def IsShownOwner(RoleName: str) -> bool:
    return "_occ_" not in RoleName and not RoleName.endswith("_base")


def LinkSketches(Author: AuthorState, Stages: tuple[PartStage, ...]) -> None:
    Reference = Author.Reference
    Roles = [] if Author.SpecValue.ProfileKind == "part" else ["rectangle_sketch"]
    NextTag = Author.Policy.FirstSketchTag + 9
    for Index, Stage in enumerate(Stages):
        for PlanValue, StemName in (
            (Stage.Sketch, "_sketch"),
            (Stage.Upper, "_up_sketch"),
        ):
            if PlanValue is not None:
                Roles.append("f" + str(Index + 1) + StemName)
                NextTag = PlanValue.NextTag
    if not Roles or (len(Roles) == 1 and Roles[0] == "rectangle_sketch"):
        return
    Author.Change(
        "sketches",
        highWaterMark=len(Roles),
        groupChildren=[Reference(RoleName) for RoleName in Roles],
    )
    Author.FindEntity("sketches").NamedPairs = MakeAttributes(crv_tag_id_idx=NextTag)
    Author.Change(
        "sketches_root",
        rootId="SketchesRoot",
        rooted=[Reference(RoleName) for RoleName in Roles],
    )


def LinkTimeline(Author: AuthorState, Stages: tuple[PartStage, ...]) -> None:
    Reference = Author.Reference
    Owners = TimelineOwners(Author, Stages)
    Author.Change(
        "creation_order",
        representationFeatures=[
            Reference(RoleName) for RoleName, _ in Owners if IsShownOwner(RoleName)
        ],
    )
    Author.Change(
        "feature_ids",
        enetityIdMap=[
            {"key": Author.Roles[RoleName], "value": list(Values)}
            for RoleName, Values in Owners
        ],
        featureIdMap=[
            {"key": Value, "value": Author.Roles[RoleName]}
            for RoleName, Values in Owners
            for Value in Values
        ],
    )
    IsPart = Author.SpecValue.ProfileKind == "part"
    Counts = {} if IsPart else {"DcExtrudeFeatureMetaType": 1, "DcSketchMetaType": 1}
    for Stage in Stages:
        NameValue = FamilyOf(Stage.Feature).ClassName + "MetaType"
        Counts[NameValue] = Counts.get(NameValue, 0) + 1
        Extra = ["DcSketchMetaType"] if IsSketched(Stage.Feature) else []
        if isinstance(Stage.Feature, LoftSpec):
            Extra = ["DcSketchMetaType", "DcSketchMetaType", "DcWorkPlaneMetaType"]
        if isinstance(Stage.Feature, SweepSpec):
            Extra = ["DcSketchMetaType", "DcSketchMetaType"]
        if isinstance(Stage.Feature, PasteSpec):
            Extra = ["DcBaseFeatureMetaType"]
        for NameValue in Extra:
            Counts[NameValue] = Counts.get(NameValue, 0) + 1
    Author.Change(
        "fragment",
        featureIndexMap=[
            {"key": KeyValue, "value": Counts[KeyValue]} for KeyValue in sorted(Counts)
        ],
    )
    Author.Change("component", operationSeedId=Owners[-1][1][-1] + 1)
    LinkSketches(Author, Stages)
