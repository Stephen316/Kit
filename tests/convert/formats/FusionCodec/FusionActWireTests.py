# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as Raises, skip as SkipCase

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Act.EmitActFields import EmitActFields
from convert.formats.Fusion.SegmentCodec.Act.EmitActTable import EmitActTable
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxWireId
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkStream import EmitBulkStream
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass, MetaOffset
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.WriteMetaWire import WriteMetaWire
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActFields import (
    KActFieldsGuid,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ReadActTable import (
    KActTableGuid,
    ReadActTable,
)
from tests.convert.formats.FusionProof.FusionActTableTests import (
    FrameAct,
    KActPrefix,
    KHeadGuid,
    KOtherGuid,
    KSnapshot,
    WireFields,
    WireTable,
)

# complete global roles include the chosen head in one native role
KTestRoles = tuple(
    (RoleValue, KHeadGuid if RoleValue is ActRole.KAppearance else KOtherGuid)
    for RoleValue in ActRole
)

# individual fields retain their own change tokens independent of global roles
KFieldRoles = ((ActRole.KGeometry, KHeadGuid),)

# different native route prefixes test one resolved shape and one unresolved route
KTestRoutes = ((17, "0_17"), (6, "3_9"))

# standalone plane captures provide two independently authored active assets
KFixtureRoot = "re/Fusion/Study/planedefinitions-6cd0820a832e"


# fresh bulk and metadata indexes must agree on the generated classes and identities
def MakeActPair(FieldSpace: str = "ACT") -> tuple[bytes, bytes]:
    TableData = EmitActTable(KSnapshot, KHeadGuid, KTestRoutes, KTestRoles)
    Records = (
        BulkRecord(256, 0, True, TableData),
        BulkRecord(257, 6, True, EmitActFields("3_9", KFieldRoles)),
        BulkRecord(257, 17, True, EmitActFields("0_17", KFieldRoles)),
    )
    BulkData, Entries = EmitBulkStream(Records)
    Header = MetaHeader(
        SegmentKind.KAct, 1, "", 1234, 8, (0, 0), SegmentKind.KAct.value, "", (5, 0)
    )
    MetaData = WriteMetaWire(
        MetaSegment(
            Header,
            (
                MetaClass(KActTableGuid, "", 0, "ACT", (0,)),
                MetaClass(KActFieldsGuid, "", 0, FieldSpace, (6, 17)),
            ),
            (),
            tuple(MetaOffset(ObjectId, Offset) for Offset, ObjectId, _ in Entries),
            (),
            18,
            0,
            (),
        )
    )
    return BulkData, MetaData


# emitting the fresh pair must preserve independently derived table and field syntax
def TestActWirePair() -> None:
    BulkData, MetaData = MakeActPair()
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=SegmentKind.KAct)
    TableValue = ReadActTable(BulkData, Spans)
    assert TableValue.SnapshotId == KSnapshot
    assert TableValue.HeadId == KHeadGuid
    assert TableValue.Roles == KTestRoles
    assert (
        tuple(
            (RouteRow.FieldsSpan.ObjectId, RouteRow.Key)
            for RouteRow in TableValue.Routes
        )
        == KTestRoutes
    )
    assert BulkData[Spans[0].PayloadOffset : Spans[0].EndOffset] == WireTable(
        KTestRoutes
    )
    assert tuple(
        BulkData[Span.PayloadOffset : Span.EndOffset] for Span in Spans[1:]
    ) == (WireFields("3_9"), WireFields("0_17"))
    assert [(RouteRow.Prefix, RouteRow.Residual) for RouteRow in TableValue.Routes] == [
        (0, 0),
        (3, 0),
    ]


# a plausible payload cannot make a record from the wrong namespace into act fields
def TestActWrongCls() -> None:
    BulkData, MetaData = MakeActPair("Design")
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=SegmentKind.KAct)
    with Raises(ValueError, match="Invalid Fusion ACT primary record"):
        ReadActTable(BulkData, Spans)


