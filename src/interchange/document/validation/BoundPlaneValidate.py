# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import dist as Distance
from typing import Mapping as TypeMap

from interchange.features.BoundPlaneValues import GetConstructionFrame
from interchange.features.FeatureBoundPlane import BoundConstructionPlane
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtAxis import GetExtVector
from interchange.features.PlaneExtFrame import GetExtFrame
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# a current support frame must reproduce the bound construction controls
def CheckBoundPlane(
    StepValue: FeatureStep,
    Definition: BoundConstructionPlane,
    Parameters: TypeMap[str, Parameter],
    Frames: TypeMap[str, SupportPlane],
) -> None:
    PlaneValue = Frames.get(Definition.SupportPlaneId)
    if PlaneValue is None:
        raise ValueError("construction plane is missing its support frame")
    Actual = PlaneValue.transform
    GetExtFrame(Actual)
    Expected = GetConstructionFrame(StepValue, Definition, Parameters)
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
