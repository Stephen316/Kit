from math import isclose as IsClose

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.PlaneBasis import (
    KUnitRows,
    IsOrthonormal,
    MatrixAxes,
)
from convert.adapters.solidworks.resolved.support.FaceFrame import FaceFrame
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the model to sketch pose must resolve the same world root and right handed normal
def PlaceCutFrame(Frame: FaceFrame) -> Transform:
    PoseValue = Frame["transform"]
    BasisValue = PoseValue["basis"]
    SavedAxes = MatrixAxes(KUnitRows if BasisValue is None else BasisValue)
    RequireArch(IsOrthonormal(SavedAxes), True, "orthonormal saved cut frame")
    First, Second, Normal = (SpaceVector(*Value) for Value in SavedAxes)
    Cross = CrossVector(First, Second)
    RequireArch(
        IsClose(DotVector(Cross, Normal), 1.0, abs_tol=1e-9),
        True,
        "right handed saved cut frame",
    )
    RequireArch(SavedAxes[2], Frame["normal_world"], "saved frame and cap normal agree")
    RootPoint = SpaceVector(*Frame["root_metres"])
    XShift, YShift, ZShift, Scale = PoseValue["translation_scale"]
    RequireArch(Scale, 1.0, "unit saved cut frame scale")
    RequireArch(
        all(
            IsClose(Shift, -DotVector(RootPoint, Direction), abs_tol=1e-9)
            for Shift, Direction in zip(
                (XShift, YShift, ZShift), (First, Second, Normal), strict=True
            )
        ),
        True,
        "saved transform reaches its own root",
    )
    return Transform(
        SpaceVector(RootPoint.x * 1000, RootPoint.y * 1000, RootPoint.z * 1000),
        First,
        Second,
        Normal,
    )
