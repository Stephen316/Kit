# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from convert.formats.Fusion.NativePlane import KPlaneObject
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionRef import ReadEntityRef
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic

# selected construction axes can be identified before their geometry is projected
KAxisObject = "19031004-3AB6-4D13-ABBF-C51EE214688D"


# selected construction objects retain each role and its exact source record chain
def AttachTargets(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    AxisId: int,
    TargetIds: tuple[int, ...],
    PlaneLinks: dict[int, tuple[SupportPlane, FeatureStep]],
) -> tuple[FeatureStep, tuple[Diagnostic, ...]]:
    Origin = StepValue.provenance
    if Origin is None:
        raise ValueError("Missing Fusion Revolve provenance")
    FeatureId = int(Origin.native_id)
    Inputs = list(StepValue.input_feature_ids)
    Attributes = dict(StepValue.attributes)
    Evidence = list(Origin.spans)
    Diagnostics: list[Diagnostic] = []
    for RoleName, SelectionId in zip(
        ("axis", "target_one", "target_two"), (AxisId,) + TargetIds
    ):
        try:
            Descriptor, Terminal, EntityId = ReadEntityRef(
                BulkData, Owners, SelectionId, FeatureId
            )
            Source = Owners.get(EntityId)
            Expected = KAxisObject if RoleName == "axis" else KPlaneObject
            if Source is None or Source.ClassGuid != Expected:
                raise ValueError("Unsupported Fusion Revolve construction object")
            PlaneLink = PlaneLinks.get(EntityId)
            if RoleName != "axis" and (
                PlaneLink is None or PlaneLink[1].order >= StepValue.order
            ):
                raise ValueError("Fusion Revolve target plane is outside prior history")
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.revolve.selection_unsupported",
                    message=f"Fusion Revolve {RoleName}: {ErrorInfo}",
                    entity_id=StepValue.id,
                    provenance=Origin,
                )
            )
            continue
        Attributes[f"fusion.revolve.{RoleName}_object_id"] = EntityId
        if RoleName != "axis" and PlaneLink is not None:
            PlaneValue, PlaneStep = PlaneLink
            Attributes[f"fusion.revolve.{RoleName}_plane_id"] = PlaneValue.id
            if PlaneStep.id not in Inputs:
                Inputs.append(PlaneStep.id)
        for Identity in (SelectionId, Descriptor, Terminal, EntityId):
            for SpanValue in ParamOrigin(Owners[Identity]).spans:
                if SpanValue not in Evidence:
                    Evidence.append(SpanValue)
    return (
        Replace(
            StepValue,
            input_feature_ids=tuple(Inputs),
            provenance=Replace(Origin, spans=tuple(Evidence)),
            attributes=FreezeMapping(Attributes),
        ),
        tuple(Diagnostics),
    )
