from math import dist as Distance, isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Validation.PrismNumbers import (
    CheckVector,
    DotPrism,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import KFaceCorners
from convert.formats.Fusion.GeometryCodec.Prism.PrismPlanes import KFaceFrames


def CheckPrismPlane(Frame: PrismFrame, Index: int) -> None:
    Value = Frame.Planes[Index]
    for Vector in (Value.OriginCm, Value.Normal, Value.Basis):
        CheckVector(Vector)
    if Value.ReverseV is not False:
        raise ValueError("Reversed prism plane parameterization is unsupported")
    SignValue = -1.0 if Frame.FaceReverse[Index] else 1.0
    Expected = tuple(SignValue * AxisValue for AxisValue in KFaceFrames[Index][0])
    BasisNorm = DotPrism(Value.Basis, Value.Basis)
    if (
        Distance(Value.Normal, Expected) > 1e-9
        or not IsFinite(BasisNorm)
        or BasisNorm <= 0
    ):
        raise ValueError("Prism plane orientation disagrees with its face")
    if not abs(DotPrism(Value.Normal, Value.Basis)) <= 1e-9:
        raise ValueError("Prism plane basis is not perpendicular")
    Corner = Frame.CornersCm[KFaceCorners[Index][0]]
    Offset = (
        Corner[0] - Value.OriginCm[0],
        Corner[1] - Value.OriginCm[1],
        Corner[2] - Value.OriginCm[2],
    )
    if not abs(DotPrism(Offset, Value.Normal)) <= 1e-8:
        raise ValueError("Prism plane origin leaves its face")
