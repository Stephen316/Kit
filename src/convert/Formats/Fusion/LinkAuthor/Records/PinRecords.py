from convert.Formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.Formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.Formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.Formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.Formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.Formats.Fusion.LinkAuthor.Records.ActionGroups import (
    ActionRecords,
    FeatureGroups,
)
from convert.Formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KAssemblyFeature,
    KFusionComponent,
    KGroundFeature,
    KGroundOverride,
    KManagedEntity,
    KOverride,
)
from convert.Formats.Fusion.LinkAuthor.Records.PathValues import (
    BasePathValue,
    ScopeValue,
)
from convert.Formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    MakeGroup,
    MakeRecord,
)
from convert.Formats.Fusion.LinkAuthor.Records.RefRecords import OccurRef, RefRecords
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the reference operation needs a consistent construction rule so cross document references retain their intended ownership
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


# pin records needs an explicit validity boundary so cross document references retain their intended ownership
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
