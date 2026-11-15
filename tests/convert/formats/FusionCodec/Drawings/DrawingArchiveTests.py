from dataclasses import replace as ReplaceValue

from pytest import raises as ExpectError

from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.formats.Fusion.DrawingCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry
from convert.formats.Fusion.DrawingCodec.Package.ReadPackage import ReadPackage
from convert.formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from tests.convert.formats.FusionCodec.Drawings.DwgAuthorTests import MakeDraft
from tests.convert.formats.FusionCodec.Drawings.DrawingSource import (
    DrawingSources,
    FrameReplay,
)

# the controls cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KControls = ("A0Views", "A1Dimension", "A2AutoDim")

# the tracked entity cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KTrackedEntity = "77102857"

# the sheet class cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSheetClass = "632EEBFC-0412-4AA4-9CF1-69C94F55C038"

# the source class cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSourceClass = "3EAD2723-67C3-4C8E-9B9E-1208F04C4C44"

# the boundary representation class cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBrepClass = "E4761EB7-1694-472F-BAC0-24B430387180"

# the file class cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFileClass = "3B30D852-778A-4752-9EBD-A154875C911C"

# the member layout cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KMemberLayout = EntryLayout(0, 0x0800, 0x6A9E, 0x5B6C, 46, 20, 0x81A40000)


# shared tracked count setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def TrackedCount(Drawing: FusionDrawing) -> int:
    Design = Drawing.Segments[0]
    assert isinstance(Design, ParsedSegment)
    return sum(
        len(Entry.OwnerIds)
        for Entry in Design.Metadata.Classes
        if Entry.ClassGuid.upper().startswith(KTrackedEntity)
    )


# shared class fields setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ClassFields(Drawing: FusionDrawing, ClassGuid: str) -> list[dict[str, object]]:
    Design = Drawing.Segments[0]
    assert isinstance(Design, ParsedSegment)
    return [
        {Field.FieldName: Field.Value for Field in Group.Fields}
        for Record in Design.Records
        for Group in Record.Groups
        if Group.ClassGuid.upper() == ClassGuid
    ]


# shared typed facts setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def TypedFacts(Drawing: FusionDrawing, Tracked: int) -> None:
    (Sheet,) = ClassFields(Drawing, KSheetClass)
    assert (Sheet["sheetId"], Sheet["sheetOrder"]) == ("2E50", 2)
    assert Sheet["isOutOfDate"] is False and Sheet["isDisassociated"] is False
    assert Sheet["titleBlockOccPath"] == "root"
    (Source,) = ClassFields(Drawing, KSourceClass)
    assert Source["animationMarker"] == ValuePair("", 0.0)
    assert Source["sheetIds"] == ValueSeries(("2E50",))
    assert Source["sourceId"] == "1_Component"
    Breps = ClassFields(Drawing, KBrepClass)
    assert len(Breps) == Tracked
    assert len({Entry["bodyPersistentId"] for Entry in Breps}) == 1


# the controls contract needs boundary coverage so stored document relationships remain consistent
def TestControls() -> None:
    Replay = FrameReplay()
    Drawings: dict[str, FusionDrawing] = {}
    for Label in KControls:
        DataValue = DrawingSources()[Label]
        Drawing = ReadDrawing(DataValue, Replay.Inflate)
        assert EmitDrawing(Drawing, Replay.Compress) == DataValue
        assert (Drawing.Root.Version, Drawing.Asset.Version) == (20, 20)
        assert all(isinstance(Segment, ParsedSegment) for Segment in Drawing.Segments)
        assert Drawing.Database is None and Drawing.Redirections is None
        assert Drawing.Sheet is not None and len(Drawing.Settings) == 9
        assert (Drawing.Sheet.Width, Drawing.Sheet.Height) == (420.0, 297.0)
        assert isinstance(Drawing.Sheet, SheetLayout)
        Drawings[Label] = Drawing
    for Label, Tracked in zip(KControls, (1, 3, 6), strict=True):
        assert TrackedCount(Drawings[Label]) == Tracked
        TypedFacts(Drawings[Label], Tracked)
    First, Second = Drawings["A0Views"].Root, Drawings["A1Dimension"].Root
    assert First.DocumentId == Second.DocumentId
    assert First.CurrentVersion != Second.CurrentVersion


# the bad members contract needs boundary coverage so stored document relationships remain consistent
def TestBadMembers() -> None:
    Replay = FrameReplay()
    DataValue = DrawingSources()["A0Views"]
    Drawing = ReadDrawing(DataValue, Replay.Inflate)
    Package = ReadPackage(DataValue, Replay.Inflate)
    Extra = PackageEntry("Documentation[Active]/Unknown.bin", b"x", KMemberLayout)
    Grown = EmitPackage(DrawingPackage(Package.Entries + (Extra,)), Replay.Compress)
    with ExpectError(ValueError, match="Unaccounted"):
        _ = ReadDrawing(Grown, Replay.Inflate)
    Stray = PackageEntry("Elsewhere/", b"", ReplaceValue(KMemberLayout, Method=0))
    Outside = EmitPackage(DrawingPackage(Package.Entries + (Stray,)), Replay.Compress)
    with ExpectError(ValueError, match="outside the active asset"):
        _ = ReadDrawing(Outside, Replay.Inflate)
    with ExpectError(ValueError, match="require a decoder"):
        _ = ReadDrawing(DataValue)
    Missing = PackageSlot("Documentation[Active]/Absent.json", KMemberLayout)
    Longer = ReplaceValue(Drawing, Layout=Drawing.Layout + (Missing,))
    with ExpectError(ValueError, match="absent member"):
        _ = EmitDrawing(Longer, Replay.Compress)
    Model = ReadDwgFile(AuthorDwg(MakeDraft()))
    Unnamed = DrawingDatabase("Nested/ExtFile.dwg", Model)
    with ExpectError(ValueError, match="database member"):
        _ = EmitDrawing(ReplaceValue(Drawing, Database=Unnamed), Replay.Compress)


# the drawing join contract needs boundary coverage so stored document relationships remain consistent
def TestDwgJoin() -> None:
    Replay = FrameReplay()
    DataValue = DrawingSources()["A1Dimension"]
    Drawing = ReadDrawing(DataValue, Replay.Inflate)
    (Serializer,) = ClassFields(Drawing, KFileClass)
    FileName = Serializer["persistedFileName"]
    assert isinstance(FileName, str) and FileName.startswith("ExtFile.")
    Model = ReadDwgFile(AuthorDwg(MakeDraft()))
    Joined = DrawingDatabase(FileName, Model)
    with ExpectError(ValueError, match="omits typed members"):
        _ = EmitDrawing(ReplaceValue(Drawing, Database=Joined), Replay.Compress)
    Renamed = DrawingDatabase("ExtFile.dwg", Model)
    with ExpectError(ValueError, match="disagrees with its segment"):
        _ = EmitDrawing(ReplaceValue(Drawing, Database=Renamed), Replay.Compress)
    Package = ReadPackage(DataValue, Replay.Inflate)
    Stray = PackageEntry(
        "Documentation[Active]/Dwg.BlobParts/ExtFile.dwg",
        AuthorDwg(MakeDraft()),
        KMemberLayout,
    )
    Grown = EmitPackage(DrawingPackage(Package.Entries + (Stray,)), Replay.Compress)
    with ExpectError(ValueError, match="disagrees with its segment"):
        _ = ReadDrawing(Grown, Replay.Inflate)
