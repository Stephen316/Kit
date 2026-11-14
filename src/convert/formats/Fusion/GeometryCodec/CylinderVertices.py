from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildVertices() -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord("vertex", (EntityRef(CurveEdge), 0, EntityRef(PointIndex)))
        for CurveEdge, PointIndex in ((15, 24), (16, 25))
    )
