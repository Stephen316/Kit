# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace
from typing import cast as CastValue
from struct import pack as PackValue

from pytest import raises as Raises

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.HistoryGroup import HistoryGroup, KGroupGuid, ReadGroup
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.NativeHistory import KHistoryGuid, ReadHistory
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Chronology.EmitGroup import EmitGroup
from convert.formats.Fusion.SegmentCodec.Chronology.EmitHistory import EmitHistory
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment

# group order is deliberately independent of the physical feature positions
KSyntheticGroup = HistoryGroup(80, "Layout 🧭", True, (55, 54))


# authored records do not need either offset table before composing the segment
def WriteChronology(
    Group: HistoryGroup, Entries: tuple[int, ...]
) -> tuple[bytes, bytes]:
    Segment = SegmentKind.KDesign
    Header = MetaHeader(Segment, 0, "", 1234, 8, (0, 0), Segment.value, "", (1, 0))
    Metadata = MetaSegment(
        Header,
        (
            MetaClass(KHistoryGuid, "", 0, "Fusion", (35,)),
            MetaClass(KGroupGuid, "", 0, "Fusion", (80,)),
            MetaClass("FeatureClass", "", 0, "Fusion", (54, 55, 72)),
            MetaClass("OwnerClass", "", 0, "Fusion", (26,)),
        ),
        (26, 35, 80),
        (),
        (),
        81,
        0,
        (),
    )
    return EmitSegment(
        Metadata,
        (
            BulkRecord(256, 35, True, EmitHistory(26, Entries)),
            BulkRecord(258, 54, True, b"feature a"),
            BulkRecord(257, 80, True, EmitGroup(Group)),
            BulkRecord(259, 26, True, b"owner"),
            BulkRecord(258, 72, True, b"feature c"),
            BulkRecord(258, 55, True, b"feature b"),
        ),
    )


# newly emitted chronology remains ordered after a group edit relocates later records
def TestHistoryEdit() -> None:
    Before = (80, 55, 54, 72)
    BulkData, MetaData = WriteChronology(KSyntheticGroup, Before)
    OldSpans = ReadBulkSpans(BulkData, MetaData)
    OldOwners = {SpanValue.ObjectId: SpanValue for SpanValue in OldSpans}
    assert ReadHistory(BulkData, OldOwners[35], OldOwners) == (
        26,
        Before,
        (KSyntheticGroup,),
    )
    Edited = Replace(
        KSyntheticGroup,
        GroupName=KSyntheticGroup.GroupName + " new",
        IsCollapsed=False,
        MemberIds=(54, 55),
    )
    After = (80, 54, 55, 72)
    NewBulk, NewMeta = WriteChronology(Edited, After)
    NewSpans = ReadBulkSpans(NewBulk, NewMeta)
    NewOwners = {SpanValue.ObjectId: SpanValue for SpanValue in NewSpans}
    assert ReadHistory(NewBulk, NewOwners[35], NewOwners) == (26, After, (Edited,))
    assert tuple(SpanValue.StartOffset for SpanValue in NewSpans) == tuple(
        SpanValue.StartOffset + (8 if Index >= 3 else 0)
        for Index, SpanValue in enumerate(OldSpans)
    )


# decoding a composed pair checks group adjacency across record boundaries
def TestGroupOrder() -> None:
    BulkData, MetaData = WriteChronology(KSyntheticGroup, (80, 54, 55, 72))
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in ReadBulkSpans(BulkData, MetaData)
    }
    with Raises(ValueError, match="group membership"):
        _ = ReadHistory(BulkData, Owners[35], Owners)


# unsigned boundary values and empty histories keep their native encoding
def TestHistWidths() -> None:
    Maximum = (1 << 64) - 1
    Expected = PackValue("<6xBQHIBQH", 1, 0, 0, 1, 1, Maximum, 0)
    assert EmitHistory(0, (Maximum,)) == Expected
    assert EmitHistory(Maximum, ()) == PackValue("<6xBQHI", 1, Maximum, 0, 0)
    Group = Replace(KSyntheticGroup, GroupName="🧭" * 512)
    assert ReadGroup(EmitGroup(Group)[4:], Group.ObjectId) == Group


# invalid ownership and repeated or excessive references fail at the payload boundary
def TestHistBad() -> None:
    for OwnerId in (-1, 1 << 64, False):
        with Raises(ValueError, match="reference"):
            _ = EmitHistory(OwnerId, ())
    for Entries in ((-1,), (1 << 64,), (True,), (9, 9), (5,) * 100001, [5]):
        with Raises(ValueError, match="reference"):
            _ = EmitHistory(26, CastValue(tuple[int, ...], Entries))


# group validation protects exact state and name widths before packing records
def TestGroupBad() -> None:
    for Group in (
        Replace(KSyntheticGroup, ObjectId=-1),
        Replace(KSyntheticGroup, ObjectId=1 << 64),
        Replace(KSyntheticGroup, IsCollapsed=CastValue(bool, 0)),
        Replace(KSyntheticGroup, GroupName=chr(0)),
        Replace(KSyntheticGroup, GroupName="🧭" * 513),
        Replace(KSyntheticGroup, MemberIds=()),
        Replace(KSyntheticGroup, MemberIds=(80,)),
        Replace(KSyntheticGroup, MemberIds=(55, 55)),
        Replace(KSyntheticGroup, MemberIds=(1 << 64,)),
        Replace(KSyntheticGroup, MemberIds=(5,) * 100001),
    ):
        with Raises(ValueError):
            _ = EmitGroup(Group)
