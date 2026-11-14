from dataclasses import replace as Replaced
from math import cos as Cosine
from math import sin as SineOf

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
    Combine,
    Length,
    Minus,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    KEdgePath,
    KPointTriple,
    LinePath,
    RoundPath,
)

KWholeGap = 1e-9


def RoundPoint(Curve: RoundPath, Angle: float) -> KPointTriple:
    return Combine(
        Curve.Center,
        (Curve.Radius * Cosine(Angle), Curve.XAxis),
        (Curve.Radius * SineOf(Angle), Curve.YAxis),
    )


def PathPoint(Curve: KEdgePath, Param: float) -> KPointTriple:
    if isinstance(Curve, LinePath):
        return Combine(Curve.Start, (Param, Minus(Curve.Finish, Curve.Start)))
    return RoundPoint(Curve, Curve.Opening + Param * Curve.Sweep)


def PathTangent(Curve: KEdgePath, Param: float) -> KPointTriple:
    if isinstance(Curve, LinePath):
        return Minus(Curve.Finish, Curve.Start)
    Angle = Curve.Opening + Param * Curve.Sweep
    return Combine(
        (0.0, 0.0, 0.0),
        (-Curve.Radius * SineOf(Angle), Curve.XAxis),
        (Curve.Radius * Cosine(Angle), Curve.YAxis),
    )


def IsWhole(Curve: KEdgePath) -> bool:
    return isinstance(Curve, RoundPath) and abs(Curve.Sweep - KFullTurn) < KWholeGap


def PathLength(Curve: KEdgePath) -> float:
    if isinstance(Curve, LinePath):
        return Length(Minus(Curve.Finish, Curve.Start))
    return Curve.Radius * Curve.Sweep


def PathPiece(Curve: KEdgePath, Begin: float, Finish: float) -> KEdgePath:
    if isinstance(Curve, LinePath):
        return LinePath(PathPoint(Curve, Begin), PathPoint(Curve, Finish))
    return Replaced(
        Curve,
        Opening=(Curve.Opening + Begin * Curve.Sweep) % KFullTurn,
        Sweep=(Finish - Begin) * Curve.Sweep,
    )
