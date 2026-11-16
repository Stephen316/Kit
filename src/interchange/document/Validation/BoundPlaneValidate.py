from math import dist as Distance
from typing import Mapping as TypeMap

from interchange.Features.BoundPlaneValues import GetDatumFrame
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtAxis import GetExtVector
from interchange.Features.PlaneExtFrame import GetExtFrame
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# a current support frame must reproduce the bound construction controls
def CheckBoundPlane(
    StepValue: FeatureStep,
    Definition: BoundDatum,
    Parameters: TypeMap[str, Parameter],
    Frames: TypeMap[str, SupportPlane],
) -> None:
    PlaneValue = Frames.get(Definition.SupportPlaneId)
    if PlaneValue is None:
        raise ValueError("construction plane is missing its support frame")
    Actual = PlaneValue.transform
    _ = GetExtFrame(Actual)
    Expected = GetDatumFrame(StepValue, Definition, Parameters)
    PositionTol, DirectionTol = (
        (1e-8, 1e-9) if Definition.Method == "angle" else (1e-9, 1e-10)
    )
    if any(
        Distance(GetExtVector(First), GetExtVector(Other)) > TolValue
        for First, Other, TolValue in (
            (Expected.origin, Actual.origin, PositionTol),
            (Expected.x_axis, Actual.x_axis, DirectionTol),
            (Expected.y_axis, Actual.y_axis, DirectionTol),
            (Expected.z_axis, Actual.z_axis, DirectionTol),
        )
    ):
        raise ValueError("construction plane controls disagree with its support frame")
