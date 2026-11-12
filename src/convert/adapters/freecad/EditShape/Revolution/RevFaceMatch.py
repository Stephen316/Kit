from math import hypot as Hypot, tan as Tangent

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsParallel,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Revolution.RevCarriers import KRevSurface
from convert.adapters.freecad.EditShape.Revolution.RevExpected import (
    RevExpected,
    RevFace,
)
from convert.adapters.freecad.EditShape.TrimGeometry import SurfaceSide
from convert.geometry.Opencascade import ApplyDirection, LocationPoint
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import (
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.models.VectorSpace import SpaceVector


# plane and rotary faces compare orientation independently of the native parameter basis
def IsRevCarrier(
    Expected: RevExpected,
    FaceValue: RevFace,
    Surface: KRevSurface,
    Matrix: tuple[float, ...],
    Sense: int,
) -> bool:
    Target = FaceValue.Surface
    if type(Surface) is not type(Target):
        return False
    Direction = Surface.normal if isinstance(Surface, PlaneSurface) else Surface.axis
    AxisValue = ApplyDirection(Matrix, Direction)
    Center = LocationPoint(Matrix, Surface.origin)
    Handedness = DotVector(
        CrossVector(Direction, Surface.reference_direction), SurfaceSide(Surface)
    )
    if isinstance(Surface, PlaneSurface) and isinstance(Target, PlaneSurface):
        return (
            IsParallel(AxisValue, Target.normal)
            and DotVector(AxisValue, Target.normal)
            * Handedness
            * Sense
            * FaceValue.Sense
            > 0.0
            and abs(DotVector(DeltaVector(Center, Target.origin), Target.normal))
            <= KPositionTolerance
        )
    if isinstance(Surface, (CylinderSurface, ConeSurface)) and isinstance(
        Target, (CylinderSurface, ConeSurface)
    ):
        return Handedness * Sense * FaceValue.Sense > 0.0 and IsRevSide(
            Expected, FaceValue, Surface, AxisValue, Center, Target
        )
    return False


# two circular stations establish radius and cone slope without relying on the seam phase
def IsRevSide(
    Expected: RevExpected,
    FaceValue: RevFace,
    Surface: CylinderSurface | ConeSurface,
    AxisValue: SpaceVector,
    Center: SpaceVector,
    Target: CylinderSurface | ConeSurface,
) -> bool:
    if (
        not IsParallel(AxisValue, Target.axis)
        or AxisOffset(Center, Target.origin, Target.axis) > KPositionTolerance
    ):
        return False
    NativeSlope = (
        Tangent(Surface.half_angle) if isinstance(Surface, ConeSurface) else 0.0
    )
    WantSlope = -Tangent(Target.half_angle) if isinstance(Target, ConeSurface) else 0.0
    if (
        abs(NativeSlope * DotVector(AxisValue, Target.axis) - WantSlope)
        > KAngleTolerance
    ):
        return False
    Orbits = tuple(
        Curve
        for LoopValue in FaceValue.Loops
        for EdgeId, _ in LoopValue
        if isinstance(
            Curve := Expected.Curves[Expected.Edges[EdgeId].curve_id], CircleCurve
        )
    )
    return len(Orbits) == 2 and all(
        IsOrbitRadius(Value, Surface.radius, Center, AxisValue, NativeSlope)
        and IsOrbitRadius(Value, Target.radius, Target.origin, Target.axis, WantSlope)
        for Value in Orbits
    )


# each orbit must lie on both the native and reconstructed radius functions
def IsOrbitRadius(
    Curve: CircleCurve,
    Radius: float,
    Center: SpaceVector,
    AxisValue: SpaceVector,
    Slope: float,
) -> bool:
    Axial = DotVector(DeltaVector(Curve.center, Center), AxisValue)
    return abs(Radius + Axial * Slope - Curve.radius) <= KPositionTolerance


# surface origins may slide along the same axis but may not shift off that line
def AxisOffset(
    First: SpaceVector, Second: SpaceVector, AxisValue: SpaceVector
) -> float:
    Offset = CrossVector(DeltaVector(First, Second), AxisValue)
    return Hypot(Offset.x, Offset.y, Offset.z)


# local offsets keep comparisons absolute across relocated solids
def DeltaVector(First: SpaceVector, Second: SpaceVector) -> SpaceVector:
    return SpaceVector(First.x - Second.x, First.y - Second.y, First.z - Second.z)
