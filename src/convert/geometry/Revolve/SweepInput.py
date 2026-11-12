from math import isclose as IsClose, tau as FullTurn

from convert.geometry.Revolve.SweepProfile import MeridianSense
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.geometry.models.VectorSpace import SpaceVector


# strict convexity gives a single outward sense to every lateral face
def OrientMeridian(
    Meridian: tuple[tuple[float, float], ...], *, AllowAxis: bool = False
) -> tuple[tuple[float, float], ...]:
    Winding = MeridianSense(Meridian, Strict=True, AllowAxis=AllowAxis)
    return Meridian if Winding > 0 else Meridian[:1] + Meridian[:0:-1]


# finite orthonormal frames and open angular ranges avoid collapsed sweeps
def CheckSweepInput(
    BodyId: str,
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    StartRadians: float,
    EndRadians: float,
) -> None:
    if not BodyId:
        raise ValueError("Revolve body identity is required")
    CheckSweepFrame(AxisOrigin, AxisDirection, Radial)
    SpanValue = EndRadians - StartRadians
    if not 0.0 < SpanValue < FullTurn:
        raise ValueError("Revolve solid requires a positive partial turn")


# partial and complete sweeps share the same source frame qualification
def CheckSweepFrame(
    AxisOrigin: SpaceVector, AxisDirection: SpaceVector, Radial: SpaceVector
) -> None:
    if not IsFiniteSpace(AxisOrigin):
        raise ValueError("Revolve axis origin must be finite")
    if (
        not IsClose(
            DotVector(AxisDirection, AxisDirection), 1.0, abs_tol=1e-9, rel_tol=0.0
        )
        or not IsClose(DotVector(Radial, Radial), 1.0, abs_tol=1e-9, rel_tol=0.0)
        or not IsClose(DotVector(AxisDirection, Radial), 0.0, abs_tol=1e-9, rel_tol=0.0)
    ):
        raise ValueError("Revolve axis and radial directions must be orthonormal")
