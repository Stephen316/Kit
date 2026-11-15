from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the points operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildPoints(
    Corners: tuple[tuple[float, float, float], ...],
) -> tuple[GeometryRecord, ...]:
    return tuple(MakeRecord("point", (Corner,)) for Corner in Corners)
