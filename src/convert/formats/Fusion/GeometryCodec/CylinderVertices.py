from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the vertices operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildVertices() -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord("vertex", (EntityRef(CurveEdge), 0, EntityRef(PointIndex)))
        for CurveEdge, PointIndex in ((15, 24), (16, 25))
    )
