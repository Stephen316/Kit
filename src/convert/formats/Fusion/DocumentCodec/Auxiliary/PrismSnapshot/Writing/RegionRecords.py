from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismCarriers import CurveInterval
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionEdges import (
    RegionEdges,
    RegionVertices,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionRoots import (
    RegionRoots,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionUses import (
    RegionUses,
)
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
