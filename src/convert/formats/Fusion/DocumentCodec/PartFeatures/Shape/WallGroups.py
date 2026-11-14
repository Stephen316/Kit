from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelSplit import LineRatio
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallPiece import WallPiece
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanHeading

KGroupLimit = 1e-9


def IsCollinear(Lower: LineSpan, Upper: LineSpan) -> bool:
    HeadX, HeadY = SpanHeading(Lower, False)
    OtherX, OtherY = SpanHeading(Upper, False)
    if HeadX * OtherX + HeadY * OtherY < 1.0 - KGroupLimit:
        return False
    Start = LineRatio(Lower, Upper.StartCm)
    Finish = LineRatio(Lower, Upper.FinishCm)
    if Start is None or Finish is None:
        return False
    return min(1.0, Finish) - max(0.0, Start) > KGroupLimit


def IsContinued(Lower: KPlaneSpan, Upper: KPlaneSpan) -> bool:
    if Lower == Upper:
        return True
    if Lower.Label != Upper.Label:
        return False
    if not isinstance(Lower, LineSpan) or not isinstance(Upper, LineSpan):
        return False
    return IsCollinear(Lower, Upper)


def RootOf(Parents: list[int], Index: int) -> int:
    Current = Index
    while Parents[Current] != Current:
        Current = Parents[Current]
    return Current


def WallGroups(Pieces: list[WallPiece]) -> list[list[int]]:
    Parents = list(range(len(Pieces)))
    for Index, Piece in enumerate(Pieces):
        for Prior in range(Index):
            Other = Pieces[Prior]
            if Other.UpperCm != Piece.LowerCm:
                continue
            if not IsContinued(Other.Span, Piece.Span):
                continue
            Roots = sorted((RootOf(Parents, Prior), RootOf(Parents, Index)))
            Parents[Roots[1]] = Roots[0]
    Groups: dict[int, list[int]] = {}
    for Index in range(len(Pieces)):
        Groups.setdefault(RootOf(Parents, Index), []).append(Index)
    return list(Groups.values())
