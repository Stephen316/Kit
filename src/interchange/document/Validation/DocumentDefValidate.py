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
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtValues import GetPlaneExt
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# the primary length can be omitted only when the saved termination is through all
def GetExtrudeErrs(
    StepValue: FeatureStep, Definition: ExtrudeFeature
) -> tuple[str, ...]:
    if Definition.length is None and Definition.end_condition != ExtrudeEnd.THROUGH_ALL:
        return (f"extrusion {StepValue.id} requires a primary length",)
    return ()


# a scoped definition carries design body references in addition to the actual extrusion
def GetScopeErrors(
    StepValue: FeatureStep, Definition: ScopedExtrude, BodyIds: set[str]
) -> tuple[str, ...]:
    ScopeIds = set(Definition.SelectedBodyIds) | set(Definition.AffectedBodyIds)
    Missing = sorted(ScopeIds - BodyIds)
    if Missing:
        return (f"scoped extrusion {StepValue.id} references missing bodies {Missing}",)
    return GetExtrudeErrs(StepValue, Definition.Extrusion)


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
    if isinstance(Definition, ScopedExtrude):
        return GetScopeErrors(StepValue, Definition, IdentitySets["bodies"])
    if isinstance(Definition, PlaneRevolve):
        return GetPlaneRevErrs(
            StepValue, Definition, Selections, IdentitySets["support_planes"]
        )
    if isinstance(Definition, AngularRevolve):
        return GetAngleRevErrs(StepValue, Definition, Selections, Params)
    if isinstance(Definition, DistanceExtrude):
        return GetDistExtErrs(StepValue, Definition, IdentitySets["sketches"], Params)
    if isinstance(Definition, ExtrudeFeature):
        return GetExtrudeErrs(StepValue, Definition)
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
