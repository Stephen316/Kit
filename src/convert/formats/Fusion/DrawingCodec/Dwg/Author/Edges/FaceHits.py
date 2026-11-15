from math import atan2 as ArcTangent
from math import cos as Cosine
from math import hypot as Distance
from math import sin as SineOf
from math import sqrt as SquareRoot

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
    Combine,
    Minus,
    TurnAngle,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    FlatArc,
    FlatFace,
    FlatLine,
    KPointPair,
    KPointTriple,
    RoundFace,
    SolidShape,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    DotProduct,
    Scaled,
)

# reach must remain consistent across callers so projected boundaries retain their intended visibility and geometry
KReach = 1e-6

# edge gap must remain consistent across callers so projected boundaries retain their intended visibility and geometry
KEdgeGap = 1e-6

# flat gap must remain consistent across callers so projected boundaries retain their intended visibility and geometry
KFlatGap = 1e-12

# ray angle must remain consistent across callers so projected boundaries retain their intended visibility and geometry
KRayAngle = 0.5772156649015329

# the ray step order must stay explicit so projected boundaries retain their intended visibility and geometry
KRayStep = (Cosine(KRayAngle), SineOf(KRayAngle))


# the on sweep decision must stay consistent so projected boundaries retain their intended visibility and geometry
def IsOnSweep(Angle: float, Opening: float, Sweep: float) -> bool:
    return Sweep >= KFullTurn - KFlatGap or (Angle - Opening) % KFullTurn <= Sweep


# the border gap contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def BorderGap(Bound: FlatLine | FlatArc, Point: KPointPair) -> float:
    if isinstance(Bound, FlatLine):
        StepX = Bound.Finish[0] - Bound.Start[0]
        StepY = Bound.Finish[1] - Bound.Start[1]
        Square = StepX * StepX + StepY * StepY
        Share = (Point[0] - Bound.Start[0]) * StepX + (
            Point[1] - Bound.Start[1]
        ) * StepY
        Share = min(1.0, max(0.0, Share / Square)) if Square > 0 else 0.0
        return Distance(
            Point[0] - Bound.Start[0] - Share * StepX,
            Point[1] - Bound.Start[1] - Share * StepY,
        )
    DeltaX, DeltaY = Point[0] - Bound.Center[0], Point[1] - Bound.Center[1]
    if IsOnSweep(ArcTangent(DeltaY, DeltaX), Bound.Opening, Bound.Sweep):
        return abs(Distance(DeltaX, DeltaY) - Bound.Radius)
    return min(
        Distance(
            Point[0] - Bound.Center[0] - Bound.Radius * Cosine(Angle),
            Point[1] - Bound.Center[1] - Bound.Radius * SineOf(Angle),
        )
        for Angle in (Bound.Opening, Bound.Opening + Bound.Sweep)
    )


# the count operation needs one geometric convention so projected boundaries retain their intended visibility and geometry
def CrossCount(Bound: FlatLine | FlatArc, Point: KPointPair) -> int:
    StepX, StepY = KRayStep
    if isinstance(Bound, FlatLine):
        SpanX = Bound.Finish[0] - Bound.Start[0]
        SpanY = Bound.Finish[1] - Bound.Start[1]
        Divisor = StepX * SpanY - StepY * SpanX
        if abs(Divisor) < KFlatGap:
            return 0
        ShiftX, ShiftY = Bound.Start[0] - Point[0], Bound.Start[1] - Point[1]
        Reach = (ShiftX * SpanY - ShiftY * SpanX) / Divisor
        Share = (ShiftX * StepY - ShiftY * StepX) / Divisor
        return int(Reach > 0 and 0 <= Share < 1)
    ShiftX, ShiftY = Point[0] - Bound.Center[0], Point[1] - Bound.Center[1]
    Middle = ShiftX * StepX + ShiftY * StepY
    Spread = Middle * Middle - (ShiftX * ShiftX + ShiftY * ShiftY - Bound.Radius**2)
    if Spread <= 0:
        return 0
    Roots = (-Middle - SquareRoot(Spread), -Middle + SquareRoot(Spread))
    return sum(
        1
        for Reach in Roots
        if Reach > 0
        and IsOnSweep(
            ArcTangent(ShiftY + Reach * StepY, ShiftX + Reach * StepX),
            Bound.Opening,
            Bound.Sweep,
        )
    )


