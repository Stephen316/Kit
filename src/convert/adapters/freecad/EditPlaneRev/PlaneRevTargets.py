from collections.abc import Mapping
from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.adapters.freecad.EditExtScope import HasEditState
from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import (
    IsSameAngPlane,
    RotatePlane,
)
from convert.formats.Fusion.NativePlane import KPlaneFeature, KPlaneObject
from convert.formats.Fusion.PlaneCollection import KDatumCollection
from convert.formats.Fusion.Revolves.OriginAxis import KAxisGuid, KOriginGuid
from convert.formats.Fusion.Revolves.PlaneRevInputs import TargetPlanes
from convert.formats.Fusion.SelectionProxy import KSelectProxy
from convert.formats.Fusion.SelectionRef import KSelectDesc, KSelectLeaf
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import KOriginZero, Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# final feature links identify targets independently from timeline and geometric sort order
def ReadPlanePicks(
    DocValue: CadDocument, FeatureValue: FeatureStep, Definition: PlaneRevolve
) -> tuple[Selection, tuple[tuple[Selection, SupportPlane], ...]]:
    PlaneIds = {Value.id: Value for Value in DocValue.support_planes}
    Picks = {Value.id: Value for Value in DocValue.selections}
    Targets = TargetPlanes(FeatureValue, DocValue.selections, PlaneIds)
    TargetIds = tuple(PickValue.id for PickValue, _ in Targets)
    PickIds = (Definition.AxisSelectionId, *TargetIds)
    Attrs = FeatureValue.attributes
    Count = len(TargetIds)
    if (
        TargetIds != Definition.PlaneSelectionIds
        or FeatureValue.selection_ids != PickIds
        or Picks.keys() != set(PickIds)
        or Attrs.get("fusion.revolve.sidedness")
        != ("one_sided" if Count == 1 else "two_sided")
        or type(Attrs.get("fusion.revolve.axis_selection_id")) is not int
        or type(Attrs.get("fusion.revolve.axis_object_id")) is not int
        or Definition.AxisSelectionId
        != f"fusion-selection-{Attrs['fusion.revolve.axis_selection_id']}-axis"
        or Definition.AxisOrigin != KOriginZero
    ):
        raise ValueError("FreeCAD editable plane Revolve axis or target links disagree")
    AxisPick = Picks[Definition.AxisSelectionId]
    Origin = AxisPick.provenance
    AxisName = AxisPick.query.get("axis")
    if (
        AxisPick.path
        or AxisName not in ("X", "Y", "Z")
        or AxisPick.query != {"kind": "component_origin_axis", "axis": AxisName}
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != str(Attrs["fusion.revolve.axis_selection_id"])
        or tuple(SpanValue.record_kind for SpanValue in Origin.spans)
        != (KSelectProxy, KSelectDesc, KSelectLeaf, KAxisGuid, KOriginGuid)
    ):
        raise ValueError("FreeCAD editable plane Revolve origin axis is unresolved")
    return AxisPick, Targets


