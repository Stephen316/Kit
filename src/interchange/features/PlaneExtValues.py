# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite
from typing import Mapping as TypeMap

from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceParam import GetDistParam
from interchange.features.DistanceValues import DistExtValues
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtFrame import GetPlaneRise, KStationTolerance
from interchange.features.PlaneExtInput import GetPlaneInputs
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


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
