from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.CoverTest import FlatSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import (
    IsWhole,
    PathPiece,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.Silhouettes import (
    Silhouettes,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    KEdgePath,
    RoundPath,
    SolidShape,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SplitPieces import (
    KShown,
    EdgePiece,
    EdgeScene,
    SplitPieces,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import ViewFrame

KPointGap = 1e-9
KWholeGap = 1e-9
KSignBit = 1 << 31
KWordSpan = 1 << 32


@MakeDataClass(frozen=True, slots=True)
class EdgeRow:
    EdgeId: int
    IsVisible: bool
    Whole: KEdgePath
    Piece: KEdgePath


def RowOrder(Entry: EdgeRow) -> int:
    return Entry.EdgeId - KWordSpan if Entry.EdgeId >= KSignBit else Entry.EdgeId


def PieceRow(EdgeId: int, Curve: KEdgePath, KeptPieces: EdgePiece) -> EdgeRow:
    if isinstance(Curve, RoundPath) and not IsWhole(Curve):
        raise ValueError(
            f"Authored DWG view edge {EdgeId} is a part arc; no recorded cached form"
        )
    IsFull = KeptPieces.Begin < KWholeGap and KeptPieces.Finish > 1 - KWholeGap
    Piece = Curve if IsFull else PathPiece(Curve, KeptPieces.Begin, KeptPieces.Finish)
    return EdgeRow(EdgeId, KeptPieces.State == KShown, Curve, Piece)


def ViewEdges(
    Shape: SolidShape, Frame: ViewFrame, ShowHidden: bool
) -> tuple[EdgeRow, ...]:
    Drawn = tuple(
        Entry for Entry in Shape.Edges if FlatSpan(Frame, Entry.Curve) > KPointGap
    )
    Scene = EdgeScene(Shape, Frame, Drawn + Silhouettes(Shape, Frame.Eye))
    EdgeRows: list[EdgeRow] = []
    for Index, Entry in enumerate(Scene.Candidates):
        AllPieces = SplitPieces(Scene, Index)
        if len(AllPieces) > 1:
            raise ValueError(
                f"Authored DWG view edge {Entry.EdgeId} splits; no split edge form"
            )
        KeptPieces = [
            Piece for Piece in AllPieces if ShowHidden or Piece.State == KShown
        ]
        if KeptPieces:
            EdgeRows.append(PieceRow(Entry.EdgeId, Entry.Curve, KeptPieces[0]))
    return tuple(sorted(EdgeRows, key=RowOrder))
