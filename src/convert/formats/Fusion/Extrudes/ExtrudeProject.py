# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Extrudes.ExtrudeAttach import AttachDistExt
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# unsupported extent layouts keep their existing timeline step and source evidence
def ProjectExtrudes(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Steps: tuple[FeatureStep, ...],
    Params: tuple[Parameter, ...],
    Frames: tuple[SupportPlane, ...],
    Sketches: tuple[Sketch, ...],
) -> tuple[tuple[FeatureStep, ...], tuple[Diagnostic, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    ByParam = {Param.id: Param for Param in Params}
    ByFrame = {Frame.id: Frame for Frame in Frames}
    SketchFrames = {
        SketchValue.id: ByFrame.get(SketchValue.support_plane_id)
        for SketchValue in Sketches
    }
    Projected: list[FeatureStep] = []
    Issues: list[Diagnostic] = []
    for StepValue in Steps:
        if StepValue.kind == FeatureKind.KExtrusion and StepValue.definition is None:
            try:
                StepValue = AttachDistExt(
                    BulkData,
                    Owners,
                    StepValue,
                    SketchFrames.get(StepValue.sketch_id or ""),
                    ByParam,
                )
            except ValueError as ErrorInfo:
                Issues.append(
                    Diagnostic(
                        code="fusion.extrude.unsupported",
                        message=str(ErrorInfo),
                        entity_id=StepValue.id,
                        provenance=StepValue.provenance,
                    )
                )
        Projected.append(StepValue)
    return tuple(Projected), tuple(Issues)
