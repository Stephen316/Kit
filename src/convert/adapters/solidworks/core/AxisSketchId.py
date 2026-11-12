from convert.adapters.solidworks.resolved.Core import (
    REVOLUTION_AXIS_SKETCH as RevolutionAxisSketch,
)


def AxisSketchId(
    ProfileId: int | None, AxisSourceKind: str | None, AxisSourceId: int | None
) -> int | None:
    if AxisSourceKind is None:
        return ProfileId
    if AxisSourceKind == RevolutionAxisSketch:
        return AxisSourceId
    return None
