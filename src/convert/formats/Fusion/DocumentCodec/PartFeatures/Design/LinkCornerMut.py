from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage

# data row must remain consistent across callers so modeling operations retain their document and timeline ownership
KDataRow = 1

# the chamfer types vocabulary must stay centralized so design feature construction agrees on supported native identities
KChamferTypes = {"equal": 1, "two": 2, "angle": 3}

# the chain modes vocabulary must stay centralized so design feature construction agrees on supported native identities
KChainModes: dict[str, object] = dict(bIsComputeChain=True)

# the fillet edge vocabulary must stay centralized so design feature construction agrees on supported native identities
KFilletEdge: dict[str, object] = dict(KChainModes, bConstantRadius=True)

# the fillet modes vocabulary must stay centralized so design feature construction agrees on supported native identities
KFilletModes: dict[str, object] = dict(
    isRollingBallCorners=True, isTangentPropagation=True
)

# the chamfer modes vocabulary must stay centralized so design feature construction agrees on supported native identities
KChamferModes: dict[str, object] = dict(cornerType=1, isTangentPropagation=True)


# the corner count contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def CornerCount(Feature: object) -> int:
    if isinstance(Feature, (FilletSpec, ChamferSpec)):
        return 1 + len(Feature.MoreCornersMm)
    return 1


# link corner must resolve unambiguously so modeling operations retain their document and timeline ownership
def LinkCornerMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    if isinstance(Stage.Feature, FilletSpec):
        Author.Allocate(Prefix + "data", "DcFilletEdgeData")
        Author.Change(
            Prefix + "data",
            connectedEdgeRef=Reference(Prefix + "target"),
            radiusValue=Reference(Prefix + "amount"),
            tangencyWeight=Reference(Prefix + "weight"),
            **KFilletEdge,
        )
        Edges = [Reference(Prefix + "data")]
        Author.Change(MainRole, filletEdgeData=Edges, **KFilletModes)
        return
    Feature = Stage.Feature
    Extra: dict[str, object] = dict(chamferType=KChamferTypes["equal"])
    if isinstance(Feature, ChamferSpec) and Feature.SecondMm > 0:
        Other = Reference(Prefix + "other")
        Extra = dict(chamferType=KChamferTypes["two"], chamferDistanceTwoParam=Other)
    elif isinstance(Feature, ChamferSpec) and Feature.AngleDegrees > 0:
        Other = Reference(Prefix + "other")
        Extra = dict(chamferType=KChamferTypes["angle"], chamferAngleParam=Other)
    Author.Change(
        Prefix + "data",
        chamferDistanceOneParam=Reference(Prefix + "amount"),
        rInputEdgesRef=Reference(Prefix + "target"),
        selIndex=KDataRow,
        **KChainModes,
        **Extra,
    )
    Author.Change(
        MainRole,
        rChamferData=[Reference(Prefix + "data")],
        primaryIDRowIndexMap=[
            {"key": Index + 1, "value": KDataRow}
            for Index in range(CornerCount(Feature))
        ],
        **KChamferModes,
    )
