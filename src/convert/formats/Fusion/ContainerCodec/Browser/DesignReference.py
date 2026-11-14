from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef


def DesignReference(Design: DesignResult, RoleName: str | None) -> SegmentRef | None:
    return None if RoleName is None else SegmentRef(Design.Roles[RoleName], 0)
