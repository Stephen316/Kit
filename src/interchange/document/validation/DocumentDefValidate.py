# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.document.validation.AngleRevValidate import GetAngleRevErrs
from interchange.document.validation.DistExtValidate import GetDistExtErrs
from interchange.document.validation.PlaneRevValidate import GetPlaneRevErrs
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.BoundScaleValues import GetScaleValues
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
    if isinstance(Definition, BoundScale):
        try:
            GetScaleValues(StepValue, Definition, Params, Selections)
        except ValueError as ErrorInfo:
            return (f"scale {StepValue.id} is invalid: {ErrorInfo}",)
    if isinstance(Definition, PlaneExtrude):
        try:
            GetPlaneExt(StepValue, Definition, Params, Selections, Frames, Sketches)
        except ValueError as ErrorInfo:
            return (f"plane extrusion {StepValue.id} is invalid: {ErrorInfo}",)
    return ()
