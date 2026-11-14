from bisect import bisect_left as BisectLeft
from math import copysign as CopySign, sqrt as SquareRoot

from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


def CornerNormal(Value: ParaMesh, Ordinal: int) -> tuple[float, float, float]:
    if type(Ordinal) is not int or not 0 <= Ordinal < len(Value.Corners):
        raise ValueError("Fusion mesh corner ordinal exceeds topology")
    Offset = BisectLeft(Value.Overrides, Ordinal)
    if Offset < len(Value.Overrides) and Value.Overrides[Offset] == Ordinal:
        Normal = Value.Normals[len(Value.Positions) + Offset]
    else:
        Normal = Value.Normals[Value.Corners[Ordinal]]
    XAxis, YAxis = Normal.First, Normal.Second
    ZAxis = 1.0 - abs(XAxis) - abs(YAxis)
    if ZAxis < 0.0:
        XAxis, YAxis = CopySign(1.0 - abs(YAxis), XAxis), CopySign(
            1.0 - abs(XAxis), YAxis
        )
    Length = SquareRoot(XAxis * XAxis + YAxis * YAxis + ZAxis * ZAxis)
    return XAxis / Length, YAxis / Length, ZAxis / Length
