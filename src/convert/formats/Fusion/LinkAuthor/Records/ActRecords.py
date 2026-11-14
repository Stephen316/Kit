from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KActChange,
    KActChangeMany,
    KActComponent,
    KActDataMany,
    KActInstance,
    KActRefdTable,
    KActRefValue,
    KChangeTypes,
    KManagedEntity,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    MakeGroup,
    MakeRecord,
    TextPairs,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def FreshRevisions() -> tuple[tuple[str, str], ...]:
    Shared, Properties, Placement = str(MakeUuid()), str(MakeUuid()), str(MakeUuid())
    return tuple(
        (
            ChangeType,
            {"Properties": Properties, "Transform": Placement}.get(ChangeType, Shared),
        )
        for ChangeType in KChangeTypes
    )


def DataRecord(
    ObjectId: int, Revisions: tuple[tuple[str, str], ...], Identifier: str
) -> EntityRecord:
    return MakeRecord(
        ObjectId,
        MakeGroup(KActDataMany, ("revGuidMap", TextPairs(Revisions))),
        MakeGroup(KActChangeMany),
        MakeGroup(KActChange, ("actIdentifier", Identifier)),
    )


def RefdRecord(
    Facts: TargetFacts, Linkage: LinkKeys, KeySet: PlaceKeys
) -> EntityRecord:
    Entry: ValueStruct[KEntityValue] = ValueStruct(
        (
            NamedValue("trackedTypes", ValueSeries(KChangeTypes)),
            NamedValue("referenceCount", 1),
        )
    )
    return FrameRecord(
        KeySet.ActTable,
        EntityFrame("", (SubjectValue(LocalRef(KeySet.ActCopy), 0),), None),
        MakeGroup(
            KActRefdTable,
            ("ACTRefdTableEntries", ValueMap((ValuePair(Facts.ActIdentifier, Entry),))),
            ("CachedRevGuid", Facts.RevisionGuid),
            ("RefdAssetGuid", Facts.AssetId),
            ("RefdDocLinkName", Linkage.LinkId),
            ("RevisionGuidForChangeType", TextPairs(Facts.ChangeRevs)),
        ),
    )


def ActRecords(
    RootInfo: RootFacts, Facts: TargetFacts, Linkage: LinkKeys, KeySet: PlaceKeys
) -> tuple[EntityRecord, ...]:
    Target = CrossRef(Facts.ActComponent, Linkage.ActToken, KActComponent)
    Identifier = f"{RootInfo.ActSegment}_{KeySet.ActInstance}"
    Reference = MakeGroup(
        KActRefValue,
        ("actRefdTable", LocalRef(KeySet.ActTable)),
        ("changeTypesToTrack", ValueSeries(KChangeTypes)),
        ("crossAsset", True),
        ("owningEntity", LocalRef(KeySet.ActInstance)),
        ("rActData", LocalRef(KeySet.ActCopy)),
        ("refdEntity", Target),
    )
    return (
        MakeRecord(
            KeySet.ActInstance,
            MakeGroup(
                KActInstance,
                ("ACTRef", ValueObject((Reference,))),
                ("actIdentifier", Identifier),
                ("bSoftDeleted", False),
                ("designInstance", SegmentRef(KeySet.Instance, RootInfo.DesignSegment)),
                ("instanceId", KeySet.InstanceId),
                ("targetComponent", Target),
            ),
            MakeGroup(KManagedEntity, ("rParent", LocalRef(RootInfo.ActInstances))),
        ),
        DataRecord(KeySet.ActData, FreshRevisions(), Identifier),
        RefdRecord(Facts, Linkage, KeySet),
        DataRecord(KeySet.ActCopy, Facts.ActRevs, Facts.ActIdentifier),
    )
