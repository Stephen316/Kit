from dataclasses import replace as Replace

from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.LinkAuthor.Records.LinkClasses import KLinkClasses
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMinClassCode
from convert.formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def ExtendClasses(Segment: ParsedSegment) -> tuple[MetaClass, ...]:
    Known = {Entry.ClassGuid.upper() for Entry in Segment.Metadata.Classes}
    Added = tuple(
        MetaClass(ClassGuid, BaseGuid, Version, Space, ())
        for KindValue, ClassGuid, BaseGuid, Version, Space in KLinkClasses
        if KindValue is Segment.Metadata.Header.Segment
        and ClassGuid.upper() not in Known
    )
    return Segment.Metadata.Classes + Added


def BindCodes(
    Classes: tuple[MetaClass, ...], Records: tuple[EntityRecord, ...]
) -> tuple[EntityRecord, ...]:
    Codes = {
        Entry.ClassGuid.upper(): Index + KMinClassCode
        for Index, Entry in enumerate(Classes)
    }
    if any(
        not Record.Groups or Record.Groups[0].ClassGuid.upper() not in Codes
        for Record in Records
    ):
        raise ValueError("Fusion link record class is not registered")
    return tuple(
        Replace(Record, TypeCode=Codes[Record.Groups[0].ClassGuid.upper()])
        for Record in Records
    )


def AddOwners(
    Classes: tuple[MetaClass, ...], Records: tuple[EntityRecord, ...]
) -> tuple[MetaClass, ...]:
    return tuple(
        Replace(
            Entry,
            OwnerIds=Entry.OwnerIds
            + tuple(
                Record.ObjectId
                for Record in Records
                if Record.IsPrimary
                and Record.Groups[0].ClassGuid.upper() == Entry.ClassGuid.upper()
            ),
        )
        for Entry in Classes
    )


def ExtendSegment(
    Segment: ParsedSegment,
    Records: tuple[EntityRecord, ...],
    Added: tuple[EntityRecord, ...],
    Bounds: tuple[int, tuple[MetaContext, ...]],
) -> ParsedSegment:
    NextId, Contexts = Bounds
    Classes = ExtendClasses(Segment)
    Ordered = tuple(
        sorted(Added, key=lambda Record: (Record.ObjectId, not Record.IsPrimary))
    )
    if Ordered and (
        Ordered[0].ObjectId < Segment.Metadata.NextId or Ordered[-1].ObjectId >= NextId
    ):
        raise ValueError("Fusion link record identities escape their plan")
    Metadata = Replace(
        Segment.Metadata,
        Classes=AddOwners(Classes, Ordered),
        NextId=NextId,
        Reserved=len(Contexts),
        Contexts=Contexts,
    )
    return Replace(
        Segment, Metadata=Metadata, Records=Records + BindCodes(Classes, Ordered)
    )
