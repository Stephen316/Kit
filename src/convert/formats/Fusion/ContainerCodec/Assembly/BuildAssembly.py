from pathlib import Path as FilePath

from convert.formats.Fusion.ContainerCodec.Assembly.RevisionMap import (
    KChangeTypes,
    RevisionMap,
)
from convert.formats.Fusion.ContainerCodec.Graph.ExternalProfile import ExternalProfile
from convert.formats.Fusion.ContainerCodec.Graph.SegmentBuilder import SegmentBuilder
from convert.formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def BuildAssembly(
    Design: DesignResult, Title: str, SnapshotId: str, InstanceRev: str
) -> AuxiliaryGraph:
    Schemas = ReadVocabulary(FilePath(__file__).with_name("ActClasses.json"))
    Profile = ExternalProfile(Design.Profile, Design.Records, 0)
    Builder = SegmentBuilder(SegmentKind.KAct, Schemas, Profile)
    Empty: ValueSeries[KEntityValue] = ValueSeries(())
    Revisions = RevisionMap(Design.RevisionId)
    _ = RevisionMap(SnapshotId)
    Entries = tuple(
        Builder.MakeValue(
            "ACTTableEntryValue",
            {"rActData": LocalRef(Revision), "tgtIdentifier": f"1_{Identity}"},
        )
        for Identity, Revision in ((100, 106), (102, 107))
    )
    Builder.AddEntity(
        103,
        "ACTTable",
        {
            "ACTTableEntries": ValueSeries(Entries),
            "AssetRevGuid": SnapshotId,
            "RevisionGuid": Design.RevisionId,
            "refdTables": Empty,
            "revisionGuidForChangeType": Revisions,
        },
        "ACTTable",
    )
    Builder.AddEntity(
        104,
        "ACTComponentsRoot",
        {
            "rootId": "ACTComponentsRoot",
            "rooted": ValueSeries((LocalRef(100),)),
            "rParent": None,
        },
        "ACTComponentsRoot",
    )
    Builder.AddEntity(
        100,
        "ACTComponent",
        {
            "ACTInstances": LocalRef(101),
            "actIdentifier": "1_100",
            "designComponent": SegmentRef(Design.Roles["component"], 0),
            "name": Title,
            "rParent": LocalRef(102),
        },
    )
    Builder.AddEntity(
        106, "RevGUIDACTDataMany", {"revGuidMap": Revisions, "actIdentifier": "1_100"}
    )
    Builder.AddEntity(
        101,
        "ACTInstances",
        {
            "rDesignInstances": SegmentRef(Design.Roles["component_instances"], 0),
            "softDeletedInstances": Empty,
            "children": Empty,
            "rParent": LocalRef(100),
        },
    )
    Builder.AddEntity(
        105,
        "ACTInstancesRoot",
        {
            "instancesMap": ValueMap((ValuePair(0, LocalRef(102)),)),
            "nextInstanceId": 1,
            "rootId": "ACTInstancesRoot",
            "rooted": ValueSeries((LocalRef(102),)),
            "rParent": None,
        },
        "ACTInstancesRoot",
    )
    ActRef = Builder.MakeValue(
        "ACTRefValue",
        {
            "actRefdTable": None,
            "changeTypesToTrack": ValueSeries(KChangeTypes),
            "crossAsset": False,
            "owningEntity": LocalRef(102),
            "rActData": None,
            "refdEntity": LocalRef(100),
        },
    )
    Builder.AddEntity(
        102,
        "ACTInstance",
        {
            "ACTRef": ActRef,
            "actIdentifier": "1_102",
            "bSoftDeleted": False,
            "designInstance": SegmentRef(Design.Roles["root_instance"], 0),
            "instanceId": 0,
            "targetComponent": LocalRef(100),
            "rParent": None,
        },
        "ACTInstanceRoot",
    )
    Builder.AddEntity(
        107,
        "RevGUIDACTDataMany",
        {"revGuidMap": RevisionMap(InstanceRev), "actIdentifier": "1_102"},
    )
    return Builder.Finish()
