from dataclasses import dataclass as MakeDataClass
from math import ceil as CeilValue

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.CoverTest import (
    FlatSpan,
    IsCovered,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.FaceHits import IsHidden
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import (
    IsWhole,
    PathLength,
    PathPoint,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    SolidEdge,
    SolidShape,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import ViewFrame

KCovered = 0
KHidden = 1
KShown = 2
KSampleStep = 0.25
KFewestSamples = 16
KMostSamples = 2048
KBisections = 52
KShortPiece = 1e-6


@MakeDataClass(frozen=True, slots=True)
class EdgeScene:
    Shape: SolidShape
    Frame: ViewFrame
    Candidates: tuple[SolidEdge, ...]


@MakeDataClass(frozen=True, slots=True)
class EdgePiece:
    Begin: float
    Finish: float
    State: int


def PointState(Scene: EdgeScene, Index: int, Param: float) -> int:
    if IsCovered(Scene.Frame, Scene.Candidates, Index, Param):
        return KCovered
    Point = PathPoint(Scene.Candidates[Index].Curve, Param)
    return KHidden if IsHidden(Scene.Shape, Point, Scene.Frame.Eye) else KShown


def Bisect(
    Scene: EdgeScene, Index: int, Lower: float, Upper: float, Below: int
) -> float:
    for _ in range(KBisections):
        Middle = (Lower + Upper) / 2
        if PointState(Scene, Index, Middle) == Below:
            Lower = Middle
        else:
            Upper = Middle
    return (Lower + Upper) / 2


def SampleCount(Scene: EdgeScene, Index: int) -> int:
    Curve = Scene.Candidates[Index].Curve
    Reach = max(FlatSpan(Scene.Frame, Curve), PathLength(Curve))
    return max(KFewestSamples, min(KMostSamples, CeilValue(Reach / KSampleStep)))


def RawPieces(Scene: EdgeScene, Index: int) -> list[EdgePiece]:
    Count = SampleCount(Scene, Index)
    Params = [(Sample + 0.5) / Count for Sample in range(Count)]
    States = [PointState(Scene, Index, Param) for Param in Params]
    Breaks, Kinds = [0.0], [States[0]]
    for Sample in range(1, Count):
        if States[Sample] != States[Sample - 1]:
            Breaks.append(
                Bisect(
                    Scene, Index, Params[Sample - 1], Params[Sample], States[Sample - 1]
                )
            )
            Kinds.append(States[Sample])
    Breaks.append(1.0)
    return [
        EdgePiece(Breaks[Sample], Breaks[Sample + 1], Kinds[Sample])
        for Sample in range(len(Kinds))
    ]


def SplitPieces(Scene: EdgeScene, Index: int) -> list[EdgePiece]:
    Pieces = RawPieces(Scene, Index)
    Curve = Scene.Candidates[Index].Curve
    if IsWhole(Curve) and len(Pieces) > 1 and Pieces[0].State == Pieces[-1].State:
        Joined = EdgePiece(Pieces[-1].Begin, Pieces[0].Finish + 1.0, Pieces[0].State)
        Pieces = [Joined, *Pieces[1:-1]]
    Length = PathLength(Curve)
    return [
        Piece
        for Piece in Pieces
        if Piece.State != KCovered
        and (Piece.Finish - Piece.Begin) * Length > KShortPiece
    ]
