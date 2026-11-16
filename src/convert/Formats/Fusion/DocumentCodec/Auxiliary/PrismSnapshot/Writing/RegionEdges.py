from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region edges contract needs a shared interpretation so supporting records retain their owning document relationships
def RegionEdges(Region: RegionFrame, Start: int) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "edge",
            (
                EntityRef(Start + 13 + Index),
                Value.LowerParam,
                EntityRef(Start + 13 + (Index + 1) % 4),
                Value.UpperParam,
                EntityRef(Start + 5 + Index),
                EntityRef(Start + 17 + Index),
                False,
                CountedText("unknown"),
            ),
        )
        for Index, Value in enumerate(Region.Edges)
    )


# the region vertices contract needs a shared interpretation so supporting records retain their owning document relationships
def RegionVertices(Region: RegionFrame, Start: int) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "vertex",
            (
                EntityRef(Start + 9 + Owner),
                int(Owner != Index),
                EntityRef(Start + 21 + Index),
            ),
        )
        for Index, Owner in enumerate(Region.VertexOwners)
    )
