# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.adapters.freecad.EditExtDepth import IsLiteralParam
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.validation.BoundPlaneValidate import CheckBoundPlane
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.payloads.PayloadRoles import PayloadRole


# an independent datum timeline has no solid consumer or unsupported configuration state
def ReadDatumPlan(DocValue: CadDocument) -> dict[str, BoundDatum]:
    Steps = DocValue.feature_timeline
    if (
        not Steps
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is not None
        or DocValue.bodies
        or DocValue.meshes
        or DocValue.sketches
        or DocValue.selections
        or any(
            Value.role != PayloadRole.KDocument
            or Value.format_id != DocValue.source.format_id
            for Value in DocValue.brep_payloads
        )
        or any(
            Value.overrides or Value.suppressed_feature_ids
            for Value in DocValue.configurations
        )
    ):
        return {}
    Parameters = {Value.id: Value for Value in DocValue.parameters}
    Frames = {Value.id: Value for Value in DocValue.support_planes}
    UsedParams: set[str] = set()
    UsedPlanes: set[str] = set()
    Result: dict[str, BoundDatum] = {}
    for StepValue in Steps:
        Definition = StepValue.definition
        if (
            not isinstance(Definition, BoundDatum)
            or StepValue.input_feature_ids
            or StepValue.sketch_id is not None
            or StepValue.operation is not None
            or StepValue.selection_ids
            or StepValue.suppressed
            or StepValue.configuration_states
            or StepValue.attributes.get("fusion.rolled_back") is True
            or (
                DocValue.source.format_id == "fusion.f3d"
                and (
                    StepValue.attributes.get("fusion.state_known") is not True
                    or StepValue.attributes.get("fusion.rolled_back") is not False
                )
            )
        ):
            return {}
        BoundIds = {Definition.ScalarParameterId, Definition.OffsetParameterId}
        Plane = Frames.get(Definition.SupportPlaneId)
        if (
            len(BoundIds) != 2
            or len(StepValue.parameter_ids) != 2
            or set(StepValue.parameter_ids) != BoundIds
            or not BoundIds <= Parameters.keys()
            or BoundIds & UsedParams
            or Plane is None
            or Plane.id in UsedPlanes
            or Plane.offset_parameter_id is not None
            or Plane.support_selection_id is not None
            or "freecad" in Plane.attributes
            or not all(
                IsLiteralParam(Parameters[Identity], AllowKit=True)
                for Identity in BoundIds
            )
        ):
            return {}
        try:
            CheckBoundPlane(StepValue, Definition, Parameters, Frames)
        except ValueError:
            return {}
        UsedParams.update(BoundIds)
        UsedPlanes.add(Plane.id)
        Result[StepValue.id] = Definition
    if (
        len(Result) != len(Steps)
        or len(UsedParams) != len(DocValue.parameters)
        or len(UsedPlanes) != len(DocValue.support_planes)
    ):
        return {}
    return Result
