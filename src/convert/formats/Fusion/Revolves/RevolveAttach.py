# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace
from math import isclose as IsClose

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolveRead import ReadRevInputs
from convert.formats.Fusion.Revolves.RevolveTargets import AttachTargets
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# the feature must own the exact binding and dimensional value for each control
def FindRevAngle(
    Params: tuple[Parameter, ...], BindingId: int, RoleName: str
) -> Parameter:
    Matches = tuple(
        ParamValue
        for ParamValue in Params
        if ParamValue.attributes.get("fusion.binding_id") == BindingId
        and ParamValue.attributes.get("fusion.native_role") == RoleName
        and ParamValue.value.kind == ValueKind.KAngle
        and ParamValue.value.unit == "rad"
        and type(ParamValue.value.value) is float
    )
    if len(Matches) != 1:
        raise ValueError(f"Missing or ambiguous Fusion Revolve {RoleName} binding")
    return Matches[0]


# signed native angles and entity selections retain their distinct edit intent
def AttachRevolve(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    FeatureParams: tuple[Parameter, ...],
    PlaneLinks: dict[int, tuple[SupportPlane, FeatureStep]],
    SketchLinks: dict[int, tuple[Sketch, FeatureStep]],
    FeatureLinks: dict[int, FeatureStep],
) -> tuple[FeatureStep, tuple[Selection, ...], tuple[Diagnostic, ...]]:
    Origin = StepValue.provenance
    if Origin is None:
        raise ValueError("Missing Fusion Revolve provenance")
    SpanValue = Owners[int(Origin.native_id)]
    Inputs = ReadRevInputs(BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset])
    Along = FindRevAngle(FeatureParams, Inputs.AlongId, "AlongAngle")
    Against = (
        None
        if Inputs.AgainstId is None
        else FindRevAngle(FeatureParams, Inputs.AgainstId, "AgainstAngle")
    )
    if Inputs.SideMode == "symmetric" and (
        Against is None
        or not IsClose(
            float(Along.value.value), float(Against.value.value), abs_tol=1e-10
        )
    ):
        raise ValueError("Fusion Revolve symmetric angle bindings disagree")
    Updated = Replace(
        StepValue,
        attributes=FreezeMapping(
            {
                **StepValue.attributes,
                "fusion.revolve.operation": Inputs.Operation,
                "fusion.revolve.extent": Inputs.ExtentKind,
                "fusion.revolve.sidedness": Inputs.SideMode,
                "fusion.revolve.project_axis": Inputs.IsProjected,
                "fusion.revolve.solid": Inputs.IsSolid,
                "fusion.revolve.along_parameter_id": Along.id,
                "fusion.revolve.along_active": Inputs.ExtentKind == "angle",
                "fusion.revolve.against_parameter_id": (
                    Against.id if Against is not None else None
                ),
                "fusion.revolve.axis_selection_id": Inputs.AxisId,
                "fusion.revolve.target_selection_ids": Inputs.TargetIds,
            }
        ),
    )
    return AttachTargets(
        BulkData,
        Owners,
        Updated,
        Inputs.AxisId,
        Inputs.TargetIds,
        PlaneLinks,
        SketchLinks,
        FeatureLinks,
    )
