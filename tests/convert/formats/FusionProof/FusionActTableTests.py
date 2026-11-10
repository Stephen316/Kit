# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as ReplaceRecord
from pathlib import Path as FilePath
from struct import pack as PackData
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as Raises

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ReadActTable import (
    ReadActTable,
)

# synthetic identifiers distinguish the archive snapshot from an individual role change
KSnapshot = "12345678-1234-4123-8123-123456789abc"

# the table head is valid only when a global role refers to the same identifier
KHeadGuid = "abcdef12-abcd-4abc-8abc-abcdef123456"

# a third token supports valid independent roles and invalid foreign head cases
KOtherGuid = "456789ab-4567-4456-8456-456789abcdef"

# independent wire labels make the synthetic fixtures detect vocabulary changes
KRoleNames = (
    "Appearance",
    "Geometry",
    "PhysicalMaterial",
    "Properties",
    "StructureChange",
    "Transform",
)

# the archive path separates genuine active records from other zip members
KActPrefix = "FusionAssetName[Active]/FusionACTSegmentType1/"


# fixture text uses character counts so wide key bounds can be tested precisely
def WireText(TextValue: str, WideText: bool = False) -> bytes:
    return PackData("<I", len(TextValue)) + TextValue.encode(
        "utf-16le" if WideText else "ascii"
    )


# distinct tokens make misplaced or incomplete global role maps observable
def WireRoles(
    RoleNames: tuple[str, ...] = KRoleNames, FirstGuid: str = KHeadGuid
) -> bytes:
    return PackData("<I", len(RoleNames)) + b"".join(
        WireText(NameValue) + WireText(FirstGuid if Index == 0 else KOtherGuid, True)
        for Index, NameValue in enumerate(RoleNames)
    )


# configurable index references expose framing and reciprocity errors independently
def WireTable(
    RouteRows: tuple[tuple[int, str], ...],
    *,
    HeadGuid: str = KHeadGuid,
    RoleNames: tuple[str, ...] = KRoleNames,
) -> bytes:
    return (
        WireText("ACTTable")
        + PackData("<HI", 0, len(RouteRows))
        + b"".join(
            PackData("<BQH", 1, FieldsId, 0) + WireText(KeyValue, True)
            for FieldsId, KeyValue in RouteRows
        )
        + WireText(KSnapshot, True)
        + WireText(HeadGuid, True)
        + bytes(4)
        + WireRoles(RoleNames)
    )


# complete field records permit independent changes to roles key or unknown tail
def WireFields(KeyValue: str, TailValue: bytes = b"") -> bytes:
    return bytes(6) + WireRoles(("Geometry",)) + WireText(KeyValue, True) + TailValue


# payload tests vary one field while keeping the indexed span boundary valid
def FrameAct(
    TableData: bytes, FieldsData: tuple[bytes, ...]
) -> tuple[bytes, tuple[RecordSpan, ...]]:
    Records: list[RecordSpan] = []
    Buffer = bytearray()
    for Identity, Payload in enumerate((TableData, *FieldsData)):
        Start = len(Buffer)
        CodeValue = 256 if Identity == 0 else 257
        ClassGuid = (
            "8EF12734-4D22-4F6A-8A80-1462E6B40A13"
            if Identity == 0
            else "ABC8C0E3-50FB-4E8C-AFF3-116759A36073"
        )
        Buffer.extend(PackData("<I3sQ", 3, str(CodeValue).encode("ascii"), Identity))
        Buffer.extend(Payload)
        Records.append(
            RecordSpan(
                Start,
                Start + 15,
                len(Buffer),
                Identity,
                CodeValue,
                ClassGuid,
                "ACT",
                True,
            )
        )
    return bytes(Buffer), tuple(Records)


# route evidence keeps owner identity separate from the act field identity and tail
def TestActRoutes() -> None:
    DataValue, Spans = FrameAct(
        WireTable(((2, "0_44"), (1, "3_900"))),
        (WireFields("3_900"), WireFields("0_44", b"xy")),
    )
    TableValue = ReadActTable(DataValue, Spans)
    assert TableValue.TableSpan == Spans[0]
    assert (TableValue.SnapshotId, TableValue.HeadId) == (KSnapshot, KHeadGuid)
    assert tuple(RoleValue.value for RoleValue, _ in TableValue.Roles) == KRoleNames
    assert dict(TableValue.Roles)[ActRole.KAppearance] == KHeadGuid
    assert tuple(
        (
            RouteRow.Key,
            RouteRow.Prefix,
            RouteRow.OwnerId,
            RouteRow.FieldsSpan,
            RouteRow.Residual,
        )
        for RouteRow in TableValue.Routes
    ) == (
        ("0_44", 0, 44, Spans[2], 2),
        ("3_900", 3, 900, Spans[1], 0),
    )
    assert TableValue.Routes[1].Roles == ((ActRole.KGeometry, KHeadGuid),)


