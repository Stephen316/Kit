from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.MapPoint import MapPoint
from convert.formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.formats.Fusion.BrepCodec.Journal.Planar.TransformScale import (
    TransformScale,
)


def MapPlanarBody(Model: PlanarShell, Value: TransformNode) -> PlanarShell:
    Factor = TransformScale(Value)
    Points = tuple(MapPoint(Value, Point) for Point in Model.PointsCm)
    Volume = Model.VolumeCm3 * abs(Factor)
    if not IsFinite(Volume) or any(
        not IsFinite(Number) for Point in Points for Number in Point
    ):
        raise ValueError("Fusion body placement produces nonfinite geometry")
    Rings = (
        tuple(tuple(reversed(RingValue)) for RingValue in Model.Rings)
        if Factor < 0
        else Model.Rings
    )
    return ReplaceValue(
        Model, PointsCm=Points, Rings=Rings, VolumeCm3=Volume, Placement=Value
    )
