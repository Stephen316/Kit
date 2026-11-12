from math import hypot as Hypot, isclose as IsClose

from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.topology.BrepMath import IsFiniteFrame
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector

# the sketch basis and the prism direction must agree within floating point frame accuracy
KFrameAccuracy = 1e-9


# a right handed rigid frame preserves physical prism area and depth
def CheckPrismFrame(FrameValue: Transform) -> None:
    if not IsFiniteFrame(FrameValue):
        raise ValueError("Extrude prism requires a finite frame")
    AxisX, AxisY, AxisZ = FrameValue.x_axis, FrameValue.y_axis, FrameValue.z_axis
    Normal = CrossVector(AxisX, AxisY)
    if (
        any(
            not IsClose(
                DotVector(Basis, Basis), 1.0, abs_tol=KFrameAccuracy, rel_tol=0.0
            )
            for Basis in (AxisX, AxisY, AxisZ)
        )
        or Hypot(Normal.x - AxisZ.x, Normal.y - AxisZ.y, Normal.z - AxisZ.z)
        > KFrameAccuracy
        or abs(DotVector(AxisX, AxisY)) > KFrameAccuracy
    ):
        raise ValueError("Extrude prism requires a right handed orthonormal frame")


# every rim point uses the same sketch placement and axial station
def PlacePrismPoint(
    FrameValue: Transform, PointValue: PlaneVector, Height: float
) -> SpaceVector:
    return OffsetVector(
        OffsetVector(
            OffsetVector(FrameValue.origin, FrameValue.x_axis, PointValue.x),
            FrameValue.y_axis,
            PointValue.y,
        ),
        FrameValue.z_axis,
        Height,
    )
