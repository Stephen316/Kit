from struct import pack as PackData

from convert.formats.Fusion.RecordSpan import RecordSpan


# route keys must start at their typed slot and stay inside the primary record
def HasRouteKey(
    BulkData: bytes, OwnerSpan: RecordSpan, Offset: int, RouteKey: str
) -> bool:
    TextValue = PackData("<I", len(RouteKey)) + RouteKey.encode("utf-16le")
    Start = OwnerSpan.PayloadOffset + Offset
    return BulkData.startswith(TextValue, Start, OwnerSpan.EndOffset)
