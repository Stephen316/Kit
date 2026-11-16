from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismCarriers import CurveInterval
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionEdges import (
    RegionEdges,
    RegionVertices,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionRoots import (
    RegionRoots,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionUses import (
    RegionUses,
)
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region records contract needs a shared interpretation so supporting records retain their owning document relationships
def RegionRecords(
    Region: RegionFrame, Start: int, BodyRoot: int
) -> tuple[GeometryRecord, ...]:
    Curves = tuple(
        MakeRecord(
            "straight-curve",
            (
                Value.Curve.OriginCm,
                Value.Curve.DirectionCm,
                *CurveInterval(Value.Curve.LowerBound),
                *CurveInterval(Value.Curve.UpperBound),
            ),
        )
        for Value in Region.Edges
    )
    Points = tuple(MakeRecord("point", (Point,)) for Point in Region.CornersCm)
    return (
        *RegionRoots(Region, Start, BodyRoot),
        *RegionUses(Start),
        *RegionEdges(Region, Start),
        *RegionVertices(Region, Start),
        *Curves,
        *Points,
    )
