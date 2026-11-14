from math import dist as Distance

from convert.formats.Fusion.BrepCodec.Prism.Validation.PrismNumbers import (
    CheckVector,
    DotPrism,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegionEdge import (
    CheckRegionEdge,
)


def CheckRegion(
    Value: RegionFrame, Corners: tuple[tuple[float, float, float], ...]
) -> None:
    for Values in (
        Value.CornersCm,
        Value.Edges,
        Value.VertexOwners,
        Value.CoedgeTags,
        Value.EdgeTags,
    ):
        if type(Values) is not tuple or len(Values) != 4:
            raise ValueError("Snapshot region requires four corners, edges and tags")
    for Point in Value.CornersCm:
        CheckVector(Point)
    if len(set(Value.CornersCm)) != 4 or any(
        not any(Distance(Point, Other) <= 1e-8 for Other in Corners[:4])
        for Point in Value.CornersCm
    ):
        raise ValueError("Snapshot region footprint disagrees with the solid")
    for Index, EdgeValue in enumerate(Value.Edges):
        Owner = Value.VertexOwners[Index]
        if type(Owner) is not int or Owner not in (Index, (Index - 1) % 4):
            raise ValueError("Snapshot vertex owner is not incident")
        StartPoint, EndPoint = Value.CornersCm[Index], Value.CornersCm[(Index + 1) % 4]
        if (
            sum(
                abs(LeftValue - Right) > 1e-8
                for LeftValue, Right in zip(StartPoint, EndPoint, strict=True)
            )
            != 1
        ):
            raise ValueError("Snapshot region contains a diagonal edge")
        CheckRegionEdge(EdgeValue, StartPoint, EndPoint)
    CheckSheetPlane(Value)


def CheckSheetPlane(Value: RegionFrame) -> None:
    Plane = Value.Plane
    for Vector in (Plane.OriginCm, Plane.Normal, Plane.Basis):
        CheckVector(Vector)
    if Plane.ReverseV is not False or Plane.Normal != (0.0, 0.0, 1.0):
        raise ValueError("Unsupported snapshot region plane orientation")
    if (
        not DotPrism(Plane.Basis, Plane.Basis) > 0
        or abs(DotPrism(Plane.Basis, Plane.Normal)) > 1e-9
    ):
        raise ValueError("Invalid snapshot region plane basis")
    if abs(Plane.OriginCm[2] - Value.CornersCm[0][2]) > 1e-8:
        raise ValueError("Snapshot plane origin leaves its profile")
