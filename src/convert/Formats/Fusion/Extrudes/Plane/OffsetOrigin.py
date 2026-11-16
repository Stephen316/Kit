from convert.Formats.Fusion.ConstructionPlane.OriginDatum import ReadOriginDatum
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.geometry.Models.Transform import Transform


# offset callers keep the original frame contract while sharing validation with sketch supports
def ReadOffsetOrg(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OriginId: int,
    ComponentId: int,
) -> tuple[Transform, int]:
    _, Frame, ContainerId = ReadOriginDatum(BulkData, Owners, OriginId, ComponentId)
    return Frame, ContainerId
