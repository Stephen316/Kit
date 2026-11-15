from dataclasses import dataclass as MakeDataClass
from math import cos as Cosine, hypot as Hypotenuse, pi as KHalfTurn, sin as SineOf
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound

# the plane point shape must stay shared so feature geometry uses one contract for compatible values
KPlanePoint: TypeAlias = tuple[float, float]

# the polynomial shape must stay shared so feature geometry uses one contract for compatible values
KPolynomial: TypeAlias = dict[tuple[int, int], float]

# gauss count needs one explicit bound so feature geometry cannot accept inconsistent resource or layout limits
KGaussCount = 32

# moment degree must remain consistent across callers so edge and face relationships survive parametric feature construction
KMomentDegree = 3

# newton limit needs one explicit bound so feature geometry cannot accept inconsistent resource or layout limits
KNewtonLimit = 100


# the legendre root contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def LegendreRoot(Count: int, Index: int) -> tuple[float, float]:
    Value = Cosine(KHalfTurn * (Index + 0.75) / (Count + 0.5))
    Slope = 1.0
    for _ in range(KNewtonLimit):
        Prior, Current = 1.0, Value
        for Order in range(2, Count + 1):
            Prior, Current = (
                Current,
                ((2 * Order - 1) * Value * Current - (Order - 1) * Prior) / Order,
            )
        Slope = Count * (Value * Current - Prior) / (Value * Value - 1.0)
        Correction = Current / Slope
        Value -= Correction
        if abs(Correction) < 1e-16:
            break
    return Value, 2.0 / ((1.0 - Value * Value) * Slope * Slope)


# gauss nodes must remain consistent across callers so edge and face relationships survive parametric feature construction
KGaussNodes = tuple(LegendreRoot(KGaussCount, Index) for Index in range(KGaussCount))


# the gauss span contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def GaussSpan(Lower: float, Upper: float) -> list[tuple[float, float]]:
    HalfWidth, Midpoint = (Upper - Lower) / 2.0, (Upper + Lower) / 2.0
    return [
        (Midpoint + HalfWidth * Abscissa, HalfWidth * Weight)
        for Abscissa, Weight in KGaussNodes
    ]


# section piece needs an explicit state contract so edge and face relationships survive parametric feature construction
@MakeDataClass(frozen=True, slots=True)
class SectionPiece:
    Center: KPlanePoint | None
    Bounds: tuple[float, float]
    Radius: float
    Ends: tuple[KPlanePoint, KPlanePoint]


# the piece point contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def PiecePoint(Piece: SectionPiece, Value: float) -> tuple[KPlanePoint, KPlanePoint]:
    if Piece.Center is None:
        Start, Finish = Piece.Ends
        Delta = (Finish[0] - Start[0], Finish[1] - Start[1])
        return (Start[0] + Delta[0] * Value, Start[1] + Delta[1] * Value), Delta
    Lower, Upper = Piece.Bounds
    Angle = Lower + (Upper - Lower) * Value
    Scale = Piece.Radius * (Upper - Lower)
    Point = (
        Piece.Center[0] + Piece.Radius * Cosine(Angle),
        Piece.Center[1] + Piece.Radius * SineOf(Angle),
    )
    return Point, (0.0 - Scale * SineOf(Angle), Scale * Cosine(Angle))


# the line piece contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def LinePiece(Start: KPlanePoint, Finish: KPlanePoint) -> SectionPiece:
    return SectionPiece(None, (0.0, 1.0), 0.0, (Start, Finish))


# the arc piece contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def ArcPiece(
    Center: KPlanePoint, Radius: float, Bounds: tuple[float, float]
) -> SectionPiece:
    return SectionPiece(Center, Bounds, Radius, ((0.0, 0.0), (0.0, 0.0)))


# the piece operation needs one geometric convention so edge and face relationships survive parametric feature construction
def BlendPiece(Round: EdgeRound) -> SectionPiece:
    CapCm, WallCm = Round.CapCm, Round.WallCm
    if not Round.Rounded:
        return LinePiece((CapCm, 0.0), (0.0, WallCm))
    return ArcPiece((CapCm, CapCm), CapCm, (0.0 - KHalfTurn / 2.0, 0.0 - KHalfTurn))


# the section loop contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def SectionLoop(Round: EdgeRound) -> tuple[SectionPiece, ...]:
    return (
        LinePiece((0.0, 0.0), (Round.CapCm, 0.0)),
        BlendPiece(Round),
        LinePiece((0.0, Round.WallCm), (0.0, 0.0)),
    )


# the section moments contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def SectionMoments(Round: EdgeRound) -> KPolynomial:
    Moments: KPolynomial = {}
    for First in range(KMomentDegree + 1):
        for Second in range(KMomentDegree + 1 - First):
            Total = 0.0
            for Piece in SectionLoop(Round):
                for Value, Weight in GaussSpan(0.0, 1.0):
                    Point, Speed = PiecePoint(Piece, Value)
                    Leading = Point[0] ** (First + 1) / (First + 1)
                    Total += Weight * Leading * Point[1] ** Second * Speed[1]
            Moments[(First, Second)] = Total
    return Moments


# the piece weight contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def PieceWeight(Piece: SectionPiece, Scale: KPolynomial) -> float:
    Total = 0.0
    for Value, Weight in GaussSpan(0.0, 1.0):
        Point, Speed = PiecePoint(Piece, Value)
        Factor = sum(
            Amount * Point[0] ** Powers[0] * Point[1] ** Powers[1]
            for Powers, Amount in Scale.items()
        )
        Total += Weight * Factor * Hypotenuse(*Speed)
    return Total
