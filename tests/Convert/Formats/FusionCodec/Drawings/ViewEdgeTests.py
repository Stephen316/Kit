from dataclasses import replace as Replaced
from math import pi as KHalfTurn

from pytest import raises as ExpectError

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Edges.ReadSolid import ReadSolid
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import LinePath
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Edges.ViewEdges import (
    EdgeRow,
    ViewEdges,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    BaseFrame,
    ChildFrame,
    ViewFrame,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.Formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from tests.Convert.Formats.FusionCodec.Drawings.DwgAuthorTests import (
    KViews,
    MakeDraft,
)
from tests.Convert.Formats.FusionCodec.Drawings.ViewSolids import (
    BallSurface,
    BoxFaces,
    BuildSolid,
    HoleSolid,
)

# the lower cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KLower = (0.0, 0.0, 0.0)

# the upper cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KUpper = (40.0, 20.0, 10.0)

# the hole cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KHole = HoleSolid(KLower, KUpper, (10.0, 10.0), 4.0)

# the source cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSource = ViewSource(
    0x1C5,
    "1_Component",
    "0f0e0d0c-0b0a-4908-8706-050403020100",
    (0.0, 0.0, 0.0),
    (4.0, 2.0, 1.0),
    Solid=KHole,
)

# the base cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBase = BaseFrame(ViewDraft((0.0, 0.0)))

# the silhouettes cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSilhouettes = (0xFFFFFFFE, 0xFFFFFFFF)


# shared rows of setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RowsOf(Frame: ViewFrame, ShowHidden: bool) -> tuple[EdgeRow, ...]:
    return ViewEdges(ReadSolid(KHole, KLower, KUpper), Frame, ShowHidden)


# shared line at setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LineAt(Entry: EdgeRow) -> tuple[tuple[float, ...], tuple[float, ...]]:
    assert isinstance(Entry.Piece, LinePath)
    return (
        tuple(round(Value, 6) for Value in Entry.Piece.Start),
        tuple(round(Value, 6) for Value in Entry.Piece.Finish),
    )


# the hole edges contract needs boundary coverage so stored document relationships remain consistent
def TestHoleEdges() -> None:
    for ShowHidden in (False, True):
        EdgeRows = RowsOf(KBase, ShowHidden)
        assert [Entry.EdgeId for Entry in EdgeRows] == [1, 2, 6, 9, 12]
        assert all(Entry.IsVisible for Entry in EdgeRows)
    Right = ChildFrame(KBase, (1.0, 0.0))
    assert [Entry.EdgeId for Entry in RowsOf(Right, False)] == [5, 6, 7, 8]
    Hidden = RowsOf(Right, True)
    assert [Entry.EdgeId for Entry in Hidden] == [*KSilhouettes, 5, 6, 7, 8]
    assert [Entry.IsVisible for Entry in Hidden[:2]] == [False, False]
    assert LineAt(Hidden[0]) == ((10.0, 14.0, 0.0), (10.0, 14.0, 10.0))
    assert LineAt(Hidden[1]) == ((10.0, 6.0, 0.0), (10.0, 6.0, 10.0))
    Above = RowsOf(ChildFrame(KBase, (0.0, 1.0)), True)
    assert [Entry.EdgeId for Entry in Above] == [*KSilhouettes, 8, 9, 10, 11]
    assert LineAt(Above[0])[0] == (14.0, 10.0, 0.0)
    assert LineAt(Above[1])[0] == (6.0, 10.0, 0.0)


# the edge on ring contract needs boundary coverage so stored document relationships remain consistent
def TestEdgeOnRing() -> None:
    EdgeRows = RowsOf(ChildFrame(KBase, (1.0, 0.0)), True)
    assert 0 not in [Entry.EdgeId for Entry in EdgeRows]
    Behind = BaseFrame(ViewDraft((0.0, 0.0), 1.0, (0.0, 0.0, 1.0)))
    assert [Entry.EdgeId for Entry in RowsOf(Behind, True)] == [0, 4, 7, 10, 13]


