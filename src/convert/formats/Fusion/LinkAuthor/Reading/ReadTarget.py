from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.LinkAuthor.Edits.RecordEdit import (
    OwnedIds,
    ReadNumber,
    ReadText,
    ReadValue,
    SoleId,
)
from convert.formats.Fusion.LinkAuthor.MatrixMath import CheckMatrix
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Reading.DocSegment import SegmentOf, TextItems
from convert.formats.Fusion.LinkAuthor.Reading.ObserverSlots import NextSlot
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KActComponent,
    KActInstance,
    KActTable,
    KComponentInstances,
    KDcOccurrence,
    KFeatures,
    KFusionComponent,
)
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def EntryRevs(
    Tracking: ParsedSegment, Table: int, Identifier: str
) -> tuple[tuple[str, str], ...]:
    Entries = ReadValue(Tracking.Records, Table, "ACTTableEntries")
    if not isinstance(Entries, ValueSeries):
        raise ValueError("Fusion link target has no ACT table entries")
    Found = tuple(
        Entry.Groups[0].Fields
        for Entry in Entries.Items
        if isinstance(Entry, ValueObject)
        and len(Entry.Groups) == 1
        and dict(
            (Field.FieldName, Field.Value) for Field in Entry.Groups[0].Fields
        ).get("tgtIdentifier")
        == Identifier
    )
    if len(Found) != 1:
        raise ValueError("Fusion link target lacks its root ACT entry")
    DataRef = dict((Field.FieldName, Field.Value) for Field in Found[0]).get("rActData")
    if not isinstance(DataRef, LocalRef):
        raise ValueError("Fusion link target lacks its root ACT data")
    return TextItems(ReadValue(Tracking.Records, DataRef.ObjectId, "revGuidMap"))


def ChildIndex(Design: ParsedSegment, Tracking: ParsedSegment) -> dict[int, int]:
    Index: dict[int, int] = {}
    for ObjectId in OwnedIds(Tracking, KActInstance):
        Instance = ReadValue(Tracking.Records, ObjectId, "designInstance")
        if not isinstance(Instance, SegmentRef) or (
            Instance.SegmentId != Design.Metadata.Header.SegmentId
        ):
            raise ValueError("Fusion link target has a foreign ACT instance")
        Index[Instance.ObjectId] = ReadNumber(Tracking.Records, ObjectId, "instanceId")
    return Index


def ReadChildren(
    Design: ParsedSegment, Tracking: ParsedSegment, Instances: int
) -> tuple[tuple[int, tuple[float, ...]], ...]:
    Children = ReadValue(Design.Records, Instances, "children")
    if not isinstance(Children, ValueSeries):
        raise ValueError("Fusion link target has malformed instances")
    Locals = tuple(Child for Child in Children.Items if isinstance(Child, LocalRef))
    if len(Locals) != len(Children.Items):
        raise ValueError("Fusion link target has malformed instances")
    Index = ChildIndex(Design, Tracking)
    Result: list[tuple[int, tuple[float, ...]]] = []
    for Child in Locals:
        Matrix = ReadValue(Design.Records, Child.ObjectId, "transform")
        if not isinstance(Matrix, MatrixValue) or Matrix.Entries is None:
            raise ValueError("Fusion nested placement needs an explicit transform")
        if Child.ObjectId not in Index:
            raise ValueError("Fusion nested placement lacks an ACT instance")
        Result.append((Index[Child.ObjectId], CheckMatrix(tuple(Matrix.Entries))))
    if len(OwnedIds(Design, KDcOccurrence)) != len(Result) + 1:
        raise ValueError("Fusion link targets support one nesting level")
    return tuple(Result)


def ReadTarget(Model: DocumentModel) -> TargetFacts:
    Design = SegmentOf(Model, SegmentKind.KDesign)
    Tracking = SegmentOf(Model, SegmentKind.KAct)
    Component = SoleId(Design, KFusionComponent)
    ActComponent = SoleId(Tracking, KActComponent)
    Table = SoleId(Tracking, KActTable)
    Identifier = ReadText(Tracking.Records, ActComponent, "actIdentifier")
    if ReadText(Tracking.Records, Table, "AssetRevGuid") != Model.Asset.SnapshotId:
        raise ValueError("Fusion link target snapshot disagrees with its ACT table")
    Instances = SoleId(Design, KComponentInstances)
    Features = SoleId(Design, KFeatures)
    Segment = Design.Metadata.Header.SegmentId
    Slots = (
        NextSlot(Model, Segment, Component),
        NextSlot(Model, Segment, Instances),
        NextSlot(Model, Segment, Features),
    )
    return TargetFacts(
        Model.Asset.AssetId,
        Model.Asset.SnapshotId,
        ReadText(Tracking.Records, Table, "RevisionGuid"),
        TextItems(ReadValue(Tracking.Records, Table, "revisionGuidForChangeType")),
        ActComponent,
        Identifier,
        EntryRevs(Tracking, Table, Identifier),
        Component,
        Instances,
        Features,
        ReadText(Design.Records, Component, "persistentId"),
        ReadText(Design.Records, Component, "revisionGuid"),
        Segment,
        Tracking.Metadata.Header.SegmentId,
        ReadChildren(Design, Tracking, Instances),
        Slots,
    )
