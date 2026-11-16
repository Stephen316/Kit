from convert.Formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the timestamp operation needs a consistent construction rule so native topology can resolve its owning modeling operation
def MakeTimestamp(Owner: int, UnixMicros: float, NextLink: int) -> GeometryRecord:
    return MakeAttribute(
        Owner, "Timestamp_attrib_def", (1, float(UnixMicros)), NextLink=NextLink
    )
