from math import pi as KHalfCircle

from convert.formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.FrustumNumbers import (
    CheckReal,
    CheckSense,
    CheckVector,
)


def CheckRimFields(Frame: RimFrame) -> None:
    for Vector in (
        Frame.CenterCm,
        Frame.Normal,
        Frame.MajorVectorCm,
        Frame.PointCm,
        Frame.PlaneOriginCm,
        Frame.PlaneNormal,
        Frame.PlaneBasis,
    ):
        CheckVector(Vector)
    for Value in (Frame.Ratio, Frame.EdgeStart, Frame.EdgeEnd):
        CheckReal(Value)
    if Frame.Normal not in ((0.0, 0.0, 1.0), (0.0, 0.0, -1.0)) or Frame.Ratio != 1:
        raise ValueError("Unsupported frustum circular carrier")
    if Frame.MajorVectorCm[0] <= 0 or Frame.MajorVectorCm[1:] != (0.0, 0.0):
        raise ValueError("Unsupported frustum circular major vector")
    if (
        Frame.PlaneNormal != (0.0, 0.0, 1.0)
        or Frame.PlaneBasis != (1.0, 0.0, 0.0)
        or Frame.PlaneReverseV is not False
    ):
        raise ValueError("Unsupported frustum cap plane")
    if (Frame.EdgeStart, Frame.EdgeEnd) != (
        -KHalfCircle,
        KHalfCircle,
    ) or Frame.EdgeReverse is not False:
        raise ValueError("Unsupported frustum periodic edge interval or sense")
    if type(Frame.VertexIndex) is not int or Frame.VertexIndex not in (0, 2):
        raise ValueError("Unsupported frustum closed-edge vertex index")
    CheckSense(Frame.SideReverse)
    CheckSense(Frame.CapReverse)
