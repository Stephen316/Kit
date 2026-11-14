from convert.formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeTimestamp(Owner: int, UnixMicros: float, NextLink: int) -> GeometryRecord:
    return MakeAttribute(
        Owner, "Timestamp_attrib_def", (1, float(UnixMicros)), NextLink=NextLink
    )
