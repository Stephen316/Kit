from typing import Mapping as TypeMap

from interchange.document.Validation.AngleRevValidate import GetAngleRevErrs
from interchange.document.Validation.BoundPlaneValidate import CheckBoundPlane
from interchange.document.Validation.DistExtValidate import GetDistExtErrs
from interchange.document.Validation.PlaneRevValidate import GetPlaneRevErrs
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.BoundScaleValues import GetScaleValues
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureBoundScale import BoundScale
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtValues import GetPlaneExt
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


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
