# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditExtDepth import IsLiteralParam
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.validation.BoundPlaneValidate import CheckBoundPlane
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBoundPlane import BoundConstructionPlane
from interchange.payloads.PayloadRoles import PayloadRole


# an independent datum timeline has no solid consumer or unsupported configuration state
def ReadDatumPlan(DocValue: CadDocument) -> dict[str, BoundConstructionPlane]:
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
    Result: dict[str, BoundConstructionPlane] = {}
    for Step in Steps:
        Definition = Step.definition
        if (
            not isinstance(Definition, BoundConstructionPlane)
            or Step.input_feature_ids
            or Step.sketch_id is not None
            or Step.operation is not None
            or Step.selection_ids
            or Step.suppressed
            or Step.configuration_states
            or Step.attributes.get("fusion.rolled_back") is True
            or (
                DocValue.source.format_id == "fusion.f3d"
                and (
                    Step.attributes.get("fusion.state_known") is not True
                    or Step.attributes.get("fusion.rolled_back") is not False
                )
            )
        ):
            return {}
        BoundIds = {Definition.ScalarParameterId, Definition.OffsetParameterId}
        Plane = Frames.get(Definition.SupportPlaneId)
        if (
            len(BoundIds) != 2
            or len(Step.parameter_ids) != 2
            or set(Step.parameter_ids) != BoundIds
            or not BoundIds <= Parameters.keys()
            or BoundIds & UsedParams
            or Plane is None
            or Plane.id in UsedPlanes
            or Plane.offset_parameter_id is not None
            or Plane.support_selection_id is not None
            or "freecad" in Plane.attributes
            or not all(IsLiteralParam(Parameters[Identity]) for Identity in BoundIds)
        ):
            return {}
        try:
            CheckBoundPlane(Step, Definition, Parameters, Frames)
        except ValueError:
            return {}
        UsedParams.update(BoundIds)
        UsedPlanes.add(Plane.id)
        Result[Step.id] = Definition
    if (
        len(Result) != len(Steps)
        or len(UsedParams) != len(DocValue.parameters)
        or len(UsedPlanes) != len(DocValue.support_planes)
    ):
        return {}
    return Result
