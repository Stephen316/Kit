from convert.adapters.solidworks.resolved.Core import (
    REVOLUTION_AXIS_SKETCH as RevolutionAxisSketch,
)


# the axis sketch id contract needs a shared interpretation so stream contents retain their geometry and feature relationships
def AxisSketchId(
    ProfileId: int | None, AxisSourceKind: str | None, AxisSourceId: int | None
) -> int | None:
    if AxisSourceKind is None:
        return ProfileId
    if AxisSourceKind == RevolutionAxisSketch:
        return AxisSourceId
    return None
