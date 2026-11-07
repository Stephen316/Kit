# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchGeometry import GroupGeometry, ProjectGeom
from convert.formats.Fusion.Sketches.SketchPlacement import (
    KSketchBase,
    KSketchFeature,
    ResolveSketch,
)
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic


# selected timeline sketches link placement and local primitives into neutral documents
def ProjectSketches(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> tuple[
    tuple[SupportPlane, ...],
    tuple[Sketch, ...],
    tuple[FeatureStep, ...],
    tuple[Diagnostic, ...],
]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Bases: dict[int, list[RecordSpan]] = {}
    for SpanValue in Spans:
        if not SpanValue.IsPrimary and SpanValue.ClassGuid == KSketchBase:
            Bases.setdefault(SpanValue.ObjectId, []).append(SpanValue)
    Geometry = GroupGeometry(BulkData, Spans)
    Planes: list[SupportPlane] = []
    Sketches: list[Sketch] = []
    Steps: list[FeatureStep] = []
    Diagnostics: list[Diagnostic] = []
    for StepValue in History.Steps:
        Steps.append(StepValue)
        Origin = StepValue.provenance
        if Origin is None:
            continue
        Feature = Owners[int(Origin.native_id)]
        if Feature.ClassGuid != KSketchFeature:
            continue
        try:
            RootSpan, Frame = ResolveSketch(BulkData, Feature, Owners, Bases)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.sketch.placement",
                    message=str(ErrorInfo),
                    provenance=RecordOrigin(Feature),
                )
            )
            continue
        Entities, Issues = ProjectGeom(BulkData, Geometry.get(RootSpan.ObjectId, []))
        Diagnostics.extend(Issues)
        SketchId = f"fusion-sketch-{RootSpan.ObjectId}"
        Planes.append(Frame)
        Sketches.append(
            Sketch(
                id=SketchId,
                name=Frame.name,
                support_plane_id=Frame.id,
                entities=Entities,
                parameter_ids=StepValue.parameter_ids,
                suppressed=StepValue.suppressed,
                provenance=RecordOrigin(RootSpan),
                attributes=FreezeMapping({"fusion.geometry_partial": True}),
            )
        )
        Steps[-1] = Replace(StepValue, name=Frame.name, sketch_id=SketchId)
    return tuple(Planes), tuple(Sketches), tuple(Steps), tuple(Diagnostics)
