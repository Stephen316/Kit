from collections import Counter
from datetime import datetime as DateTime

from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    DimensionDraft,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DwgDraft import DwgDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.SheetDraft import SheetDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import FrameParts
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from tests.convert.formats.FusionCodec.Drawings.ViewSolids import BoxSolid

KMoment = DateTime(2026, 11, 12, 12, 0, 0)
KLayoutHandle = 0x2E50
KSource = ViewSource(
    0x1C5,
    "1_Component",
    "0f0e0d0c-0b0a-4908-8706-050403020100",
    (-1.0, 0.0, 0.5),
    (4.0, 2.0, 1.5),
    Solid=BoxSolid((-10.0, 0.0, 5.0), (40.0, 20.0, 15.0)),
)
KViews = (
    ViewDraft((180.46875, 120.609375), 4.0),
    ViewDraft((298.0, 120.609375), 4.0, Parent=0),
    ViewDraft((180.46875, 197.203125), 4.0, Parent=0),
)
KDimension = DimensionDraft((260.46875, 80.609375), (100.46875, 80.609375), 70.109375)


def MakeDraft(
    Views: tuple[ViewDraft, ...] = (),
    Dimensions: tuple[DimensionDraft, ...] = (),
    LayoutHandle: int = KLayoutHandle,
    SheetSize: str = "A3 Landscape",
    Version: str = "66666666-7777-4888-8999-aaaaaaaaaaaa",
) -> DwgDraft:
    Sheet = SheetDraft("Kit Sheet", (TitleText("TITLE_1", "Kit Drawing"),), SheetSize)
    return DwgDraft(
        Sheet,
        LayoutHandle,
        KMoment,
        "11111111-2222-4333-8444-555555555555",
        Version,
        Views,
        KSource if Views else None,
        Dimensions,
    )


def ReadBack(Content: bytes) -> DwgFile:
    Model = ReadDwgFile(Content)
    assert EmitDwgFile(Model) == Content
    Handles = [Entry.ObjectHandle for Entry in Model.DwgObjects]
    assert len(Handles) == len(set(Handles))
    return Model


def KindCounts(Model: DwgFile) -> Counter[str]:
    return Counter(Entry.ClassKind for Entry in Model.DwgObjects)


def FieldsOf(Model: DwgFile, ClassKind: str) -> list[dict[str, object]]:
    return [
        {Member.FieldName: Member.FieldValue for Member in Entry.ClassData.RecordFields}
        for Entry in Model.DwgObjects
        if Entry.ClassKind == ClassKind
    ]


def ItemsOf(Fields: dict[str, object]) -> tuple[DwgField, ...]:
    Items = Fields["Items"]
    assert isinstance(Items, DwgRecord)
    return Items.RecordFields


def TestNewSheet() -> None:
    Content = AuthorDwg(MakeDraft())
    assert AuthorDwg(MakeDraft()) == Content
    Model = ReadBack(Content)
    Counts = KindCounts(Model)
    assert Counts["LAYOUT"] == 2
    assert Counts["ACDBVIEWREP"] == 0
    assert Counts["DIMENSION_LINEAR"] == 0
    Layouts = [Fields["LayoutName"] for Fields in FieldsOf(Model, "LAYOUT")]
    assert set(Layouts) == {"Kit Sheet", "Model"}
    Stamps = [
        Fields
        for Fields in FieldsOf(Model, "XRECORD")
        if [(Member.FieldName, Member.FieldValue) for Member in ItemsOf(Fields)]
        == [("70", 45)]
    ]
    assert not Stamps


def TestNewShell() -> None:
    Model = ReadBack(AuthorDwg(MakeDraft()))
    Numbers = sorted(
        Section.SectionId for Section in Model.SectionInfos if Section.SectionName
    )
    assert Numbers == list(range(1, len(Numbers) + 1))
    Names = {Section.SectionName for Section in Model.SectionInfos}
    assert "AcDb:RevHistory" in Names
    assert "AcDb:AcDsPrototype_1b" not in Names
    Flags = [
        Member.FieldValue
        for Entry in Model.DwgObjects
        for Member in Entry.CommonData.RecordFields
        if Member.FieldName == "HasDsData"
    ]
    assert Flags and not any(Flags)


