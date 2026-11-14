from dataclasses import replace as Replace

from convert.formats.Fusion.DocumentCodec.EnvelopePolicy import KSoftwareVersion
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from convert.formats.Fusion.DrawingCodec.Author.Defaults.ActClasses import KActClasses
from convert.formats.Fusion.DrawingCodec.Author.Defaults.ActRecords import KActRecords
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DesignClasses import (
    KDesignClasses,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KActProps,
    KDesignProps,
    KMetaMagic,
    KMetaVersion,
    KZeroGuid,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.ClassRow import ClassRow
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Author.Records.DesignRecords import (
    DesignNextId,
    DesignRecords,
)
from convert.formats.Fusion.DrawingCodec.Segments.DrawingProfile import DrawingProfile
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.MetaIndex import KSegmentLayout, SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaProperty,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

KStorageSpace = "FusionDoc"


def DrawingSegments(
    SpecValue: DrawingSpec, FileName: str, History: SaveState
) -> tuple[ParsedSegment, ...]:
    DesignRows = OrderRows(KDesignClasses, History.DesignOrder)
    ActRows = OrderRows(KActClasses, History.ActOrder)
    DesignItems = AssignTypes(DesignRecords(SpecValue, FileName, History), DesignRows)
    ActItems = AssignTypes(KActRecords, ActRows)
    NextId = DesignNextId(SpecValue, History)
    Metas = (
        SegmentMeta(
            SegmentKind.KDrawingDesign, DesignRows, DesignItems, NextId, KDesignProps
        ),
        SegmentMeta(
            SegmentKind.KDrawingAct, ActRows, ActItems, ActNextId(History), KActProps
        ),
    )
    Result: list[ParsedSegment] = []
    for MetaValue, Records in zip(Metas, (DesignItems, ActItems), strict=True):
        Profile = DrawingProfile(Metas, MetaValue.Header.SegmentId)
        Streams = EmitDocSegment(ParsedSegment(MetaValue, Records, Profile))
        Final = ReadMetaWire(Streams.Metadata, Segment=MetaValue.Header.Segment)
        Result.append(ParsedSegment(Final, Records, Profile))
    return tuple(Result)


def OrderRows(
    ClassRows: tuple[ClassRow, ...], Order: tuple[str, ...]
) -> tuple[ClassRow, ...]:
    Known = {RowValue.ClassGuid: RowValue for RowValue in ClassRows}
    if len(Order) != len(Known) or set(Order) != set(Known):
        raise ValueError("Fusion drawing class order must permute the known classes")
    return tuple(Known[ClassGuid] for ClassGuid in Order)


def AssignTypes(
    Records: tuple[EntityRecord, ...], ClassRows: tuple[ClassRow, ...]
) -> tuple[EntityRecord, ...]:
    Codes = {
        RowValue.ClassGuid.upper(): 256 + Index
        for Index, RowValue in enumerate(ClassRows)
    }
    return tuple(
        Replace(Record, TypeCode=Codes[Record.Groups[0].ClassGuid.upper()])
        for Record in Records
    )


def SegmentMeta(
    KindValue: SegmentKind,
    ClassRows: tuple[ClassRow, ...],
    Records: tuple[EntityRecord, ...],
    NextId: int,
    Props: tuple[tuple[str, int], ...],
) -> MetaSegment:
    SegmentId, StorageWords = KSegmentLayout[KindValue]
    if SegmentId is None:
        raise ValueError("Fusion drawing segments need a fixed segment identity")
    Header = MetaHeader(
        KindValue,
        SegmentId,
        KZeroGuid,
        KMetaMagic,
        KMetaVersion,
        (KSoftwareVersion & 0xFFFFFFFF, KSoftwareVersion >> 32),
        KindValue.value,
        KStorageSpace,
        StorageWords,
    )
    Classes = tuple(
        MetaClass(
            RowValue.ClassGuid,
            RowValue.BaseGuid,
            RowValue.SchemaVersion,
            RowValue.ClassSpace,
            tuple(
                Record.ObjectId
                for Record in Records
                if Record.IsPrimary
                and Record.Groups[0].ClassGuid.upper() == RowValue.ClassGuid.upper()
            ),
        )
        for RowValue in ClassRows
    )
    Stored = tuple(
        Record.ObjectId
        for Record in Records
        if Record.IsPrimary and Record.Frame.RootId
    )
    Properties = tuple(MetaProperty(NameValue, Value) for NameValue, Value in Props)
    return MetaSegment(Header, Classes, Stored, (), (), NextId, 0, Properties)


def ActNextId(History: SaveState) -> int:
    if History.ActNextId is not None:
        return History.ActNextId
    return 1 + max(Record.ObjectId for Record in KActRecords)