# selected plane geometry and its history feature must retain exact reciprocal evidence
def ReadTargetStep(
    FeatureValue: FeatureStep,
    Steps: dict[int, FeatureStep],
    PickValue: Selection,
    PlaneValue: SupportPlane,
    Index: int,
) -> FeatureStep:
    RoleName = ("target_one", "target_two")[Index]
    Attrs = FeatureValue.attributes
    TargetIds = Attrs["fusion.revolve.target_selection_ids"]
    PathValue = PickValue.path[0]
    PickOrigin, Origin = PickValue.provenance, PlaneValue.provenance
    if (
        PickValue.query
        or PathValue.subelement
        or PickOrigin is None
        or PickOrigin.adapter != "fusion.f3d"
        or PickValue.id != f"fusion-selection-{PickOrigin.native_id}-{RoleName}"
        or not IsObjectTuple(TargetIds)
        or Index >= len(TargetIds)
        or TargetIds[Index] != int(PickOrigin.native_id)
        or tuple(SpanValue.record_kind for SpanValue in PickOrigin.spans)
        != (KSelectProxy, KSelectDesc, KSelectLeaf, KPlaneObject)
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or len(Origin.spans) < 2
        or Origin.spans[0] != PickOrigin.spans[-1]
        or Origin.spans[1].record_kind != KPlaneFeature
        or Attrs.get(f"fusion.revolve.{RoleName}_object_id") != int(Origin.native_id)
        or Attrs.get(f"fusion.revolve.{RoleName}_plane_id") != PlaneValue.id
        or PlaneValue.id != f"fusion-plane-{Origin.native_id}"
        or PlaneValue.attributes.get("fusion.cached_plane_mode") != 2
        or PlaneValue.attributes.get("fusion.coordinate_space") != "component"
        or PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
    ):
        raise ValueError("FreeCAD editable plane Revolve selected datum is unresolved")
    FeatureId = PlaneValue.attributes["fusion.feature_object_id"]
    if type(FeatureId) is not int:
        raise ValueError(
            "FreeCAD editable plane Revolve native datum identity is invalid"
        )
    StepValue = Steps[FeatureId]
    StepOrigin = StepValue.provenance
    FinalOrigin = FeatureValue.provenance
    Definition = StepValue.definition
    if (
        StepValue.kind != FeatureKind.KReference
        or StepValue.operation is not None
        or (
            Definition is not None
            and (
                not isinstance(Definition, BoundDatum)
                or Definition.Method != "angle"
                or Definition.SupportPlaneId != PlaneValue.id
            )
        )
        or StepValue.input_feature_ids
        or StepValue.sketch_id is not None
        or not HasEditState(StepValue)
        or StepOrigin is None
        or StepOrigin.spans != (Origin.spans[1],)
        or FinalOrigin is None
        or not all(SpanValue in FinalOrigin.spans for SpanValue in PickOrigin.spans)
        or not any(
            SpanValue.record_kind == KDatumCollection and SpanValue in FinalOrigin.spans
            for SpanValue in Origin.spans
        )
    ):
        raise ValueError(
            "FreeCAD editable plane Revolve native datum history is unresolved"
        )
    return StepValue


# zero basis is immutable source evidence while angle and current cached frame can change
def ReadTargetBase(
    Proof: Mapping[str, object],
    AxisPick: Selection,
    PlaneValue: SupportPlane,
    SketchPlane: SupportPlane,
    FeatureValue: FeatureStep,
    Angle: float,
) -> Transform:
    AxisOrigin = AxisPick.provenance
    PlaneOrigin = PlaneValue.provenance
    if (
        AxisOrigin is None
        or PlaneOrigin is None
        or not all(SpanValue in PlaneOrigin.spans for SpanValue in AxisOrigin.spans[3:])
        or Proof.get("axis_object_id")
        != FeatureValue.attributes.get("fusion.revolve.axis_object_id")
        or Proof.get("component_id")
        != SketchPlane.attributes.get("fusion.component_object_id")
    ):
        raise ValueError(
            "FreeCAD editable plane Revolve datum and axis ownership disagree"
        )
    Pivot = ReadProofVec(Proof.get("zero_origin"))
    AxisValue = ReadProofVec(Proof.get("zero_axis"))
    AxisName = AxisPick.query["axis"]
    if AxisValue != SpaceVector(*(float(Label == AxisName) for Label in "XYZ")):
        raise ValueError("FreeCAD editable plane source axis name disagrees")
    Normal = ReadProofVec(Proof.get("zero_normal"))
    ZeroFrame = Transform(Pivot, AxisValue, CrossVector(Normal, AxisValue), Normal)
    CheckPrismFrame(ZeroFrame)
    if not IsClose(
        abs(DotVector(Normal, SketchPlane.transform.z_axis)),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ) or not IsSameAngPlane(RotatePlane(ZeroFrame, Angle), PlaneValue.transform):
        raise ValueError(
            "FreeCAD editable plane authored angle disagrees with its frame"
        )
    return ZeroFrame


# serialized construction evidence must have precise spatial coordinates
def ReadProofVec(Value: object) -> SpaceVector:
    if (
        not IsObjectTuple(Value)
        or len(Value) != 3
        or any(type(PartValue) is not float for PartValue in Value)
    ):
        raise ValueError("FreeCAD editable plane basis is unresolved")
    return SpaceVector(*CastValue(tuple[float, float, float], Value))
