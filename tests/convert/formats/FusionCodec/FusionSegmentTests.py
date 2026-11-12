from dataclasses import replace as Replace
from zipfile import ZipFile

import pytest as Pytest

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import KSegmentLayout, SegmentKind
from convert.formats.Fusion.SegmentCodec.Browser.EmitBrowserRoot import EmitBrowserRoot
from convert.formats.Fusion.SegmentCodec.Browser.ReadBrowserRoot import ReadBrowserRoot
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.ClassLineage import MapLineage
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass, MetaOffset
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# these typed records cover a continuation and independently owned primaries
KNativeRows = (
    BulkRecord(256, 34, False, b"common"),
    BulkRecord(257, 34, True, b"detail"),
    BulkRecord(258, 92, True, b"second"),
)


# generated metadata can declare classes and owners before offsets are available
def MakeMeta(Segment: SegmentKind) -> MetaSegment:
    SegmentId, Storage = KSegmentLayout[Segment]
    return MetaSegment(
        MetaHeader(
            Segment, SegmentId or 0, "", 1234, 8, (0, 0), Segment.value, "", Storage
        ),
        (
            MetaClass("Parent", "", 0, "TestSpace", ()),
            MetaClass("Child", "Parent", 0, "TestSpace", (34,)),
            MetaClass("Sibling", "", 0, "TestSpace", (92,)),
        ),
        (34, 92),
        (),
        (),
        93,
        0,
        (),
    )


# metadata uses actual payload widths for all three supported segment headers
@Pytest.mark.parametrize("Segment", tuple(SegmentKind))
def TestEmitSegment(Segment: SegmentKind) -> None:
    Metadata = MakeMeta(Segment)
    BulkData, MetaData = EmitSegment(Metadata, iter(KNativeRows))
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=Segment)
    assert tuple(SpanValue.StartOffset for SpanValue in Spans) == (0, 21, 42)
    assert tuple(SpanValue.IsPrimary for SpanValue in Spans) == (False, True, True)
    assert tuple(
        BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset] for SpanValue in Spans
    ) == tuple(RecordValue.Payload for RecordValue in KNativeRows)
    assert ReadMetaWire(MetaData, Segment=Segment) == Replace(
        Metadata,
        Primary=(MetaOffset(34, 21), MetaOffset(92, 42)),
        Continuations=(MetaOffset(34, 0),),
    )


# editing a record relocates downstream entries even when prior metadata is supplied
def TestRelocation() -> None:
    Metadata = MakeMeta(SegmentKind.KDesign)
    _, OldMeta = EmitSegment(Metadata, KNativeRows)
    Changed = (
        Replace(KNativeRows[0], Payload=b"longer edited continuation"),
        *KNativeRows[1:],
    )
    BulkData, MetaData = EmitSegment(ReadMetaWire(OldMeta), Changed)
    Spans = ReadBulkSpans(BulkData, MetaData)
    First, Owner, Other = Spans
    assert BulkData[First.PayloadOffset : First.EndOffset] == Changed[0].Payload
    assert Owner.StartOffset == 15 + len(Changed[0].Payload)
    assert Other.StartOffset == Owner.EndOffset
    assert ReadMetaWire(MetaData).Primary == (
        MetaOffset(34, Owner.StartOffset),
        MetaOffset(92, Other.StartOffset),
    )


# complete emission requires registered primaries and legitimate ancestor continuations
@Pytest.mark.parametrize(
    "Records",
    (
        (Replace(KNativeRows[0], TypeCode=258), *KNativeRows[1:]),
        (KNativeRows[0], Replace(KNativeRows[1], TypeCode=258), KNativeRows[2]),
        (*KNativeRows[:2], Replace(KNativeRows[2], ObjectId=93)),
        KNativeRows[:2],
    ),
)
def TestOwnerGuard(Records: tuple[BulkRecord, ...]) -> None:
    with Pytest.raises(ValueError, match="class registry"):
        _ = EmitSegment(MakeMeta(SegmentKind.KDesign), Records)


# deep class trees must avoid recursion and disconnected cycles have no valid lineage
def TestLineage() -> None:
    Parents = {str(Index): str(Index - 1) for Index in range(4000)}
    Ranges = MapLineage(Parents)
    assert (Ranges["0"], Ranges["3999"]) == ((0, 4000), (3999, 4000))
    Parents["0"] = "3999"
    with Pytest.raises(ValueError, match="Cyclic"):
        _ = MapLineage(Parents)


# native fixtures tie segment composition to an independent saved index and browser layout
@KRequiresCodec
@Pytest.mark.parametrize("Segment", tuple(SegmentKind))
def TestNativePair(Segment: SegmentKind) -> None:
    Source = KStudyPath / "planedefinitions-6cd0820a832e" / "offset.f3d"
    Prefix = f"FusionAssetName[Active]/{Segment.value}1/"
    with ZipFile(Source) as Archive:
        BulkData = Archive.read(Prefix + "BulkStream.dat")
        MetaData = Archive.read(Prefix + "MetaStream.dat")
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=Segment)
    Records: list[BulkRecord] = []
    for SpanValue in Spans:
        Payload = BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
        if (
            Segment is SegmentKind.KBrowser
            and SpanValue.ObjectId == 0
            and SpanValue.IsPrimary
        ):
            Payload = EmitBrowserRoot(ReadBrowserRoot(Payload))
        Records.append(
            BulkRecord(
                SpanValue.TypeCode, SpanValue.ObjectId, SpanValue.IsPrimary, Payload
            )
        )
    assert EmitSegment(ReadMetaWire(MetaData, Segment=Segment), Records) == (
        BulkData,
        MetaData,
    )
