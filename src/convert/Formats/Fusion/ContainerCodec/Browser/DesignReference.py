from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef


# the design reference contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def DesignReference(Design: DesignResult, RoleName: str | None) -> SegmentRef | None:
    return None if RoleName is None else SegmentRef(Design.Roles[RoleName], 0)
