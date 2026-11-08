# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Callable
from functools import partial as BindArgs

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.AngleRevAttach import AttachAngleRev
from convert.formats.Fusion.Revolves.EdgeAxis.EdgeAxisPick import ReadEdgeAxis
from convert.formats.Fusion.Revolves.PlaneRevAttach import AttachPlaneRev
from convert.formats.Fusion.Revolves.RevolveAttach import AttachRevolve
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
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
    Frames: tuple[SupportPlane, ...],
    Sketches: tuple[Sketch, ...],
    LoadBody: Callable[[str], bytes],
) -> tuple[tuple[FeatureStep, ...], tuple[Selection, ...], tuple[Diagnostic, ...]]:
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
    SketchSteps = {
        StepValue.sketch_id: StepValue
        for StepValue in Steps
        if StepValue.sketch_id is not None
        and StepValue.provenance is not None
        and Owners[int(StepValue.provenance.native_id)].ClassGuid == KSketchFeature
    }
    SketchLinks = {
        int(SketchValue.provenance.native_id): (
            SketchValue,
            SketchSteps[SketchValue.id],
        )
        for SketchValue in Sketches
        if SketchValue.provenance is not None
    }
    ByFrame = {PlaneValue.id: PlaneValue for PlaneValue in Planes + Frames}
    BySketch = {SketchValue.id: SketchValue for SketchValue in Sketches}
    Projected: list[FeatureStep] = []
    Selections: list[Selection] = []
    Diagnostics: list[Diagnostic] = []
    for StepValue in Steps:
        if StepValue.kind == FeatureKind.KRevolution:
            try:
                StepValue, Picks, Issues = AttachRevolve(
                    BulkData,
                    Owners,
                    StepValue,
                    tuple(ByParam[ParamId] for ParamId in StepValue.parameter_ids),
                    PlaneLinks,
                    SketchLinks,
                    ByNative,
                )
            except ValueError as ErrorInfo:
                Diagnostics.append(
                    Diagnostic(
                        code="fusion.revolve.unsupported",
                        message=str(ErrorInfo),
                        entity_id=StepValue.id,
                        provenance=StepValue.provenance,
                    )
                )
            else:
                Selections.extend(Picks)
                Diagnostics.extend(Issues)
                Extent = StepValue.attributes.get("fusion.revolve.extent")
                try:
                    if Extent == "to_entity":
                        StepValue, AxisPick = AttachPlaneRev(
                            BulkData,
                            Owners,
                            StepValue,
                            Picks,
                            ByFrame,
                            BySketch.get(StepValue.sketch_id or ""),
                        )
                    else:
                        LoadEdge = (
                            BindArgs(
                                ReadEdgeAxis,
                                BulkData,
                                Owners,
                                StepValue,
                                ByNative,
                                ByFrame,
                                BySketch,
                                ByParam,
                                LoadBody,
                            )
                            if "fusion.revolve.axis_edge_source" in StepValue.attributes
                            else None
                        )
                        StepValue, AxisPick = AttachAngleRev(
                            BulkData,
                            Owners,
                            StepValue,
                            Picks,
                            ByFrame,
                            BySketch,
                            ByParam,
                            LoadEdge,
                        )
                except ValueError as ErrorInfo:
                    Diagnostics.append(
                        Diagnostic(
                            code=(
                                "fusion.revolve.plane_extent_unsupported"
                                if Extent == "to_entity"
                                else "fusion.revolve.angular_extent_unsupported"
                            ),
                            message=str(ErrorInfo),
                            entity_id=StepValue.id,
                            provenance=StepValue.provenance,
                        )
                    )
                else:
                    if all(PickValue.id != AxisPick.id for PickValue in Picks):
                        Selections.append(AxisPick)
        Projected.append(StepValue)
    return tuple(Projected), tuple(Selections), tuple(Diagnostics)
