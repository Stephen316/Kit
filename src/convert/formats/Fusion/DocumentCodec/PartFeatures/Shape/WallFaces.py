from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ChainUses import ChainUses
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelSplit import (
    KPointTable,
    LevelPoints,
    PointTable,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.RiseEdge import RiseEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallBounds import (
    KLevelMap,
    KSides,
    GroupLevels,
    GroupSides,
    SideBreaks,
    SideUses,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallGroups import (
    WallGroups,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallPiece import WallPiece
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import (
    IsSameRing,
    SlabPairs,
    SlabRoof,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
    SpanFinish,
)


def SeatLoop(
    Slabs: tuple[PrismSlab, ...], Index: int, LoopValue: KPlaneLoop, Upright: bool
) -> KPlaneLoop:
    if Upright or not Index:
        return LoopValue
    Below = SlabRoof(Slabs[Index - 1])
    return next((Other for Other in Below if IsSameRing(Other, LoopValue)), LoopValue)


def WallFor(
    Spans: tuple[KPlaneSpan, KPlaneSpan, KPlaneSpan],
    Joints: tuple[tuple[float, float], ...],
    Lower: float,
    Upper: float,
) -> WallFace:
    SpanValue, RoofSpan, SeatSpan = Spans
    Bottom = LevelEdge(SeatSpan, Lower)
    TopValue = LevelEdge(RoofSpan, Upper)
    Flared = None if RoofSpan == SpanValue else RoofSpan
    if IsFullCircle(SpanValue):
        Loops = ((ShapeUse(Bottom, True),), (ShapeUse(TopValue, False),))
        return WallFace(SpanValue, Lower, Upper, Loops, Flared)
    if Flared is not None and not isinstance(Flared, LineSpan):
        raise ValueError("Fusion part tapered walls must be full circles or planes")
    Summits = (Joints[2], Joints[3]) if Flared is not None else (None, None)
    RingValue = (
        ShapeUse(Bottom, True),
        ShapeUse(RiseEdge(Joints[1], Lower, Upper, Summits[1]), True),
        ShapeUse(TopValue, False),
        ShapeUse(RiseEdge(Joints[0], Lower, Upper, Summits[0]), False),
    )
    return WallFace(SpanValue, Lower, Upper, (RingValue,), Flared)


def SlabEntries(Slabs: tuple[PrismSlab, ...]) -> list[WallPiece | WallFace]:
    Entries: list[WallPiece | WallFace] = []
    for Index, SlabValue in enumerate(Slabs):
        Bounds = (SlabValue.LowerCm, SlabValue.UpperCm)
        for LoopValue, RoofValue in SlabPairs(SlabValue):
            Upright = LoopValue == RoofValue
            SeatValue = SeatLoop(Slabs, Index, LoopValue, Upright)
            for Place, SpanValue in enumerate(LoopValue):
                Joints = (SpanFinish(LoopValue[Place - 1]), SpanFinish(SpanValue))
                if Upright:
                    Entries.append(WallPiece(SpanValue, *Bounds, Joints))
                    continue
                Spans = (SpanValue, RoofValue[Place], SeatValue[Place])
                Summits = (
                    SpanFinish(RoofValue[Place - 1]),
                    SpanFinish(RoofValue[Place]),
                )
                Entries.append(WallFor(Spans, Joints + Summits, *Bounds))
    return Entries


def GroupFace(
    Members: list[WallPiece],
    Sides: tuple[KSides, dict[tuple[float, float], list[float]]],
    Points: KLevelMap,
    Table: KPointTable,
) -> WallFace:
    Bottoms, TopUses = GroupLevels(Members, Points, Table)
    Upward, Downward = SideUses(Sides[0], Sides[1], Table)
    Loops = ChainUses(Bottoms + Upward + TopUses + Downward)
    Lower = min(Member.LowerCm for Member in Members)
    Upper = max(Member.UpperCm for Member in Members)
    return WallFace(Members[0].Span, Lower, Upper, Loops)


def WallFaces(Slabs: tuple[PrismSlab, ...]) -> tuple[WallFace, ...]:
    Entries = SlabEntries(Slabs)
    Pieces = [Entry for Entry in Entries if isinstance(Entry, WallPiece)]
    Groups = WallGroups(Pieces)
    Members = [[Pieces[Index] for Index in Group] for Group in Groups]
    Sides = [GroupSides(Items) for Items in Members]
    Breaks = SideBreaks(Sides)
    Table, Points = PointTable(Slabs), LevelPoints(Slabs)
    Leaders = {Group[0]: Number for Number, Group in enumerate(Groups)}
    Faces: list[WallFace] = []
    Counter = 0
    for Entry in Entries:
        if isinstance(Entry, WallFace):
            Faces.append(Entry)
            continue
        Number = Leaders.get(Counter)
        Counter += 1
        if Number is not None:
            Context = (Sides[Number], Breaks)
            Faces.append(GroupFace(Members[Number], Context, Points, Table))
    return tuple(Faces)
