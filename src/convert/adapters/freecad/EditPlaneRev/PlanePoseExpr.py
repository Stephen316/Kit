from math import atan2 as AtanTwo, degrees as Degrees, hypot as Hypot

from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.geometry.models.VectorSpace import SpaceVector


# native vector literals distinguish positions in millimetres from unit directions
def VectorExpr(Value: SpaceVector, Suffix: str = "") -> str:
    Fields = "; ".join(f"{Coord:.17g}{Suffix}" for Coord in (Value.x, Value.y, Value.z))
    return f"vector({Fields})"


# native expression rotations take an axis and angle instead of a quaternion
def RotationExpr(Quaternion: tuple[float, float, float, float]) -> str:
    First, Second, Third, Scalar = Quaternion
    Length = Hypot(First, Second, Third)
    if Length <= 1e-15:
        return "rotation(vector(0; 0; 1); 0 deg)"
    AxisValue = SpaceVector(First / Length, Second / Length, Third / Length)
    Angle = Degrees(2.0 * AtanTwo(Length, Scalar))
    return f"rotation({VectorExpr(AxisValue)}; {Angle:.17g} deg)"


# left composition rotates the entire zero frame about the source pivot
def PlanePoseExpr(
    AxisOrigin: SpaceVector,
    RotationAxis: SpaceVector,
    ZeroOrigin: SpaceVector,
    ZeroQuat: tuple[float, float, float, float],
    ParameterRef: str,
) -> str:
    Relative = OffsetVector(ZeroOrigin, AxisOrigin, -1.0)
    Pivot = VectorExpr(AxisOrigin, " mm")
    Offset = VectorExpr(Relative, " mm")
    AxisText = VectorExpr(RotationAxis)
    return (
        f"placement({Pivot}; rotation({AxisText}; {ParameterRef}))"
        f" * placement({Offset}; {RotationExpr(ZeroQuat)})"
    )