# malformed keys cannot name segment lanes or native identities with alternative text
@TestMarks.parametrize(
    "KeyValue",
    ("", "0_0", "1_02", "2_1", "0_1_2", "1_٢", "3_18446744073709551616"),
)
def TestBadActKey(KeyValue: str) -> None:
    with Raises(ValueError, match="Invalid Fusion ACT route key"):
        EmitActFields(KeyValue, KFieldRoles)


# route keys and field references each require their own unique canonical identity
@TestMarks.parametrize(
    "Routes",
    (
        (),
        ((0, "0_7"),),
        ((-1, "0_7"),),
        ((True, "0_7"),),
        ((KMaxWireId, "0_7"),),
        ((4, "0_7"), (4, "1_7")),
        ((4, "0_7"), (5, "0_7")),
        ((4, "1_7"), (5, "0_7")),
    ),
)
def TestBadActRows(Routes: tuple[tuple[int, str], ...]) -> None:
    with Raises(ValueError):
        EmitActTable(KSnapshot, KHeadGuid, Routes, KTestRoles)


# malformed tokens and conflicting roles must be rejected before returning bytes
@TestMarks.parametrize(
    "Roles",
    (
        (),
        (("Geometry", KHeadGuid),),
        ((ActRole.KGeometry, "not-a-uuid"),),
        ((ActRole.KGeometry, KHeadGuid.upper()),),
        ((ActRole.KGeometry, "00000000-0000-0000-0000-000000000000"),),
        ((ActRole.KGeometry, KHeadGuid), (ActRole.KGeometry, KOtherGuid)),
        ((ActRole.KProperties, KHeadGuid), (ActRole.KGeometry, KOtherGuid)),
    ),
)
def TestBadActRoles(Roles: tuple[tuple[ActRole, str], ...]) -> None:
    with Raises(ValueError):
        EmitActFields("0_7", Roles)


# global snapshot identity and role membership are independent native checks
def TestBadActHead() -> None:
    with Raises(ValueError, match="identifiers or roles"):
        EmitActTable(KHeadGuid, KHeadGuid, KTestRoutes, KTestRoles)
    with Raises(ValueError, match="identifiers or roles"):
        EmitActTable(KSnapshot, KHeadGuid, KTestRoutes, KTestRoles[1:])
    with Raises(ValueError, match="identifiers or roles"):
        EmitActTable(KHeadGuid, KSnapshot, KTestRoutes, KTestRoles)


# source only residual bytes are never included in a freshly written field
def TestActTail() -> None:
    BulkData, Spans = FrameAct(WireTable(((1, "0_7"),)), (WireFields("0_7", b"xy"),))
    (RouteRow,) = ReadActTable(BulkData, Spans).Routes
    assert RouteRow.Residual == 2
    assert EmitActFields(RouteRow.Key, RouteRow.Roles) == WireFields("0_7")


# captured schemas must match the generated payloads without passing through their bytes
@TestMarks.parametrize("FileName", ("offset.f3d", "angle.f3d"))
def TestActWireReal(FileName: str) -> None:
    SourcePath = FilePath(__file__).resolve().parents[4] / KFixtureRoot / FileName
    with ZipFile(SourcePath) as Archive:
        try:
            BulkData = Archive.read(KActPrefix + "BulkStream.dat")
            MetaData = Archive.read(KActPrefix + "MetaStream.dat")
        except NotImplementedError:
            SkipCase("The selected Python ZIP reader does not support this compression")
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=SegmentKind.KAct)
    TableValue = ReadActTable(BulkData, Spans)
    TableSpan = TableValue.TableSpan
    Routes = tuple(
        (RouteRow.FieldsSpan.ObjectId, RouteRow.Key) for RouteRow in TableValue.Routes
    )
    assert (
        EmitActTable(TableValue.SnapshotId, TableValue.HeadId, Routes, TableValue.Roles)
        == BulkData[TableSpan.PayloadOffset : TableSpan.EndOffset]
    )
    for RouteRow in TableValue.Routes:
        FieldsSpan = RouteRow.FieldsSpan
        assert (
            EmitActFields(RouteRow.Key, RouteRow.Roles)
            == BulkData[
                FieldsSpan.PayloadOffset : FieldsSpan.EndOffset - RouteRow.Residual
            ]
        )
