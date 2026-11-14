from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstEdge,
    KFirstPoint,
)


def PrismVertices(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "vertex",
            (
                EntityRef(KFirstEdge + Owner),
                int(Frame.Edges[Owner].EndCorner == Corner),
                EntityRef(KFirstPoint + Corner),
            ),
        )
        for Corner, Owner in enumerate(Frame.VertexOwners)
    )
