from typing import cast as CastValue
from math import dist as Distance
from sys import float_info as FloatInfo

from convert.geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.geometry.Revolve.SweepInput import CheckSweepFrame
from convert.geometry.Revolve.SweepMetrics import MeasureFullTurn
from convert.geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform


# capped circular extrusions reuse exact periodic topology and analytic solid measures
def BuildCircular(
    BodyId: str,
    FrameValue: Transform,
    Profile: CircleGeometry,
    LowerMm: float,
    UpperMm: float,
    LowerRadius: float,
    UpperRadius: float,
) -> tuple[BrepModel, float, float, BoundingBox]:
    if not isinstance(CastValue(object, BodyId), str) or not BodyId.strip():
        raise ValueError("Circular extrusion requires a design body identity")
    Dimensions = (
        Profile.center.x,
        Profile.center.y,
        Profile.radius,
        LowerMm,
        UpperMm,
        LowerRadius,
        UpperRadius,
    )
    if not all(
        type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
        for Value in Dimensions
    ) or not (
        LowerMm < UpperMm and min(Profile.radius, LowerRadius, UpperRadius) > 0.0
    ):
        raise ValueError(
            "Circular extrusion requires finite ordered heights and positive radii"
        )
    Origin, Radial, Tangent, AxisValue = (
        FrameValue.origin,
        FrameValue.x_axis,
        FrameValue.y_axis,
        FrameValue.z_axis,
    )
    CheckSweepFrame(Origin, AxisValue, Radial)
    Cross = CrossVector(AxisValue, Radial)
    if (
        not Distance((Cross.x, Cross.y, Cross.z), (Tangent.x, Tangent.y, Tangent.z))
        <= 1e-9
    ):
        raise ValueError("Circular extrusion profile frame must be right handed")
    Center = OffsetVector(
        OffsetVector(Origin, Radial, Profile.center.x), Tangent, Profile.center.y
    )
    Meridian = (
        (0.0, LowerMm),
        (LowerRadius, LowerMm),
        (UpperRadius, UpperMm),
        (0.0, UpperMm),
    )
    Volume, AreaValue, Bounds = MeasureFullTurn(Meridian, Center, AxisValue, Radial)
    return (
        BuildFullSweep(BodyId, Meridian, Center, AxisValue, Radial),
        Volume,
        AreaValue,
        Bounds,
    )
