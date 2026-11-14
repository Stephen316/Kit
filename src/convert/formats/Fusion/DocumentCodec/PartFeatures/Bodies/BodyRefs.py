from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import BodyRole
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    TagInfoOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    BodyRecipeOf,
    KBodyOperationType,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import (
    FaceLabelOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    LabelGroups,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes

KCreationState = 3
KIdentity: dict[str, object] = {"identity": True}


def AddBodyRefMut(
    Author: AuthorState,
    Prefix: str,
    NameValue: str,
    Solid: PrismSolid,
    Tracking: tuple[int, int],
) -> list[str]:
    Reference = Author.Reference
    Owner = Prefix + "feature"
    DataRole, BodyRefRole = Prefix + NameValue, Prefix + NameValue + "_body"
    AddNodeMut(Author, DataRole, "ModelDataRef", Owner)
    AddNodeMut(Author, BodyRefRole, "DRBody", Owner)
    Author.Allocate(DataRole + "_cache", "ETCachedMatrix3d")
    Label = Solid.BodyLabel
    Recipe: dict[str, object] = {"m_Recipe": BodyRecipeOf(Label)}
    Author.Allocate(BodyRefRole + "_recipe", "ASMRecipe", Fields=Recipe)
    Author.Change(
        DataRole,
        dataRefs=[Reference(BodyRefRole)],
        caches=[Reference(DataRole + "_cache")],
        trackingType=Tracking[0],
    )
    Author.Change(
        BodyRefRole,
        rRecipe=Reference(BodyRefRole + "_recipe"),
        rScope=PartScope(Author),
        refBodies=[Reference(BodyRole(Solid.Ordinal, "dc_body"))],
        trackingType=Tracking[1],
        operIdTypeMap=[{"key": int(Label.PrimaryId), "value": KBodyOperationType}],
    )
    return [DataRole, BodyRefRole]


def MarkOperation(Author: AuthorState, RoleName: str, Operation: int) -> None:
    Author.FindEntity(RoleName).NamedPairs = MakeAttributes(
        DcFeatureOperationIdFlag=Operation
    )


def FaceIdsOf(Solid: PrismSolid) -> dict[int, list[str]]:
    Found: dict[int, set[str]] = {}
    for FaceValue in BuildShape(Solid).Faces:
        for Group in LabelGroups(FaceLabelOf(FaceValue)):
            for Operation in Group.OperationIds:
                Found.setdefault(Operation, set()).add(Group.PrimaryId)
    return {Operation: sorted(Found[Operation]) for Operation in sorted(Found)}


def AddBodySeedMut(
    Author: AuthorState,
    RoleName: str,
    Solid: PrismSolid,
    Context: tuple[str, int, bool],
) -> dict[str, object] | None:
    BodyUuid, Primary, IsShared = Context
    Author.Allocate(RoleName, "BodyProgenitor")
    Entries = [
        {
            "key": TagInfoOf(
                Author,
                tuple(Value.encode("ascii") for Value in Values),
                Operation,
                Operation == Primary,
            ),
            "value": 1,
        }
        for Operation, Values in FaceIdsOf(Solid).items()
    ]
    Author.Change(
        RoleName,
        bodyUuid=BodyUuid,
        featureTagOccMap=Entries,
        shareTargetBodyAddress=IsShared,
    )
    return Author.Reference(RoleName)


def ActRefValue(Author: AuthorState) -> list[dict[str, object]]:
    Fields: dict[str, object] = dict(
        actRefdTable=None,
        changeTypesToTrack=[],
        crossAsset=False,
        owningEntity=None,
        rActData=None,
        refdEntity=None,
    )
    return [Author.MakeGroup("ACTRefValue", Fields)]


def LocalActRef(Author: AuthorState) -> list[dict[str, object]]:
    PathValue: dict[str, object] = dict(
        componentInstances=[],
        creationState=KCreationState,
        passiveOccurrencePath=Author.MakeValue("ACTPassivePathValue"),
        sourceACTComponent=None,
        sourceComponent=None,
    )
    Fields: dict[str, object] = dict(
        actDataForCIs=[],
        actRef=ActRefValue(Author),
        deepTracking=False,
        path=[Author.MakeGroup("BaseOccurrencePathValue", PathValue)],
        topCompActRef=ActRefValue(Author),
    )
    return [Author.MakeGroup("OccurrenceACTRefValue", Fields)]


def AddOccurMut(Author: AuthorState, Prefix: str, Operation: int) -> object:
    RoleName = Prefix + "occurrence"
    Fields: dict[str, object] = dict(
        OccurrenceACTRef=LocalActRef(Author),
        cachedTransform=dict(KIdentity),
        parentFeature=Author.Reference(Prefix + "feature"),
    )
    Author.Allocate(RoleName, "OccurrenceDataRef", Fields=Fields)
    return [{"key": Author.Reference(RoleName), "value": Operation}]
