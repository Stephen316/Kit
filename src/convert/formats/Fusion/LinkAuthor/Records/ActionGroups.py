from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KComputable,
    KDcAction,
    KDcFeature,
    KDcNode,
    KDcStatus,
    KProgenitor,
    KUpdateData,
    KZeroGuid,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    LocalSeries,
    MakeGroup,
    MakeRecord,
    ParentRecord,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KBirthday = 260


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
