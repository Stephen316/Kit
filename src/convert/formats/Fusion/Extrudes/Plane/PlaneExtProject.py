# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import ReadAsmScopes
from convert.formats.Fusion.Extrudes.Plane.PlaneExtAttach import AttachPlaneExt
from convert.formats.Fusion.Extrudes.Plane.PlaneExtRead import ReadPlaneExt
from convert.formats.Fusion.Extrudes.Plane.PlaneExtScope import CheckPlaneScope
from convert.formats.Fusion.NativePlane import KPlaneObject
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtValues import GetPlaneExt
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# selected plane features are typed only after native and neutral operands both qualify
def ProjectPlaneExts(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    OwnerId: int,
    Steps: tuple[FeatureStep, ...],
    Params: tuple[Parameter, ...],
    Frames: tuple[SupportPlane, ...],
    Sketches: tuple[Sketch, ...],
) -> tuple[tuple[FeatureStep, ...], tuple[Selection, ...], tuple[Diagnostic, ...]]:
    if not any(
        Step.kind == FeatureKind.KExtrusion and Step.definition is None
        for Step in Steps
    ):
        return Steps, (), ()
    Owners = {Span.ObjectId: Span for Span in Spans if Span.IsPrimary}
    ByNative = {
        int(Step.provenance.native_id): Step
        for Step in Steps
        if Step.provenance is not None
    }
    NativePlanes = {
        Identity: Plane
        for Plane in Frames
        if Plane.provenance is not None
        and (Identity := int(Plane.provenance.native_id)) in Owners
        and Owners[Identity].ClassGuid == KPlaneObject
    }
    if not NativePlanes:
        return Steps, (), ()
    ByStep = {Step.id: Step for Step in Steps}
    ByParam = {Param.id: Param for Param in Params}
    ByFrame = {Frame.id: Frame for Frame in Frames}
    BySketch = {SketchValue.id: SketchValue for SketchValue in Sketches}
    Scopes = None
    Updated = {}
    Selections = []
    Diagnostics = []
    for Identity, Step in ByNative.items():
        if Step.kind != FeatureKind.KExtrusion or Step.definition is not None:
            continue
        try:
            Native = ReadPlaneExt(BulkData, Owners, Identity, NativePlanes)
        except ValueError:
            continue
        try:
            PlaneStep = ByNative.get(Native.PlaneFeatureId)
            SketchValue = BySketch.get(Step.sketch_id or "")
            FrameValue = (
                None
                if SketchValue is None
                else ByFrame.get(SketchValue.support_plane_id)
            )
            if PlaneStep is None or FrameValue is None:
                raise ValueError("Missing selected Fusion plane or source sketch frame")
            if Scopes is None:
                Scopes = ReadAsmScopes(BulkData, Owners, OwnerId, frozenset(ByNative))
            CheckPlaneScope(
                Step, Identity, PlaneStep, Native, FrameValue, ByStep, Scopes
            )
            StepValue, Pick = AttachPlaneExt(
                Step,
                Identity,
                Native,
                NativePlanes[Native.PlaneId],
                PlaneStep,
                ByParam,
                Owners,
            )
            Definition = StepValue.definition
            assert isinstance(Definition, PlaneExtrude)
            GetPlaneExt(
                StepValue, Definition, ByParam, {Pick.id: Pick}, ByFrame, BySketch
            )
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.extrude.plane_unsupported",
                    message=str(ErrorInfo),
                    entity_id=Step.id,
                    provenance=Step.provenance,
                )
            )
            continue
        Updated[Step.id] = StepValue
        Selections.append(Pick)
    return (
        tuple(Updated.get(Step.id, Step) for Step in Steps),
        tuple(Selections),
        tuple(Diagnostics),
    )
