# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditExtScope import EditSketchInput, ReadSketchInput
from convert.formats.Fusion.Revolves.SketchAxis import KFrameGuid, KSketchGuid
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchBase, KSketchFeature
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.payloads.PayloadRoles import PayloadRole


# only two independent input sketches and their standalone solid may participate
def ReadAxisScope(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> tuple[EditSketchInput, EditSketchInput, DesignBody]:
    if (
        DocValue.source.format_id != "fusion.f3d"
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is None
        or DocValue.meshes
        or len(DocValue.bodies) != 1
        or len(DocValue.feature_timeline) != 3
        or len(DocValue.sketches) != 2
        or len(DocValue.support_planes) != 2
        or len(DocValue.selections) != 1
        or len(DocValue.configurations) != 1
        or any(Value.role != PayloadRole.KDocument for Value in DocValue.brep_payloads)
    ):
        raise ValueError(
            "FreeCAD editable sketch axis Revolve requires one independent solid"
        )
    CheckAxisHist(DocValue, FeatureValue)
    Inputs = ReadAxisInputs(DocValue)
    Profile, AxisInput = tuple(
        Inputs[Identity] for Identity in FeatureValue.input_feature_ids
    )
    if (
        Profile.SketchValue.id != FeatureValue.sketch_id
        or AxisInput.SketchValue.id == Profile.SketchValue.id
        or AxisInput.PlaneValue.id == Profile.PlaneValue.id
        or AxisInput.PlaneValue.attributes.get("fusion.component_object_id")
        != Profile.PlaneValue.attributes.get("fusion.component_object_id")
    ):
        raise ValueError("FreeCAD editable sketch axis inputs are not independent")
    return Profile, AxisInput, DocValue.bodies[0]


# exact active history keeps the selected sketch axis ahead of its sole consumer
def CheckAxisHist(DocValue: CadDocument, FeatureValue: FeatureStep) -> None:
    (Config,) = DocValue.configurations
    First, Second, Final = DocValue.feature_timeline
    if (
        not Config.active
        or Config.parent_id
        or Config.overrides
        or Config.suppressed_feature_ids
        or Final != FeatureValue
        or Final.kind != FeatureKind.KRevolution
        or Final.operation != BooleanOp.KCreate
        or Final.suppressed
        or Final.configuration_states
        or Final.attributes.get("fusion.state_known") is not True
        or Final.attributes.get("fusion.rolled_back") is not False
        or not First.order < Second.order < Final.order
        or DocValue.bodies[0].final_feature_id != Final.id
        or len(Final.input_feature_ids) != 2
        or set(Final.input_feature_ids) != {First.id, Second.id}
    ):
        raise ValueError(
            "FreeCAD editable sketch axis Revolve source history is unresolved"
        )


# reciprocal typed source frames and sketch roots exclude flattened or generated input
def ReadAxisInputs(DocValue: CadDocument) -> dict[str, EditSketchInput]:
    Sketches = {Value.id: Value for Value in DocValue.sketches}
    Planes = {Value.id: Value for Value in DocValue.support_planes}
    Result: dict[str, EditSketchInput] = {}
    for StepValue in DocValue.feature_timeline[:-1]:
        Source = ReadSketchInput(StepValue, Sketches, Planes)
        if Source is None:
            raise ValueError("FreeCAD editable sketch axis support frame is unresolved")
        SketchValue, PlaneValue = Source.SketchValue, Source.PlaneValue
        Component = PlaneValue.attributes.get("fusion.component_object_id")
        SketchOrigin = SketchValue.provenance
        if (
            type(Component) is not int
            or Component <= 0
            or PlaneValue.attributes.get("fusion.coordinate_space") != "component"
            or SketchOrigin is None
            or SketchValue.id != f"fusion-sketch-{SketchOrigin.native_id}"
            or PlaneValue.id != f"fusion-sketch-frame-{SketchOrigin.native_id}"
            or any(
                Origin is None
                or Origin.adapter != "fusion.f3d"
                or tuple(SpanValue.record_kind for SpanValue in Origin.spans) != Kinds
                for Origin, Kinds in (
                    (StepValue.provenance, (KSketchFeature,)),
                    (SketchValue.provenance, (KSketchGuid,)),
                    (PlaneValue.provenance, (KFrameGuid, KSketchBase)),
                )
            )
        ):
            raise ValueError("FreeCAD editable sketch axis input provenance disagrees")
        Result[StepValue.id] = Source
    return Result
