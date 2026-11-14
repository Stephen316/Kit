from math import acos as ArcCosine
from math import atan2 as ArcTangent
from math import cos as Cosine
from math import hypot as Distance
from math import sin as SineOf

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
    Combine,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.FaceHits import IsOnSweep
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    KPointTriple,
    LinePath,
    RoundFace,
    SolidEdge,
    SolidShape,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Cross,
    DotProduct,
)

KSilhouetteTop = 0xFFFFFFFF
KFaceStride = 2048
KSeamGap = 1e-9
KSideGap = 1e-12


def AngleGap(First: float, Second: float) -> float:
    return abs((First - Second + KFullTurn / 2) % KFullTurn - KFullTurn / 2)


def SideAngles(Shape: RoundFace, Sight: KPointTriple) -> tuple[float, ...]:
    Climb = DotProduct(Sight, Shape.Along)
    Across = DotProduct(Sight, Shape.XAxis)
    Upward = DotProduct(Sight, Shape.YAxis)
    Spread = Distance(Across, Upward)
    if Spread < KSideGap:
        return ()
    Ratio = Shape.Slope * Climb / Spread
    if abs(Ratio) >= 1 - KSideGap:
        return ()
    Middle = ArcTangent(Upward, Across)
    Halfway = ArcCosine(Ratio)
    return ((Middle + Halfway) % KFullTurn, (Middle - Halfway) % KFullTurn)


def SideSpan(Shape: RoundFace, Angle: float) -> tuple[float, float] | None:
    if any(AngleGap(Angle, SeamItem.Angle) < KSeamGap for SeamItem in Shape.Seams):
        return None
    Heights: list[float] = []
    for Bound in Shape.Rings:
        BoundEnds = (Bound.Opening, Bound.Opening + Bound.Sweep)
        if (
            Bound.Sweep < KFullTurn
            and min(AngleGap(Angle, BoundEnd) for BoundEnd in BoundEnds) < KSeamGap
        ):
            return None
        if IsOnSweep(Angle, Bound.Opening, Bound.Sweep):
            Heights.append(Bound.Height)
    if not Heights:
        return None
    if len(Heights) != 2:
        raise ValueError("Authored DWG view silhouette crosses its face more than once")
    return (min(Heights), max(Heights))


def SideLine(Shape: RoundFace, Angle: float, Height: float) -> KPointTriple:
    Radial = Combine(
        (0.0, 0.0, 0.0), (Cosine(Angle), Shape.XAxis), (SineOf(Angle), Shape.YAxis)
    )
    Width = Shape.Radius + Shape.Slope * Height
    return Combine(Shape.Origin, (Height, Shape.Along), (Width, Radial))


def Silhouettes(Shape: SolidShape, Sight: KPointTriple) -> tuple[SolidEdge, ...]:
    Found: list[SolidEdge] = []
    for Round in Shape.Rounds:
        Facing = Cross(Sight, Round.Along)
        for Angle in SideAngles(Round, Sight):
            Extent = SideSpan(Round, Angle)
            if Extent is None:
                continue
            Radial = Combine(
                (0.0, 0.0, 0.0),
                (Cosine(Angle), Round.XAxis),
                (SineOf(Angle), Round.YAxis),
            )
            SideIndex = 0 if DotProduct(Radial, Facing) > 0 else 1
            Found.append(
                SolidEdge(
                    KSilhouetteTop - KFaceStride * Round.FaceIndex - SideIndex,
                    LinePath(
                        SideLine(Round, Angle, Extent[0]),
                        SideLine(Round, Angle, Extent[1]),
                    ),
                )
            )
    return tuple(Found)
