from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstEdge,
    KFirstPoint,
)


# the prism vertices contract needs a shared interpretation so profile topology remains connected to its extrusion history
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
