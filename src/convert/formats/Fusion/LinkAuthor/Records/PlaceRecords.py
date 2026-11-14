from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.ActionGroups import (
    ActionRecords,
    FeatureGroups,
    NodeGroup,
    UpdateRecord,
)
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KAssemblyFeature,
    KBaseInstance,
    KCommonBase,
    KComponentInstance,
    KDcData,
    KDcInstance,
    KFusionComponent,
    KManagedEntity,
    KPlaceFeature,
    KPlaceInstance,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    MakeGroup,
    MakeRecord,
    ParentRecord,
    PlaceMatrix,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def PlaceAction(KeySet: PlaceKeys) -> ActionKeys:
    return ActionKeys(
        KeySet.Feature,
        KeySet.FeatureData,
        KeySet.Status,
        KeySet.Table,
        KeySet.FeatureId,
        KeySet.FeatureIndex,
        (),
    )


def InstanceRecord(
    RootInfo: RootFacts,
    Facts: TargetFacts,
    Linkage: LinkKeys,
    KeySet: PlaceKeys,
    Matrix: tuple[float, ...],
    IsFirst: bool,
) -> EntityRecord:
    Target = CrossRef(Facts.Component, Linkage.DesignToken, KFusionComponent)
    return FrameRecord(
        KeySet.Instance,
        EntityFrame("", (SubjectValue(Target, Facts.Slots[0] + 1),), ()),
        MakeGroup(KComponentInstance),
        MakeGroup(
            KBaseInstance,
            ("bGroundToParent", IsFirst),
            ("bRigidSubAssembly", False),
            ("creationIndex", 1),
            ("initialTransform", PlaceMatrix(Matrix)),
            ("lastSavedTargetRevisionGuid", Facts.ComponentRev),
            ("persistentId", KeySet.PersistentId),
            ("rACTInstance", SegmentRef(KeySet.ActInstance, RootInfo.ActSegment)),
            ("rOwningDeriveFeature", None),
            ("rTargetComponent", Target),
            ("transform", PlaceMatrix(Matrix)),
            ("userName", ""),
            ("xAssetLinkName", Linkage.LinkId),
        ),
        MakeGroup(KCommonBase, ("rClientObject", None)),
        MakeGroup(KManagedEntity, ("rParent", LocalRef(RootInfo.Instances))),
    )


def PlaceRecords(
    RootInfo: RootFacts,
    Facts: TargetFacts,
    Linkage: LinkKeys,
    KeySet: PlaceKeys,
    Matrix: tuple[float, ...],
    IsFirst: bool,
) -> tuple[EntityRecord, ...]:
    Action = PlaceAction(KeySet)
    return (
        InstanceRecord(RootInfo, Facts, Linkage, KeySet, Matrix, IsFirst),
        MakeRecord(
            KeySet.NodeId,
            MakeGroup(KDcInstance, ("rComponentInstance", LocalRef(KeySet.Instance))),
            MakeGroup(KDcData),
            NodeGroup(KeySet.NodeData, KeySet.Feature),
        ),
        ParentRecord(KeySet.NodeId, RootInfo.NodesId),
        UpdateRecord(KeySet.NodeData, KeySet.NodeId),
        MakeRecord(
            KeySet.Feature,
            MakeGroup(
                KPlaceFeature,
                ("missingCompInstances", ValueSeries(())),
                ("refedDocAssetsHashCache", 0),
            ),
            MakeGroup(
                KPlaceInstance,
                ("occTransformMap", ValueMap(())),
                ("rComponentInstance", LocalRef(KeySet.NodeId)),
                ("showInBrowser", True),
                ("transform", PlaceMatrix(Matrix)),
            ),
            MakeGroup(KAssemblyFeature),
            *FeatureGroups(
                "Component Insert", Action, RootInfo.ContextId, (KeySet.NodeId,)
            ),
        ),
        *ActionRecords(Action, RootInfo.NodesId),
    )
