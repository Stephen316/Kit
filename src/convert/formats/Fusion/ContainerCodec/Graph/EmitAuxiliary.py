from convert.formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.MetaIndex import KSegmentLayout, SegmentKind
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaProperty,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


def EmitAuxiliary(
    Segment: SegmentKind,
    Schemas: tuple[NativeSchema, ...],
    Records: tuple[EntityRecord, ...],
    Profile: EntityProfile,
) -> AuxiliaryGraph:
    SegmentId, Storage = KSegmentLayout[Segment]
    if SegmentId is None or not Records:
        raise ValueError("Invalid Fusion auxiliary segment")
    Ordered = tuple(
        sorted(Records, key=lambda Entry: (Entry.ObjectId, not Entry.IsPrimary))
    )
    Owners: dict[int, list[int]] = {}
    for Entry in Ordered:
        if Entry.IsPrimary:
            Owners.setdefault(Entry.TypeCode, []).append(Entry.ObjectId)
    Classes = tuple(
        MetaClass(
            Entry.Value.ClassGuid,
            Entry.Value.BaseGuid,
            Entry.Value.SchemaVersion,
            Entry.ClassSpace,
            tuple(Owners.get(Index, ())),
        )
        for Index, Entry in enumerate(Schemas, 256)
    )
    Roots = tuple(
        Entry.ObjectId for Entry in Ordered if Entry.IsPrimary and Entry.Frame.RootId
    )
    Header = MetaHeader(
        Segment,
        SegmentId,
        "00000000-0000-0000-0000-000000000000",
        1234,
        8,
        (17, 709361728),
        Segment.value,
        "Fusion",
        Storage,
    )
    Properties = tuple(
        MetaProperty(NameValue, SegmentId) for NameValue in ("Application", "Server")
    )
    Metadata = MetaSegment(
        Header,
        Classes,
        Roots,
        (),
        (),
        max(Entry.ObjectId for Entry in Ordered) + 1,
        0,
        Properties,
    )
    BulkData, MetaData = EmitSegment(
        Metadata, EncodeEntities(Ordered, Classes, Profile)
    )
    return AuxiliaryGraph(
        SegmentStreams(SegmentId, MetaData, BulkData), Ordered, Profile
    )