# the flat cover decision must stay consistent so projected boundaries retain their intended visibility and geometry
def IsFlatCover(Shape: FlatFace, Point: KPointTriple, Sight: KPointTriple) -> bool:
    Facing = DotProduct(Sight, Shape.Normal)
    if abs(Facing) < KFlatGap:
        return False
    Reach = DotProduct(Minus(Shape.Origin, Point), Shape.Normal) / Facing
    if Reach <= KReach:
        return False
    Offset = Minus(Combine(Point, (Reach, Sight)), Shape.Origin)
    OnPlane = (DotProduct(Offset, Shape.XAxis), DotProduct(Offset, Shape.YAxis))
    if any(BorderGap(Bound, OnPlane) < KEdgeGap for Bound in Shape.Bounds):
        return False
    return sum(CrossCount(Bound, OnPlane) for Bound in Shape.Bounds) % 2 == 1


# the round reaches contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def RoundReaches(
    Shape: RoundFace, Point: KPointTriple, Sight: KPointTriple
) -> list[float]:
    Offset = Minus(Point, Shape.Origin)
    Height, Climb = DotProduct(Offset, Shape.Along), DotProduct(Sight, Shape.Along)
    Radial = Minus(Offset, Scaled(Shape.Along, Height))
    Drift = Minus(Sight, Scaled(Shape.Along, Climb))
    Width = Shape.Radius + Shape.Slope * Height
    Square = DotProduct(Drift, Drift) - (Shape.Slope * Climb) ** 2
    Linear = 2 * (DotProduct(Radial, Drift) - Shape.Slope * Width * Climb)
    Constant = DotProduct(Radial, Radial) - Width * Width
    if abs(Square) < KFlatGap:
        return [] if abs(Linear) < KFlatGap else [-Constant / Linear]
    Spread = Linear * Linear - 4 * Square * Constant
    if Spread < 0:
        return []
    Rooted = SquareRoot(Spread)
    return [(-Linear - Rooted) / (2 * Square), (-Linear + Rooted) / (2 * Square)]


# the inside round decision must stay consistent so projected boundaries retain their intended visibility and geometry
def IsInsideRound(Shape: RoundFace, Point: KPointTriple) -> bool:
    Offset = Minus(Point, Shape.Origin)
    Height = DotProduct(Offset, Shape.Along)
    Width = Shape.Radius + Shape.Slope * Height
    if Width < 0:
        return False
    Angle = TurnAngle(Offset, Shape.XAxis, Shape.YAxis)
    Above = 0
    for Bound in Shape.Rings:
        if IsOnSweep(Angle, Bound.Opening, Bound.Sweep):
            if abs(Bound.Height - Height) < KEdgeGap:
                return False
            Above += int(Bound.Height > Height)
    for SeamItem in Shape.Seams:
        Apart = abs(
            (Angle - SeamItem.Angle + KFullTurn / 2) % KFullTurn - KFullTurn / 2
        )
        if Apart * Width < KEdgeGap and SeamItem.Lowest <= Height <= SeamItem.Highest:
            return False
    return Above % 2 == 1


# the hidden decision must stay consistent so projected boundaries retain their intended visibility and geometry
def IsHidden(Shape: SolidShape, Point: KPointTriple, Sight: KPointTriple) -> bool:
    if any(IsFlatCover(Planar, Point, Sight) for Planar in Shape.Flats):
        return True
    return any(
        IsInsideRound(Round, Combine(Point, (Reach, Sight)))
        for Round in Shape.Rounds
        for Reach in RoundReaches(Round, Point, Sight)
        if Reach > KReach
    )
