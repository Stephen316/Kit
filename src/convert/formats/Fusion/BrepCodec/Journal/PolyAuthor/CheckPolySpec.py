from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.Polyhedron import Polyhedron
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


def CheckPolySpec(Model: Polyhedron) -> None:
    if type(Model.PointsMm) is not tuple or not 4 <= len(Model.PointsMm) <= 128:
        raise ValueError("Fusion polyhedron requires four to 128 immutable points")
    if type(Model.FaceLoops) is not tuple or not 4 <= len(Model.FaceLoops) <= 128:
        raise ValueError("Fusion polyhedron requires four to 128 immutable faces")
    for Point in Model.PointsMm:
        if type(Point) is not tuple or len(Point) != 3:
            raise ValueError("Fusion polyhedron requires immutable 3D vectors")
        if any(isinstance(Value, bool) or not IsFinite(Value) for Value in Point):
            raise ValueError("Fusion polyhedron coordinates must be finite numbers")
    if len(set(Model.PointsMm)) != len(Model.PointsMm):
        raise ValueError("Fusion polyhedron points must be distinct")
    UsedPoints: set[int] = set()
    for RingValue in Model.FaceLoops:
        if (
            type(RingValue) is not tuple
            or not 3 <= len(RingValue) <= 128
            or len(set(RingValue)) != len(RingValue)
        ):
            raise ValueError("Fusion polyhedron face requires distinct vertex ordinals")
        for Reference in RingValue:
            CheckInteger(
                Reference, "polyhedron vertex", Lower=0, Upper=len(Model.PointsMm) - 1
            )
            UsedPoints.add(Reference)
    if UsedPoints != set(range(len(Model.PointsMm))):
        raise ValueError("Fusion polyhedron contains unused vertices")
    CheckInteger(Model.EntityTag, "polyhedron body tag", Lower=0, Upper=(1 << 31) - 1)
