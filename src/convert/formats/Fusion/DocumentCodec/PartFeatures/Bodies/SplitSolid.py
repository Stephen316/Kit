from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    StackSlabs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    MergeLabels,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopPolygon
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionOp import RegionOp
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionBool import KRegion
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSealed

KSplitSides = ("1", "-1")
KSplitBodies = (2, 3)


def HalfRegion(
    Plane: PlaneSpec, Bounds: tuple[float, float], SideIndex: int, Label: FaceLabel
) -> KRegion:
    Level, Reach = Bounds
    Outer = FaceLabel("0", Label.OperationIds)
    Lower, Upper = (-Reach, Level) if SideIndex == 0 else (Level, Reach)
    if Plane.BasePlane == "yz":
        Corners = [(Lower, -Reach), (Upper, -Reach), (Upper, Reach), (Lower, Reach)]
        CutIndex = 1 if SideIndex == 0 else 3
    else:
        Corners = [(-Reach, Lower), (Reach, Lower), (Reach, Upper), (-Reach, Upper)]
        CutIndex = 2 if SideIndex == 0 else 0
    Spans = tuple(
        LineSpan(
            Corners[Index],
            Corners[(Index + 1) % 4],
            Label if Index == CutIndex else Outer,
        )
        for Index in range(4)
    )
    return (CanonLoop(Spans),)


def UprightPiece(
    Solid: PrismSolid, Plane: PlaneSpec, SideIndex: int, Label: FaceLabel
) -> tuple[PrismSlab | None, ...]:
    Level = Plane.OffsetMm / 10.0
    Points = [
        Point
        for SlabValue in Solid.Slabs
        for LoopValue in SlabValue.Loops
        for Point in LoopPolygon(LoopValue)
    ]
    Reach = 2.0 * max(abs(Value) for Point in Points for Value in Point) + 2.0 * abs(
        Level
    )
    Shaper = HalfRegion(Plane, (Level, Reach + 1.0), SideIndex, Label)
    Pieces: list[PrismSlab | None] = []
    for SlabValue in Solid.Slabs:
        Loops = RegionOp(SlabValue.Loops, Shaper, "intersect")
        Pieces.append(ReplaceValue(SlabValue, Loops=Loops) if Loops else None)
    return tuple(Pieces)


def LevelPiece(
    Solid: PrismSolid, Level: float, SideIndex: int, Label: FaceLabel
) -> tuple[PrismSlab | None, ...]:
    Pieces: list[PrismSlab | None] = []
    for SlabValue in Solid.Slabs:
        Lower, Upper = SlabValue.LowerCm, SlabValue.UpperCm
        if (Upper <= Level) if SideIndex else (Lower >= Level):
            Pieces.append(None)
        elif Lower < Level < Upper and SideIndex:
            Pieces.append(ReplaceValue(SlabValue, LowerCm=Level, FloorLabel=Label))
        elif Lower < Level < Upper:
            Pieces.append(ReplaceValue(SlabValue, UpperCm=Level, RoofLabel=Label))
        else:
            Pieces.append(SlabValue)
    return tuple(Pieces)


def SplitSolid(
    Solid: PrismSolid, Plane: PlaneSpec, Operation: int, Ordinal: int
) -> tuple[PrismSolid, PrismSolid]:
    if IsSealed(Solid):
        raise ValueError("Fusion splits take bodies that are not tapered or swept")
    Results: list[PrismSolid] = []
    for SideIndex in (0, 1):
        Label = FaceLabel(KSplitSides[SideIndex], (Operation,))
        if Plane.BasePlane == "xy":
            Pieces = LevelPiece(Solid, Plane.OffsetMm / 10.0, SideIndex, Label)
        else:
            Pieces = UprightPiece(Solid, Plane, SideIndex, Label)
        if not any(Piece is not None for Piece in Pieces):
            raise ValueError("Fusion split planes must cross the body")
        Marker = FaceLabel(str(Operation), (), KSplitBodies[SideIndex])
        Results.append(
            ReplaceValue(
                Solid,
                Slabs=StackSlabs(list(Pieces)),
                BodyLabel=MergeLabels(Solid.BodyLabel, Marker),
                Ordinal=Ordinal if SideIndex else Solid.Ordinal,
            )
        )
    return Results[0], Results[1]
