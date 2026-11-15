from dataclasses import replace as ReplaceValue

from pytest import importorskip as ImportSkip
from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Author.BuildBundle import BuildBundle
from convert.formats.Fusion.DrawingCodec.Author.BuildDrawing import BuildDrawing
from convert.formats.Fusion.DrawingCodec.Author.MakeIdentity import MakeIdentity
from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordIds import PlanIds
from convert.formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from tests.convert.formats.FusionCodec.Drawings.DwgAuthorTests import (
    FieldsOf,
    KDimension,
    KLayoutHandle,
    KViews,
    MakeDraft,
)

# the design cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KDesign = DesignTarget(
    DisplayName="Kit Bracket",
    AssetId="a1a1a1a1-b2b2-4c3c-8d4d-e5e5e5e5e5e5",
    SnapshotId="b1b1b1b1-c2c2-4d3d-8e4e-f5f5f5f5f5f5",
    ChangeGuid="c1c1c1c1-d2d2-4e3e-8f4f-a5a5a5a5a5a5",
    ComponentGuid="d1d1d1d1-e2e2-4f3f-8a4a-b5b5b5b5b5b5",
    BodyPersistentId="e1e1e1e1-f2f2-4a3a-8b4b-c5c5c5c5c5c5",
    InstanceId=7,
    ComponentId=8,
    BodiesId=9,
    SketchesId=10,
)

# the database name cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KDatabaseName = "ExtFile.f1f1f1f1-a2a2-4b3b-8c4c-d5d5d5d5d5d5.dwg"

# the design data cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KDesignData = b"PK\x05\x06" + bytes(18)


# shared make specification setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def MakeSpec() -> DrawingSpec:
    return DrawingSpec(
        "Kit Bracket Drawing",
        KDesign,
        SheetSpec("Kit Sheet"),
        MakeIdentity(),
        KLayoutHandle,
    )


# the fresh ids contract needs boundary coverage so stored document relationships remain consistent
def TestFreshIds() -> None:
    First, Second = MakeIdentity(), MakeIdentity()
    assert First.DocumentId != Second.DocumentId
    assert First.DrawingFile != Second.DrawingFile
    assert len(First.DrawingToken) == 22


# the new bundle contract needs boundary coverage so stored document relationships remain consistent
def TestNewBundle() -> None:
    Codec = ImportSkip("compression.zstd")
    Content = AuthorDwg(MakeDraft(KViews, (KDimension,)))
    SpecValue = MakeSpec()
    Drawing = BuildDrawing(SpecValue, DrawingDatabase(KDatabaseName, Content))
    Bundle = BuildBundle(SpecValue, Drawing, KDesignData)
    Emitted = EmitDrawBundle(Bundle, Codec.compress)

    # shared inflate zstd setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
    def InflateZstd(Packed: bytes, Expected: int) -> bytes:
        Result = Codec.decompress(Packed)
        assert isinstance(Result, bytes) and len(Result) == Expected
        return Result

    Again = ReadDrawBundle(Emitted, InflateZstd)
    Database = Again.Drawing.Database
    assert Database is not None
    assert Database.FileName == KDatabaseName
    assert Database.Content == Content
    assert Again.Description.DesignName == "Kit Bracket Drawing"
    assert [Entry.DataValue for Entry in Again.Documents] == [KDesignData]


# the specification rejects contract needs boundary coverage so stored document relationships remain consistent
def TestSpecRejects() -> None:
    Database = DrawingDatabase(KDatabaseName, AuthorDwg(MakeDraft()))
    with ExpectError(ValueError, match="ExtFile"):
        _ = BuildDrawing(MakeSpec(), DrawingDatabase("Drawing.dwg", Database.Content))
    Broken = ReplaceValue(KDesign, AssetId="NOT-A-GUID")
    with ExpectError(ValueError, match="GUID"):
        _ = BuildDrawing(ReplaceValue(MakeSpec(), Design=Broken), Database)
    Drawing = BuildDrawing(MakeSpec(), Database)
    with ExpectError(ValueError, match="design bytes"):
        _ = BuildBundle(MakeSpec(), Drawing, b"")


# the sheet paper contract needs boundary coverage so stored document relationships remain consistent
def TestSheetPaper() -> None:
    Database = DrawingDatabase(KDatabaseName, AuthorDwg(MakeDraft()))
    Larger = ReplaceValue(MakeSpec(), Sheet=SheetSpec("Kit Sheet", "A1 Landscape"))
    Sheet = BuildDrawing(Larger, Database).Sheet
    assert Sheet is not None
    assert (Sheet.Width, Sheet.Height) == (841.0, 594.0)
    assert (Sheet.HorizontalZones, Sheet.VerticalZones) == (16, 12)
    Images = [PartValue.Name for PartValue in BuildDrawing(MakeSpec(), Database).Images]
    assert len(Images) == 3
    assert all("D3_" not in NameText for NameText in Images)
    Mixed = ReplaceValue(MakeSpec(), Sheet=SheetSpec("Kit Sheet", "B Landscape"))
    with ExpectError(ValueError, match="standard"):
        _ = BuildDrawing(Mixed, Database)


# the record ids contract needs boundary coverage so stored document relationships remain consistent
def TestRecordIds() -> None:
    Single = PlanIds(1, 1, ())
    assert (Single.Sources, Single.Sheets, Single.NextFree) == ((39,), (41,), 42)
    Several = PlanIds(2, 3, ())
    assert (Several.Sources, Several.Sheets, Several.NextFree) == (
        (39, 41),
        (43, 44, 45),
        46,
    )
    with ExpectError(ValueError, match="model source"):
        _ = PlanIds(0, 1, ())
    Database = DrawingDatabase(KDatabaseName, AuthorDwg(MakeDraft()))
    Design = BuildDrawing(MakeSpec(), Database).Segments[0]
    assert isinstance(Design, ParsedSegment)
    Numbers = sorted({Record.ObjectId for Record in Design.Records})
    assert Numbers[-3:] == [39, 40, 41]
    assert Design.Metadata.NextId == 42
    PaperTabs = [
        Fields["TabOrder"]
        for Fields in FieldsOf(ReadModel(Database), "LAYOUT")
        if Fields["LayoutName"] != "Model"
    ]
    assert SheetOrders(Design) == PaperTabs == [2]


# shared sheet orders setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def SheetOrders(Design: ParsedSegment) -> list[object]:
    return [
        Member.Value
        for Record in Design.Records
        for Group in Record.Groups
        for Member in Group.Fields
        if Member.FieldName == "sheetOrder"
    ]


# shared read model setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadModel(Database: DrawingDatabase) -> DwgFile:
    return ReadDwgFile(Database.Content)