# wire mutations distinguish a valid index from a lookalike with corrupted routing
@TestMarks.parametrize(
    ("TableData", "FieldsData"),
    (
        (WireTable(()), ()),
        (
            WireText("ACTTable") + PackData("<HI", 0, 65537),
            (),
        ),
        (
            WireTable(((1, "0_44"), (2, "0_44"))),
            (WireFields("0_44"), WireFields("0_44")),
        ),
        (
            WireTable(((1, "0_44"), (1, "1_55"))),
            (WireFields("0_44"), WireFields("1_55")),
        ),
        (WireTable(((1, "0_44"),)), (WireFields("0_45"),)),
        (WireTable(((1, "0_044"),)), (WireFields("0_044"),)),
        (WireTable(((1, "0_0"),)), (WireFields("0_0"),)),
        (
            WireTable(((1, "0_18446744073709551616"),)),
            (WireFields("0_18446744073709551616"),),
        ),
        (WireTable(((1, "2_44"),)), (WireFields("2_44"),)),
        (
            WireTable(((1, "1_55"), (2, "0_44"))),
            (WireFields("1_55"), WireFields("0_44")),
        ),
        (WireTable(((2, "0_44"),)), (WireFields("0_44"),)),
        (WireTable(((1, "0_44"),)), (WireFields("0_44"), WireFields("1_55"))),
        (WireTable(((1, "0_44"),)), (WireFields("0_44", b"x"),)),
        (
            WireTable(((1, "0_44"), (2, "1_55"))),
            (WireFields("0_44", b"xy"), WireFields("1_55")),
        ),
        (WireTable(((1, "0_44"),)) + b"x", (WireFields("0_44"),)),
        (WireTable(((1, "0_44"),), HeadGuid=KSnapshot), (WireFields("0_44"),)),
        (WireTable(((1, "0_44"),), HeadGuid=KHeadGuid.upper()), (WireFields("0_44"),)),
        (
            WireTable(((1, "0_44"),), HeadGuid="fedcba98-fedc-4fed-8fed-fedcba987654"),
            (WireFields("0_44"),),
        ),
        (WireTable(((1, "0_44"),), RoleNames=KRoleNames[:-1]), (WireFields("0_44"),)),
        (
            WireTable(((1, "0_44"),), RoleNames=("Unknown", *KRoleNames[1:])),
            (WireFields("0_44"),),
        ),
        (
            WireTable(((1, "0_44"),), RoleNames=(*KRoleNames[:-1], KRoleNames[-2])),
            (WireFields("0_44"),),
        ),
        (
            WireTable(((1, "0_44"),)).replace(
                PackData("<BQH", 1, 1, 0), PackData("<BQH", 0, 1, 0), 1
            ),
            (WireFields("0_44"),),
        ),
        (WireTable(((1, "0_44"),)), (b"\1" + WireFields("0_44")[1:],)),
    ),
)
def TestActBadWire(TableData: bytes, FieldsData: tuple[bytes, ...]) -> None:
    with Raises(ValueError):
        _ = ReadActTable(*FrameAct(TableData, FieldsData))


# indexed class namespace and exact extent must corroborate each data record
def TestActBadSpans() -> None:
    DataValue, Spans = FrameAct(WireTable(((1, "1_44"),)), (WireFields("1_44"),))
    TableSpan, FieldsSpan = Spans
    for BadSpans in (
        (FieldsSpan,),
        (TableSpan, TableSpan, FieldsSpan),
        (TableSpan, FieldsSpan, FieldsSpan),
        (ReplaceRecord(TableSpan, ObjectId=1), FieldsSpan),
        (TableSpan, ReplaceRecord(FieldsSpan, ClassSpace="Design")),
        (TableSpan, ReplaceRecord(FieldsSpan, ClassGuid=TableSpan.ClassGuid)),
        (TableSpan, ReplaceRecord(FieldsSpan, IsPrimary=False)),
        (TableSpan, ReplaceRecord(FieldsSpan, EndOffset=len(DataValue) + 1)),
    ):
        with Raises(ValueError):
            _ = ReadActTable(DataValue, BadSpans)


# captured cases protect exceptional route prefixes and opaque field boundaries
@TestMarks.parametrize(
    ("RelativePath", "ExpectedKey", "ExpectedTail"),
    (
        ("boundaryfills-a0953038318b/plane_first.f3d", "3_22", 0),
        ("componentcolorcontrast-775cb30dfc1e/known_component_color.f3d", "1_6", 2),
        ("namedvertexprobe-8d81619f74e6/scale_rational_vertex2.f3d", "0_273", 2),
        ("timeline-expanded-2396e32f2574/expanded.f3d", "0_386", 2),
    ),
)
def TestActCaptures(RelativePath: str, ExpectedKey: str, ExpectedTail: int) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    with ZipFile(RootPath / "re/Fusion/Study" / RelativePath) as Archive:
        DataValue = Archive.read(KActPrefix + "BulkStream.dat")
        MetaData = Archive.read(KActPrefix + "MetaStream.dat")
    Spans = ReadBulkSpans(DataValue, MetaData, Segment=SegmentKind.KAct)
    TableValue = ReadActTable(DataValue, Spans)
    Routes = {Value.Key: Value for Value in TableValue.Routes}
    assert Routes[ExpectedKey].Residual == ExpectedTail
    assert TableValue.HeadId in dict(TableValue.Roles).values()
