from math import isfinite as IsFinite
from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.DistanceValues import DistExtValues
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtFrame import GetPlaneRise, KStationTolerance
from interchange.Features.PlaneExtInput import GetPlaneInputs
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# geometry consumers evaluate the current plane and owned controls without baking editable values
def GetPlaneExt(
    StepValue: FeatureStep,
    Definition: PlaneExtrude,
    Params: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Sketches: TypeMap[str, Sketch],
) -> DistExtValues:
    """Evaluate bounds in mm and return the profile-relative start as OffsetMm."""
    if (
        StepValue.kind != FeatureKind.KExtrusion
        or StepValue.operation != BooleanOp.KCreate
    ):
        raise ValueError("plane extrusion requires a create extrusion feature")
    Profile, Limit = GetPlaneInputs(
        StepValue, Definition.PlaneSelectionId, Selections, Frames, Sketches
    )
    Station = GetPlaneRise(Profile.transform, Limit.transform, Definition.Direction)
    Offset = GetDistParam(
        StepValue, Definition.OffsetParameterId, Params, ValueKind.KLength
    )
    if Offset < 0.0:
        raise ValueError("plane extrusion selected-plane offset must be nonnegative")
    TaperId = Definition.TaperParameterId
    if (
        TaperId is not None
        and GetDistParam(StepValue, TaperId, Params, ValueKind.KAngle) != 0.0
    ):
        raise ValueError("plane extrusion requires zero taper")
    LimitMm = Station + Offset
    LengthId = Definition.LengthParameterId
    if LengthId is None:
        Lower, Upper = 0.0, LimitMm
    else:
        Length = GetDistParam(StepValue, LengthId, Params, ValueKind.KLength)
        Lower, Upper = LimitMm, LimitMm + Length
    if not IsFinite(Upper) or Upper - Lower <= KStationTolerance:
        raise ValueError(
            "plane extrusion requires finite and positively separated limits"
        )
    return DistExtValues(Lower, Upper, Lower, 0.0, None)
