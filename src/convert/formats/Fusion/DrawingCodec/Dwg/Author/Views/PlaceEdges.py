from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import SoftPointer
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
    ArbitraryAxis,
    Minus,
    TurnAngle,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import (
    IsWhole,
    RoundPoint,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    KEdgePath,
    LinePath,
    RoundPath,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.ViewEdges import EdgeRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import OwnMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBorder import (
    EntityCommon,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Cross,
    DotProduct,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewKeys import ViewKeys

KVisibleLayer = "LAYER:Visible"
KHiddenLayer = "LAYER:Hidden"
KLineCurve = 23
KRoundCurve = 11
KDraftItems = tuple[tuple[str, KDraftValue], ...]


def CachedCurve(Curve: KEdgePath) -> KDraftItems:
    if isinstance(Curve, LinePath):
        return (
            ("CurveKind", KLineCurve),
            ("StartPoint", Curve.Start),
            ("Direction", Minus(Curve.Finish, Curve.Start)),
        )
    return (
        ("CurveKind", KRoundCurve),
        ("Center", Curve.Center),
        ("Normal", Curve.Normal),
        ("RefAxis", ArbitraryAxis(Curve.Normal)),
        ("Radius", Curve.Radius),
        ("StartAngle", 0.0),
        ("EndAngle", KFullTurn),
        ("CurveReal", 0.0),
    )


def LineFields(Curve: LinePath) -> dict[str, KDraftValue]:
    IsFlat = Curve.Start[2] == 0 and Curve.Finish[2] == 0
    Fields: dict[str, KDraftValue] = {
        "ZeroDepth": int(IsFlat),
        "StartX": Curve.Start[0],
        "EndX": Curve.Finish[0],
        "StartY": Curve.Start[1],
        "EndY": Curve.Finish[1],
        "Thickness": 0.0,
        "UnitExtrusion": 1,
    }
    if not IsFlat:
        Fields.update({"StartZ": Curve.Start[2], "EndZ": Curve.Finish[2]})
    return Fields


def RoundFields(Curve: RoundPath) -> dict[str, KDraftValue]:
    Across = ArbitraryAxis(Curve.Normal)
    Upward = Cross(Curve.Normal, Across)
    Fields: dict[str, KDraftValue] = {
        "Center": (
            DotProduct(Curve.Center, Across),
            DotProduct(Curve.Center, Upward),
            DotProduct(Curve.Center, Curve.Normal),
        ),
        "Radius": Curve.Radius,
        "Thickness": 0.0,
        "Extrusion": Curve.Normal,
    }
    if IsWhole(Curve):
        return Fields
    Opening = TurnAngle(
        Minus(RoundPoint(Curve, Curve.Opening), Curve.Center), Across, Upward
    )
    Fields.update(
        {"StartAngle": Opening, "EndAngle": (Opening + Curve.Sweep) % KFullTurn}
    )
    return Fields


def EdgeRecord(Entry: EdgeRow, KeyText: str) -> DraftRecord:
    return DraftRecord(
        (
            ("EdgeId", Entry.EdgeId),
            ("EdgeLongA", 1),
            ("EdgeLongB", 1),
            ("EdgeFlagA", int(Entry.IsVisible)),
            ("EdgeLongC", 0),
            ("HasCurve", 1),
            *CachedCurve(Entry.Whole),
            ("EdgeFlagB", 0),
            ("EdgeEntity", SoftPointer(KeyText)),
        )
    )


def PlacePieceMut(
    Ledger: DraftBook, KeySet: ViewKeys, Entry: EdgeRow, KeyText: str
) -> None:
    Layer = KVisibleLayer if Entry.IsVisible else KHiddenLayer
    Piece = Entry.Piece
    if isinstance(Piece, LinePath):
        ClassName, Fields = "LINE", LineFields(Piece)
    else:
        ClassName, Fields = ("CIRCLE" if IsWhole(Piece) else "ARC"), RoundFields(Piece)
    _ = OwnMut(Ledger, KeySet.Inner, KeyText)
    _ = PlaceMut(Ledger, KeyText, ClassName, EntityCommon(KeySet.Inner, Layer), Fields)


def PlaceEdgesMut(
    Ledger: DraftBook, KeySet: ViewKeys, EdgeRows: tuple[EdgeRow, ...]
) -> tuple[DraftRecord, ...]:
    Records: list[DraftRecord] = []
    for Index, Entry in enumerate(EdgeRows):
        KeyText = f"{KeySet.Inner}/Edge{Index}"
        PlacePieceMut(Ledger, KeySet, Entry, KeyText)
        Records.append(EdgeRecord(Entry, KeyText))
    return tuple(Records)
