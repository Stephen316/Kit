# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Mapping as TypeMap

from interchange.document.validation.AngleRevValidate import GetAngleRevErrs
from interchange.document.validation.BoundPlaneValidate import CheckBoundPlane
from interchange.document.validation.DistExtValidate import GetDistExtErrs
from interchange.document.validation.PlaneRevValidate import GetPlaneRevErrs
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.BoundScaleValues import GetScaleValues
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtValues import GetPlaneExt
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# supported editable definitions require checks beyond generic dependency validation
def GetDefErrors(
    StepValue: FeatureStep,
    IdentitySets: TypeMap[str, set[str]],
    Selections: TypeMap[str, Selection],
    Params: TypeMap[str, Parameter],
    Frames: TypeMap[str, SupportPlane],
    Sketches: TypeMap[str, Sketch],
) -> tuple[str, ...]:
    Definition = StepValue.definition
    if isinstance(Definition, PlaneRevolve):
        return GetPlaneRevErrs(
            StepValue, Definition, Selections, IdentitySets["support_planes"]
        )
    if isinstance(Definition, AngularRevolve):
        return GetAngleRevErrs(StepValue, Definition, Selections, Params)
    if isinstance(Definition, DistanceExtrude):
        return GetDistExtErrs(StepValue, Definition, IdentitySets["sketches"], Params)
    if isinstance(Definition, BoundDatum):
        try:
            CheckBoundPlane(StepValue, Definition, Params, Frames)
        except ValueError as ErrorInfo:
            return (f"construction plane {StepValue.id} is invalid: {ErrorInfo}",)
    if isinstance(Definition, BoundScale):
        try:
            _ = GetScaleValues(StepValue, Definition, Params, Selections)
        except ValueError as ErrorInfo:
            return (f"scale {StepValue.id} is invalid: {ErrorInfo}",)
    if isinstance(Definition, PlaneExtrude):
        try:
            _ = GetPlaneExt(StepValue, Definition, Params, Selections, Frames, Sketches)
        except ValueError as ErrorInfo:
            return (f"plane extrusion {StepValue.id} is invalid: {ErrorInfo}",)
    return ()
