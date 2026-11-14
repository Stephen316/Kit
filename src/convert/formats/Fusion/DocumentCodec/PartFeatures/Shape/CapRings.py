from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ChainUses import ChainUses
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelSplit import (
    KPointTable,
    LoopPoints,
    SplitSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import IsInRegion
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SideProbe import SideProbe
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import SlabRoof

KRegions = tuple[tuple[KPlaneLoop, ...], tuple[KPlaneLoop, ...]]


def IsCapSide(Regions: KRegions, Point: tuple[float, float]) -> bool:
    return IsInRegion(Regions[0], Point) and not IsInRegion(Regions[1], Point)


def RingPieces(
    LoopValue: KPlaneLoop,
    Regions: KRegions,
    Place: tuple[float, bool],
    Table: KPointTable,
) -> list[ShapeUse]:
    Level, Upward = Place
    Points = LoopPoints(Regions[0] + Regions[1])
    Pieces: list[ShapeUse] = []
    for SpanValue in LoopValue:
        for Piece in SplitSpan(SpanValue, Points, Table):
            LeftPoint, RightPoint = SideProbe(Piece)
            IsLeftIn = IsCapSide(Regions, LeftPoint)
            if IsLeftIn != IsCapSide(Regions, RightPoint):
                Pieces.append(ShapeUse(LevelEdge(Piece, Level), IsLeftIn == Upward))
    if Pieces and not Pieces[0].Forward:
        Pieces.reverse()
    return Pieces


def CapRings(
    Level: float,
    Upward: bool,
    Below: PrismSlab | None,
    Above: PrismSlab | None,
    Table: KPointTable,
) -> tuple[tuple[ShapeUse, ...], ...]:
    BelowLoops = () if Below is None else SlabRoof(Below)
    AboveLoops = () if Above is None else Above.Loops
    Regions = (BelowLoops, AboveLoops) if Upward else (AboveLoops, BelowLoops)
    Candidates = [
        LoopValue for LoopValue in BelowLoops if LoopValue not in AboveLoops
    ] + [LoopValue for LoopValue in AboveLoops if LoopValue not in BelowLoops]
    UseList: list[ShapeUse] = []
    for LoopValue in Candidates:
        Pieces = RingPieces(LoopValue, Regions, (Level, Upward), Table)
        UseList.extend(UseValue for UseValue in Pieces if UseValue not in UseList)
    return ChainUses(UseList)
