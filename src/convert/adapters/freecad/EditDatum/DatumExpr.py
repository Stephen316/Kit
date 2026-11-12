from convert.adapters.freecad.EditPlaneRev.PlanePoseExpr import (
    PlanePoseExpr,
    RotationExpr,
)
from interchange.features.FeatureBoundPlane import BoundDatum


# a whole placement expression preserves the reference basis and the signed live control
def DatumPoseExpr(
    Definition: BoundDatum,
    ZeroQuat: tuple[float, float, float, float],
    ParamRef: str,
) -> str:
    Frame = Definition.ReferenceFrame
    if Definition.Method == "angle":
        return PlanePoseExpr(
            Frame.origin, Frame.x_axis, Frame.origin, ZeroQuat, ParamRef
        )
    Origin = Frame.origin
    Normal = Frame.z_axis
    Coordinates = "; ".join(
        f"{BaseValue:.17g} mm + ({AxisValue:.17g}) * {ParamRef}"
        for BaseValue, AxisValue in (
            (Origin.x, Normal.x),
            (Origin.y, Normal.y),
            (Origin.z, Normal.z),
        )
    )
    return f"placement(vector({Coordinates}); {RotationExpr(ZeroQuat)})"
