# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from struct import pack as PackData
from zipfile import ZipFile

from pytest import raises as Raises

from convert.formats.Fusion import ReadFusionDoc
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.HistoryGroup import KGroupGuid
from convert.formats.Fusion.HistoryProjection import ProjectHistory
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from tests.convert.formats.FusionParamTests import NativeText


# synthetic references isolate history ordering from physical record placement
def NativeRef(Identity: int) -> bytes:
    return PackData("<BQH", 1, Identity, 0)


# the bounded history fixture orders a later record ahead of an earlier one
def HistoryFixture(MemberId: int = 102) -> tuple[bytes, dict[int, RecordSpan]]:
    Owners: dict[int, RecordSpan] = {}
    BulkData = bytearray()
    for Identity, ClassGuid, BodyValue in (
        (100, "Owner", b""),
        (101, "Unmapped", b""),
        (
            102,
            "E3849A15-2FC6-42A0-AF3A-2F1D7273B406",
            NativeText("Revolve") + PackData("<Q", 0) + NativeText("Test sweep"),
        ),
        (
            103,
            KGroupGuid,
            b"\0\0\1\0\0\0\0"
            + PackData("<I", 1)
            + NativeRef(MemberId)
            + bytes(2)
            + NativeText("Group"),
        ),
        (
            104,
            KHistoryGuid,
            bytes(2)
            + NativeRef(100)
            + PackData("<I", 3)
            + NativeRef(103)
            + NativeRef(102)
            + NativeRef(101),
        ),
    ):
        Offset = len(BulkData)
        BulkData.extend(bytes(4) + BodyValue)
        Owners[Identity] = RecordSpan(
            Offset, Offset, len(BulkData), Identity, 256, ClassGuid, "", True
        )
    return bytes(BulkData), Owners


# group entries preserve structure without consuming a neutral feature order
def TestHistLinks() -> None:
    BulkData, Owners = HistoryFixture()
    PartValue = ProjectHistory(BulkData, Owners[104], Owners, {102: ["param"]})
    assert PartValue.EntryIds == (103, 102, 101)
    assert PartValue.Groups[0].MemberIds == (102,)
    assert PartValue.Groups[0].IsCollapsed
    First, Second = PartValue.Steps
    assert First.name == "Test sweep"
    assert First.kind == FeatureKind.KRevolution
    assert First.order == 0 and Second.order == 1
    assert First.parameter_ids == ("param",)
    assert First.attributes["fusion.history_group_id"] == 103
    assert Second.kind == FeatureKind.KNative


# group references cannot silently reorder features or borrow a neighbor
def TestHistGroup() -> None:
    BulkData, Owners = HistoryFixture(101)
    with Raises(ValueError, match="history group membership"):
        _ = ProjectHistory(BulkData, Owners[104], Owners, {})


# serialize independent index and payload records for an archive level document check
def HistoryArchive() -> bytes:
    BulkData, Owners = HistoryFixture()
    Payload = bytearray()
    Classes = bytearray()
    IndexData = bytearray()
    for CodeValue, SpanValue in enumerate(Owners.values(), start=256):
        Identity = SpanValue.ObjectId
        Classes.extend(
            NativeText(SpanValue.ClassGuid, False)
            + PackData("<IIIIQ", 0, 0, 0, 1, Identity)
        )
        IndexData.extend(PackData("<QQ", Identity, len(Payload)))
        Payload.extend(PackData("<I3sQ", 3, str(CodeValue).encode("ascii"), Identity))
        Payload.extend(BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset])
    KindValue = NativeText("FusionDesignSegmentType", False)
    MetaData = (
        KindValue
        + PackData("<IIIIII", 0, 0, 1234, 8, 0, 0)
        + KindValue
        + PackData("<IIII", 0, 1, 0, len(Owners))
        + Classes
        + PackData("<II", 0, len(Owners))
        + IndexData
        + PackData("<IQII", 0, 105, 0, 0)
    )
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        Archive.writestr(KDesignPrefix + "BulkStream.dat", Payload)
        Archive.writestr(KDesignPrefix + "MetaStream.dat", MetaData)
    return Buffer.getvalue()


# document projection retains source evidence and survives neutral interchange
def TestFusionDoc() -> None:
    DataValue = HistoryArchive()
    Document = ReadFusionDoc(DataValue, HistoryId=104)
    assert Document.validate() == ()
    assert Document.source.format_id == "fusion.f3d"
    assert Document.feature_timeline[0].name == "Test sweep"
    assert Document.metadata["fusion.history_entries"] == (103, 102, 101)
    assert Document.brep_payloads[0].data == DataValue
    assert Document.diagnostics[-1].code == "fusion.history.partial"
    assert CadDocument.from_json(Document.to_json()) == Document
    with Raises(ValueError, match="Select exactly one Fusion history"):
        _ = ReadFusionDoc(DataValue, HistoryId=42)