# shared edge records setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def EdgeRecords(Model: DwgFile) -> list[tuple[int, tuple[DwgRecord, ...]]]:
    Found: list[tuple[int, tuple[DwgRecord, ...]]] = []
    for Entry in Model.DwgObjects:
        if Entry.ClassKind != "ACDBVIEWREP":
            continue
        Fields = {
            Member.FieldName: Member.FieldValue
            for Member in Entry.ClassData.RecordFields
        }
        Bodies = Fields["Bodies"]
        assert isinstance(Bodies, tuple) and isinstance(Bodies[0], DwgRecord)
        Edges = {
            Member.FieldName: Member.FieldValue for Member in Bodies[0].RecordFields
        }["Edges"]
        assert isinstance(Edges, tuple)
        Style = Fields["ViewLongB"]
        assert isinstance(Style, int)
        Found.append(
            (
                Style,
                tuple(
                    EdgeItem for EdgeItem in Edges if isinstance(EdgeItem, DwgRecord)
                ),
            )
        )
    return Found


# shared field map setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def FieldMap(Record: DwgRecord) -> dict[str, object]:
    return {Member.FieldName: Member.FieldValue for Member in Record.RecordFields}


# shared authored edges setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def AuthoredEdges(ShowHidden: bool) -> list[tuple[int, tuple[DwgRecord, ...]]]:
    Views = tuple(Replaced(Drafted, ShowHidden=ShowHidden) for Drafted in KViews)
    return EdgeRecords(
        ReadDwgFile(AuthorDwg(Replaced(MakeDraft(Views), Source=KSource)))
    )


# the stored edges contract needs boundary coverage so stored document relationships remain consistent
def TestStoredEdges() -> None:
    for ShowHidden, Styles, Counts in (
        (False, [2, 6, 6], [5, 4, 4]),
        (True, [1, 5, 5], [5, 6, 6]),
    ):
        Found = AuthoredEdges(ShowHidden)
        assert [Style for Style, _ in Found] == Styles
        assert [len(Edges) for _, Edges in Found] == Counts
    Model = ReadDwgFile(AuthorDwg(Replaced(MakeDraft(KViews), Source=KSource)))
    Circle = FieldMap(EdgeRecords(Model)[0][1][0])
    assert (Circle["EdgeId"], Circle["EdgeFlagA"], Circle["CurveKind"]) == (1, 1, 11)
    assert Circle["Center"] == (10.0, 10.0, 0.0)
    assert Circle["Normal"] == (0.0, 0.0, -1.0)
    assert Circle["RefAxis"] == (-1.0, 0.0, 0.0)
    assert (Circle["StartAngle"], Circle["EndAngle"]) == (0.0, 2 * KHalfTurn)
    Kinds = {Entry.ClassKind for Entry in Model.DwgObjects}
    assert {"LINE", "CIRCLE"} <= Kinds
    Drawn = [Entry for Entry in Model.DwgObjects if Entry.ClassKind == "CIRCLE"]
    assert FieldMap(Drawn[0].ClassData)["Center"] == (-10.0, 10.0, 0.0)


# the edge rejects contract needs boundary coverage so stored document relationships remain consistent
def TestEdgeRejects() -> None:
    with ExpectError(ValueError, match="solid"):
        _ = AuthorDwg(Replaced(MakeDraft(KViews), Source=Replaced(KSource, Solid=None)))
    Outside = HoleSolid(KLower, (50.0, 20.0, 10.0), (10.0, 10.0), 4.0)
    with ExpectError(ValueError, match="outside"):
        _ = ReadSolid(Outside, KLower, KUpper)
    Faces = BoxFaces(KLower, KUpper)
    Faces[0] = (BallSurface((20.0, 10.0, 5.0), 5.0), Faces[0][1])
    with ExpectError(ValueError, match="SphereSurface"):
        _ = ReadSolid(BuildSolid(tuple(Faces)), KLower, KUpper)
    Mixed = (KViews[0], Replaced(KViews[1], ShowHidden=True), KViews[2])
    with ExpectError(ValueError, match="hidden"):
        _ = AuthorDwg(Replaced(MakeDraft(Mixed), Source=KSource))
