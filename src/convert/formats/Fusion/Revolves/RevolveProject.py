# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolveAttach import AttachRevolve
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# native controls are projected independently from profile geometry coverage
def ProjectRevolves(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Steps: tuple[FeatureStep, ...],
    Params: tuple[Parameter, ...],
    Planes: tuple[SupportPlane, ...],
) -> tuple[tuple[FeatureStep, ...], tuple[Diagnostic, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    ByParam = {ParamValue.id: ParamValue for ParamValue in Params}
    ByNative = {
        int(StepValue.provenance.native_id): StepValue
        for StepValue in Steps
        if StepValue.provenance is not None
    }
    PlaneLinks = {
        int(PlaneValue.provenance.native_id): (
            PlaneValue,
            ByNative[PlaneValue.attributes["fusion.feature_object_id"]],
        )
        for PlaneValue in Planes
        if PlaneValue.provenance is not None
    }
    Projected: list[FeatureStep] = []
    Diagnostics: list[Diagnostic] = []
    for StepValue in Steps:
        if StepValue.kind == FeatureKind.KRevolution:
            try:
                StepValue, Issues = AttachRevolve(
                    BulkData,
                    Owners,
                    StepValue,
                    tuple(ByParam[ParamId] for ParamId in StepValue.parameter_ids),
                    PlaneLinks,
                )
                Diagnostics.extend(Issues)
            except ValueError as ErrorInfo:
                Diagnostics.append(
                    Diagnostic(
                        code="fusion.revolve.unsupported",
                        message=str(ErrorInfo),
                        entity_id=StepValue.id,
                        provenance=StepValue.provenance,
                    )
                )
        Projected.append(StepValue)
    return tuple(Projected), tuple(Diagnostics)
