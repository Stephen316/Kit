from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFirstEdge,
    KFirstPoint,
)


def BuildVertices() -> tuple[GeometryRecord, ...]:
    Owners = {
        Corner: (KFirstEdge + Index, Endpoint)
        for Index, Corners in enumerate(KEdgeCorners)
        for Endpoint, Corner in enumerate(Corners)
    }
    return tuple(
        MakeRecord(
            "vertex",
            (
                EntityRef(Owners[Corner][0]),
                Owners[Corner][1],
                EntityRef(KFirstPoint + Corner),
            ),
        )
        for Corner in range(8)
    )
