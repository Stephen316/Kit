from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.Formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KComputable,
    KDcAction,
    KDcFeature,
    KDcNode,
    KDcStatus,
    KProgenitor,
    KUpdateData,
    KZeroGuid,
)
from convert.Formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    LocalSeries,
    MakeGroup,
    MakeRecord,
    ParentRecord,
)
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

# birthday must remain consistent across callers so cross document references retain their intended ownership
KBirthday = 260


# the node group contract needs a shared interpretation so cross document references retain their intended ownership
def NodeGroup(DataId: int, Parent: int | None) -> EntityGroup[KEntityValue]:
    return MakeGroup(
        KDcNode,
        ("isActive", True),
        ("isEdited", False),
        ("isEliminated", False),
        ("rDynamicUpdateData", LocalRef(DataId)),
        ("rGroupRepresentative", None),
        ("rParentFeature", None if Parent is None else LocalRef(Parent)),
    )


# the feature groups contract needs a shared interpretation so cross document references retain their intended ownership
def FeatureGroups(
    BaseName: str, KeySet: ActionKeys, Context: int | None, Children: tuple[int, ...]
) -> tuple[EntityGroup[KEntityValue], ...]:
    return (
        MakeGroup(
            KDcFeature,
            ("associationId", KZeroGuid),
            ("bDisabled", False),
            ("bLockedForTimelineReorder", False),
            ("bLockedForTimelineRoll", False),
            ("childNodes", LocalSeries(Children)),
            ("endModelHS", -1),
            ("featureBaseName", BaseName),
            ("featureIndex", KeySet.FeatureIndex),
            ("featureUserName", ""),
            ("groupMembers", ValueSeries(())),
            ("isImplicitlySuppressed", False),
            ("isSuppressed", False),
            ("isZombieFeature", False),
            ("rProgenitorTable", LocalRef(KeySet.Table)),
            ("rReferencedContext", None if Context is None else LocalRef(Context)),
            ("startModelHS", -1),
        ),
        MakeGroup(
            KComputable,
            ("birthday", KBirthday),
            ("computeTime", 0.0),
            ("firstBirthday", KBirthday),
            ("status", LocalRef(KeySet.Status)),
        ),
        MakeGroup(KDcAction),
        NodeGroup(KeySet.FeatureData, None),
    )


# the update record contract needs a shared interpretation so cross document references retain their intended ownership
def UpdateRecord(ObjectId: int, Owner: int) -> EntityRecord:
    return MakeRecord(
        ObjectId,
        MakeGroup(
            KUpdateData,
            ("bodies", ValueMap(())),
            ("isBodyOK", False),
            ("isPredecessorOK", False),
            ("predecessors", ValueMap(())),
            ("rOwnerNode", LocalRef(Owner)),
            ("timeStamp", 0),
            ("xRefPredecessorsHash", 0),
        ),
    )


# the action records contract needs a shared interpretation so cross document references retain their intended ownership
def ActionRecords(KeySet: ActionKeys, NodesId: int) -> tuple[EntityRecord, ...]:
    return (
        ParentRecord(KeySet.Feature, NodesId),
        UpdateRecord(KeySet.FeatureData, KeySet.Feature),
        FrameRecord(
            KeySet.Status,
            EntityFrame("", None, ()),
            MakeGroup(KDcStatus, ("statusCodes", ValueSeries(())), ("statusType", 0)),
        ),
        MakeRecord(
            KeySet.Table,
            MakeGroup(KProgenitor, ("ProgenitorTagVec", ValueSeries(())), ("tagId", 1)),
        ),
        ParentRecord(KeySet.Table, None),
    )
