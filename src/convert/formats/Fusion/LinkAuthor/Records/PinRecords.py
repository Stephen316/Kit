from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.ActionGroups import (
    ActionRecords,
    FeatureGroups,
)
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KAssemblyFeature,
    KFusionComponent,
    KGroundFeature,
    KGroundOverride,
    KManagedEntity,
    KOverride,
)
from convert.formats.Fusion.LinkAuthor.Records.PathValues import (
    BasePathValue,
    ScopeValue,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    MakeGroup,
    MakeRecord,
)
from convert.formats.Fusion.LinkAuthor.Records.RefRecords import OccurRef, RefRecords
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def PlaceRef(
    RootInfo: RootFacts,
    Facts: TargetFacts,
    Place: PlaceKeys,
    Identities: tuple[int, int, int],
    Parent: int,
) -> OccurRef:
    return OccurRef(
        Identities,
        1,
        Place.Occurrence,
        None,
        Parent,
        False,
        (Place.PersistentId,),
        ScopeValue(Facts.AssetId, Facts.PersistentId, 2),
        ScopeValue(RootInfo.AssetId, RootInfo.PersistentId, 2),
    )


def PinRecords(
    RootInfo: RootFacts,
    Facts: TargetFacts,
    Linkage: LinkKeys,
    Place: PlaceKeys,
    KeySet: ActionKeys,
) -> tuple[EntityRecord, ...]:
    if len(KeySet.Extra) != 4:
        raise ValueError("Fusion ground feature plan needs four extra identities")
    Override, DataId, RecipeId, XAssetId = KeySet.Extra
    Target = CrossRef(Facts.Component, Linkage.DesignToken, KFusionComponent)
    Subjects = (
        SubjectValue(Target, Facts.Slots[0] + 2),
        SubjectValue(LocalRef(Place.Instance), 2),
    )
    return (
        FrameRecord(
            Override,
            EntityFrame("", Subjects, None),
            MakeGroup(KGroundOverride),
            MakeGroup(
                KOverride, ("path", BasePathValue(RootInfo, (Place.InstanceId,)))
            ),
            MakeGroup(KManagedEntity, ("rParent", LocalRef(RootInfo.Overrides))),
        ),
        MakeRecord(
            KeySet.Feature,
            MakeGroup(
                KGroundFeature, ("isGround", True), ("occurrenceRef", LocalRef(DataId))
            ),
            MakeGroup(KAssemblyFeature),
            *FeatureGroups("Pin", KeySet, None, ()),
        ),
        *RefRecords(
            PlaceRef(
                RootInfo, Facts, Place, (DataId, RecipeId, XAssetId), KeySet.Feature
            )
        ),
        *ActionRecords(KeySet, RootInfo.NodesId),
    )