def HeaderShorts(Model: DwgFile) -> tuple[list[int], int]:
    Width, TailBits, _ = FrameParts(dict(Model.SectionVars)["AcDb:Header"])
    Padding = Width - 72
    Chunks = [
        (TailBits >> (Padding + 18 * (3 - Index))) & 0x3FFFF for Index in range(4)
    ]
    assert all(Chunk >> 16 == 0 for Chunk in Chunks)
    Values = [int.from_bytes(Chunk.to_bytes(2, "big"), "little") for Chunk in Chunks]
    FillMask = (1 << Padding) - 1
    return Values, (TailBits & FillMask) ^ (0x55 & FillMask)


def TestSaveShorts() -> None:
    Values, Mismatch = HeaderShorts(ReadBack(AuthorDwg(MakeDraft(KViews))))
    assert Values == [0x6666, 0x6666, 0x7777, 0x8848]
    assert Mismatch == 0
    Model = ReadBack(
        AuthorDwg(MakeDraft(Version="00000000-0000-4000-8000-000000000000"))
    )
    assert HeaderShorts(Model)[0] == [0x5555, 0x5555, 0x5555, 0x0040]


def TestNewViews() -> None:
    Model = ReadBack(AuthorDwg(MakeDraft(KViews, (KDimension,))))
    Counts = KindCounts(Model)
    assert Counts["ACDBVIEWREP"] == 3
    assert Counts["DRAWINGVIEW"] == 3
    assert Counts["ACDBVIEWREPSOURCEMGR"] == 1
    assert Counts["DIMENSION_LINEAR"] == 1
    ViewReps = [Entry for Entry in Model.DwgObjects if Entry.ClassKind == "ACDBVIEWREP"]
    RepHandles = {Entry.ObjectHandle for Entry in ViewReps}
    for Entry in ViewReps:
        Fields = {
            Member.FieldName: Member.FieldValue
            for Member in Entry.ClassData.RecordFields
        }
        assert Fields["ViewRepKey"] == Entry.ObjectHandle
        assert Fields["BodyCount"] == 1
    Listed = [
        Member.FieldValue
        for Entry in ViewReps
        for Block in Entry.EedBlocks
        for Member in Block.EedItems.RecordFields
        if Member.FieldName == "1071" and Member.FieldValue in RepHandles
    ]
    assert len(Listed) == 3 and set(Listed) == RepHandles


def TestViewPorts() -> None:
    Model = ReadBack(AuthorDwg(MakeDraft(KViews)))
    Ports = {
        Entry.ObjectHandle: Entry
        for Entry in Model.DwgObjects
        if Entry.ClassKind == "VIEWPORT"
    }
    Drawn = {Fields["Viewport"] for Fields in FieldsOf(Model, "DRAWINGVIEW")}
    for Fields in FieldsOf(Model, "ACDBVIEWREP"):
        Linked = Fields["Viewport"]
        assert isinstance(Linked, DwgHandleRef) and Linked.RefCode == 4
        assert Linked not in Drawn
        Frame = {
            Member.FieldName: Member.FieldValue
            for Member in Ports[Linked.RefValue].ClassData.RecordFields
        }
        assert Frame["ViewDirection"] == (0.0, 0.0, 1.0)
        assert Frame["ViewTarget"] == (0.0, 0.0, 0.0)


def TestDimension() -> None:
    Model = ReadBack(AuthorDwg(MakeDraft((), (KDimension,))))
    Fields = FieldsOf(Model, "DIMENSION_LINEAR")[0]
    assert Fields["Measurement"] == 160.0
    Texts = [Entry["TextValue"] for Entry in FieldsOf(Model, "MTEXT")]
    assert Texts == ["160"]


def TestNewRejects() -> None:
    with ExpectError(ValueError, match="reserved"):
        _ = AuthorDwg(MakeDraft(LayoutHandle=0))
    with ExpectError(ValueError, match="unsupported"):
        _ = AuthorDwg(MakeDraft(SheetSize="A9 Portrait"))
    with ExpectError(ValueError, match="parent"):
        _ = AuthorDwg(MakeDraft((ViewDraft((10.0, 10.0), Parent=0),)))
    Coincident = DimensionDraft((100.0, 80.0), (100.0, 80.0), 70.0)
    with ExpectError(ValueError, match="coincident"):
        _ = AuthorDwg(MakeDraft((), (Coincident,)))
